# RTL Diagram Generation Prompt

Use this prompt with an LLM to analyze RTL code and generate a Graphviz visualization.

---

## The Prompt

```
You are a Digital Design Automation Expert. Your goal is to generate a Graphviz (DOT) visualization that functionally represents the provided RTL code.

**CRITICAL INSTRUCTION: DO NOT USE PRE-DEFINED TEMPLATES.** You must derive the diagram structure strictly from the signal dependencies in the code.

### **PHASE 1: STATIC ANALYSIS (Required Before Code Generation)**

1. **Identify Pipeline Barriers (Registers):**
   - Look for `always @(posedge clk)` blocks
   - Identify non-blocking assignments (`<=`)
   - These create boundaries between your pipeline stage Clusters

2. **Trace Logic "Home" (The Golden Rule):**
   - For every logic block, identify its **INPUTS**
   - **Rule:** A component belongs to the stage where its inputs are available
   - Example: If a "Branch Adder" uses `IF_ID_pc` and `Imm`, it belongs in **ID** (not IF)

3. **Detect Control Flow:**
   - Find the signal that updates PC
   - Does it depend on ALU flags? → Late Branch (EX/MEM)
   - Does it depend on register comparison? → Early Branch (ID)

### **PHASE 2: VISUALIZATION RULES**

1. **Layout:** `rankdir=LR` (Left-to-Right)
2. **Splines:** `splines=ortho` (orthogonal routing)
3. **Clustering:** Create `subgraph cluster_X` for each pipeline stage or functional group

4. **Component Shapes (V4 Standard):**
   - **MUX:** `shape=trapezium, orientation=90, width=0.5, height=0.8` (right-facing)
   - **ALU:** `shape=octagon`
   - **Memory/Registers:** `shape=box3d`
   - **Pipeline Registers:** `shape=record`
   - **Control Units:** `shape=component`
   - **Logic Blocks:** `shape=box, style=rounded`
   - **Comparators:** `shape=diamond`

5. **Edge Styling:**
   - Data Paths: `penwidth=1.5` (solid black)
   - Control Signals: `style=dashed, color="#1565C0"` (dashed blue)
   - Feedback Loops: Use `constraint=false`

6. **Extensions:** If Vector/FPU logic exists, create sub-clusters in EX stage

### **INPUT RTL:**
[PASTE RTL CODE HERE]

### **OUTPUT:**
Provide ONLY the Graphviz DOT code inside a code block.
```

---

## Usage Example

1. Copy the prompt above
2. Paste your RTL code where indicated
3. Submit to LLM (Claude, GPT-4, etc.)
4. Save the returned DOT code to a `.dot` file
5. Run `python dot_to_html.py input.dot output.html` to generate HTML viewer
6. Serve via HTTP: `python -m http.server 8080`

---

## Tips for Better Results

1. **Include the full top-level module** - not just snippets
2. **Highlight important signals** if the RTL is very large
3. **Ask for Phase 1 analysis first** before requesting DOT code
4. **Iterate** - ask the LLM to refine specific areas

---

## MUX Shape Example

```dot
// CORRECT: Right-facing trapezium MUX
pcSelect [label="MUX\n(PC Sel)", shape=trapezium, orientation=90, width=0.5, height=0.8, style="filled", fillcolor="#E1F5FE"]

// WRONG: Default trapezium (points up, too wide)
// pcSelect [label="MUX", shape=trapezium, style="filled", fillcolor="#E1F5FE"]
```
