"""Tests for hash-based ID generation."""

import pytest
from htmlgraph.ids import (
    generate_id,
    generate_hierarchical_id,
    parse_id,
    is_valid_id,
    is_legacy_id,
    get_parent_id,
    get_root_id,
    get_depth,
    PREFIXES,
)


class TestGenerateId:
    """Tests for generate_id function."""

    def test_generates_correct_format(self):
        """ID should be prefix-hash format."""
        id = generate_id("feature", "Test Feature")
        assert id.startswith("feat-")
        assert len(id) == 13  # "feat-" (5) + 8 hex chars

    def test_uses_correct_prefix_for_types(self):
        """Each node type should use its designated prefix."""
        assert generate_id("feature", "").startswith("feat-")
        assert generate_id("bug", "").startswith("bug-")
        assert generate_id("chore", "").startswith("chr-")
        assert generate_id("spike", "").startswith("spk-")
        assert generate_id("epic", "").startswith("epc-")
        assert generate_id("session", "").startswith("sess-")
        assert generate_id("track", "").startswith("trk-")

    def test_unknown_type_uses_truncated_prefix(self):
        """Unknown types should use first 4 chars as prefix."""
        id = generate_id("customtype", "Test")
        assert id.startswith("cust-")

    def test_collision_resistance(self):
        """Multiple IDs with same title should be unique."""
        ids = [generate_id("feature", "Same Title") for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    def test_concurrent_generation(self):
        """IDs generated at same time should be unique."""
        import concurrent.futures

        def gen():
            return generate_id("feature", "Concurrent Test")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(gen) for _ in range(50)]
            ids = [f.result() for f in futures]

        assert len(set(ids)) == 50


class TestGenerateHierarchicalId:
    """Tests for generate_hierarchical_id function."""

    def test_creates_subtask_id(self):
        """Should append index to parent ID."""
        parent = "feat-a1b2c3d4"
        child = generate_hierarchical_id(parent, 1)
        assert child == "feat-a1b2c3d4.1"

    def test_creates_nested_subtask(self):
        """Should support nested hierarchies."""
        parent = "feat-a1b2c3d4.1"
        child = generate_hierarchical_id(parent, 2)
        assert child == "feat-a1b2c3d4.1.2"

    def test_rejects_zero_index(self):
        """Index must be >= 1."""
        with pytest.raises(ValueError, match="index must be >= 1"):
            generate_hierarchical_id("feat-a1b2c3d4", 0)

    def test_rejects_negative_index(self):
        """Index must be positive."""
        with pytest.raises(ValueError, match="index must be >= 1"):
            generate_hierarchical_id("feat-a1b2c3d4", -1)

    def test_requires_index(self):
        """Index is required (no auto-increment yet)."""
        with pytest.raises(ValueError, match="index is required"):
            generate_hierarchical_id("feat-a1b2c3d4", None)


class TestParseId:
    """Tests for parse_id function."""

    def test_parses_simple_hash_id(self):
        """Should parse prefix-hash format."""
        result = parse_id("feat-a1b2c3d4")
        assert result["prefix"] == "feat"
        assert result["node_type"] == "feature"
        assert result["hash"] == "a1b2c3d4"
        assert result["hierarchy"] == []
        assert result["is_legacy"] is False

    def test_parses_hierarchical_id(self):
        """Should parse IDs with hierarchy."""
        result = parse_id("feat-a1b2c3d4.1.2")
        assert result["prefix"] == "feat"
        assert result["hash"] == "a1b2c3d4"
        assert result["hierarchy"] == [1, 2]

    def test_parses_legacy_id(self):
        """Should parse old timestamp format."""
        result = parse_id("feature-20241222-143022")
        assert result["prefix"] == "feature"
        assert result["node_type"] == "feature"
        assert result["hash"] == "20241222-143022"
        assert result["is_legacy"] is True

    def test_returns_none_for_invalid(self):
        """Should return None values for invalid IDs."""
        result = parse_id("invalid")
        assert result["prefix"] is None
        assert result["node_type"] is None
        assert result["hash"] is None


class TestValidation:
    """Tests for validation functions."""

    def test_is_valid_id_hash_format(self):
        """Hash-based IDs should be valid."""
        assert is_valid_id("feat-a1b2c3d4") is True
        assert is_valid_id("bug-12345678") is True
        assert is_valid_id("sess-abcdef12") is True

    def test_is_valid_id_hierarchical(self):
        """Hierarchical IDs should be valid."""
        assert is_valid_id("feat-a1b2c3d4.1") is True
        assert is_valid_id("feat-a1b2c3d4.1.2") is True
        assert is_valid_id("feat-a1b2c3d4.1.2.3") is True

    def test_is_valid_id_legacy(self):
        """Legacy IDs should be valid."""
        assert is_valid_id("feature-20241222-143022") is True
        assert is_valid_id("session-20241222-143022") is True

    def test_is_valid_id_invalid(self):
        """Invalid formats should not be valid."""
        assert is_valid_id("invalid") is False
        assert is_valid_id("feat") is False
        assert is_valid_id("feat-") is False
        assert is_valid_id("feat-xyz") is False  # Not hex

    def test_is_legacy_id(self):
        """Should correctly identify legacy IDs."""
        assert is_legacy_id("feature-20241222-143022") is True
        assert is_legacy_id("feat-a1b2c3d4") is False


class TestHierarchyFunctions:
    """Tests for hierarchy helper functions."""

    def test_get_parent_id(self):
        """Should return parent ID."""
        assert get_parent_id("feat-a1b2c3d4.1.2") == "feat-a1b2c3d4.1"
        assert get_parent_id("feat-a1b2c3d4.1") == "feat-a1b2c3d4"
        assert get_parent_id("feat-a1b2c3d4") is None

    def test_get_root_id(self):
        """Should return root ID without hierarchy."""
        assert get_root_id("feat-a1b2c3d4.1.2") == "feat-a1b2c3d4"
        assert get_root_id("feat-a1b2c3d4.1") == "feat-a1b2c3d4"
        assert get_root_id("feat-a1b2c3d4") == "feat-a1b2c3d4"

    def test_get_depth(self):
        """Should return hierarchy depth."""
        assert get_depth("feat-a1b2c3d4") == 0
        assert get_depth("feat-a1b2c3d4.1") == 1
        assert get_depth("feat-a1b2c3d4.1.2") == 2
        assert get_depth("feat-a1b2c3d4.1.2.3") == 3


class TestPrefixes:
    """Tests for prefix mapping."""

    def test_all_node_types_have_prefixes(self):
        """All common node types should have prefixes."""
        expected_types = [
            "feature", "bug", "chore", "spike", "epic",
            "session", "track", "phase", "agent", "spec", "plan", "event"
        ]
        for node_type in expected_types:
            assert node_type in PREFIXES, f"Missing prefix for {node_type}"

    def test_prefixes_are_short(self):
        """Prefixes should be 3-4 characters."""
        for node_type, prefix in PREFIXES.items():
            assert 3 <= len(prefix) <= 4, f"Prefix '{prefix}' for {node_type} should be 3-4 chars"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_hash_format_is_always_8_hex_chars(self):
        """Hash portion should always be exactly 8 hexadecimal characters."""
        for _ in range(20):
            id = generate_id("feature", "Test")
            parsed = parse_id(id)
            hash_part = parsed["hash"]
            assert len(hash_part) == 8, f"Hash should be 8 chars, got {len(hash_part)}"
            assert all(c in "0123456789abcdef" for c in hash_part), f"Hash should be hex: {hash_part}"

    def test_empty_title_works(self):
        """Empty title should still generate valid ID."""
        id = generate_id("feature", "")
        assert is_valid_id(id)
        assert id.startswith("feat-")
        assert len(id) == 13

    def test_very_long_title(self):
        """Very long titles should work without issues."""
        long_title = "A" * 10000
        id = generate_id("feature", long_title)
        assert is_valid_id(id)
        assert len(id) == 13  # Still compact

    def test_unicode_title(self):
        """Unicode characters in title should work."""
        id = generate_id("feature", "测试功能 🚀")
        assert is_valid_id(id)
        assert id.startswith("feat-")

    def test_special_characters_in_title(self):
        """Special characters should be handled safely."""
        id = generate_id("feature", "Test: <script>alert('xss')</script>")
        assert is_valid_id(id)

    def test_deep_nesting(self):
        """Should support very deep hierarchies."""
        id = "feat-a1b2c3d4"
        for i in range(1, 11):  # 10 levels deep
            id = generate_hierarchical_id(id, i)

        assert is_valid_id(id)
        assert get_depth(id) == 10
        assert get_root_id(id) == "feat-a1b2c3d4"

    def test_all_prefix_types_generate_valid_ids(self):
        """All node types in PREFIXES should generate valid IDs."""
        for node_type, prefix in PREFIXES.items():
            id = generate_id(node_type, f"Test {node_type}")
            assert is_valid_id(id), f"Invalid ID for {node_type}: {id}"
            assert id.startswith(f"{prefix}-"), f"Wrong prefix for {node_type}"

    def test_parse_id_with_single_hierarchy_level(self):
        """Should correctly parse single-level hierarchy."""
        result = parse_id("feat-a1b2c3d4.5")
        assert result["hierarchy"] == [5]
        assert result["hash"] == "a1b2c3d4"

    def test_get_root_id_with_legacy_format(self):
        """get_root_id should work with legacy IDs."""
        legacy_id = "feature-20241222-143022"
        root = get_root_id(legacy_id)
        assert root == legacy_id  # Legacy IDs don't have hierarchy

    def test_get_parent_id_with_single_level(self):
        """get_parent_id should work correctly with single-level hierarchy."""
        parent = get_parent_id("feat-a1b2c3d4.1")
        assert parent == "feat-a1b2c3d4"

    def test_hierarchical_id_with_large_index(self):
        """Should handle large index numbers."""
        id = generate_hierarchical_id("feat-a1b2c3d4", 999)
        assert id == "feat-a1b2c3d4.999"
        assert is_valid_id(id)

    def test_parse_unknown_prefix(self):
        """Should handle unknown prefixes gracefully."""
        result = parse_id("xyz-a1b2c3d4")
        assert result["prefix"] == "xyz"
        # node_type should be 'xyz' since it's not in PREFIX_TO_TYPE
        assert result["node_type"] == "xyz"
        assert result["hash"] == "a1b2c3d4"

    def test_entropy_bytes_parameter(self):
        """Different entropy_bytes should still produce valid IDs."""
        id1 = generate_id("feature", "Test", entropy_bytes=2)
        id2 = generate_id("feature", "Test", entropy_bytes=8)

        assert is_valid_id(id1)
        assert is_valid_id(id2)
        # Both should still be 8 hex chars (SHA256 truncated)
        assert len(id1) == 13
        assert len(id2) == 13
