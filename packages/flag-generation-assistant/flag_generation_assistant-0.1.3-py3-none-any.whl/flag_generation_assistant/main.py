import uuid
import hashlib
import yaml
import questionary
from rich.console import Console
import importlib.resources as pkg_resources

from .module.qsnctf_welcome import hello, about

console = Console()

# 1. 核心默认配置（内置 L33t 映射表）
DEFAULT_CONFIG = {
    "settings": {
        "flag_format": "flag{{{}}}"
    },
    "leet_map": {
        'A': '4', 'B': '8', 'E': '3', 'G': '6', 
        'L': '1', 'O': '0', 'S': '5', 'T': '7', 
        'Z': '2', 'I': '!'
    }
}

def load_config():
    try:
        with pkg_resources.open_text("flag_generation_assistant", "config.yml", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)
            if user_config:
                return user_config
    except Exception:
        pass
    return DEFAULT_CONFIG

# 全局初始化配置
CONFIG = load_config()

def to_leet_speak(text):
    """L33t Sp34k 转换逻辑"""
    mapping = CONFIG.get("leet_map", DEFAULT_CONFIG["leet_map"])
    res = ""
    for char in text.upper():
        res += str(mapping.get(char, char))
    return res

def generate_flag(content):
    """格式化最终 Flag"""
    fmt = CONFIG.get("settings", {}).get("flag_format", "flag{{{}}}")
    try:
        return fmt.format(content)
    except:
        return f"flag{{{content}}}"

def return_to_main_menu():
    input("\n按回车键返回主菜单...")
    main_menu()

def main_menu():
    # 欢迎信息
    hello()
    
    action = questionary.select(
        "请选择你要执行的操作:",
        choices=[
            "⭐ 基于 UUID 生成 (随机型)",
            "🪐 基于 MD5 生成 (哈希型)",
            "💦 基于语义化字符串 (L33t变体)",
            "💡 关于青少年CTF",
            "🔄 刷新本地配置",
            "❌ 退出程序"
        ],
        pointer="👉"
    ).ask()

    if action == "⭐ 基于 UUID 生成 (随机型)":
        val = str(uuid.uuid4())
        console.print(f"\n[bold green]生成成功:[/bold green] [yellow]{generate_flag(val)}[/yellow]")
        return_to_main_menu()

    elif action == "🪐 基于 MD5 生成 (哈希型)":
        val = str(uuid.uuid4())
        if val:
            val = hashlib.md5(val.encode()).hexdigest()
            console.print(f"\n[bold green]生成成功:[/bold green] [yellow]{generate_flag(val)}[/yellow]")
        return_to_main_menu()

    elif action == "💦 基于语义化字符串 (L33t变体)":
        raw = questionary.text("请输入语义化原文 (例如 Welcome):").ask()
        if raw:
            leet_val = to_leet_speak(raw)
            console.print(f"\n[bold cyan]L33t 转换结果:[/bold cyan] {leet_val}")
            console.print(f"[bold green]最终 Flag:[/bold green] [yellow]{generate_flag(leet_val)}[/yellow]")
        return_to_main_menu()

    elif action == "💡 关于青少年CTF":
        about()
        return_to_main_menu()

    elif action == "🔄 刷新本地配置":
        global CONFIG
        CONFIG = load_config()
        console.print("[bold green]配置刷新成功！(已同步自 config.yml)[/bold green]")
        return_to_main_menu()


def main():
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[bold red]程序已强制终止[/bold red]")

if __name__ == "__main__":
    main()