#!/usr/bin/env python3
"""
RTLViz MCP Server

Provides:
- Resource: rtlviz://prompt - The RTL diagram generation prompt
- Resource: rtlviz://skill - The skill documentation
- Tool: render_diagram - Converts DOT code to an interactive HTML viewer
- Tool: generate_rtl_diagram - Generate diagram from Verilog source
"""

import os
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

# Import telemetry
from rtlviz.telemetry import (
    ping_session_start,
    ping_resource_read,
    ping_tool_call,
    ping_diagram_rendered
)

# Import RTL processing modules
from rtlviz.rtl_parser import parse_project, get_connections, Module
from rtlviz.dot_generator import generate_dot
from rtlviz.llm_analyzer import enhance_instances, is_llm_available
from rtlviz.diagram_validator import validate_diagram

# Get the assets directory (relative to this file)
ASSETS_DIR = Path(__file__).parent / "assets"

# Create the MCP server
server = Server("rtlviz")

# Send telemetry ping on import (server start)
ping_session_start()


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="rtlviz://prompt",
            name="RTL Diagram Prompt",
            description="The prompt template for RTL analysis and diagram generation",
            mimeType="text/markdown",
        ),
        Resource(
            uri="rtlviz://skill",
            name="RTL Diagram Skill",
            description="Documentation for the RTL diagram skill",
            mimeType="text/markdown",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    # Log FIRST before responding
    if uri == "rtlviz://prompt":
        ping_resource_read("prompt")
        prompt_path = ASSETS_DIR / "PROMPT.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return "Error: PROMPT.md not found"
    elif uri == "rtlviz://skill":
        ping_resource_read("skill")
        skill_path = ASSETS_DIR / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return "Error: SKILL.md not found"
    else:
        return f"Unknown resource: {uri}"


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="render_diagram",
            description="Convert Graphviz DOT code to an interactive HTML viewer with pan/zoom",
            inputSchema={
                "type": "object",
                "properties": {
                    "dot_content": {
                        "type": "string",
                        "description": "The Graphviz DOT code to render",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Absolute path for the output HTML file",
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the diagram (default: RTL Block Diagram)",
                        "default": "RTL Block Diagram",
                    },
                },
                "required": ["dot_content", "output_path"],
            },
        ),
        Tool(
            name="generate_rtl_diagram",
            description="Generate an RTL block diagram from Verilog source files. Returns HTML and DOT content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_dir": {
                        "type": "string",
                        "description": "Absolute path to the directory containing Verilog (.v) source files",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Absolute path for the output HTML file",
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the diagram",
                        "default": "RTL Block Diagram",
                    },
                    "use_llm": {
                        "type": "boolean",
                        "description": "Use LLM for enhanced semantic analysis (requires OPENAI_API_KEY env var)",
                        "default": False,
                    },
                },
                "required": ["source_dir", "output_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    # Log FIRST before executing tool
    ping_tool_call(name)
    
    if name == "render_diagram":
        return await render_diagram(
            dot_content=arguments["dot_content"],
            output_path=arguments["output_path"],
            title=arguments.get("title", "RTL Block Diagram"),
        )
    elif name == "generate_rtl_diagram":
        return await generate_rtl_diagram(
            source_dir=arguments["source_dir"],
            output_path=arguments["output_path"],
            title=arguments.get("title", "RTL Block Diagram"),
            use_llm=arguments.get("use_llm", False),
        )
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def render_diagram(dot_content: str, output_path: str, title: str) -> list[TextContent]:
    """Generate an interactive HTML viewer from DOT code."""
    try:
        # Escape DOT content for JavaScript template literal
        dot_escaped = (
            dot_content
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
        )

        # Generate HTML
        html = generate_html(dot_escaped, title)

        # Ensure output directory exists
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        out_path.write_text(html, encoding="utf-8")

        # Telemetry: diagram rendered successfully
        ping_diagram_rendered(success=True)

        return [
            TextContent(
                type="text",
                text=f"✅ Successfully generated: {output_path}\n\nOpen in browser or serve with: python -m http.server 8080",
            )
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error generating diagram: {e}")]


async def generate_rtl_diagram(
    source_dir: str, 
    output_path: str, 
    title: str,
    use_llm: bool = False
) -> list[TextContent]:
    """Generate an RTL block diagram from Verilog source files."""
    try:
        # Parse the Verilog project
        modules, top_module = parse_project(source_dir)
        
        if not modules:
            return [TextContent(
                type="text", 
                text=f"❌ No valid Verilog modules found in: {source_dir}"
            )]
        
        if not top_module:
            return [TextContent(
                type="text",
                text=f"❌ Could not determine top module. Found modules: {list(modules.keys())}"
            )]
        
        # If LLM enhancement requested, enhance instances
        top = modules.get(top_module)
        if top and use_llm:
            if is_llm_available():
                enhance_instances(top.instances, modules, use_llm=True)
            else:
                # Fall back to pattern-based detection if LLM not available
                pass
        
        # Generate DOT code
        dot_code = generate_dot(modules, top_module, title)
        
        # Strict Quality Validation
        validation = validate_diagram(dot_code)
        score = validation.get("score", 0)
        validation_pass = validation.get("pass", True)
        
        validation_msg = f"\n🔍 **Quality Score:** {score}/100"
        if not validation_pass:
            issues = validation.get("issues", [])
            validation_msg += "\n⚠️ **Issues Detected:**"
            for issue in issues[:3]:
                 validation_msg += f"\n- {issue}"
        else:
            validation_msg += " ✅ Passed Strict Validation"
        
        # Escape DOT content for JavaScript
        dot_escaped = (
            dot_code
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
        )
        
        # Generate HTML
        html = generate_html(dot_escaped, title)
        
        # Write HTML file
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        
        # Also write DOT file
        dot_path = out_path.with_suffix('.dot')
        dot_path.write_text(dot_code, encoding="utf-8")
        
        # Generate SVG using graphviz Python package
        svg_path = out_path.with_suffix('.svg')
        svg_generated = False
        try:
            import graphviz
            source = graphviz.Source(dot_code)
            svg_content = source.pipe(format='svg').decode('utf-8')
            svg_path.write_text(svg_content, encoding='utf-8')
            svg_generated = True
        except Exception:
            pass  # Graphviz binary not installed
        
        # Telemetry
        ping_diagram_rendered(success=True)
        
        # Build response with stats
        module_count = len(modules)
        instance_count = len(top.instances) if top else 0
        llm_status = "✅ LLM enhanced" if (use_llm and is_llm_available()) else "⚡ Pattern-based"
        
        svg_info = f"\n- SVG: `{svg_path}`" if svg_generated else "\n- SVG: Not generated (install Graphviz binary)"
        
        return [
            TextContent(
                type="text",
                text=f"✅ **Diagram Generated**\n\nOpen: `{output_path}`",
            )
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error generating RTL diagram: {e}")]


def generate_html(dot_escaped: str, title: str) -> str:
    """Generate the HTML content with Viz.js for client-side rendering."""
    safe_title = title.replace('"', "&quot;")
    download_name = title.replace(" ", "_").lower() + "_diagram.svg"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{safe_title}</title>
    <script src="https://unpkg.com/@viz-js/viz@3.2.4/lib/viz-standalone.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; padding: 20px; }}
        .container {{ background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 30px; max-width: 100%; }}
        h1 {{ color: #333; margin-bottom: 10px; font-weight: 600; }}
        .subtitle {{ color: #666; margin-bottom: 20px; font-size: 14px; }}
        .controls {{ margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; }}
        button {{ padding: 10px 20px; border: none; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; cursor: pointer; font-weight: 500; transition: all 0.2s; }}
        button:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }}
        #diagram {{ border: 1px solid #eee; border-radius: 8px; padding: 20px; background: #fafafa; overflow: auto; min-height: 500px; }}
        #diagram svg {{ max-width: 100%; height: auto; }}
        .legend {{ margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; display: flex; gap: 25px; flex-wrap: wrap; align-items: center; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 13px; }}
        .legend-line {{ width: 30px; height: 3px; }}
        .loading {{ text-align: center; padding: 40px; color: #666; }}
        .error {{ color: #d32f2f; padding: 20px; background: #ffebee; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 {safe_title}</h1>
        <p class="subtitle">Generated with RTLViz | ⚠️ RtlViz can make mistakes, so double-check it</p>
        
        <div class="controls">
            <button onclick="zoomIn()">🔍 Zoom In</button>
            <button onclick="zoomOut()">🔍 Zoom Out</button>
            <button onclick="resetZoom()">↺ Reset</button>
            <button onclick="downloadSVG()">💾 Download SVG</button>
        </div>
        
        <div id="diagram">
            <div class="loading">⏳ Rendering diagram with Viz.js...</div>
        </div>
        
        <div class="legend">
            <strong>Legend:</strong>
            <div class="legend-item">
                <span class="legend-line" style="background: black;"></span>
                <span>Data Path</span>
            </div>
            <div class="legend-item">
                <span class="legend-line" style="background: transparent; border-top: 2px dashed #1565C0;"></span>
                <span>Control Signal</span>
            </div>
        </div>
    </div>
    
    <script>
        const dotSource = `{dot_escaped}`;
        let scale = 1;
        let svgContent = '';
        
        async function renderDiagram() {{
            try {{
                const viz = await Viz.instance();
                const svg = viz.renderSVGElement(dotSource);
                svgContent = svg.outerHTML;
                document.getElementById('diagram').innerHTML = svgContent;
            }} catch (error) {{
                document.getElementById('diagram').innerHTML = 
                    '<div class="error">❌ Error rendering diagram: ' + error.message + '</div>';
                console.error(error);
            }}
        }}
        
        function zoomIn() {{ scale *= 1.2; applyZoom(); }}
        function zoomOut() {{ scale *= 0.8; applyZoom(); }}
        function resetZoom() {{ scale = 1; applyZoom(); }}
        
        function applyZoom() {{
            const svg = document.querySelector('#diagram svg');
            if (svg) {{
                svg.style.transform = `scale(${{scale}})`;
                svg.style.transformOrigin = 'top left';
            }}
        }}
        
        function downloadSVG() {{
            if (svgContent) {{
                const blob = new Blob([svgContent], {{ type: 'image/svg+xml' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '{download_name}';
                a.click();
                URL.revokeObjectURL(url);
            }}
        }}
        
        renderDiagram();
    </script>
</body>
</html>'''


def main():
    """Entry point for the CLI."""
    import asyncio
    asyncio.run(run_server())


async def run_server():
    """Run the MCP server on stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
