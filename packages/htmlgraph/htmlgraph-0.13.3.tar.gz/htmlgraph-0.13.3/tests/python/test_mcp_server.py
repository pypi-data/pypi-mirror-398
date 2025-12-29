from __future__ import annotations

import json
from pathlib import Path

from htmlgraph.graph import HtmlGraph
from htmlgraph.mcp_server import McpServer
from htmlgraph.models import Node


def _call(server: McpServer, method: str, params: dict | None = None, msg_id: int = 1):
    msg = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        msg["params"] = params
    resp = server.handle(msg)
    assert resp is not None
    return resp


def test_mcp_initialize_and_list_tools(tmp_path: Path):
    graph_dir = tmp_path / ".htmlgraph"
    server = McpServer(graph_dir=graph_dir)

    init = _call(server, "initialize", {"protocolVersion": "2024-11-05"})
    assert init["result"]["capabilities"]["tools"] == {}

    tools = _call(server, "tools/list")
    names = [t["name"] for t in tools["result"]["tools"]]
    assert names == ["log_event", "get_active_feature", "set_active_feature"]

    # Resources are optional, but Codex expects list endpoints to exist.
    resources = _call(server, "resources/list")
    assert "resources" in resources["result"]

    templates = _call(server, "resources/templates/list")
    assert templates["result"]["resourceTemplates"] == []


def test_mcp_log_event_writes_activity(tmp_path: Path):
    graph_dir = tmp_path / ".htmlgraph"
    server = McpServer(graph_dir=graph_dir)
    _call(server, "initialize", {"protocolVersion": "2024-11-05"})

    resp = _call(
        server,
        "tools/call",
        {
            "name": "log_event",
            "arguments": {"tool": "Bash", "summary": "Bash: echo hi", "files": ["a.txt"]},
        },
    )
    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert "session_id" in payload

    # Should have written at least one JSONL event file in graph_dir/events/
    events_dir = graph_dir / "events"
    assert events_dir.exists()
    assert list(events_dir.glob("*.jsonl"))


def test_mcp_log_event_uses_agent_scoped_session(tmp_path: Path):
    graph_dir = tmp_path / ".htmlgraph"

    # Create an active Claude session
    from htmlgraph.session_manager import SessionManager

    sm = SessionManager(graph_dir)
    sm.start_session(session_id="s-claude", agent="claude-code", title="t")

    # MCP server should not reuse claude session when default agent is codex
    server = McpServer(graph_dir=graph_dir, default_agent="codex")
    _call(server, "initialize", {"protocolVersion": "2024-11-05"})

    resp = _call(
        server,
        "tools/call",
        {"name": "log_event", "arguments": {"tool": "MCP", "summary": "test"}},
    )
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["session_id"] != "s-claude"


def test_mcp_set_active_feature_marks_primary(tmp_path: Path):
    graph_dir = tmp_path / ".htmlgraph"
    features_dir = graph_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)

    g = HtmlGraph(features_dir, auto_load=True)
    g.add(
        Node(
            id="feature-1",
            title="Feature 1",
            type="feature",
            status="todo",
            priority="high",
        )
    )

    server = McpServer(graph_dir=graph_dir)
    _call(server, "initialize", {"protocolVersion": "2024-11-05"})

    resp = _call(
        server,
        "tools/call",
        {"name": "set_active_feature", "arguments": {"feature_id": "feature-1"}},
    )
    assert resp["result"]["isError"] is False

    # Reload and verify primary flag set
    g2 = HtmlGraph(features_dir, auto_load=True)
    node = g2.get("feature-1")
    assert node is not None
    val = node.properties.get("is_primary")
    assert str(val).lower() in {"true", "1", "yes"}

    # Should have logged a high-signal activation event (agent defaults to mcp).
    events_dir = graph_dir / "events"
    paths = list(events_dir.glob("*.jsonl"))
    assert paths
    text = paths[0].read_text(encoding="utf-8").strip().splitlines()[-1]
    event = json.loads(text)
    assert event["tool"] == "FeatureActivate"
    assert event["agent"] == "mcp"
    assert event["feature_id"] == "feature-1"


def test_mcp_resources_read_roundtrip(tmp_path: Path):
    graph_dir = tmp_path / ".htmlgraph"
    repo_root = tmp_path
    (repo_root / "AGENTS.md").write_text("# Repository Guidelines\n", encoding="utf-8")

    server = McpServer(graph_dir=graph_dir)
    _call(server, "initialize", {"protocolVersion": "2024-11-05"})

    listed = _call(server, "resources/list")
    uris = [r["uri"] for r in listed["result"]["resources"]]
    assert "htmlgraph://file/AGENTS.md" in uris

    read = _call(server, "resources/read", {"uri": "htmlgraph://file/AGENTS.md"})
    contents = read["result"]["contents"]
    assert contents and contents[0]["mimeType"].startswith("text/")
    assert "Repository Guidelines" in contents[0]["text"]


def test_mcp_get_active_feature_autologs(tmp_path: Path):
    graph_dir = tmp_path / ".htmlgraph"
    features_dir = graph_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)

    g = HtmlGraph(features_dir, auto_load=True)
    g.add(
        Node(
            id="feature-1",
            title="Feature 1",
            type="feature",
            status="in-progress",
            priority="high",
            properties={"is_primary": True},
        )
    )

    server = McpServer(graph_dir=graph_dir, default_agent="codex")
    _call(server, "initialize", {"protocolVersion": "2024-11-05"})

    resp = _call(server, "tools/call", {"name": "get_active_feature", "arguments": {}})
    assert resp["result"]["isError"] is False

    events_dir = graph_dir / "events"
    paths = list(events_dir.glob("*.jsonl"))
    assert paths
    last = json.loads(paths[0].read_text(encoding="utf-8").strip().splitlines()[-1])
    assert last["agent"] == "codex"
    assert last["tool"] == "MCP:get_active_feature"
