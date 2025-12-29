from __future__ import annotations

import json
from io import BytesIO

from htmlgraph.mcp_server import StdioTransport


def test_stdio_transport_reads_content_length_message():
    msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}
    body = json.dumps(msg).encode("utf-8")
    payload = b"Content-Length: %d\r\n\r\n" % len(body) + body

    inp = BytesIO(payload)
    out = BytesIO()
    t = StdioTransport(inp=inp, out=out, force_content_length=None, log_to_stderr=False)

    read = t.read_message()
    assert read is not None
    assert read["method"] == "initialize"


def test_stdio_transport_writes_content_length_when_detected():
    inp = BytesIO(b"Content-Length: 2\r\n\r\n{}")
    out = BytesIO()
    t = StdioTransport(inp=inp, out=out, force_content_length=None, log_to_stderr=False)

    # Detection happens on read
    assert t.read_message() == {}
    t.write_message({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}})

    written = out.getvalue()
    assert written.startswith(b"Content-Length:")
    assert b"\r\n\r\n" in written


def test_stdio_transport_reads_newline_json_message():
    inp = BytesIO(b"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}\n")
    out = BytesIO()
    t = StdioTransport(inp=inp, out=out, force_content_length=None, log_to_stderr=False)
    read = t.read_message()
    assert read is not None
    assert read["method"] == "tools/list"

