"""Tests for CLI commands."""
import pytest
from typer.testing import CliRunner

from planecompose.main import app
from planecompose import __version__


runner = CliRunner()


class TestCLIRoot:
    """Tests for root CLI commands."""
    
    def test_help(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Plane CLI" in result.stdout
        assert "init" in result.stdout
        assert "push" in result.stdout
        assert "pull" in result.stdout
    
    def test_version(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        
        assert result.exit_code == 0
        assert __version__ in result.stdout
    
    def test_version_short(self):
        """Test -V short flag."""
        result = runner.invoke(app, ["-V"])
        
        assert result.exit_code == 0
        assert __version__ in result.stdout
    
    def test_no_args_shows_help(self):
        """Test that no arguments shows help."""
        result = runner.invoke(app, [])
        
        # Exit code 2 is standard for typer when showing help due to missing args
        assert result.exit_code in [0, 2]
        assert "Usage:" in result.stdout


class TestInitCommand:
    """Tests for init command."""
    
    def test_init_help(self):
        """Test init --help."""
        result = runner.invoke(app, ["init", "--help"])
        
        assert result.exit_code == 0
        assert "Initialize" in result.stdout
    
    def test_init_creates_structure(self, tmp_path, monkeypatch):
        """Test that init creates proper directory structure."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Run init with non-interactive inputs
        result = runner.invoke(
            app,
            ["init", "test-project", "--workspace", "test", "--project", "TEST"],
        )
        
        assert result.exit_code == 0
        
        project_path = tmp_path / "test-project"
        assert project_path.exists()
        assert (project_path / "plane.yaml").exists()
        assert (project_path / "schema").is_dir()
        assert (project_path / "schema" / "types.yaml").exists()
        assert (project_path / "schema" / "workflows.yaml").exists()
        assert (project_path / "schema" / "labels.yaml").exists()
        assert (project_path / "work").is_dir()
        assert (project_path / ".plane").is_dir()


class TestAuthCommands:
    """Tests for auth commands."""
    
    def test_auth_help(self):
        """Test auth --help."""
        result = runner.invoke(app, ["auth", "--help"])
        
        assert result.exit_code == 0
        assert "login" in result.stdout
        assert "logout" in result.stdout
        assert "whoami" in result.stdout
    
    def test_auth_login_help(self):
        """Test auth login --help."""
        result = runner.invoke(app, ["auth", "login", "--help"])
        
        assert result.exit_code == 0
        assert "API key" in result.stdout


class TestSchemaCommands:
    """Tests for schema commands."""
    
    def test_schema_help(self):
        """Test schema --help."""
        result = runner.invoke(app, ["schema", "--help"])
        
        assert result.exit_code == 0
        assert "validate" in result.stdout
        assert "push" in result.stdout
    
    def test_schema_validate_no_project(self, tmp_path, monkeypatch):
        """Test schema validate outside a project."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["schema", "validate"])
        
        assert result.exit_code == 1
        assert "plane init" in result.stdout or "Error" in result.stdout


class TestPushCommand:
    """Tests for push command."""
    
    def test_push_help(self):
        """Test push --help."""
        result = runner.invoke(app, ["push", "--help"])
        
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout
        assert "--force" in result.stdout
    
    def test_push_no_project(self, tmp_path, monkeypatch):
        """Test push outside a project."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["push"])
        
        assert result.exit_code == 1


class TestPullCommand:
    """Tests for pull command."""
    
    def test_pull_help(self):
        """Test pull --help."""
        result = runner.invoke(app, ["pull", "--help"])
        
        assert result.exit_code == 0
        assert "--output" in result.stdout
        assert "--merge" in result.stdout


class TestStatusCommand:
    """Tests for status command."""
    
    def test_status_help(self):
        """Test status --help."""
        result = runner.invoke(app, ["status", "--help"])
        
        assert result.exit_code == 0


class TestRateStatsCommands:
    """Tests for rate stats commands."""
    
    def test_rate_help(self):
        """Test rate --help."""
        result = runner.invoke(app, ["rate", "--help"])
        
        assert result.exit_code == 0
        assert "stats" in result.stdout
        assert "reset" in result.stdout
    
    def test_rate_stats(self):
        """Test rate stats command."""
        result = runner.invoke(app, ["rate", "stats"])
        
        assert result.exit_code == 0
        assert "Rate Limit" in result.stdout
    
    def test_rate_reset(self):
        """Test rate reset command."""
        result = runner.invoke(app, ["rate", "reset"])
        
        assert result.exit_code == 0
        assert "reset" in result.stdout.lower()


class TestApplyCommand:
    """Tests for apply command."""
    
    def test_apply_help(self):
        """Test apply --help."""
        result = runner.invoke(app, ["apply", "--help"])
        
        assert result.exit_code == 0
        assert "--scope-labels" in result.stdout
        assert "--scope-assignee" in result.stdout
        assert "--scope-prefix" in result.stdout
    
    def test_apply_requires_scope(self, tmp_path, monkeypatch):
        """Test that apply requires a scope."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["apply"])
        
        assert result.exit_code == 1
        assert "scope" in result.stdout.lower()


class TestDoctorCommand:
    """Tests for doctor command."""
    
    def test_doctor_help(self):
        """Test doctor --help."""
        result = runner.invoke(app, ["doctor", "--help"])
        
        assert result.exit_code == 0
        assert "Diagnose" in result.stdout or "diagnose" in result.stdout
    
    def test_doctor_runs(self, tmp_path, monkeypatch):
        """Test that doctor runs diagnostic checks."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["doctor"])
        
        assert result.exit_code == 0
        assert "Diagnostic" in result.stdout or "Check" in result.stdout


class TestCompletionCommand:
    """Tests for completion command."""
    
    def test_completion_help(self):
        """Test completion --help."""
        result = runner.invoke(app, ["completion", "--help"])
        
        assert result.exit_code == 0
        assert "bash" in result.stdout.lower() or "shell" in result.stdout.lower()
    
    def test_completion_bash(self):
        """Test bash completion generation."""
        result = runner.invoke(app, ["completion", "bash"])
        
        assert result.exit_code == 0
        assert "plane" in result.stdout.lower()
    
    def test_completion_zsh(self):
        """Test zsh completion generation."""
        result = runner.invoke(app, ["completion", "zsh"])
        
        assert result.exit_code == 0
        assert "plane" in result.stdout.lower()
    
    def test_completion_invalid_shell(self):
        """Test invalid shell type."""
        result = runner.invoke(app, ["completion", "invalid"])
        
        assert result.exit_code == 1
        assert "Invalid" in result.stdout or "invalid" in result.stdout

