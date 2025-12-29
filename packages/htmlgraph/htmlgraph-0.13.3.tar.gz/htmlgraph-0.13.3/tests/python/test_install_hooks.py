"""
Tests for Git hooks installation and management.
"""

import json
import shutil
import tempfile
from pathlib import Path
import pytest

from htmlgraph.hooks.installer import HookInstaller, HookConfig
from htmlgraph.hooks import AVAILABLE_HOOKS


@pytest.fixture
def temp_project():
    """Create a temporary project directory with .git and .htmlgraph."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create .git directory
        git_dir = project_dir / ".git"
        git_dir.mkdir()
        (git_dir / "hooks").mkdir()

        # Create .htmlgraph directory
        htmlgraph_dir = project_dir / ".htmlgraph"
        htmlgraph_dir.mkdir()

        yield project_dir


@pytest.fixture
def hook_config(temp_project):
    """Create a HookConfig instance for testing."""
    config_path = temp_project / ".htmlgraph" / "hooks-config.json"
    config = HookConfig(config_path)
    # Ensure default config is used for each test
    config.config = HookConfig.DEFAULT_CONFIG.copy()
    config.config["enabled_hooks"] = HookConfig.DEFAULT_CONFIG["enabled_hooks"].copy()
    return config


@pytest.fixture
def installer(temp_project, hook_config):
    """Create a HookInstaller instance for testing."""
    return HookInstaller(temp_project, hook_config)


class TestHookConfig:
    """Tests for HookConfig class."""

    def test_default_config(self, hook_config):
        """Test default configuration values."""
        assert set(hook_config.config["enabled_hooks"]) == set(AVAILABLE_HOOKS)
        assert hook_config.config["use_symlinks"] is True
        assert hook_config.config["backup_existing"] is True
        assert hook_config.config["chain_existing"] is True

    def test_is_hook_enabled(self, hook_config):
        """Test checking if a hook is enabled."""
        assert hook_config.is_hook_enabled("pre-commit") is True
        assert hook_config.is_hook_enabled("post-commit") is True

        # Disable a hook
        hook_config.disable_hook("pre-commit")
        assert hook_config.is_hook_enabled("pre-commit") is False

    def test_enable_disable_hook(self, hook_config):
        """Test enabling and disabling hooks."""
        # Disable
        hook_config.disable_hook("post-commit")
        assert "post-commit" not in hook_config.config["enabled_hooks"]

        # Re-enable
        hook_config.enable_hook("post-commit")
        assert "post-commit" in hook_config.config["enabled_hooks"]

    def test_save_load_config(self, temp_project):
        """Test saving and loading configuration."""
        config_path = temp_project / ".htmlgraph" / "hooks-config.json"

        # Create and modify config
        config1 = HookConfig(config_path)
        config1.disable_hook("pre-commit")
        config1.config["use_symlinks"] = False
        config1.save()

        # Load config
        config2 = HookConfig(config_path)
        assert config2.is_hook_enabled("pre-commit") is False
        assert config2.config["use_symlinks"] is False

    def test_load_nonexistent_config(self, temp_project):
        """Test loading config when file doesn't exist."""
        config_path = temp_project / ".htmlgraph" / "nonexistent.json"
        config = HookConfig(config_path)

        # Should use defaults
        assert set(config.config["enabled_hooks"]) == set(AVAILABLE_HOOKS)


class TestHookInstaller:
    """Tests for HookInstaller class."""

    def test_validate_environment_success(self, installer):
        """Test environment validation with valid setup."""
        is_valid, error_msg = installer.validate_environment()
        assert is_valid is True
        assert error_msg == ""

    def test_validate_environment_no_git(self, temp_project):
        """Test environment validation without .git directory."""
        # Remove .git
        shutil.rmtree(temp_project / ".git")

        config = HookConfig(temp_project / ".htmlgraph" / "hooks-config.json")
        installer = HookInstaller(temp_project, config)

        is_valid, error_msg = installer.validate_environment()
        assert is_valid is False
        assert "git repository" in error_msg.lower()

    def test_validate_environment_no_htmlgraph(self, temp_project):
        """Test environment validation without .htmlgraph directory."""
        # Remove .htmlgraph
        shutil.rmtree(temp_project / ".htmlgraph")

        config = HookConfig()
        installer = HookInstaller(temp_project, config)

        is_valid, error_msg = installer.validate_environment()
        assert is_valid is False
        assert "htmlgraph" in error_msg.lower()

    def test_install_hook_basic(self, installer):
        """Test basic hook installation."""
        success, message = installer.install_hook("pre-commit")

        assert success is True
        assert "pre-commit" in message

        # Check files exist
        versioned_hook = installer.htmlgraph_dir / "hooks" / "pre-commit.sh"
        git_hook = installer.git_dir / "hooks" / "pre-commit"

        assert versioned_hook.exists()
        assert git_hook.exists()

        # Check executable
        assert versioned_hook.stat().st_mode & 0o111  # Has execute bit

    def test_install_hook_disabled(self, installer):
        """Test installing a disabled hook."""
        installer.config.disable_hook("pre-commit")

        success, message = installer.install_hook("pre-commit")

        assert success is False
        assert "disabled" in message.lower()

    def test_install_hook_dry_run(self, installer):
        """Test dry-run mode."""
        success, message = installer.install_hook("pre-commit", dry_run=True)

        assert success is True
        assert "DRY RUN" in message

        # Check files don't exist
        git_hook = installer.git_dir / "hooks" / "pre-commit"
        assert not git_hook.exists()

    def test_install_hook_with_symlink(self, installer):
        """Test hook installation using symlinks."""
        installer.config.config["use_symlinks"] = True

        success, message = installer.install_hook("pre-commit")

        assert success is True

        git_hook = installer.git_dir / "hooks" / "pre-commit"
        versioned_hook = installer.htmlgraph_dir / "hooks" / "pre-commit.sh"

        assert git_hook.is_symlink()
        assert git_hook.resolve() == versioned_hook.resolve()

    def test_install_hook_with_copy(self, installer):
        """Test hook installation using file copy."""
        installer.config.config["use_symlinks"] = False

        success, message = installer.install_hook("pre-commit")

        assert success is True

        git_hook = installer.git_dir / "hooks" / "pre-commit"

        assert git_hook.exists()
        assert not git_hook.is_symlink()

    def test_install_hook_existing_backup(self, installer):
        """Test handling existing hooks with backup."""
        # Create existing hook
        git_hook = installer.git_dir / "hooks" / "pre-commit"
        git_hook.write_text("#!/bin/bash\necho 'existing hook'")
        git_hook.chmod(0o755)

        installer.config.config["backup_existing"] = True
        installer.config.config["chain_existing"] = False

        success, message = installer.install_hook("pre-commit")

        assert success is False  # Should fail without force
        assert "backup" in message.lower()

        # Check backup exists
        backup = installer.git_dir / "hooks" / "pre-commit.backup"
        assert backup.exists()

    def test_install_hook_existing_chain(self, installer):
        """Test chaining with existing hooks."""
        # Create existing hook
        git_hook = installer.git_dir / "hooks" / "pre-commit"
        git_hook.write_text("#!/bin/bash\necho 'existing hook'")
        git_hook.chmod(0o755)

        installer.config.config["chain_existing"] = True

        success, message = installer.install_hook("pre-commit")

        assert success is True
        assert "chained" in message.lower()

        # Check backup exists
        backup = installer.git_dir / "hooks" / "pre-commit.backup"
        assert backup.exists()

        # Check chained hook content
        content = git_hook.read_text()
        assert "existing hook" not in content  # Original replaced
        assert "backup" in content  # References backup
        assert "htmlgraph" in content.lower()  # References our hook

    def test_install_hook_force(self, installer):
        """Test force installation over existing hook."""
        # Create existing hook
        git_hook = installer.git_dir / "hooks" / "pre-commit"
        git_hook.write_text("#!/bin/bash\necho 'existing hook'")

        success, message = installer.install_hook("pre-commit", force=True)

        assert success is True

        # Check hook was replaced
        assert git_hook.exists()

    def test_install_all_hooks(self, installer):
        """Test installing all enabled hooks."""
        results = installer.install_all_hooks()

        # Check all hooks installed
        assert len(results) == len(AVAILABLE_HOOKS)

        for hook_name, (success, message) in results.items():
            assert success is True
            assert hook_name in AVAILABLE_HOOKS

    def test_install_all_hooks_with_disabled(self, installer):
        """Test installing hooks with some disabled."""
        installer.config.disable_hook("post-checkout")
        installer.config.disable_hook("post-merge")

        results = installer.install_all_hooks()

        # Only enabled hooks should be in results
        assert "post-commit" in results
        assert "pre-commit" in results
        assert "post-checkout" not in results
        assert "post-merge" not in results

    def test_uninstall_hook_symlink(self, installer):
        """Test uninstalling a symlinked hook."""
        # Install hook
        installer.install_hook("pre-commit")

        git_hook = installer.git_dir / "hooks" / "pre-commit"
        assert git_hook.exists()

        # Uninstall
        success, message = installer.uninstall_hook("pre-commit")

        assert success is True
        assert not git_hook.exists()

    def test_uninstall_hook_with_backup(self, installer):
        """Test uninstalling hook and restoring backup."""
        # Create existing hook
        git_hook = installer.git_dir / "hooks" / "pre-commit"
        existing_content = "#!/bin/bash\necho 'existing hook'"
        git_hook.write_text(existing_content)
        git_hook.chmod(0o755)

        # Install (creates backup and chains)
        installer.config.config["use_symlinks"] = False
        installer.install_hook("pre-commit")

        backup = git_hook.with_suffix(".backup")
        assert backup.exists()

        # Uninstall
        success, message = installer.uninstall_hook("pre-commit")

        assert success is True
        assert "restored backup" in message.lower()
        assert git_hook.exists()
        assert git_hook.read_text() == existing_content
        assert not backup.exists()

    def test_uninstall_hook_not_installed(self, installer):
        """Test uninstalling a hook that's not installed."""
        success, message = installer.uninstall_hook("pre-commit")

        assert success is False
        assert "not installed" in message.lower()

    def test_list_hooks(self, installer):
        """Test listing hook status."""
        # Install some hooks
        installer.install_hook("pre-commit")
        installer.install_hook("post-commit")

        # Disable one
        installer.config.disable_hook("post-checkout")

        status = installer.list_hooks()

        # Check all hooks are listed
        assert len(status) == len(AVAILABLE_HOOKS)

        # Check pre-commit status
        assert status["pre-commit"]["enabled"] is True
        assert status["pre-commit"]["installed"] is True
        assert status["pre-commit"]["versioned"] is True

        # Check post-checkout status
        assert status["post-checkout"]["enabled"] is False
        assert status["post-checkout"]["installed"] is False

    def test_list_hooks_symlink_info(self, installer):
        """Test listing hooks with symlink information."""
        installer.config.config["use_symlinks"] = True
        installer.install_hook("pre-commit")

        status = installer.list_hooks()

        assert status["pre-commit"]["is_symlink"] is True
        assert status["pre-commit"]["our_hook"] is True
        assert "symlink_target" in status["pre-commit"]

    def test_list_hooks_copy_info(self, installer):
        """Test listing hooks installed as copies."""
        installer.config.config["use_symlinks"] = False
        installer.install_hook("pre-commit")

        status = installer.list_hooks()

        assert status["pre-commit"]["is_symlink"] is False
        assert status["pre-commit"]["installed"] is True


class TestHookContent:
    """Tests for hook script content and behavior."""

    def test_hook_files_exist(self):
        """Test that all hook template files exist."""
        from htmlgraph.hooks import HOOKS_DIR

        for hook_name in AVAILABLE_HOOKS:
            hook_file = HOOKS_DIR / f"{hook_name}.sh"
            assert hook_file.exists(), f"Hook template {hook_name}.sh not found"

    def test_hook_files_have_shebang(self):
        """Test that all hooks have proper shebang."""
        from htmlgraph.hooks import HOOKS_DIR

        for hook_name in AVAILABLE_HOOKS:
            hook_file = HOOKS_DIR / f"{hook_name}.sh"
            content = hook_file.read_text()
            assert content.startswith("#!/bin/bash"), f"{hook_name}.sh missing shebang"

    def test_hook_files_have_description(self):
        """Test that all hooks have description comments."""
        from htmlgraph.hooks import HOOKS_DIR

        for hook_name in AVAILABLE_HOOKS:
            hook_file = HOOKS_DIR / f"{hook_name}.sh"
            content = hook_file.read_text()
            # Should have comment explaining what it does
            assert "#" in content
            assert "HtmlGraph" in content


class TestCLIIntegration:
    """Tests for CLI integration (requires CLI to be importable)."""

    def test_cli_command_exists(self):
        """Test that install-hooks command exists in CLI."""
        from htmlgraph.cli import main
        import sys

        # This will raise SystemExit, but we just want to check parsing works
        with pytest.raises(SystemExit):
            sys.argv = ["htmlgraph", "install-hooks", "--help"]
            main()

    def test_available_hooks_constant(self):
        """Test that AVAILABLE_HOOKS is properly defined."""
        assert len(AVAILABLE_HOOKS) == 5
        assert "pre-commit" in AVAILABLE_HOOKS
        assert "post-commit" in AVAILABLE_HOOKS
        assert "post-checkout" in AVAILABLE_HOOKS
        assert "post-merge" in AVAILABLE_HOOKS
        assert "pre-push" in AVAILABLE_HOOKS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
