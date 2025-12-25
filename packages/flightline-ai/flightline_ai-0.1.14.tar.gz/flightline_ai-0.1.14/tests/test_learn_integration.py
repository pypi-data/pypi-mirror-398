"""Integration tests for the learn command file routing."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from flightline.learn_cmd import learn


@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for different formats."""
    # TypeScript
    ts_file = tmp_path / "schema.ts"
    ts_file.write_text("interface User { id: string; }")

    # Pydantic
    py_file = tmp_path / "models.py"
    py_file.write_text("from pydantic import BaseModel\nclass User(BaseModel): id: str")

    # JSON
    json_file = tmp_path / "data.json"
    json_file.write_text('{"id": "123"}')

    return {
        "ts": ts_file,
        "py": py_file,
        "json": json_file
    }

class TestLearnRouting:
    """Tests that the learn command routes to the correct parser based on file type."""

    @patch("flightline.learn_cmd.analyze_typescript")
    def test_routes_to_typescript(self, mock_analyze, runner, sample_files):
        """Test routing to TypeScript parser."""
        mock_analyze.return_value = ({"schema_data": {}}, "raw content")

        result = runner.invoke(learn, [str(sample_files["ts"])])

        assert result.exit_code == 0
        mock_analyze.assert_called_once()

    @patch("flightline.learn_cmd.analyze_pydantic")
    def test_routes_to_pydantic(self, mock_analyze, runner, sample_files):
        """Test routing to Pydantic parser."""
        mock_analyze.return_value = ({"schema_data": {}}, "raw content")

        result = runner.invoke(learn, [str(sample_files["py"])])

        assert result.exit_code == 0
        mock_analyze.assert_called_once()

    @patch("flightline.learn_cmd.analyze_data_file")
    def test_routes_to_llm_for_json(self, mock_analyze, runner, sample_files):
        """Test routing to LLM for JSON data files."""
        # Mock API key to avoid exit
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "fake-key"}):
            mock_analyze.return_value = ({"schema_data": {}}, None)

            # Force the legacy direct-to-OpenRouter path so we can validate routing without a backend.
            result = runner.invoke(learn, [str(sample_files["json"]), "--engine", "openrouter"])

            assert result.exit_code == 0
            mock_analyze.assert_called_once()

    @patch("flightline.learn_cmd.sync_profile_to_cloud")
    def test_sync_flag_calls_cloud_sync(self, mock_sync, runner, sample_files):
        """Test that --sync flag triggers cloud synchronization."""
        mock_sync.return_value = "profile-123"

        # Use TS file to avoid LLM call
        result = runner.invoke(learn, [str(sample_files["ts"]), "--sync"])

        assert result.exit_code == 0
        mock_sync.assert_called_once()
        # The HUD displays everything in uppercase, so we check for uppercase
        assert "SYNCED: PROFILE-123" in result.output

    def test_role_option_validation(self, runner, sample_files):
        """Test validation of the --role option."""
        # Valid roles
        assert runner.invoke(learn, [str(sample_files["ts"]), "--role", "input"]).exit_code == 0
        assert runner.invoke(learn, [str(sample_files["ts"]), "--role", "output"]).exit_code == 0

        # Invalid role
        result = runner.invoke(learn, [str(sample_files["ts"]), "--role", "invalid"])
        assert result.exit_code != 0
        assert "Invalid value for '--role' / '-r'" in result.output
