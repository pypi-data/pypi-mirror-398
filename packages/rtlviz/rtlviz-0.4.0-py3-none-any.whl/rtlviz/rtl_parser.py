#!/usr/bin/env python3
"""
RTL Parser Module

Parses Verilog source files to extract module hierarchy,
ports, instances, and signal connections.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Port:
    """Represents a module port."""
    name: str
    direction: str  # 'input', 'output', 'inout'
    width: int = 1


@dataclass
class ModuleInstance:
    """Represents an instantiation of a module."""
    instance_name: str
    module_type: str
    connections: Dict[str, str] = field(default_factory=dict)
    # Semantic info (populated by analyzer)
    semantic_type: str = "logic"
    pipeline_stage: str = "other"
    description: str = ""


@dataclass
class Module:
    """Represents a Verilog module."""
    name: str
    code: str = ""
    ports: List[Port] = field(default_factory=list)
    instances: List[ModuleInstance] = field(default_factory=list)


def parse_verilog_file(filepath: str) -> Optional[Module]:
    """
    Parse a single Verilog file and extract module information.
    
    Args:
        filepath: Path to the .v file
        
    Returns:
        Module object or None if parsing fails
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return None
    
    # Remove comments for cleaner parsing
    clean_content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    clean_content = re.sub(r'/\*.*?\*/', '', clean_content, flags=re.DOTALL)
    
    # Find module declaration
    module_match = re.search(r'module\s+(\w+)\s*[\(#]', clean_content)
    if not module_match:
        return None
    
    module = Module(
        name=module_match.group(1),
        code=content[:3000]  # Keep first 3000 chars for potential LLM analysis
    )
    
    # Extract ports
    module.ports = _extract_ports(clean_content)
    
    # Extract instances
    module.instances = _extract_instances(clean_content)
    
    return module


def _extract_ports(content: str) -> List[Port]:
    """Extract port declarations from module."""
    ports = []
    
    # Match port declarations: input/output/inout [width] name
    port_pattern = r'(input|output|inout)\s+(?:\[(\d+):(\d+)\])?\s*(\w+)'
    
    for match in re.finditer(port_pattern, content):
        direction = match.group(1)
        high = int(match.group(2)) if match.group(2) else 0
        low = int(match.group(3)) if match.group(3) else 0
        name = match.group(4)
        width = abs(high - low) + 1 if match.group(2) else 1
        
        ports.append(Port(name=name, direction=direction, width=width))
    
    return ports


def _extract_instances(content: str) -> List[ModuleInstance]:
    """Extract module instantiations."""
    instances = []
    
    # Keywords that aren't module instantiations
    keywords = {
        'always', 'assign', 'initial', 'wire', 'reg', 
        'input', 'output', 'inout', 'parameter', 'localparam',
        'function', 'task', 'generate', 'endgenerate'
    }
    
    # Pattern: ModuleType InstanceName (.port(signal), ...);
    inst_pattern = r'(\w+)\s+(\w+)\s*\(\s*\.([\s\S]*?)\);'
    
    for match in re.finditer(inst_pattern, content):
        module_type = match.group(1)
        instance_name = match.group(2)
        port_section = match.group(3)
        
        # Skip keywords
        if module_type.lower() in keywords:
            continue
        
        # Extract connections
        connections = {}
        for conn_match in re.finditer(r'\.(\w+)\s*\(\s*([^)]*)\s*\)', port_section):
            port_name = conn_match.group(1)
            signal = conn_match.group(2).strip()
            if signal:  # Only add non-empty connections
                connections[port_name] = signal
        
        if connections:
            instances.append(ModuleInstance(
                instance_name=instance_name,
                module_type=module_type,
                connections=connections
            ))
    
    return instances


def parse_project(src_dir: str) -> Tuple[Dict[str, Module], Optional[str]]:
    """
    Parse all Verilog files in a project directory.
    
    Args:
        src_dir: Path to source directory containing .v files
        
    Returns:
        Tuple of (modules dict, top module name)
    """
    modules: Dict[str, Module] = {}
    top_module = None
    max_instances = 0
    
    # Files to skip
    skip_patterns = ['testbench', '_tb', 'WIN', 'CHIP', '_syn', '.sdf', 'test_']
    
    if not os.path.isdir(src_dir):
        return modules, None
    
    for filename in os.listdir(src_dir):
        if not filename.endswith('.v'):
            continue
        
        # Skip test/synthesis files
        if any(skip in filename.lower() for skip in skip_patterns):
            continue
        
        filepath = os.path.join(src_dir, filename)
        
        # Skip very large files
        if os.path.getsize(filepath) > 100000:
            continue
        
        module = parse_verilog_file(filepath)
        if module and len(module.instances) <= 100:
            modules[module.name] = module
            
            # Guess top module by number of instances
            if len(module.instances) > max_instances:
                max_instances = len(module.instances)
                top_module = module.name
    
    return modules, top_module


def build_signal_map(modules: Dict[str, Module], top_module: str) -> Dict[str, str]:
    """
    Build a map of signal names to their producer instances.
    
    Args:
        modules: Dict of parsed modules
        top_module: Name of top-level module
        
    Returns:
        Dict mapping signal name -> producer instance name
    """
    signal_producers = {}
    
    top = modules.get(top_module)
    if not top:
        return signal_producers
    
    for inst in top.instances:
        for port, signal in inst.connections.items():
            # Signals on output ports are produced by this instance
            if signal and ('_o' in port or 'out' in port.lower()):
                signal_producers[signal] = inst.instance_name
    
    return signal_producers


def get_connections(modules: Dict[str, Module], top_module: str) -> List[Tuple[str, str, bool]]:
    """
    Get all connections between instances in the top module.
    
    Args:
        modules: Dict of parsed modules
        top_module: Name of top-level module
        
    Returns:
        List of (source_instance, target_instance, is_control) tuples
    """
    connections = []
    signal_producers = build_signal_map(modules, top_module)
    
    top = modules.get(top_module)
    if not top:
        return connections
    
    seen = set()
    
    for inst in top.instances:
        for port, signal in inst.connections.items():
            # Check if this is an input port connected to a known producer
            if signal and ('_i' in port or 'in' in port.lower()):
                if signal in signal_producers:
                    producer = signal_producers[signal]
                    edge_key = (producer, inst.instance_name)
                    
                    if edge_key not in seen:
                        seen.add(edge_key)
                        
                        # Detect control signals
                        is_control = any(x in signal.lower() for x in [
                            'ctrl', 'control', 'select', 'sel', 
                            'write', 'read', 'enable', 'en',
                            'regwrite', 'memread', 'memwrite',
                            'aluop', 'alusrc', 'branch', 'jump',
                            'hazard', 'stall', 'flush', 'forward'
                        ])
                        
                        connections.append((producer, inst.instance_name, is_control))
    
    return connections
