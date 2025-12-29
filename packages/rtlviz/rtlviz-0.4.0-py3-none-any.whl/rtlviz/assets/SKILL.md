# RTL Diagram Skill V4

## Overview

A **Graphviz-based** RTL visualization skill that generates publication-quality block diagrams from Verilog/SystemVerilog code using **data-driven component placement**.

## Key Philosophy

> **"Don't assume textbook layouts. Trace the signals."**

Components are placed based on **where their inputs come from**, not where textbooks say they should be.

---

## What's New in V4

### MUX Shape Fix
- **Right-facing trapezium**: `shape=trapezium, orientation=90`
- **Narrower dimensions**: `width=0.5, height=0.8`
- **Wires connect left/right**: Inputs from left, output to right

```dot
// Correct MUX styling
MUX_name [label="MUX\nLabel", shape=trapezium, orientation=90, width=0.5, height=0.8, style="filled", fillcolor="#FFF9C4"]
```

---

## Architecture

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  RTL Analysis    │───▶│  Graph Model     │───▶│  DOT Generator   │
│  (LLM-assisted)  │    │  (JSON/Python)   │    │  (Graphviz)      │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                                         │
                                                         ▼
                                               ┌──────────────────┐
                                               │  HTML Viewer     │
                                               │  (Viz.js)        │
                                               └──────────────────┘
```

---

## Component Shape Reference

| Component Type | Shape | Example |
|----------------|-------|---------|
| **MUX** | `shape=trapezium, orientation=90, width=0.5, height=0.8` | Right-facing trapezium |
| **ALU** | `shape=octagon` | 8-sided for computation |
| **Memory/Registers** | `shape=box3d` | 3D box for storage |
| **Pipeline Reg** | `shape=record` | Vertical bar |
| **Control** | `shape=component` | Component block |
| **Logic** | `shape=box, style=rounded` | Rounded rectangle |
| **Compare** | `shape=diamond` | Diamond |

---

## Usage

### Step 1: Analyze RTL (LLM-assisted)
Provide RTL code with the PROMPT.md analysis prompt.

### Step 2: Generate DOT
Use the generated graph model to produce DOT code with correct shapes.

### Step 3: Render HTML
```bash
python dot_to_html.py <input.dot> <output.html>
```

### Step 4: View
Serve via HTTP and open in browser:
```bash
python -m http.server 8080
```

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This documentation |
| `PROMPT.md` | LLM prompt template for RTL analysis |
| `dot_to_html.py` | DOT → HTML converter |
| `outputs/` | Generated diagram outputs |
