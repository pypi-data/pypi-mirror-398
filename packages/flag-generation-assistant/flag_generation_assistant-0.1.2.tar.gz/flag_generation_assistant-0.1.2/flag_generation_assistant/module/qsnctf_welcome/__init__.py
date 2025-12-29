import yaml

# ANSI 彩虹色
COLORS = [
    "\033[31m",  # 红
    "\033[33m",  # 黄
    "\033[32m",  # 绿
    "\033[36m",  # 青
    "\033[34m",  # 蓝
    "\033[35m",  # 紫
]

RESET = "\033[0m"
BOLD = "\033[1m"


# 按行彩虹（给 ASCII Art 用）
def rainbow_print_lines(text):
    for i, line in enumerate(text.splitlines()):
        color = COLORS[i % len(COLORS)]
        print(color + line + RESET)


# 按字符渐变彩虹（给标题 / 版本用）
def rainbow_print_chars(text, bold=False):
    output = ""
    color_index = 0

    for ch in text:
        if ch.strip() == "":
            output += ch
            continue

        color = COLORS[color_index % len(COLORS)]
        style = BOLD if bold else ""
        output += f"{style}{color}{ch}{RESET}"
        color_index += 1

    print(output)


def hello():
    art = """
  █████    ██████  ███▄    █  ▄████▄  ▄▄▄█████▓  █████▒
▒██▓  ██▒▒██    ▒  ██ ▀█   █ ▒██▀ ▀█  ▓  ██▒ ▓▒▓██   ▒ 
▒██▒  ██░░ ▓██▄   ▓██  ▀█ ██▒▒▓█    ▄ ▒ ▓██░ ▒░▒████ ░ 
░██  █▀ ░  ▒   ██▒▓██▒  ▐▌██▒▒▓▓▄ ▄██▒░ ▓██▓ ░ ░▓█▒  ░ 
░▒███▒█▄ ▒██████▒▒▒██░   ▓██░▒ ▓███▀ ░  ▒██▒ ░ ░▒█░    
░░ ▒▒░ ▒ ▒ ▒▓▒ ▒ ░░ ▒░   ▒ ▒ ░ ░▒ ▒  ░  ▒ ░░    ▒ ░    
 ░ ▒░  ░ ░ ░▒  ░ ░░ ░░   ░ ▒░  ░  ▒       ░     ░      
   ░   ░ ░  ░  ░     ░   ░ ░ ░          ░       ░ ░    
    ░          ░           ░ ░ ░                       
                             ░
    """

    # ASCII Art（普通彩虹）
    rainbow_print_lines(art)

    # 读取配置
    with open("config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print()  # 空行

    # 标题：更亮 + 更粗 + 按字符渐变
    rainbow_print_chars(f"{config['title']}", bold=True)

    # 版本：稍微弱一点，但仍然是字符渐变
    rainbow_print_chars(f"Version: {config['version']}", bold=False)


def about():
    art = """
    青少年CTF是一个专门为青少年网络安全爱好者打造，提供在线CTF比赛、题库练习和网络安全技能训练的全公益平台。
    """
    rainbow_print_chars(art)


def return_to_exit():
    input("\n按回车键退出程序...")
    exit()