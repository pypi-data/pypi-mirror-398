# word-latex-mcp

[![PyPI version](https://badge.fury.io/py/word-latex-mcp.svg)](https://badge.fury.io/py/word-latex-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Windows](https://img.shields.io/badge/platform-Windows-blue.svg)](https://www.microsoft.com/windows)

将 Word 文档中的 LaTeX 公式批量转换为原生数学公式的 MCP (Model Context Protocol) 工具。

## ✨ 功能特性

- ✅ **一键批量转换** - 将 `$...$` 和 `$$...$$` 格式的 LaTeX 公式转换为 Word 原生公式
- ✅ **多区域支持** - 支持正文、表格、页眉页脚、脚注、批注、文本框等
- ✅ **自动备份** - 转换前自动创建备份，安全可靠
- ✅ **智能识别** - 跳过金额（如 `$100$`）等误判场景
- ✅ **风险评估** - 6 种文档类型预设，适配不同场景
- ✅ **零配置运行** - 通过 `uvx` 按需下载运行，无需预装

## 📋 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 |
| Microsoft Word | 2016 或更高版本 |
| Python | 3.10+ |

> ⚠️ **注意**：由于使用 Windows COM 自动化，此工具仅支持 Windows 平台。

## 🚀 快速开始

### 1. 配置 Cursor MCP

将以下配置添加到 Cursor 的 MCP 配置文件：

**Windows 配置文件位置**：`%APPDATA%\Cursor\User\globalStorage\cursor.mcp\config.json`

```json
{
  "mcpServers": {
    "word-latex": {
      "command": "uvx",
      "args": ["word-latex-mcp"]
    }
  }
}
```

### 2. 重启 Cursor

配置完成后，重启 Cursor 以加载 MCP 工具。

### 3. 使用

1. **打开 Word 文档** - 在 Microsoft Word 中打开包含 LaTeX 公式的文档
2. **调用工具** - 在 Cursor 中告诉 AI：
   > "帮我把这个 Word 文档中的 LaTeX 公式转换为 Word 公式"
3. **查看结果** - AI 会调用 `convert_latex` 工具并返回转换报告

## 📖 工具参数

### convert_latex

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `mode` | string | `"quick"` | 运行模式 |
| `backup` | bool | `true` | 是否自动备份 |
| `work_on_copy` | bool | `false` | 是否在副本上操作 |
| `skip_money_patterns` | bool | `true` | 是否跳过金额模式 |
| `profile` | string | `"balanced"` | 文档类型预设 |
| `selection` | string | `"all"` | 选择策略 |

### 运行模式 (mode)

| 值 | 说明 |
|------|------|
| `quick` | 仅转换正文区域（含表格），速度最快 |
| `full` | 转换全部区域（含页眉页脚、脚注、批注等） |
| `scan` | 仅扫描统计，不做任何转换 |

### 文档类型预设 (profile)

| 值 | 说明 | 适用场景 |
|------|------|----------|
| `balanced` | 平衡模式 | 通用文档（默认） |
| `paper` | 论文模式 | 学术论文，更激进识别 |
| `engineering` | 工程模式 | 工程计算文档 |
| `strict` | 严格模式 | 减少误转换 |
| `contract` | 合同模式 | 避免金额误判 |
| `finance` | 财务模式 | 最保守，强金额保护 |

## 💡 使用示例

### 快速转换正文

```
用户：把这个文档的 LaTeX 公式转换一下
AI：我来帮您转换。[调用 convert_latex(mode='quick')]
```

### 扫描预览

```
用户：先看看文档里有多少公式
AI：我来扫描一下。[调用 convert_latex(mode='scan')]
```

### 全区域转换

```
用户：把所有区域的公式都转换，包括页眉页脚
AI：好的。[调用 convert_latex(mode='full')]
```

### 保守转换（合同类文档）

```
用户：这是份合同，帮我转换公式，但别把金额搞错了
AI：我用合同模式来处理。[调用 convert_latex(profile='contract')]
```

## 🔧 备选安装方式

### 方式一：pipx 运行

```json
{
  "mcpServers": {
    "word-latex": {
      "command": "pipx",
      "args": ["run", "word-latex-mcp"]
    }
  }
}
```

### 方式二：全局安装后运行

```bash
pip install word-latex-mcp
```

```json
{
  "mcpServers": {
    "word-latex": {
      "command": "word-latex-mcp"
    }
  }
}
```

## ❓ 常见问题

### Q: 提示"无法连接到 Word 应用程序"

**A**: 请确保：
1. Microsoft Word 已安装并能正常打开
2. 有一个 Word 文档处于打开状态

### Q: 转换后公式显示异常

**A**: 可能原因：
1. LaTeX 语法在 Word 中不支持 - 工具会保留原文本不破坏
2. Word 版本过低 - 建议使用 Word 2016 或更高版本

### Q: 某些公式被跳过了

**A**: 默认会跳过：
- 疑似金额的模式（如 `$100$`）
- 过长的片段
- 高风险内容

可使用 `skip_money_patterns=false` 关闭金额跳过，或使用 `selection='all'` 转换全部识别到的内容。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**Made with ❤️ for Word users who love LaTeX**



