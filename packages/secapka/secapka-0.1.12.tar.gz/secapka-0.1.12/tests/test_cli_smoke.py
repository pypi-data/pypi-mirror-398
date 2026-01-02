from click.testing import CliRunner

from secapka.cli import cli


def test_help():
    r = CliRunner().invoke(cli, ["--help"])
    assert r.exit_code == 0
    assert "Secapka CLI" in r.output


def test_commands_present():
    r = CliRunner().invoke(cli, ["--help"])
    assert "scan" in r.output
    assert "show" in r.output
    assert "export" in r.output
