"""Tests for the CLI module."""

from click.testing import CliRunner

from flightline.cli import cli


class TestCLI:
    """Tests for the main CLI."""

    def test_cli_help(self):
        """CLI should show help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Flightline" in result.output
        assert "learn" in result.output
        assert "generate" in result.output

    def test_cli_version(self):
        """CLI should show version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_discover_accepts_api_url_and_md_format(self, tmp_path):
        """GitHub Action compatibility: discover accepts --api-url and --format md."""
        # Minimal file so discovery has something to scan
        (tmp_path / "app.js").write_text('console.log("hello");\n')

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["discover", str(tmp_path), "--format", "md", "--api-url", "https://example.com", "--quiet"],
        )
        assert result.exit_code == 0
        assert "## 🛰️ Flightline Mission Briefing" in result.output

    def test_learn_help(self):
        """Learn command should show help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["learn", "--help"])
        assert result.exit_code == 0
        assert "Learn data structure" in result.output

    def test_generate_help(self):
        """Generate command should show help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0

    def test_gen_alias_exists(self):
        """Gen should be an alias for generate."""
        runner = CliRunner()
        result = runner.invoke(cli, ["gen", "--help"])
        assert result.exit_code == 0


class TestLearnCommand:
    """Tests for the learn command."""

    def test_learn_requires_file(self):
        """Learn should require a file argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ["learn"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_learn_file_not_found(self):
        """Learn should error on missing file."""
        runner = CliRunner()
        result = runner.invoke(cli, ["learn", "nonexistent.json"])
        assert result.exit_code != 0
