#!/usr/bin/env python3
"""
RTLViz CLI - Command-line interface for RTL diagram generation.

Note: CLI uses pattern-based detection only (no LLM).
For LLM-enhanced analysis, use the MCP server via an AI IDE.

Usage:
    rtlviz generate /path/to/verilog -o diagram.html
    rtlviz setup
"""

import argparse
import sys
from pathlib import Path

from .rtl_parser import parse_project
from .dot_generator import generate_dot
from .telemetry import ping_cli_generate, ping_cli_setup


def generate_html(dot_code: str, title: str) -> str:
    """Generate interactive HTML from DOT code."""
    dot_escaped = (
        dot_code
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )
    
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
        <p class="subtitle">Generated with RTLViz</p>
        
        <div class="controls">
            <button onclick="zoomIn()">🔍 Zoom In</button>
            <button onclick="zoomOut()">🔍 Zoom Out</button>
            <button onclick="resetZoom()">↺ Reset</button>
            <button onclick="downloadSVG()">💾 Download SVG</button>
        </div>
        
        <div id="diagram">
            <div class="loading">⏳ Rendering diagram...</div>
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
                    '<div class="error">❌ Error rendering: ' + error.message + '</div>';
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


def cmd_generate(args):
    """Generate RTL diagram from Verilog source."""
    source_dir = Path(args.source).resolve()
    
    if not source_dir.exists():
        print(f"❌ Error: Source directory not found: {source_dir}")
        return 1
    
    print(f"📂 Parsing Verilog files in: {source_dir}")
    
    # Parse project
    modules, top_module = parse_project(str(source_dir))
    
    if not modules:
        print(f"❌ Error: No valid Verilog modules found")
        return 1
    
    print(f"✅ Found {len(modules)} modules, top module: {top_module}")
    
    # CLI always uses pattern-based detection (no MCP context available)
    print("⚡ Using pattern-based detection")
    print("💡 Tip: For LLM-enhanced analysis, use the MCP server via an AI IDE")
    
    # Generate DOT
    title = args.title or f"{top_module} Block Diagram"
    dot_code = generate_dot(modules, top_module, title)
    
    # Validate diagram quality
    try:
        from .diagram_validator import validate_diagram
        
        validation = validate_diagram(dot_code)
        score = validation.get("score", 100)
        issues = validation.get("issues", [])
        
        if not validation.get("pass", True):
            print(f"⚠️  Quality check: {score}/100 - ISSUES DETECTED")
            for issue in issues[:3]:
                print(f"   ❌ {issue}")
        else:
            print(f"✅ Quality check passed ({score}/100)")
    except Exception as e:
        print(f"⚠️  Validator error: {e}")
    
    # Determine output path
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate and save HTML
    html = generate_html(dot_code, title)
    output_path.write_text(html, encoding="utf-8")
    
    # Also save DOT file
    dot_path = output_path.with_suffix('.dot')
    dot_path.write_text(dot_code, encoding="utf-8")
    
    # Generate SVG using graphviz Python package
    svg_path = output_path.with_suffix('.svg')
    svg_generated = False
    try:
        import graphviz
        source = graphviz.Source(dot_code)
        svg_content = source.pipe(format='svg').decode('utf-8')
        svg_path.write_text(svg_content, encoding='utf-8')
        svg_generated = True
    except Exception:
        pass  # Graphviz binary not installed on system
    
    print(f"\n✅ Diagram generated successfully!")
    print(f"📄 HTML: {output_path}")
    print(f"📄 DOT:  {dot_path}")
    if svg_generated:
        print(f"📄 SVG:  {svg_path}")
    else:
        print(f"💡 Tip: SVG available via 'Download SVG' button in the viewer")
    print(f"\n🌐 Opening diagram in browser...")
    
    # Auto-open in browser
    import webbrowser
    webbrowser.open(f'file:///{output_path}')
    
    # Telemetry - CLI always uses pattern-based
    ping_cli_generate(len(modules), use_llm=False)
    
    return 0


def cmd_setup(args):
    """Run IDE setup."""
    from .setup import main as setup_main
    import sys
    original_argv = sys.argv
    
    # Build new argv for setup module
    new_argv = ['rtlviz-setup']
    if args.all:
        new_argv.append('--all')
    if args.antigravity:
        new_argv.append('--antigravity')
    if args.claude:
        new_argv.append('--claude')
    if args.cursor:
        new_argv.append('--cursor')
    if args.vscode:
        new_argv.append('--vscode')
    if args.windsurf:
        new_argv.append('--windsurf')
    
    sys.argv = new_argv
    result = setup_main()
    sys.argv = original_argv
    
    if result == 0:
        print("\n🔄 **Please restart your IDE** (Cursor, VS Code, etc.) to load the new MCP configuration.")
        
    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="rtlviz",
        description="Generate interactive RTL block diagrams from Verilog source files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rtlviz generate ./src -o diagram.html   # Pattern-based detection
  rtlviz setup                            # Configure all detected IDEs
  
Note: For LLM-enhanced analysis, use RTLViz via an AI IDE (Cursor, Claude, etc.)
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate RTL diagram")
    gen_parser.add_argument("source", help="Path to Verilog source directory")
    gen_parser.add_argument("-o", "--output", required=True, help="Output HTML file path")
    gen_parser.add_argument("--title", help="Diagram title (default: <TopModule> Block Diagram)")
    gen_parser.set_defaults(func=cmd_generate)
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Configure MCP server for AI IDEs")
    setup_parser.add_argument("--all", action="store_true", help="Force configure all IDEs")
    setup_parser.add_argument("--antigravity", action="store_true", help="Configure Antigravity only")
    setup_parser.add_argument("--claude", action="store_true", help="Configure Claude Desktop only")
    setup_parser.add_argument("--cursor", action="store_true", help="Configure Cursor only")
    setup_parser.add_argument("--vscode", action="store_true", help="Configure VS Code Copilot only")
    setup_parser.add_argument("--windsurf", action="store_true", help="Configure Windsurf only")
    setup_parser.set_defaults(func=cmd_setup)
    
    # Parse args
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
