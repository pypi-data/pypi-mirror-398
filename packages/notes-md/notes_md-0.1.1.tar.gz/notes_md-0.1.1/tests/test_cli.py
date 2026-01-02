from click.testing import CliRunner
from notes_md.cli import cli

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "notes_md" in result.output
