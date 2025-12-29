"""Tests for Pydantic deployment models."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from htmlgraph.deployment_models import (
    SemanticVersion,
    DeploymentStep,
    GitConfig,
    BuildConfig,
    PyPIConfig,
    PluginConfig,
    DeploymentHooks,
    DeploymentConfig,
    DeploymentResult
)


class TestSemanticVersion:
    """Test semantic version parsing and validation."""

    def test_parse_simple_version(self):
        """Test parsing simple semantic version."""
        version = SemanticVersion.from_string("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease is None
        assert version.build is None

    def test_parse_prerelease_version(self):
        """Test parsing version with prerelease."""
        version = SemanticVersion.from_string("2.0.0-alpha.1")
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 0
        assert version.prerelease == "alpha.1"

    def test_parse_version_with_build(self):
        """Test parsing version with build metadata."""
        version = SemanticVersion.from_string("3.1.4-beta+build.123")
        assert version.major == 3
        assert version.minor == 1
        assert version.patch == 4
        assert version.prerelease == "beta"
        assert version.build == "build.123"

    def test_invalid_version_format(self):
        """Test invalid version format raises error."""
        with pytest.raises(ValueError, match="Invalid semantic version"):
            SemanticVersion.from_string("not-a-version")

        with pytest.raises(ValueError):
            SemanticVersion.from_string("1.2")  # Missing patch

        with pytest.raises(ValueError):
            SemanticVersion.from_string("1.2.3.4")  # Too many parts

    def test_version_to_string(self):
        """Test converting version to string."""
        version = SemanticVersion(major=1, minor=2, patch=3)
        assert version.to_string() == "1.2.3"
        assert str(version) == "1.2.3"

        version_pre = SemanticVersion(major=2, minor=0, patch=0, prerelease="alpha.1")
        assert version_pre.to_string() == "2.0.0-alpha.1"

    def test_version_comparison(self):
        """Test version comparison."""
        v1 = SemanticVersion(major=1, minor=0, patch=0)
        v2 = SemanticVersion(major=2, minor=0, patch=0)
        v3 = SemanticVersion(major=1, minor=1, patch=0)

        assert v1 < v2
        assert v1 < v3
        assert not v2 < v1

    def test_prerelease_precedence(self):
        """Test that prerelease versions have lower precedence."""
        v1 = SemanticVersion(major=1, minor=0, patch=0, prerelease="alpha")
        v2 = SemanticVersion(major=1, minor=0, patch=0)

        assert v1 < v2  # Prerelease < release


class TestGitConfig:
    """Test Git configuration validation."""

    def test_default_git_config(self):
        """Test default Git configuration."""
        config = GitConfig()
        assert config.branch == "main"
        assert config.remote == "origin"
        assert config.push_tags is True

    def test_custom_git_config(self):
        """Test custom Git configuration."""
        config = GitConfig(branch="develop", remote="upstream", push_tags=False)
        assert config.branch == "develop"
        assert config.remote == "upstream"
        assert config.push_tags is False

    def test_invalid_branch_name(self):
        """Test invalid branch name raises error."""
        with pytest.raises(ValidationError, match="Branch name cannot be empty"):
            GitConfig(branch="")

        with pytest.raises(ValidationError, match="Invalid branch name"):
            GitConfig(branch="branch with spaces")


class TestBuildConfig:
    """Test build configuration validation."""

    def test_default_build_config(self):
        """Test default build configuration."""
        config = BuildConfig()
        assert config.command == "uv build"
        assert config.clean_dist is True

    def test_invalid_build_command(self):
        """Test empty build command raises error."""
        with pytest.raises(ValidationError, match="Build command cannot be empty"):
            BuildConfig(command="")


class TestPyPIConfig:
    """Test PyPI configuration validation."""

    def test_default_pypi_config(self):
        """Test default PyPI configuration."""
        config = PyPIConfig()
        assert config.token_env_var == "PyPI_API_TOKEN"
        assert config.wait_after_publish == 10

    def test_wait_time_validation(self):
        """Test wait time must be in valid range."""
        # Valid
        config = PyPIConfig(wait_after_publish=0)
        assert config.wait_after_publish == 0

        config = PyPIConfig(wait_after_publish=60)
        assert config.wait_after_publish == 60

        # Invalid - out of range
        with pytest.raises(ValidationError):
            PyPIConfig(wait_after_publish=-1)

        with pytest.raises(ValidationError):
            PyPIConfig(wait_after_publish=61)

    def test_invalid_token_env_var(self):
        """Test invalid environment variable name."""
        with pytest.raises(ValidationError, match="Invalid environment variable name"):
            PyPIConfig(token_env_var="invalid-name")  # Hyphens not allowed

        with pytest.raises(ValidationError):
            PyPIConfig(token_env_var="123INVALID")  # Can't start with number


class TestPluginConfig:
    """Test plugin configuration validation."""

    def test_valid_plugin_config(self):
        """Test valid plugin configuration."""
        config = PluginConfig(
            name="claude",
            command="claude plugin update {package}"
        )
        assert config.name == "claude"
        assert config.required is False

    def test_plugin_command_must_have_placeholder(self):
        """Test plugin command must have placeholder."""
        with pytest.raises(ValidationError, match="must contain .* placeholder"):
            PluginConfig(name="test", command="some command")

        # Valid with package placeholder
        config = PluginConfig(name="test", command="update {package}")
        assert config.command == "update {package}"

        # Valid with version placeholder
        config = PluginConfig(name="test", command="update --version {version}")
        assert config.command == "update --version {version}"


class TestDeploymentConfig:
    """Test deployment configuration validation."""

    def test_minimal_deployment_config(self):
        """Test minimal valid deployment configuration."""
        config = DeploymentConfig(project_name="test-project")
        assert config.project_name == "test-project"
        assert len(config.steps) > 0

    def test_invalid_project_name(self):
        """Test invalid project name raises error."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            DeploymentConfig(project_name="")

        with pytest.raises(ValidationError, match="Invalid project name"):
            DeploymentConfig(project_name="invalid name!")  # Spaces not allowed

    def test_invalid_version_format(self):
        """Test invalid version format raises error."""
        with pytest.raises(ValidationError, match="Invalid version format"):
            DeploymentConfig(
                project_name="test",
                version="not-a-version"
            )

    def test_valid_version_format(self):
        """Test valid version format accepted."""
        config = DeploymentConfig(
            project_name="test",
            version="1.2.3"
        )
        assert config.version == "1.2.3"

    def test_duplicate_steps_rejected(self):
        """Test duplicate deployment steps are rejected."""
        with pytest.raises(ValidationError, match="Duplicate deployment steps"):
            DeploymentConfig(
                project_name="test",
                steps=[
                    DeploymentStep.BUILD,
                    DeploymentStep.BUILD  # Duplicate
                ]
            )

    def test_empty_steps_rejected(self):
        """Test empty steps list is rejected."""
        with pytest.raises(ValidationError, match="Must specify at least one"):
            DeploymentConfig(
                project_name="test",
                steps=[]
            )

    def test_pypi_publish_requires_build(self):
        """Test PyPI publish step requires build step."""
        with pytest.raises(ValidationError, match="PyPI publish requires build"):
            DeploymentConfig(
                project_name="test",
                steps=[DeploymentStep.PYPI_PUBLISH]
            )

    def test_build_must_come_before_publish(self):
        """Test build step must come before publish."""
        with pytest.raises(ValidationError, match="Build step must come before"):
            DeploymentConfig(
                project_name="test",
                steps=[
                    DeploymentStep.PYPI_PUBLISH,
                    DeploymentStep.BUILD  # Wrong order
                ]
            )

    def test_valid_step_order(self):
        """Test valid step ordering."""
        config = DeploymentConfig(
            project_name="test",
            steps=[
                DeploymentStep.BUILD,
                DeploymentStep.PYPI_PUBLISH,
                DeploymentStep.LOCAL_INSTALL
            ]
        )
        assert config.steps[0] == DeploymentStep.BUILD

    def test_to_toml_dict(self):
        """Test exporting config to TOML dict."""
        config = DeploymentConfig(
            project_name="test-project",
            version="1.0.0",
            steps=[DeploymentStep.BUILD]
        )

        toml_dict = config.to_toml_dict()
        assert toml_dict['project']['name'] == "test-project"
        assert toml_dict['project']['version'] == "1.0.0"
        assert 'build' in toml_dict['deployment']['steps'][0]


class TestDeploymentResult:
    """Test deployment result model."""

    def test_successful_deployment(self):
        """Test successful deployment result."""
        result = DeploymentResult(
            success=True,
            version="1.0.0",
            steps_completed=[DeploymentStep.BUILD, DeploymentStep.PYPI_PUBLISH],
            steps_failed=[],
            duration_seconds=45.5
        )

        assert result.success
        assert result.completion_rate == 1.0
        assert not result.is_partial

    def test_partial_deployment(self):
        """Test partially successful deployment."""
        result = DeploymentResult(
            success=True,
            version="1.0.0",
            steps_completed=[DeploymentStep.BUILD],
            steps_failed=[DeploymentStep.PYPI_PUBLISH],
            errors=["PyPI publish failed"]
        )

        assert result.success
        assert result.is_partial
        assert result.completion_rate == 0.5

    def test_failed_deployment(self):
        """Test failed deployment result."""
        result = DeploymentResult(
            success=False,
            version="1.0.0",
            steps_completed=[],
            steps_failed=[DeploymentStep.BUILD],
            errors=["Build command failed"]
        )

        assert not result.success
        assert result.completion_rate == 0.0
        assert not result.is_partial
