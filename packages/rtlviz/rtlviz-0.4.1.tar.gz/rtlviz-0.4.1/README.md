# RTLViz - AI-Powered RTL Diagram Generator

Generate beautiful, interactive block diagrams from Verilog source files.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🚀 Quick Start

### Step 1: Install

```bash
pip install rtlviz
```

> 💡 **Tip**: If you install without admin/root (e.g. `pip install --user`), the `rtlviz` command might not be in your PATH.
> You can always run it directly:
> ```bash
> python -m rtlviz generate ./src
> ```


### Step 2: Setup (Auto-configures your IDE)

```bash
rtlviz setup
```

This auto-detects and configures:
- ✅ Antigravity (Google DeepMind)
- ✅ Claude Desktop
- ✅ Cursor
- ✅ VS Code Copilot
- ✅ Windsurf

### Step 3: Use

**Option A: Ask your AI** (after setup)
> "Generate an RTL diagram for the Verilog files in ./src"

**Option B: CLI command**
```bash
rtlviz generate ./src -o diagram.html
```

---

## 📖 Commands

### `rtlviz generate`

Generate a diagram directly:

```bash
rtlviz generate ./src -o diagram.html
rtlviz generate ./src -o diagram.html --llm    # With LLM enhancement
rtlviz generate ./src -o diagram.html --title "My CPU"
```

### `rtlviz setup`

Configure MCP server for AI IDEs:

```bash
rtlviz setup                  # Auto-detect and configure all found IDEs
rtlviz setup --all            # Force configure all IDEs
rtlviz setup --antigravity    # Configure Antigravity only
rtlviz setup --claude         # Configure Claude Desktop only
rtlviz setup --cursor         # Configure Cursor only
rtlviz setup --vscode         # Configure VS Code Copilot only
rtlviz setup --windsurf       # Configure Windsurf only
```

---

## ✨ Features

- **🔧 Automatic Parsing** - Extracts modules, ports, and connections from Verilog
- **📊 Pipeline Detection** - Auto-identifies stages (IF, ID, EX, MEM, WB)
- **🎨 Beautiful Diagrams** - Orthogonal routing, color-coded clusters
- **🤖 LLM Enhancement** - Built-in GPT integration for semantic labels
- **🌐 Interactive HTML** - Pan, zoom, download SVG

---

## 🛠️ MCP Server (for AI IDEs)

After running `rtlviz setup`, your AI assistant can use these tools:

### `generate_rtl_diagram`

```json
{
  "source_dir": "/path/to/verilog",
  "output_path": "/path/to/output.html",
  "use_llm": true
}
```

### `render_diagram`

```json
{
  "dot_content": "digraph { ... }",
  "output_path": "/path/to/output.html"
}
```

---

## 📋 Requirements

- Python 3.10+
- Internet connection (for Viz.js CDN)

All dependencies installed automatically.

---

## 🔧 Troubleshooting

### "Command not found: rtlviz"

```bash
pip install rtlviz
```

### "No valid Verilog modules found"

- Check directory contains `.v` files
- Ensure files have `module ... endmodule` declarations

---

## 📄 License

MIT License

## 🔗 Links

- [GitHub](https://github.com/haran2001/rtlviz)
- [PyPI](https://pypi.org/project/rtlviz/)
