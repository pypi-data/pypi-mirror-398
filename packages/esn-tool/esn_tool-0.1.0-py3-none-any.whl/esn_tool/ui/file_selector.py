"""
交互式文件选择器模块

使用 Textual 实现分栏布局的文件多选界面。
"""

from pathlib import Path
from typing import Callable

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static, RichLog
from textual.reactive import reactive
from rich.text import Text


class FileItem(ListItem):
    """文件列表项"""
    
    def __init__(self, status: str, file_path: str, diff_content: str = "") -> None:
        super().__init__()
        self.status = status
        self.file_path = file_path
        self.diff_content = diff_content
        self.selected = False
    
    def compose(self) -> ComposeResult:
        yield Label(self._get_label_text(), id="file-label")
    
    def _get_label_text(self) -> str:
        """生成标签文本"""
        # 根据状态设置颜色
        if self.status == "+":
            status_style = "green"
        elif self.status == "-":
            status_style = "red"
        elif self.status == "M":
            status_style = "yellow"
        else:
            status_style = "dim"
        
        checkbox = "☑" if self.selected else "☐"
        return f"{checkbox} [{status_style}]{self.status}[/{status_style}] {self.file_path}"
    
    def toggle_selection(self) -> None:
        """切换选中状态"""
        self.selected = not self.selected
        # 更新标签内容
        label = self.query_one("#file-label", Label)
        label.update(self._get_label_text())


class DiffPreview(Static):
    """Diff 预览面板"""
    
    DEFAULT_CSS = """
    DiffPreview {
        width: 100%;
        height: 100%;
        background: $surface;
        padding: 1;
        overflow-y: auto;
    }
    """
    
    def __init__(self, content: str = "", **kwargs) -> None:
        super().__init__(content, **kwargs)
    
    def update_diff(self, content: str) -> None:
        """更新 diff 内容"""
        if not content:
            self.update("[dim]选择文件查看 diff 内容[/dim]")
            return
        
        # 格式化 diff 以显示颜色，过滤掉头部元数据
        lines = []
        for line in content.split("\n")[:500]:  # 最多显示500行
            # 跳过 diff 头部元数据
            if line.startswith("diff --git"):
                continue
            if line.startswith("index "):
                continue
            if line.startswith("---"):
                continue
            if line.startswith("+++"):
                continue
            
            # 格式化显示
            if line.startswith("+"):
                lines.append(f"[green]{self._escape(line)}[/green]")
            elif line.startswith("-"):
                lines.append(f"[red]{self._escape(line)}[/red]")
            elif line.startswith("@@"):
                lines.append(f"[cyan]{self._escape(line)}[/cyan]")
            else:
                lines.append(self._escape(line))
        
        if len(content.split("\n")) > 500:
            lines.append("\n[dim]... 内容过长，已截断 ...[/dim]")
        
        self.update("\n".join(lines))
    
    def _escape(self, text: str) -> str:
        """转义特殊字符"""
        return text.replace("[", "\\[").replace("]", "\\]")


class FileSelectApp(App):
    """文件选择器应用"""
    
    CSS = """
    #main-container {
        layout: horizontal;
    }
    
    #file-list-container {
        width: 50%;
        height: 100%;
        border: solid $primary;
    }
    
    #diff-container {
        width: 50%;
        height: 100%;
        border: solid $secondary;
    }
    
    #file-list-title {
        dock: top;
        height: 1;
        padding: 0 1;
        background: $primary;
        color: $text;
    }
    
    #diff-title {
        dock: top;
        height: 1;
        padding: 0 1;
        background: $secondary;
        color: $text;
    }
    
    ListView {
        height: 1fr;
        overflow-x: auto;
    }
    
    FileItem {
        height: auto;
    }
    
    #diff-log {
        height: 1fr;
    }
    
    #diff-log:focus {
        border: solid $accent;
    }
    """
    
    BINDINGS = [
        Binding("space", "toggle_select", "选择/取消"),
        Binding("a", "select_all", "全选"),
        Binding("n", "select_none", "全不选"),
        Binding("c", "confirm", "确认提交"),
        Binding("q", "quit", "取消"),
        Binding("tab", "switch_focus", "切换焦点", show=False),
        Binding("left", "focus_files", "文件列表", show=False),
        Binding("right", "focus_diff", "预览区", show=False),
        Binding("j", "scroll_down", "向下", show=False),
        Binding("k", "scroll_up", "向上", show=False),
    ]
    
    def __init__(
        self,
        files: list[tuple[str, str, str]],  # [(status, file_path, diff_content), ...]
        repo_name: str = "",
    ) -> None:
        super().__init__()
        self.files = files
        self.repo_name = repo_name
        self.result: list[tuple[str, str, str]] = []  # 选中的文件
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal(id="main-container"):
            with Vertical(id="file-list-container"):
                yield Label(f"📁 {self.repo_name} (空格选择, c确认)", id="file-list-title")
                with ListView(id="file-list"):
                    for status, file_path, diff_content in self.files:
                        yield FileItem(status, file_path, diff_content)
            
            with Vertical(id="diff-container"):
                yield Label("📄 Diff 预览 (j/k滚动)", id="diff-title")
                yield RichLog(id="diff-log", highlight=True, markup=True)
        
        yield Footer()
    
    @on(ListView.Highlighted)
    def on_file_highlighted(self, event: ListView.Highlighted) -> None:
        """当文件被高亮时，显示其 diff 内容"""
        if event.item and isinstance(event.item, FileItem):
            log = self.query_one("#diff-log", RichLog)
            log.clear()
            self._write_diff_to_log(log, event.item.diff_content)
    
    def _write_diff_to_log(self, log: RichLog, content: str) -> None:
        """将 diff 内容写入 RichLog"""
        if not content:
            log.write("[dim]选择文件查看 diff 内容[/dim]")
            return
        
        for line in content.split("\n"):
            # 跳过 diff 头部元数据
            if line.startswith("diff --git"):
                continue
            if line.startswith("index "):
                continue
            if line.startswith("---"):
                continue
            if line.startswith("+++"):
                continue
            
            # 格式化显示
            if line.startswith("+"):
                log.write(Text(line, style="green"))
            elif line.startswith("-"):
                log.write(Text(line, style="red"))
            elif line.startswith("@@"):
                log.write(Text(line, style="cyan"))
            else:
                log.write(line)
    
    def action_toggle_select(self) -> None:
        """切换当前文件的选中状态"""
        list_view = self.query_one("#file-list", ListView)
        if list_view.highlighted_child and isinstance(list_view.highlighted_child, FileItem):
            list_view.highlighted_child.toggle_selection()
    
    def action_select_all(self) -> None:
        """全选"""
        for item in self.query(FileItem):
            item.selected = True
            label = item.query_one("#file-label", Label)
            label.update(item._get_label_text())
    
    def action_select_none(self) -> None:
        """全不选"""
        for item in self.query(FileItem):
            item.selected = False
            label = item.query_one("#file-label", Label)
            label.update(item._get_label_text())
    
    def action_confirm(self) -> None:
        """确认选择"""
        self.result = [
            (item.status, item.file_path, item.diff_content)
            for item in self.query(FileItem)
            if item.selected
        ]
        self.exit()
    
    def action_quit(self) -> None:
        """取消"""
        self.result = []
        self.exit()
    
    def action_switch_focus(self) -> None:
        """切换焦点"""
        if self.query_one("#file-list", ListView).has_focus:
            self.query_one("#diff-log", RichLog).focus()
        else:
            self.query_one("#file-list", ListView).focus()
    
    def action_focus_files(self) -> None:
        """焦点移到文件列表"""
        self.query_one("#file-list", ListView).focus()
    
    def action_focus_diff(self) -> None:
        """焦点移到 diff 预览"""
        self.query_one("#diff-log", RichLog).focus()
    
    def action_scroll_down(self) -> None:
        """向下滚动 diff"""
        log = self.query_one("#diff-log", RichLog)
        log.scroll_down(animate=False)
    
    def action_scroll_up(self) -> None:
        """向上滚动 diff"""
        log = self.query_one("#diff-log", RichLog)
        log.scroll_up(animate=False)


def select_files_interactive(
    files: list[tuple[str, str, str]],
    repo_name: str = "",
) -> list[tuple[str, str, str]]:
    """
    交互式选择文件。
    
    Args:
        files: [(status, file_path, diff_content), ...]
        repo_name: 仓库名称
        
    Returns:
        选中的文件列表
    """
    app = FileSelectApp(files, repo_name)
    app.run()
    return app.result
