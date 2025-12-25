# toolbox-iop - JSON 处理工具箱

[![PyPI Version](https://img.shields.io/pypi/v/toolbox-iop.svg)](https://pypi.org/project/toolbox-iop/)
[![Python Versions](https://img.shields.io/pypi/pyversions/toolbox-iop.svg)](https://pypi.org/project/toolbox-iop)
[![License](https://img.shields.io/pypi/l/toolbox-iop.svg)](https://choosealicense.com/licenses/mit/)

> The essential toolbox for JSON operations: loading, saving, printing, and more.  
> JSON 操作必备工具箱：加载、保存、打印等实用功能

---

## Features / 功能特点

- 🚀 **Advanced Printing** - Flexible file reading with multiple options  
  **高级打印** - 支持多种选项的灵活文件读取
- 🎲 **Random Access** - Read lines in random order  
  **随机访问** - 支持随机顺序读取内容
- 🔍 **Keyword Filtering** - Find specific content by keywords  
  **关键词过滤** - 通过关键词筛选特定内容
- 🔁 **Loop Mode** - Continuously display all content  
  **循环模式** - 持续显示所有内容
- 📊 **Quantity Control** - Read specific amount of content  
  **数量控制** - 读取特定数量的内容
- ⚙️ **Output Control** - Toggle printing as needed  
  **输出控制** - 根据需要开关打印输出
- ✔️ **Python 3.6+** - Compatible with modern Python versions  
  **Python 3.6+** - 兼容现代 Python 版本

---

## Installation / 安装

```bash
pip install toolbox-iop
```

---

## Command Line Tools / 命令行工具

### 1. Print File Content / 打印文件内容
```bash
toolbox-iop-print path/to/file.json [options]
```
功能特点：
- Multiple reading modes / 多种读取模式
- Keyword filtering / 关键词过滤
- Content output control / 内容输出控制
- Quantity control / 数量控制

#### 参数 / Arguments
| 选项 | 描述 | 默认值 |
|------|------|--------|
| `file_path` | File path to read | (必需) |
| 文件路径 | 要读取的文件路径 | (必需) |
| `-r, --random` | Read lines in random order | False |
| `-r, --random` | 随机顺序读取内容 | 关闭 |
| `-k KEY, --key KEY` | Filter lines by keyword | "" (all) |
| `-k KEY, --key KEY` | 按关键词过滤行 | "" (全部) |
| `-a, --all` | Continuously display all content | False |
| `-a, --all` | 持续显示所有内容 | 关闭 |
| `-n NUMBER, --number NUMBER` | Number of lines to read | "1.0" (all) |
| `-n NUMBER, --number NUMBER` | 读取的行数 | "1.0" (全部) |
| `--print_off` | Disable output printing | True (print on) |
| `--print_off` | 关闭打印输出 | 开启 |

### 2. Check for Duplicates / 检查ID字段重复项
```bash
toolbox-iop-duplicate path/to/file.json --key KEY
```
功能特点：
- Duplicate key detection / 重复键检测。默认为`id`字段
- JSON structure validation / JSON 结构验证
- Progress visualization / 进度可视化


---

## Usage Examples / 使用示例

### Basic File Reading / 基础文件读取
```bash
# Read single file / 读取单个文件
toolbox-iop-print data.json

# Read random lines / 随机读取行
toolbox-iop-print log.txt -r

# Filter by keyword / 按关键词过滤
toolbox-iop-print records.json -k "error"

# Continuous display / 持续显示内容
toolbox-iop-print stream.json -a

# Read specific quantity / 读取特定数量
toolbox-iop-print log.txt -n 10  # Read 10 lines
toolbox-iop-print data.json -n 0.5  # Read 50% of content
```

### Duplicate Checking / 重复项检查
```bash
# Check file / 检查文件
toolbox-iop-duplicate data.json

toolbox-iop-duplicate data.json --key name

```


---

## Dependencies / 依赖项

- [Rich](https://github.com/Textualize/rich) - Terminal formatting / 终端格式化
- [tqdm](https://github.com/tqdm/tqdm) - Progress bars / 进度条显示

---

## Contributing / 贡献指南

Contributions are welcome! Please open an issue or submit a PR:  
欢迎贡献代码！请提交 issue 或 PR:  
[https://github.com/yourusername/toolbox-iop](https://github.com/yourusername/toolbox-iop)

---

## License / 许可证

MIT License - Free for personal and commercial use  
MIT 许可证 - 可免费用于个人和商业用途