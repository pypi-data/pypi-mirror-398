"""FlaxKV2 MCP CLI 命令

提供 MCP 服务的安装和管理命令。
"""

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Literal

from rich import print
from rich.console import Console

console = Console()

# 支持的目标类型
TargetType = Literal["desktop", "code", "all"]


def get_claude_desktop_config_path() -> Path:
    """获取 Claude Desktop 配置文件路径"""
    system = platform.system()

    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        raise RuntimeError(f"不支持的操作系统: {system}")


def get_claude_code_config_path() -> Path:
    """获取 Claude Code 配置文件路径"""
    return Path.home() / ".claude.json"


def get_flaxkv2_mcp_command() -> list[str]:
    """获取 flaxkv2-mcp 命令"""
    # 检查 flaxkv2-mcp 是否在 PATH 中
    if shutil.which("flaxkv2-mcp"):
        # 使用命令名而非绝对路径，更简洁且便于跨环境使用
        return ["flaxkv2-mcp"]

    # 回退到 python -m
    return [sys.executable, "-m", "flaxkv2.mcp"]


def _install_to_config(config_path: Path, name: str, target_name: str) -> bool:
    """安装 MCP 服务到指定配置文件

    Returns:
        True 成功，False 失败
    """
    # 确保配置目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取现有配置
    config = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            console.print(f"[yellow]警告:[/yellow] {target_name} 配置文件格式错误，将创建新配置")

    # 确保 mcpServers 字段存在
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # 获取命令
    command = get_flaxkv2_mcp_command()

    # 添加 flaxkv2 MCP 服务配置
    config["mcpServers"][name] = {
        "type": "stdio",
        "command": command[0],
        "args": command[1:] if len(command) > 1 else [],
    }

    # 写入配置
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        console.print(f"[bold red]错误:[/bold red] 无法写入 {target_name} 配置文件: {e}")
        return False


def _uninstall_from_config(config_path: Path, name: str, target_name: str) -> bool:
    """从指定配置文件移除 MCP 服务

    Returns:
        True 成功移除，False 未找到或失败
    """
    if not config_path.exists():
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        return False

    if "mcpServers" not in config or name not in config["mcpServers"]:
        return False

    del config["mcpServers"][name]

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def _show_config_status(config_path: Path, target_name: str):
    """显示单个配置文件的状态"""
    console.print(f"\n[bold]{target_name} 配置:[/bold]")
    console.print(f"  路径: [bold blue]{config_path}[/bold blue]")
    console.print(f"  存在: {'[green]是[/green]' if config_path.exists() else '[yellow]否[/yellow]'}")

    if not config_path.exists():
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        console.print("  [red]配置文件格式错误[/red]")
        return

    mcp_servers = config.get("mcpServers", {})
    if mcp_servers:
        console.print("  已安装的 MCP 服务:")
        for name, server_config in mcp_servers.items():
            command = server_config.get("command", "N/A")
            is_flaxkv2 = "flaxkv2" in name.lower() or "flaxkv2" in str(command)
            marker = "[green]*[/green]" if is_flaxkv2 else " "
            console.print(f"    {marker} [cyan]{name}[/cyan]")


class MCPCommands:
    """MCP 服务管理命令"""

    def install(self, name: str = "flaxkv2", target: str = "all"):
        """
        安装 FlaxKV2 MCP 服务

        Args:
            name: MCP 服务名称（默认: flaxkv2）
            target: 安装目标 - 'desktop'(Claude Desktop), 'code'(Claude Code), 'all'(两者)

        示例:
            # 安装到所有目标（推荐）
            flaxkv2 mcp install

            # 仅安装到 Claude Code
            flaxkv2 mcp install --target code

            # 仅安装到 Claude Desktop
            flaxkv2 mcp install --target desktop

            # 自定义服务名称
            flaxkv2 mcp install --name my-flaxkv2
        """
        command = get_flaxkv2_mcp_command()
        installed_targets = []

        # Claude Desktop
        if target in ("desktop", "all"):
            try:
                desktop_path = get_claude_desktop_config_path()
                if _install_to_config(desktop_path, name, "Claude Desktop"):
                    installed_targets.append(("Claude Desktop", desktop_path))
            except RuntimeError:
                if target == "desktop":
                    console.print("[bold red]错误:[/bold red] 不支持的操作系统")
                    return

        # Claude Code
        if target in ("code", "all"):
            code_path = get_claude_code_config_path()
            if _install_to_config(code_path, name, "Claude Code"):
                installed_targets.append(("Claude Code", code_path))

        if not installed_targets:
            console.print("[bold red]错误:[/bold red] 安装失败")
            return

        console.print(f"\n[bold green]FlaxKV2 MCP 服务安装成功[/bold green]\n")
        console.print(f"服务名称: [bold blue]{name}[/bold blue]")
        console.print(f"命令: [bold blue]{' '.join(command)}[/bold blue]")
        console.print(f"\n已安装到:")
        for target_name, config_path in installed_targets:
            console.print(f"  - {target_name}: [dim]{config_path}[/dim]")

        console.print(f"\n[dim]请重启 Claude Desktop/Code 以使配置生效[/dim]")

    def uninstall(self, name: str = "flaxkv2", target: str = "all"):
        """
        移除 FlaxKV2 MCP 服务

        Args:
            name: MCP 服务名称（默认: flaxkv2）
            target: 移除目标 - 'desktop', 'code', 'all'

        示例:
            flaxkv2 mcp uninstall
            flaxkv2 mcp uninstall --target code
        """
        removed_targets = []

        # Claude Desktop
        if target in ("desktop", "all"):
            try:
                desktop_path = get_claude_desktop_config_path()
                if _uninstall_from_config(desktop_path, name, "Claude Desktop"):
                    removed_targets.append("Claude Desktop")
            except RuntimeError:
                pass

        # Claude Code
        if target in ("code", "all"):
            code_path = get_claude_code_config_path()
            if _uninstall_from_config(code_path, name, "Claude Code"):
                removed_targets.append("Claude Code")

        if removed_targets:
            console.print(f"\n[bold green]FlaxKV2 MCP 服务已移除[/bold green]")
            console.print(f"从以下位置移除: {', '.join(removed_targets)}")
            console.print(f"\n[dim]请重启 Claude Desktop/Code 以使配置生效[/dim]")
        else:
            console.print(f"[yellow]未找到名为 '{name}' 的 MCP 服务[/yellow]")

    def status(self):
        """
        查看 FlaxKV2 MCP 服务安装状态

        示例:
            flaxkv2 mcp status
        """
        # Claude Desktop
        try:
            desktop_path = get_claude_desktop_config_path()
            _show_config_status(desktop_path, "Claude Desktop")
        except RuntimeError:
            pass

        # Claude Code
        code_path = get_claude_code_config_path()
        _show_config_status(code_path, "Claude Code")

        # 检查 mcp 依赖是否安装
        console.print(f"\n[bold]依赖状态:[/bold]")
        try:
            import mcp

            console.print(f"  mcp: [green]已安装[/green]")
        except ImportError:
            console.print(f"  mcp: [red]未安装[/red] (运行 'pip install flaxkv2[mcp]')")

    def test(self):
        """
        测试 FlaxKV2 MCP 服务是否正常工作

        示例:
            flaxkv2 mcp test
        """
        console.print("\n[bold]测试 FlaxKV2 MCP 服务...[/bold]\n")

        # 检查依赖
        try:
            from flaxkv2.mcp import mcp

            console.print("[green]OK[/green] MCP 模块导入成功")
        except ImportError as e:
            console.print(f"[red]FAIL[/red] MCP 模块导入失败: {e}")
            console.print("\n请安装 mcp 依赖: pip install flaxkv2[mcp]")
            return

        # 检查文档
        try:
            from flaxkv2.mcp.docs import DOCS, TOPICS

            console.print(f"[green]OK[/green] 文档加载成功 ({len(TOPICS)} 个主题)")
        except ImportError as e:
            console.print(f"[red]FAIL[/red] 文档加载失败: {e}")
            return

        # 检查命令
        command = get_flaxkv2_mcp_command()
        console.print(f"[green]OK[/green] MCP 命令: {' '.join(command)}")

        console.print("\n[bold green]所有测试通过[/bold green]")
