"""Tests for HtmlGraph Pydantic models."""

import pytest
from datetime import datetime

from htmlgraph.models import Node, Edge, Step, Graph


class TestStep:
    """Tests for Step model."""

    def test_step_creation_defaults(self):
        """Step should have sensible defaults."""
        step = Step(description="Do something")
        assert step.description == "Do something"
        assert step.completed is False
        assert step.agent is None
        assert step.timestamp is None

    def test_step_to_html_incomplete(self):
        """Incomplete step should render with pending emoji."""
        step = Step(description="Do something")
        html = step.to_html()
        assert "⏳" in html
        assert "Do something" in html
        assert 'data-completed="false"' in html

    def test_step_to_html_completed(self):
        """Completed step should render with checkmark emoji."""
        step = Step(description="Done task", completed=True, agent="claude")
        html = step.to_html()
        assert "✅" in html
        assert 'data-completed="true"' in html
        assert 'data-agent="claude"' in html

    def test_step_to_context(self):
        """Context should be compact checkbox format."""
        incomplete = Step(description="Task 1")
        complete = Step(description="Task 2", completed=True)

        assert incomplete.to_context() == "[ ] Task 1"
        assert complete.to_context() == "[x] Task 2"


class TestEdge:
    """Tests for Edge model."""

    def test_edge_creation_defaults(self):
        """Edge should have sensible defaults."""
        edge = Edge(target_id="node-002")
        assert edge.target_id == "node-002"
        assert edge.relationship == "related"
        assert edge.title is None
        assert edge.since is None
        assert edge.properties == {}

    def test_edge_to_html_simple(self):
        """Simple edge should render as anchor."""
        edge = Edge(target_id="feature-002", title="Feature 2")
        html = edge.to_html()
        assert 'href="feature-002.html"' in html
        assert 'data-relationship="related"' in html
        assert ">Feature 2</a>" in html

    def test_edge_to_html_with_since(self):
        """Edge with since date should include data-since."""
        edge = Edge(
            target_id="task-001",
            relationship="blocks",
            since=datetime(2024, 12, 16, 10, 30)
        )
        html = edge.to_html()
        assert 'data-relationship="blocks"' in html
        assert 'data-since="2024-12-16' in html

    def test_edge_to_context(self):
        """Context should show arrow format."""
        edge = Edge(target_id="task-001", relationship="blocks", title="Task 1")
        assert edge.to_context() == "→ blocks: Task 1"


class TestNode:
    """Tests for Node model."""

    def test_node_creation_defaults(self):
        """Node should have sensible defaults."""
        node = Node(id="test-001", title="Test Node")
        assert node.id == "test-001"
        assert node.title == "Test Node"
        assert node.type == "node"
        assert node.status == "todo"
        assert node.priority == "medium"
        assert node.properties == {}
        assert node.edges == {}
        assert node.steps == []

    def test_node_completion_percentage_no_steps(self):
        """Node without steps: 0% if todo, 100% if done."""
        todo = Node(id="n1", title="T1", status="todo")
        done = Node(id="n2", title="T2", status="done")

        assert todo.completion_percentage == 0
        assert done.completion_percentage == 100

    def test_node_completion_percentage_with_steps(self):
        """Completion percentage should reflect step completion."""
        node = Node(
            id="n1",
            title="T1",
            steps=[
                Step(description="S1", completed=True),
                Step(description="S2", completed=True),
                Step(description="S3", completed=False),
                Step(description="S4", completed=False),
            ]
        )
        assert node.completion_percentage == 50

    def test_node_next_step(self):
        """next_step should return first incomplete step."""
        node = Node(
            id="n1",
            title="T1",
            steps=[
                Step(description="S1", completed=True),
                Step(description="S2", completed=False),
                Step(description="S3", completed=False),
            ]
        )
        assert node.next_step.description == "S2"

    def test_node_next_step_all_complete(self):
        """next_step should return None if all complete."""
        node = Node(
            id="n1",
            title="T1",
            steps=[
                Step(description="S1", completed=True),
                Step(description="S2", completed=True),
            ]
        )
        assert node.next_step is None

    def test_node_add_edge(self):
        """add_edge should add edge to correct relationship bucket."""
        node = Node(id="n1", title="T1")
        edge = Edge(target_id="n2", relationship="blocks")

        node.add_edge(edge)

        assert "blocks" in node.edges
        assert len(node.edges["blocks"]) == 1
        assert node.edges["blocks"][0].target_id == "n2"

    def test_node_complete_step(self):
        """complete_step should mark step as done."""
        node = Node(
            id="n1",
            title="T1",
            steps=[Step(description="S1"), Step(description="S2")]
        )

        result = node.complete_step(0, agent="claude")

        assert result is True
        assert node.steps[0].completed is True
        assert node.steps[0].agent == "claude"
        assert node.steps[1].completed is False

    def test_node_complete_step_invalid_index(self):
        """complete_step should return False for invalid index."""
        node = Node(id="n1", title="T1", steps=[Step(description="S1")])
        assert node.complete_step(99) is False

    def test_node_to_html(self):
        """to_html should generate valid HTML document."""
        node = Node(
            id="feature-001",
            title="User Auth",
            type="feature",
            status="in-progress",
            priority="high",
            content="<p>Implement user authentication.</p>",
            steps=[
                Step(description="Create routes", completed=True),
                Step(description="Add middleware", completed=False),
            ],
            edges={
                "blocked_by": [Edge(target_id="feature-002", title="Database")]
            }
        )

        html = node.to_html()

        # Check structure
        assert "<!DOCTYPE html>" in html
        assert '<article id="feature-001"' in html
        assert 'data-type="feature"' in html
        assert 'data-status="in-progress"' in html
        assert 'data-priority="high"' in html

        # Check content
        assert "<h1>User Auth</h1>" in html
        assert "Implement user authentication" in html

        # Check steps
        assert "Create routes" in html
        assert "Add middleware" in html

        # Check edges
        assert 'href="feature-002.html"' in html
        assert ">Database</a>" in html

    def test_node_to_context(self):
        """to_context should generate compact summary."""
        node = Node(
            id="feature-001",
            title="User Auth",
            status="in-progress",
            priority="high",
            agent_assigned="claude",
            steps=[
                Step(description="S1", completed=True),
                Step(description="S2", completed=False),
            ],
            edges={
                "blocked_by": [Edge(target_id="f-002", title="Database")]
            }
        )

        context = node.to_context()

        assert "feature-001" in context
        assert "User Auth" in context
        assert "in-progress" in context
        assert "high" in context
        assert "claude" in context
        assert "1/2 steps" in context
        assert "50%" in context
        assert "Blocked by" in context
        assert "Database" in context
        assert "Next: S2" in context

    def test_node_from_dict(self):
        """from_dict should handle nested structures."""
        data = {
            "id": "n1",
            "title": "Test",
            "edges": {
                "related": [{"target_id": "n2", "relationship": "related"}]
            },
            "steps": [{"description": "Step 1", "completed": False}]
        }

        node = Node.from_dict(data)

        assert node.id == "n1"
        assert len(node.edges["related"]) == 1
        assert isinstance(node.edges["related"][0], Edge)
        assert len(node.steps) == 1
        assert isinstance(node.steps[0], Step)


class TestGraph:
    """Tests for Graph model."""

    def test_graph_add_and_get(self):
        """Graph should store and retrieve nodes."""
        graph = Graph()
        node = Node(id="n1", title="Node 1")

        graph.add(node)

        assert graph.get("n1") == node
        assert graph.get("nonexistent") is None

    def test_graph_remove(self):
        """Graph should remove nodes."""
        graph = Graph()
        graph.add(Node(id="n1", title="Node 1"))

        assert graph.remove("n1") is True
        assert graph.get("n1") is None
        assert graph.remove("n1") is False  # Already removed

    def test_graph_all_edges(self):
        """all_edges should return all edges from all nodes."""
        graph = Graph()
        node1 = Node(
            id="n1",
            title="N1",
            edges={"related": [Edge(target_id="n2")]}
        )
        node2 = Node(
            id="n2",
            title="N2",
            edges={"blocks": [Edge(target_id="n1", relationship="blocks")]}
        )

        graph.add(node1)
        graph.add(node2)

        edges = graph.all_edges()
        assert len(edges) == 2

    def test_graph_to_context(self):
        """to_context should summarize all nodes."""
        graph = Graph()
        graph.add(Node(id="n1", title="Node 1", status="todo"))
        graph.add(Node(id="n2", title="Node 2", status="done"))

        context = graph.to_context()

        assert "n1" in context
        assert "n2" in context
        assert "Node 1" in context
        assert "Node 2" in context
