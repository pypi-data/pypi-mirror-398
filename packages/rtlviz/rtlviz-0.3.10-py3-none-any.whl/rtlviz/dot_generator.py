#!/usr/bin/env python3
"""
DOT Generator Module

Generates optimized Graphviz DOT code for RTL diagrams with:
- Orthogonal routing (splines=ortho)
- Pipeline stage clustering
- Feedback edge handling
- Compact layout optimization
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

from .rtl_parser import Module, ModuleInstance


class FlowDirection(Enum):
    """Diagram flow direction."""
    LEFT_TO_RIGHT = "LR"
    TOP_TO_BOTTOM = "TB"


@dataclass
class NodeStyle:
    """Styling for a node type."""
    shape: str
    fillcolor: str
    style: str = "filled"
    width: float = 1.0
    height: float = 0.5
    fontsize: int = 9
    
    def to_dot(self) -> str:
        attrs = [
            f'shape={self.shape}',
            f'style="{self.style}"',
            f'fillcolor="{self.fillcolor}"',
            f'width={self.width}',
            f'height={self.height}',
            f'fontsize={self.fontsize}',
        ]
        # Special handling for MUX (trapezium)
        if self.shape == 'trapezium':
            attrs.append('orientation=90')
            attrs[3] = 'width=0.5'
            attrs[4] = 'height=0.7'
        return ', '.join(attrs)


# Component type styles
COMPONENT_STYLES: Dict[str, NodeStyle] = {
    'alu': NodeStyle('octagon', '#FFECB3', width=1.0, height=0.5),
    'memory': NodeStyle('box3d', '#C8E6C9', width=1.0, height=0.5),
    'register': NodeStyle('box3d', '#B3E5FC', width=0.9, height=0.45),
    'mux': NodeStyle('trapezium', '#FFF9C4'),
    'control': NodeStyle('component', '#F8BBD9', width=1.0, height=0.5),
    'pipeline_reg': NodeStyle('box', '#E8EAF6', width=0.3, height=0.8, fontsize=8),
    'adder': NodeStyle('ellipse', '#E1BEE7', width=0.8, height=0.45),
    'compare': NodeStyle('diamond', '#FFCDD2', width=0.6, height=0.6),
    'logic': NodeStyle('box', '#ECEFF1', width=0.9, height=0.45),
    'transform': NodeStyle('box', '#B2EBF2', width=0.8, height=0.4),
}

# Generic functional group colors (fill, border) - works for any RTL design
GROUP_COLORS: Dict[str, Tuple[str, str]] = {
    'Datapath': ('#E3F2FD', '#1976D2'),     # Blue
    'Control': ('#FCE4EC', '#C2185B'),      # Pink
    'Memory': ('#E8F5E9', '#388E3C'),       # Green
    'Queue': ('#FFF3E0', '#F57C00'),        # Orange
    'Buffer': ('#F3E5F5', '#7B1FA2'),       # Purple
    'Conversion': ('#E0F7FA', '#00838F'),   # Cyan
    'Interface': ('#FFF8E1', '#FF8F00'),    # Amber
    'Parser': ('#E8EAF6', '#3F51B5'),       # Indigo
    'Arbiter': ('#FFEBEE', '#C62828'),      # Red
    'Logic': ('#F5F5F5', '#424242'),         # Gray for unclassified
    # CPU-specific stages (for backward compatibility)
    'IF': ('#E3F2FD', '#1976D2'),
    'ID': ('#E8F5E9', '#388E3C'),
    'EX': ('#FFF3E0', '#F57C00'),
    'MEM': ('#FCE4EC', '#C2185B'),
    'WB': ('#F3E5F5', '#7B1FA2'),
    'IF_ID': ('#E8EAF6', '#5C6BC0'),
    'ID_EX': ('#E8EAF6', '#5C6BC0'),
    'EX_MEM': ('#E8EAF6', '#5C6BC0'),
    'MEM_WB': ('#E8EAF6', '#5C6BC0'),
    'other': ('#ECEFF1', '#607D8B'),
}

# Also keep STAGE_COLORS as alias for backward compatibility
STAGE_COLORS = GROUP_COLORS

STAGE_LABELS: Dict[str, str] = {
    'IF': 'Instruction Fetch',
    'IF_ID': 'IF/ID Latch',
    'ID': 'Instruction Decode',
    'ID_EX': 'ID/EX Latch',
    'EX': 'Execute',
    'EX_MEM': 'EX/MEM Latch',
    'MEM': 'Memory Access',
    'MEM_WB': 'MEM/WB Latch',
    'WB': 'Write Back',
    'other': 'Other',
}

# Not used for dynamic grouping - kept for backward compatibility
STAGE_ORDER = ['IF', 'IF_ID', 'ID', 'ID_EX', 'EX', 'EX_MEM', 'MEM', 'MEM_WB', 'WB', 'other']


def detect_component_type(module_type: str, instance_name: str) -> str:
    """Detect the semantic component type from module/instance names."""
    name = (module_type + ' ' + instance_name).lower()
    
    if any(x in name for x in ['if_id', 'id_ex', 'ex_mem', 'mem_wb']):
        return 'pipeline_reg'
    if 'alu' in name and 'control' not in name and 'ctrl' not in name:
        return 'alu'
    if any(x in name for x in ['memory', 'mem_', 'instruction_memory', 'data_memory']):
        return 'memory'
    if any(x in name for x in ['register', 'regfile', 'reg_file']):
        return 'register'
    if name == 'pc' or 'program_counter' in name:
        return 'register'
    if 'mux' in name or 'select' in name:
        return 'mux'
    if 'control' in name or 'ctrl' in name:
        return 'control'
    if any(x in name for x in ['forward', 'hazard', 'detect']):
        return 'compare'
    if any(x in name for x in ['add', 'adder', 'increment']):
        return 'adder'
    if any(x in name for x in ['sign', 'extend', 'shift']):
        return 'transform'
    
    return 'logic'


def detect_pipeline_stage(instance_name: str, module_type: str) -> str:
    """Detect functional group - works for CPU stages AND generic RTL."""
    name = (instance_name + ' ' + module_type).lower()
    
    # CPU-specific pipeline stages
    if any(x in name for x in ['pc', 'instruction_memory', 'pcselect', 'add_pc']):
        return 'IF'
    if 'if_id' in name:
        return 'IF_ID'
    if any(x in name for x in ['control', 'registers', 'sign_extend', 'hazard']) and 'alu' not in name:
        return 'ID'
    if 'id_ex' in name:
        return 'ID_EX'
    if any(x in name for x in ['alu', 'forward']) and 'mem' not in name:
        return 'EX'
    if 'ex_mem' in name:
        return 'EX_MEM'
    if any(x in name for x in ['data_memory', 'datamemory']):
        return 'MEM'
    if 'mem_wb' in name:
        return 'MEM_WB'
    if any(x in name for x in ['memtoreg', 'writeback']):
        return 'WB'
    
    # Generic functional groups for any RTL
    if any(x in name for x in ['parser', 'header']):
        return 'Parser'
    if any(x in name for x in ['queue', 'qp', 'dpq', 'fifo']):
        return 'Queue'
    if any(x in name for x in ['buffer', 'buf', 'fdb']):
        return 'Buffer'
    if any(x in name for x in ['nibble', 'word', 'byte', 'dword', 'convert']):
        return 'Conversion'
    if any(x in name for x in ['memory', 'mem_', 'ram', 'rom']):
        return 'Memory'
    if any(x in name for x in ['xbar', 'arbiter', 'switch', 'crossbar']):
        return 'Arbiter'
    if any(x in name for x in ['interface', 'port', 'io', 'phy']):
        return 'Interface'
    if any(x in name for x in ['alu', 'adder', 'multiply']):
        return 'Datapath'
    
    return 'Logic'


def get_graph_header(
    title: str = "RTL Block Diagram",
    direction: FlowDirection = FlowDirection.LEFT_TO_RIGHT,
    node_sep: float = 0.8,
    rank_sep: float = 1.5,
) -> str:
    """Generate optimized graph header - always ortho for readability."""
    return f'''digraph "{title}" {{
    // Layout for readable RTL diagrams
    layout=dot;
    rankdir={direction.value};
    splines=ortho;
    overlap=false;
    newrank=true;
    compound=true;
    
    // Wide spacing for clarity
    nodesep={node_sep};
    ranksep={rank_sep};
    margin=0.5;
    pad=0.5;
    
    // Default node style
    node [
        fontname="Arial",
        fontsize=10,
        penwidth=1.2,
        margin="0.15,0.08"
    ];
    
    // Default edge style  
    edge [
        fontname="Arial",
        fontsize=8,
        penwidth=1.0,
        arrowsize=0.6
    ];
'''


def get_graph_footer() -> str:
    """Close the graph definition."""
    return '}'


def get_cluster_header(
    cluster_id: str,
    label: str,
    fillcolor: str,
    border_color: str = "#666666",
    rank: Optional[str] = None,
) -> str:
    """Generate a cluster (subgraph) header."""
    # Sanitize cluster_id: replace spaces and special chars with underscores
    safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', cluster_id)
    lines = [
        f'    subgraph cluster_{safe_id} {{',
        f'        label="{label}";',
        f'        labeljust=l;',
        f'        style="filled,rounded";',
        f'        fillcolor="{fillcolor}";',
        f'        color="{border_color}";',
        f'        fontname="Arial Bold";',
        f'        fontsize=10;',
        f'        margin=8;',
    ]
    if rank:
        lines.append(f'        rank={rank};')
    lines.append('')
    return '\n'.join(lines)


def get_cluster_footer() -> str:
    """Close a cluster."""
    return '    }\n'


def get_node_def(
    node_id: str,
    label: str,
    component_type: str,
    tooltip: str = "",
    fill_color: str = None,
) -> str:
    """Generate a node definition with appropriate styling."""
    style = COMPONENT_STYLES.get(component_type, COMPONENT_STYLES['logic'])
    safe_label = label.replace('"', '\\"').replace('\n', '\\n')
    safe_tooltip = tooltip.replace('"', '\\"') if tooltip else safe_label
    
    # Use custom fill color if provided (from LLM analysis)
    if fill_color:
        custom_style = f'shape={style.shape}, style="filled", fillcolor="{fill_color}", width={style.width}, height={style.height}, fontsize=9'
        return f'        {node_id} [label="{safe_label}", {custom_style}, tooltip="{safe_tooltip}"];'
    
    return f'        {node_id} [label="{safe_label}", {style.to_dot()}, tooltip="{safe_tooltip}"];'


def get_edge_def(
    source: str,
    target: str,
    is_control: bool = False,
    is_feedback: bool = False,
) -> str:
    """Generate an edge definition."""
    attrs = []
    
    if is_control:
        attrs.append('style=dashed')
        attrs.append('color="#1565C0"')
        attrs.append('penwidth=0.8')
    else:
        attrs.append('penwidth=1.0')
    
    if is_feedback:
        attrs.append('constraint=false')
        attrs.append('weight=0')
    else:
        attrs.append('weight=2')
    
    return f'    {source} -> {target} [{", ".join(attrs)}];'


def get_invisible_edge(source: str, target: str) -> str:
    """Create an invisible edge for layout control."""
    return f'    {source} -> {target} [style=invis, weight=10];'


def generate_dot(
    modules: Dict[str, Module],
    top_module: str,
    title: str = "RTL Block Diagram",
) -> str:
    """
    Generate DOT code from parsed modules.
    
    Args:
        modules: Dict of parsed modules
        top_module: Name of top-level module
        title: Diagram title
        
    Returns:
        Complete DOT code string
    """
    top = modules.get(top_module)
    if not top:
        return f'digraph "{title}" {{ label="Error: Top module {top_module} not found"; }}'
    
    # Analyze instances - pattern detection as fallback
    for inst in top.instances:
        current_type = getattr(inst, 'semantic_type', None)
        current_stage = getattr(inst, 'pipeline_stage', None)
        current_desc = getattr(inst, 'description', None)
        
        if not current_type or current_type == 'logic':
            inst.semantic_type = detect_component_type(inst.module_type, inst.instance_name)
        if not current_stage or current_stage == 'other':
            inst.pipeline_stage = detect_pipeline_stage(inst.instance_name, inst.module_type)
        if not current_desc or current_desc == inst.module_type:
            inst.description = inst.module_type
    
    # Group by functional group (dynamic, not hardcoded)
    groups: Dict[str, List[ModuleInstance]] = {}
    for inst in top.instances:
        group = inst.pipeline_stage  # Can be CPU stage or generic functional group
        if group not in groups:
            groups[group] = []
        groups[group].append(inst)
    
    # Sort groups - put known CPU stages first if present, then alphabetically
    known_stages = ['IF', 'IF_ID', 'ID', 'ID_EX', 'EX', 'EX_MEM', 'MEM', 'MEM_WB', 'WB']
    sorted_groups = []
    for stage in known_stages:
        if stage in groups:
            sorted_groups.append(stage)
    for group in sorted(groups.keys()):
        if group not in sorted_groups:
            sorted_groups.append(group)
    
    # Adaptive layout - Tighter spacing to reduce whitespace
    node_count = len(top.instances)
    node_sep = 0.4  # Match reference diagram spacing
    rank_sep = 0.8  # Match reference diagram spacing
    
    # Build DOT
    lines = [get_graph_header(title, FlowDirection.LEFT_TO_RIGHT, node_sep, rank_sep)]
    
    group_nodes: Dict[str, List[str]] = {}
    
    # Create clusters for each functional group
    for group in sorted_groups:
        if group not in groups:
            continue
        
        instances = groups[group]
        
        # Use color from first instance if available (set by LLM), otherwise fallback
        first_inst = instances[0]
        
        # Check for cluster-specific color first, then node fill color, then default dictionary
        fill = getattr(first_inst, 'cluster_fill_color', None) or \
               getattr(first_inst, 'fill_color', None) or \
               GROUP_COLORS.get(group, ('#ECEFF1', '#607D8B'))[0]
               
        border = getattr(first_inst, 'cluster_border_color', None) or \
                 getattr(first_inst, 'border_color', None) or \
                 GROUP_COLORS.get(group, ('#ECEFF1', '#607D8B'))[1]
                 
        label = STAGE_LABELS.get(group, group)  # Use label if CPU stage, else use group name
        
        lines.append(get_cluster_header(group, label, fill, border, None))
        
        group_nodes[group] = []
        for inst in instances:
            node_label = f"{inst.description}\\n[{inst.instance_name}]"
            inst_fill = getattr(inst, 'fill_color', None)
            lines.append(get_node_def(inst.instance_name, node_label, inst.semantic_type, inst.description, inst_fill))
            group_nodes[group].append(inst.instance_name)
        
        lines.append(get_cluster_footer())
    
    # Minimal rank constraints - don't force all nodes in same rank
    lines.append('\n    // Cluster ordering')
    
    # Invisible edges between groups for left-to-right flow
    prev_group = None
    for group in sorted_groups:
        if group in group_nodes and group_nodes[group]:
            if prev_group and prev_group in group_nodes and group_nodes[prev_group]:
                lines.append(get_invisible_edge(group_nodes[prev_group][0], group_nodes[group][0]))
            prev_group = group
    
    # Build signal producer map
    OUTPUT_PATTERNS = ['_o', '_out', 'output', '_q', '_dout', '_data_out', '_tx', '_valid']
    INPUT_PATTERNS = ['_i', '_in', 'input', '_d', '_din', '_data_in', '_rx', '_ready']
    
    signal_producers = {}
    for inst in top.instances:
        for port, signal in inst.connections.items():
            if signal:
                port_lower = port.lower()
                is_output = any(pat in port_lower for pat in OUTPUT_PATTERNS)
                if not is_output and not any(pat in port_lower for pat in INPUT_PATTERNS):
                    is_output = True
                if is_output:
                    signal_producers[signal] = inst.instance_name
    
    # Create group order for feedback detection
    group_order_map = {g: i for i, g in enumerate(sorted_groups)}
    
    # Add edges (no limit - some IPs are huge)
    lines.append('\n    // Connections')
    edges_added = set()
    for inst in top.instances:
        for port, signal in inst.connections.items():
            if signal and signal in signal_producers:
                port_lower = port.lower()
                is_input = any(pat in port_lower for pat in INPUT_PATTERNS)
                producer = signal_producers[signal]
                if producer != inst.instance_name:
                    if is_input or not any(pat in port_lower for pat in OUTPUT_PATTERNS):
                        edge_key = (producer, inst.instance_name)
                        
                        if edge_key not in edges_added:
                            edges_added.add(edge_key)
                            
                            is_control = any(x in signal.lower() for x in [
                                'ctrl', 'select', 'write', 'read', 'regwrite', 
                                'mem', 'aluop', 'alusrc', 'hazard', 'branch',
                                'valid', 'ready', 'enable', 'clk', 'rst'
                            ])
                            
                            prod_group = group_order_map.get(getattr(top.instances[0] if inst == top.instances[0] else inst, 'pipeline_stage', 'other'), 99)
                            cons_group = group_order_map.get(inst.pipeline_stage, 99) 
                            is_feedback = prod_group > cons_group
                            
                            lines.append(get_edge_def(producer, inst.instance_name, is_control, is_feedback))
    
    lines.append(get_graph_footer())
    return '\n'.join(lines)

