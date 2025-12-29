"""
Test drift detection for system overhead activities.

This test verifies that system overhead activities (Skill invocations for system skills,
reads from .htmlgraph/ directory) are not flagged as high-drift.
"""

import pytest

from htmlgraph.session_manager import SessionManager


@pytest.fixture
def temp_graph(tmp_path):
    """Create a temporary graph directory."""
    graph_dir = tmp_path / ".htmlgraph"
    graph_dir.mkdir()
    (graph_dir / "sessions").mkdir()
    (graph_dir / "features").mkdir()
    (graph_dir / "bugs").mkdir()
    return graph_dir


@pytest.fixture
def manager(temp_graph):
    """Create a SessionManager with a test graph."""
    return SessionManager(temp_graph)


def test_skill_invocations_no_drift(manager):
    """Test that system skill invocations (htmlgraph-tracker) have no drift score."""
    # Create a feature
    feature = manager.create_feature(
        title="User Authentication",
        collection="features",
        description="Implement user auth",
        priority="high",
    )

    # Start the feature
    manager.start_feature(feature.id, agent="claude-code")

    # Start a session
    session = manager.start_session(agent="claude-code")

    # Track a Skill invocation for htmlgraph-tracker
    skill_activity = manager.track_activity(
        session_id=session.id,
        tool="Skill",
        summary="Skill: {'skill': 'htmlgraph-tracker'}",
        file_paths=[]
    )

    # Verify the skill invocation has NO drift score (system overhead)
    assert skill_activity.drift_score is None
    assert skill_activity.feature_id == feature.id  # Still attributed to feature
    assert "system_overhead" in str(skill_activity.payload.get("attribution_reason", ""))


def test_htmlgraph_metadata_reads_no_drift(manager):
    """Test that reads from .htmlgraph/ directory have no drift score."""
    # Create a feature
    feature = manager.create_feature(
        title="Bug Tracking",
        collection="features",
        description="Track bugs",
        priority="high",
    )

    # Start the feature
    manager.start_feature(feature.id, agent="claude-code")

    # Start a session
    session = manager.start_session(agent="claude-code")

    # Track a Read of .htmlgraph metadata file
    read_activity = manager.track_activity(
        session_id=session.id,
        tool="Read",
        summary="Read: /path/to/.htmlgraph/bugs/bug-001.html",
        file_paths=["/path/to/.htmlgraph/bugs/bug-001.html"]
    )

    # Verify the read has NO drift score (system overhead)
    assert read_activity.drift_score is None
    assert read_activity.feature_id == feature.id  # Still attributed to feature


def test_htmlgraph_metadata_writes_no_drift(manager):
    """Test that writes to .htmlgraph/ directory have no drift score."""
    # Create a feature
    feature = manager.create_feature(
        title="Feature Tracking",
        collection="features",
        description="Track features",
        priority="high",
    )

    # Start the feature
    manager.start_feature(feature.id, agent="claude-code")

    # Start a session
    session = manager.start_session(agent="claude-code")

    # Track a Write to .htmlgraph metadata file
    write_activity = manager.track_activity(
        session_id=session.id,
        tool="Write",
        summary="Write: .htmlgraph/features/feat-001.html",
        file_paths=[".htmlgraph/features/feat-001.html"]
    )

    # Verify the write has NO drift score (system overhead)
    assert write_activity.drift_score is None
    assert write_activity.feature_id == feature.id  # Still attributed to feature


def test_non_system_activities_still_have_drift(manager):
    """Test that non-system activities still get drift scores when appropriate."""
    # Create a feature with specific file patterns (but NO agent assignment)
    feature = manager.create_feature(
        title="User Authentication",
        collection="features",
        description="Implement user auth",
        priority="high",
    )

    # Set file patterns via properties
    feature.properties["file_patterns"] = ["src/auth/*.py"]
    manager.features_graph.update(feature)

    # Start the feature WITHOUT agent assignment
    manager.start_feature(feature.id, agent=None)

    # Start a session
    session = manager.start_session(agent="claude-code")

    # Track a Read of an unrelated file (should have drift)
    unrelated_activity = manager.track_activity(
        session_id=session.id,
        tool="Read",
        summary="Read: /tmp/unrelated.txt",
        file_paths=["/tmp/unrelated.txt"]
    )

    # Verify this activity HAS a drift score (not system overhead)
    assert unrelated_activity.drift_score is not None
    assert unrelated_activity.drift_score > 0.5  # High drift expected


def test_multiple_skill_invocations_no_drift(manager):
    """Test that repeated skill invocations don't accumulate drift."""
    # Create a feature
    feature = manager.create_feature(
        title="Self-Tracking",
        collection="features",
        description="Use HtmlGraph to track HtmlGraph",
        priority="high",
    )

    # Start the feature
    manager.start_feature(feature.id, agent="claude-code")

    # Start a session
    session = manager.start_session(agent="claude-code")

    # Track multiple skill invocations (simulating repeated tracker calls)
    activities = []
    for i in range(5):
        activity = manager.track_activity(
            session_id=session.id,
            tool="Skill",
            summary=f"Skill: {{'skill': 'htmlgraph:htmlgraph-tracker'}}",
            file_paths=[]
        )
        activities.append(activity)

    # Verify ALL skill invocations have NO drift score
    for activity in activities:
        assert activity.drift_score is None
        assert activity.feature_id == feature.id


def test_mixed_activities_correct_drift(manager):
    """Test that a mix of system and non-system activities are handled correctly."""
    # Create a feature (without agent assignment for realistic drift scores)
    feature = manager.create_feature(
        title="Mixed Work",
        collection="features",
        description="Mix of system and real work",
        priority="high",
    )

    # Set file patterns via properties
    feature.properties["file_patterns"] = ["src/*.py"]
    manager.features_graph.update(feature)

    # Start the feature WITHOUT agent assignment
    manager.start_feature(feature.id, agent=None)

    # Start a session
    session = manager.start_session(agent="claude-code")

    # 1. System overhead - Skill invocation
    skill_act = manager.track_activity(
        session_id=session.id,
        tool="Skill",
        summary="Skill: {'skill': 'htmlgraph-tracker'}",
        file_paths=[]
    )

    # 2. System overhead - .htmlgraph read
    meta_act = manager.track_activity(
        session_id=session.id,
        tool="Read",
        summary="Read: .htmlgraph/features/feat-001.html",
        file_paths=[".htmlgraph/features/feat-001.html"]
    )

    # 3. Real work - matching file pattern
    work_act = manager.track_activity(
        session_id=session.id,
        tool="Edit",
        summary="Edit: src/main.py",
        file_paths=["src/main.py"]
    )

    # 4. Real work - unrelated file (drift)
    drift_act = manager.track_activity(
        session_id=session.id,
        tool="Read",
        summary="Read: /tmp/unrelated.txt",
        file_paths=["/tmp/unrelated.txt"]
    )

    # Verify drift scores
    assert skill_act.drift_score is None  # System overhead
    assert meta_act.drift_score is None  # System overhead
    assert work_act.drift_score is not None  # Real work (should be low drift)
    assert work_act.drift_score < 0.5  # Low drift (matches pattern)
    assert drift_act.drift_score is not None  # Real work (should be high drift)
    assert drift_act.drift_score > 0.5  # High drift (doesn't match)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
