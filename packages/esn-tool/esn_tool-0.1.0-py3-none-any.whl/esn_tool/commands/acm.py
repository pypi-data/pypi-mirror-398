"""
ACM (Auto Commit Message) 命令模块

使用 AI 自动生成 Git 提交信息。
"""

import subprocess
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def find_git_repos(base_path: Path) -> list[Path]:
    """查找指定目录下的所有一级 Git 仓库"""
    git_repos = []
    if not base_path.is_dir():
        return git_repos
    for item in base_path.iterdir():
        if item.is_dir() and (item / ".git").exists():
            git_repos.append(item)
    return sorted(git_repos, key=lambda p: p.name.lower())


def run_git_command(repo_path: Path, args: tuple[str, ...]) -> tuple[bool, str]:
    """在指定仓库目录执行 git 命令"""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "命令执行超时"
    except Exception as e:
        return False, str(e)


def get_git_diff(repo_path: Path, staged: bool = True) -> str:
    """获取 Git diff 内容"""
    args = ["diff", "--cached"] if staged else ["diff"]
    success, output = run_git_command(repo_path, tuple(args))
    return output if success else ""


def get_file_diff(repo_path: Path, file_path: str) -> str:
    """获取单个文件的 diff 内容"""
    # 同时尝试 staged 和 unstaged 的 diff
    # 使用 HEAD 作为参考
    success, output = run_git_command(repo_path, ("diff", "HEAD", "--", file_path))
    if success and output:
        return output
    
    # 尝试获取 staged 的 diff
    success, output = run_git_command(repo_path, ("diff", "--cached", "--", file_path))
    if success and output:
        return output
    
    # 再尝试获取 unstaged 的 diff
    success, output = run_git_command(repo_path, ("diff", "--", file_path))
    if success and output:
        return output
    
    # 对于新文件（未跟踪），显示文件内容
    full_path = repo_path / file_path
    if full_path.exists():
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            # 格式化为类似 diff 的输出
            diff_lines = [f"+++ {file_path}", f"@@ -0,0 +1,{len(lines)} @@"]
            diff_lines.extend(f"+{line}" for line in lines[:100])
            if len(lines) > 100:
                diff_lines.append(f"... 还有 {len(lines) - 100} 行 ...")
            return "\n".join(diff_lines)
        except Exception:
            pass
    
    return f"无法获取 {file_path} 的 diff 内容"


def get_status_files_with_diff(repo_path: Path) -> list[tuple[str, str, str]]:
    """
    获取仓库中带状态标识的文件列表和 diff 内容。
    
    Returns:
        [(状态标识, 文件路径, diff内容), ...] 
        状态标识: +=新增, M=修改, -=删除, ?=未跟踪
    """
    files = []
    
    # 使用 git status --porcelain 获取状态
    success, output = run_git_command(repo_path, ("status", "--porcelain"))
    if success and output:
        for line in output.strip().split("\n"):
            if not line:
                continue
            
            # 直接使用 split 方式解析，更可靠
            parts = line.split(None, 1)  # 按空白分割，最多分割一次
            if len(parts) == 2:
                status_raw = parts[0]
                file_path = parts[1]
            elif len(parts) == 1:
                # 未跟踪文件等特殊情况
                status_raw = line[:2]
                file_path = line[3:] if len(line) > 3 else ""
            else:
                continue
            
            # 转换状态标识
            if "A" in status_raw:
                status_char = "+"  # 新增
            elif "M" in status_raw:
                status_char = "M"  # 修改
            elif "D" in status_raw:
                status_char = "-"  # 删除
            elif status_raw.strip() == "??":
                status_char = "?"  # 未跟踪
            elif "R" in status_raw:
                status_char = "R"  # 重命名
            else:
                status_char = status_raw.strip()[0] if status_raw.strip() else "?"
            
            # 获取该文件的 diff 内容
            diff_content = get_file_diff(repo_path, file_path)
            
            files.append((status_char, file_path, diff_content))
    
    return files


def get_status_files(repo_path: Path) -> list[tuple[str, str]]:
    """
    获取仓库中带状态标识的文件列表。
    
    Returns:
        [(状态标识, 文件路径), ...] 
        状态标识: +=新增, M=修改, -=删除, ?=未跟踪
    """
    files = []
    
    # 使用 git status --porcelain 获取状态
    success, output = run_git_command(repo_path, ("status", "--porcelain"))
    if success and output:
        for line in output.strip().split("\n"):
            if not line:
                continue
            
            if len(line) >= 3:
                # 使用 split 方式更可靠
                parts = line.split(None, 1)  # 按空白分割，最多分割一次
                if len(parts) == 2:
                    status_raw = parts[0]
                    file_path = parts[1]
                elif len(parts) == 1:
                    # 可能是未跟踪文件
                    status_raw = line[:2]
                    file_path = line[3:] if len(line) > 3 else ""
                else:
                    continue
                
                # 转换状态标识
                if "A" in status_raw:
                    status_char = "+"  # 新增
                elif "M" in status_raw:
                    status_char = "M"  # 修改
                elif "D" in status_raw:
                    status_char = "-"  # 删除
                elif status_raw.strip() == "??":
                    status_char = "?"  # 未跟踪
                elif "R" in status_raw:
                    status_char = "R"  # 重命名
                else:
                    status_char = status_raw.strip()[0] if status_raw.strip() else "?"
                
                files.append((status_char, file_path))
    
    return files


def has_changes(repo_path: Path) -> tuple[bool, bool, list[str]]:
    """检查仓库是否有更改"""
    staged_success, staged_output = run_git_command(repo_path, ("diff", "--cached", "--name-only"))
    has_staged = staged_success and bool(staged_output.strip())
    
    unstaged_success, unstaged_output = run_git_command(repo_path, ("diff", "--name-only"))
    has_unstaged = unstaged_success and bool(unstaged_output.strip())
    
    success, output = run_git_command(repo_path, ("ls-files", "--others", "--exclude-standard"))
    untracked = output.strip().split("\n") if success and output else []
    
    return has_staged, has_unstaged, untracked


@click.command()
@click.option(
    "-d", "--directory",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="指定要搜索的目录，默认为当前目录",
)
@click.option(
    "-m", "--model",
    default=None,
    help="指定 AI 模型",
)
@click.option(
    "-a", "--auto-stage",
    is_flag=True,
    help="自动暂存所有更改后再生成提交信息",
)
@click.option(
    "-y", "--yes",
    is_flag=True,
    help="跳过确认直接提交",
)
def acm(directory: str, model: str | None, auto_stage: bool, yes: bool) -> None:
    """
    \b
    自动生成 Git 提交信息 (Auto Commit Message)
    
    \b
    检测所有 Git 项目的待提交文件，调用 AI 接口
    自动生成符合 Conventional Commits 规范的提交信息。
    
    \b
    示例:
        esntool acm
        esntool acm -a          # 自动暂存所有更改
        esntool acm -y          # 跳过确认直接提交
        esntool acm -m Qwen/Qwen2.5-32B-Instruct
    """
    from esn_tool.utils.ai import AIClient, generate_commit_message
    
    base_path = Path(directory)
    git_repos = find_git_repos(base_path)
    
    if not git_repos:
        console.print(f"[yellow]⚠ 在 {base_path} 下未找到任何 Git 项目[/yellow]")
        return
    
    # 初始化 AI 客户端
    try:
        client = AIClient(model=model) if model else AIClient()
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        console.print("[dim]提示: 运行 'esntool config' 配置 API Key[/dim]")
        return
    
    console.print(f"\n[bold cyan]📂 在 {base_path} 下找到 {len(git_repos)} 个 Git 项目[/bold cyan]")
    console.print(f"[dim]使用模型: {client.model}[/dim]\n")
    
    # 检查每个仓库的更改
    repos_with_changes: list[tuple[Path, str]] = []
    
    for repo in git_repos:
        has_staged, has_unstaged, untracked = has_changes(repo)
        
        if not has_staged and not has_unstaged and not untracked:
            continue
        
        # 如果需要自动暂存
        if auto_stage and (has_unstaged or untracked):
            run_git_command(repo, ("add", "-A"))
            has_staged = True
        
        # 获取 diff
        if has_staged:
            diff = get_git_diff(repo, staged=True)
        elif has_unstaged:
            diff = get_git_diff(repo, staged=False)
        else:
            continue
        
        if diff:
            repos_with_changes.append((repo, diff))
    
    if not repos_with_changes:
        console.print("[yellow]⚠ 没有发现需要提交的更改[/yellow]")
        return
    
    console.print(f"[bold]发现 {len(repos_with_changes)} 个项目有待提交的更改[/bold]\n")
    
    # 先显示所有项目的更改概览表格
    overview_table = Table(show_header=True, header_style="bold", expand=False)
    overview_table.add_column("项目", style="cyan", min_width=15)
    overview_table.add_column("更改的文件", style="white")
    
    for repo, diff in repos_with_changes:
        # 获取带状态标识的文件列表
        status_files = get_status_files(repo)
        
        # 格式化文件列表
        file_lines = []
        for status, file_path in status_files[:10]:
            # 根据状态设置颜色
            if status == "+":
                file_lines.append(f"[green]{status}[/green] {file_path}")
            elif status == "-":
                file_lines.append(f"[red]{status}[/red] {file_path}")
            elif status == "M":
                file_lines.append(f"[yellow]{status}[/yellow] {file_path}")
            else:
                file_lines.append(f"[dim]{status}[/dim] {file_path}")
        
        if len(status_files) > 10:
            file_lines.append(f"[dim]... 还有 {len(status_files) - 10} 个文件[/dim]")
        
        overview_table.add_row(repo.name, "\n".join(file_lines))
    
    console.print(overview_table)
    console.print()
    
    # 为每个有更改的仓库处理
    for repo, diff in repos_with_changes:
        console.print(Panel(f"[bold cyan]{repo.name}[/bold cyan]", expand=False))
        
        # 获取带 diff 的文件列表
        files_with_diff = get_status_files_with_diff(repo)
        
        if not files_with_diff:
            console.print("[yellow]没有可提交的文件[/yellow]\n")
            continue
        
        # 如果指定了 -y 选项，直接提交所有文件
        if yes:
            selected_files = files_with_diff
        else:
            # 显示交互式文件选择器
            try:
                from esn_tool.ui.file_selector import select_files_interactive
                selected_files = select_files_interactive(files_with_diff, repo.name)
            except Exception as e:
                console.print(f"[yellow]交互式选择器加载失败，使用全部文件: {e}[/yellow]")
                selected_files = files_with_diff
        
        if not selected_files:
            console.print("[yellow]未选择任何文件，已跳过[/yellow]\n")
            continue
        
        console.print(f"\n[bold]选中 {len(selected_files)} 个文件[/bold]")
        
        # 构建选中文件的 diff 内容
        selected_diff = "\n\n".join(
            f"文件: {file_path}\n{diff_content}"
            for status, file_path, diff_content in selected_files
        )
        
        # 调用 AI 生成提交信息
        with console.status("[dim]正在生成提交信息...[/dim]"):
            try:
                commit_msg = generate_commit_message(selected_diff, client)
            except Exception as e:
                console.print(f"[red]✗ 生成失败: {e}[/red]\n")
                continue
        
        # 显示生成的提交信息
        console.print("\n[bold green]生成的提交信息:[/bold green]")
        console.print(Panel(commit_msg.strip(), border_style="green"))
        
        # 确认并提交
        if yes or click.confirm("是否使用此提交信息提交?", default=True):
            # 只暂存选中的文件
            for status, file_path, _ in selected_files:
                run_git_command(repo, ("add", "--", file_path))
            
            # 提交
            success, output = run_git_command(repo, ("commit", "-m", commit_msg.strip()))
            
            if success:
                console.print(f"[green]✓ 提交成功[/green]\n")
            else:
                console.print(f"[red]✗ 提交失败: {output}[/red]\n")
        else:
            console.print("[yellow]已跳过[/yellow]\n")
