import pytest
from click.testing import CliRunner
from sft.cli import cli, parse_time_duration, format_size, format_time_remaining
from datetime import datetime, timedelta


class TestTimeUtils:
    def test_parse_time_duration_minutes(self):
        assert parse_time_duration('30m') == 1800
        assert parse_time_duration('1m') == 60
    
    def test_parse_time_duration_hours(self):
        assert parse_time_duration('1h') == 3600
        assert parse_time_duration('2h') == 7200
    
    def test_parse_time_duration_days(self):
        assert parse_time_duration('1d') == 86400
        assert parse_time_duration('7d') == 604800
    
    def test_parse_time_duration_weeks(self):
        assert parse_time_duration('1w') == 604800
        assert parse_time_duration('2w') == 1209600
    
    def test_parse_time_duration_invalid(self):
        with pytest.raises(ValueError):
            parse_time_duration('invalid')
    
    def test_format_size_bytes(self):
        assert 'B' in format_size(100)
    
    def test_format_size_kb(self):
        result = format_size(2048)
        assert 'KB' in result
    
    def test_format_size_mb(self):
        result = format_size(5 * 1024 * 1024)
        assert 'MB' in result
    
    def test_format_size_gb(self):
        result = format_size(3 * 1024 * 1024 * 1024)
        assert 'GB' in result
    
    def test_format_time_remaining_seconds(self):
        future = datetime.now() + timedelta(seconds=30)
        result = format_time_remaining(future.isoformat())
        assert 's' in result
    
    def test_format_time_remaining_minutes(self):
        future = datetime.now() + timedelta(minutes=45)
        result = format_time_remaining(future.isoformat())
        assert 'min' in result
    
    def test_format_time_remaining_hours(self):
        future = datetime.now() + timedelta(hours=5)
        result = format_time_remaining(future.isoformat())
        assert 'h' in result
    
    def test_format_time_remaining_days(self):
        future = datetime.now() + timedelta(days=3)
        result = format_time_remaining(future.isoformat())
        assert 'd' in result
    
    def test_format_time_remaining_expired(self):
        past = datetime.now() - timedelta(hours=1)
        result = format_time_remaining(past.isoformat())
        assert result == "expired"


class TestCLI:
    def test_cli_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'upload' in result.output or 'download' in result.output
    
    def test_upload_connection_failure(self):
        """Test upload fails gracefully when service is unreachable."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('test.txt', 'w') as f:
                f.write('test')
            
            result = runner.invoke(cli, ['upload', '--service', 'localhost:99999', 'test.txt', '1h'])
            assert result.exit_code != 0
            assert 'Error' in result.output
    
    def test_download_missing_service(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['download', '123456'], env={})
        assert result.exit_code != 0
    
    def test_upload_with_custom_id_option(self):
        """Test that --id option is recognized by upload command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['upload', '--help'])
        assert result.exit_code == 0
        assert '--id' in result.output
        assert 'Custom file ID' in result.output
