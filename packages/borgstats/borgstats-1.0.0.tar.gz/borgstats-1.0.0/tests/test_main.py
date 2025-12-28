import subprocess

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import json
from borgstats.borgstats  import main


@patch('subprocess.run')
def test_subprocess_runs_borgmatic_command(mock_run):
    mock_run.return_value = MagicMock(stdout=json.dumps([{'archives': []}]).encode('utf-8'))

    runner = CliRunner()
    result = runner.invoke(main, ['--archive', 'test_archive'])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(['borgmatic', '--no-color', 'info', '--json'], capture_output=True, check=True)


@patch('subprocess.run')
def test_subprocess_handles_json_decode_error(mock_run):
    mock_run.return_value = MagicMock(stdout=b'invalid json')

    runner = CliRunner()
    result = runner.invoke(main, ['--archive', 'test_archive'])

    assert 'Something is wrong with the JSON returned' in result.output


@patch('subprocess.run')
def test_subprocess_handles_empty_archives(mock_run):
    mock_run.return_value = MagicMock(stdout=json.dumps([{'archives': []}]).encode('utf-8'))

    runner = CliRunner()
    result = runner.invoke(main, ['--archive', 'test_archive'])

    assert 'No archives in repo.' in result.output


@patch('subprocess.run')
def test_subprocess_handles_valid_archives(mock_run):
    mock_run.return_value = MagicMock(
        stdout=json.dumps(
            [
                {
                    'archives': [
                        {
                            'name': 'test',
                            'duration': 3600,
                            'start': 'start_time',
                            'end': 'end_time',
                            'stats': {'deduplicated_size': 1024},
                        }
                    ]
                }
            ]
        ).encode('utf-8')
    )

    runner = CliRunner()
    result = runner.invoke(main, ['--archive', 'test_archive'])

    assert 'test' in result.output
    assert '01:00:00' in result.output
    assert 'start_time' in result.output
    assert 'end_time' in result.output
    assert '1.0 kB' in result.output


@patch('subprocess.run')
def test_subprocess_general_error(mock_run):
    # mock_run.return_value = MagicMock(stdout='Repository "does_not_exist" not found in configuration files')
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd='borgmatic', output=b'Repository "does_not_exist" not found in configuration files'
    )

    runner = CliRunner()
    result = runner.invoke(main, ['--repo', 'does_not_exist'])

    assert result.exit_code == 1
    assert 'Repository "does_not_exist" not found in configuration files' in result.output
