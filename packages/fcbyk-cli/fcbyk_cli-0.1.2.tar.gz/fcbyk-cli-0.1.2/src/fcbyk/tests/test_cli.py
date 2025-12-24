import pytest
from click.testing import CliRunner
from ..cli import cli

def test_version_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert 'v' in result.output

def test_lansend_command_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['lansend', '--help'])
    assert result.exit_code == 0
    assert 'Start a local web server for sharing files over LAN' in result.output 