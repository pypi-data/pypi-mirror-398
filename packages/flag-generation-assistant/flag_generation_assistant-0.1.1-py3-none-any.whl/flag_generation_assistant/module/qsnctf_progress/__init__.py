import sys
import time

# ANSI 颜色
COLORS = [
    "\033[31m", "\033[33m", "\033[32m",
    "\033[36m", "\033[34m", "\033[35m"
]
BLUE = "\033[34m"
RESET = "\033[0m"

def rainbow_progress(current, total, width=40, show_percent=True):
    # 1. 旋转字符序列
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]  # 这里换了一组更现代的盲文点阵
    
    # 2. 计算当前帧的索引
    frame_idx = current % len(spinner_frames)
    color_idx = current % len(COLORS)
    
    # 3. 组合彩色的 spinner
    spinner = f"{COLORS[color_idx]}{spinner_frames[frame_idx]}{RESET}"

    percent = current / total if total else 0
    filled = int(width * percent)

    # 进度条主体
    bar = ""
    for i in range(filled):
        bar += COLORS[i % len(COLORS)] + "█"
    bar += RESET + "-" * (width - filled)

    # 拼接最终输出：spinner + [进度条] + 百分比
    output = f"\r{spinner} {BLUE}[{RESET}{bar}{BLUE}]{RESET}"
    if show_percent:
        output += f" {BLUE}{percent:.0%}{RESET}"

    sys.stdout.write(output)
    sys.stdout.flush()