"""
CLI 基础测试
"""

from click.testing import CliRunner

from esn_tool.cli import cli


def test_cli_version() -> None:
    """测试版本命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "esn-tool" in result.output


def test_cli_help() -> None:
    """测试帮助命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ESN Tool" in result.output


def test_git_help() -> None:
    """测试 Git 子命令帮助"""
    runner = CliRunner()
    result = runner.invoke(cli, ["git", "--help"])
    assert result.exit_code == 0
    assert "Git" in result.output
    assert "exec" in result.output
    assert "genc" in result.output


def test_git_exec_help() -> None:
    """测试 git exec 子命令帮助"""
    runner = CliRunner()
    result = runner.invoke(cli, ["git", "exec", "--help"])
    assert result.exit_code == 0
    assert "执行 git 命令" in result.output


def test_git_genc_help() -> None:
    """测试 git genc 子命令帮助"""
    runner = CliRunner()
    result = runner.invoke(cli, ["git", "genc", "--help"])
    assert result.exit_code == 0
    assert "生成" in result.output
