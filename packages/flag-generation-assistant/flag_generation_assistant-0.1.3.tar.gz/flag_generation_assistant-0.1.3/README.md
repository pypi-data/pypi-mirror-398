# 青少年CTF FLAG生成器

一个专为青少年CTF竞赛设计的FLAG生成工具，支持多种FLAG生成方式，界面美观易用。

## 功能特性

### 🔑 FLAG生成方式

1. **基于UUID生成 (随机型)**
   - 自动生成唯一的UUID
   - 格式：`flag{uuid}`
   - 适用于需要唯一标识符的场景

2. **基于MD5生成 (哈希型)**
   - 自动生成随机的MD5
   - 格式：`flag{md5_hash}`

3. **基于语义化字符串 (L33t变体)**
   - 支持L33t Sp34k转换
   - 字符替换规则：
     - A → 4
     - B → 8  
     - E → 3
     - G → 6
     - L → 1
     - O → 0
     - S → 5
     - T → 7
     - Z → 2
     - I → !
   - 格式：`flag{l33t_text}`
   - 适用于需要趣味性和可读性的FLAG

### 🎨 界面特色

- 使用 `rich` 库实现彩色终端输出
- 使用 `questionary` 提供交互式菜单
- 支持中文界面，操作简单直观
- 美观的ASCII艺术标题

## 安装要求

### Python版本
- Python 3.7+

## PIP安装
```bash
pip install flag-generation-assistant
```

## 运行
```bash

flag_generation_assistant
flag
flag_generator

```

### 依赖包
```bash
pip install rich questionary
```

## 使用方法

1. **启动程序**
   ```bash
   python main.py
   ```

2. **选择功能**
   - 使用方向键选择菜单选项
   - 按回车确认选择

3. **生成FLAG**
   - 根据提示输入相应内容
   - 程序会自动生成并显示FLAG

## 项目结构

```
Flag Generator/
├── main.py                 # 主程序入口
├── config.yml              # 配置文件
├── README.md               # 项目说明
└── module/                 # 功能模块
    ├── qsnctf_welcome.py   # 欢迎界面模块
    └── flag_generator.py   # FLAG生成器核心模块
```

## 配置说明

### config.yml
```yaml
title: 青少年CTF工具示例
version: 1.0.0
flag_format: "flag{.*}"
```

- `title`: 程序标题
- `version`: 版本号
- `flag_format`: FLAG格式正则表达式

## 开发说明

### 添加新的FLAG生成方式

1. 在 `module/flag_generator.py` 中添加新的生成函数
2. 在 `flag_generator_menu()` 函数中添加菜单选项
3. 更新主菜单调用

### 示例代码结构

```python
def generate_flag_custom():
    """自定义FLAG生成函数"""
    # 实现生成逻辑
    pass

def flag_generator_menu():
    # 添加菜单选项
    choices = [
        "🔑 根据UUID生成FLAG",
        "🔒 根据MD5生成FLAG", 
        "💬 根据语义化字符串生成FLAG",
        "🆕 自定义生成方式",  # 新增选项
        "⬅️ 返回主菜单"
    ]
    # 添加处理逻辑
```

## 使用示例

### UUID FLAG生成
```
生成的FLAG: flag{123e4567-e89b-12d3-a456-426614174000}
```

### MD5 FLAG生成
```
输入的文本: hello world
MD5哈希值: 5eb63bbbe01eeed093cb22bb8f5acdc3
生成的FLAG: flag{5eb63bbbe01eeed093cb22bb8f5acdc3}
```

### L33t Sp34k FLAG生成
```
原始字符串: HELLO WORLD
L33t Sp34k转换: H3LL0 W0RLD
生成的FLAG: flag{H3LL0 W0RLD}
```

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

本项目采用MIT许可证。

## 联系方式

如有问题或建议，请通过项目Issue进行反馈。