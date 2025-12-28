"""
Tests for CLI Module
"""

import pytest
from click.testing import CliRunner
from payloadforge.cli import main


class TestCLI:
    """Test cases for PayloadForge CLI."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    def test_version(self, runner):
        """Test --version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "PayloadForge" in result.output
    
    def test_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "PayloadForge" in result.output
        assert "--xss" in result.output
        assert "--sqli" in result.output
    
    def test_xss_basic(self, runner):
        """Test XSS basic command."""
        result = runner.invoke(main, ["--xss", "basic"])
        assert result.exit_code == 0
        assert "XSS" in result.output
    
    def test_xss_dom(self, runner):
        """Test XSS DOM command."""
        result = runner.invoke(main, ["--xss", "dom"])
        assert result.exit_code == 0
    
    def test_xss_event(self, runner):
        """Test XSS event handler command."""
        result = runner.invoke(main, ["--xss", "event"])
        assert result.exit_code == 0
    
    def test_sqli_error_mysql(self, runner):
        """Test SQLi error MySQL command."""
        result = runner.invoke(main, ["--sqli", "error", "mysql"])
        assert result.exit_code == 0
        assert "SQLi" in result.output
    
    def test_sqli_time_mssql(self, runner):
        """Test SQLi time MSSQL command."""
        result = runner.invoke(main, ["--sqli", "time", "mssql"])
        assert result.exit_code == 0
    
    def test_ssti_jinja2(self, runner):
        """Test SSTI Jinja2 command."""
        result = runner.invoke(main, ["--ssti", "jinja2"])
        assert result.exit_code == 0
        assert "SSTI" in result.output
    
    def test_cmd_linux(self, runner):
        """Test CMDi Linux command."""
        result = runner.invoke(main, ["--cmd", "linux"])
        assert result.exit_code == 0
    
    def test_cmd_windows(self, runner):
        """Test CMDi Windows command."""
        result = runner.invoke(main, ["--cmd", "windows"])
        assert result.exit_code == 0
    
    def test_cmd_with_encoding(self, runner):
        """Test CMDi with encoding."""
        result = runner.invoke(main, ["--cmd", "linux", "--encode", "url"])
        assert result.exit_code == 0
        assert "encoded" in result.output.lower()
    
    def test_encode_url(self, runner):
        """Test encode URL subcommand."""
        result = runner.invoke(main, ["encode", "--url", "<script>"])
        assert result.exit_code == 0
        assert "%3C" in result.output
    
    def test_encode_html(self, runner):
        """Test encode HTML subcommand."""
        result = runner.invoke(main, ["encode", "--html", "<script>"])
        assert result.exit_code == 0
        assert "&lt;" in result.output
    
    def test_encode_base64(self, runner):
        """Test encode Base64 subcommand."""
        result = runner.invoke(main, ["encode", "--base64", "hello"])
        assert result.exit_code == 0
        assert "aGVsbG8=" in result.output
    
    def test_count_parameter(self, runner):
        """Test --count parameter."""
        result = runner.invoke(main, ["--xss", "basic", "--count", "3"])
        assert result.exit_code == 0
        assert "Total: 3" in result.output
    
    def test_list_all(self, runner):
        """Test list-all subcommand."""
        result = runner.invoke(main, ["list-all"])
        assert result.exit_code == 0
        assert "XSS" in result.output
        assert "SQLi" in result.output
        assert "SSTI" in result.output
        assert "CMDi" in result.output
