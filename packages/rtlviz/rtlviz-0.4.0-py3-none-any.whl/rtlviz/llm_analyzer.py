#!/usr/bin/env python3
"""
LLM Analyzer Module - Generic for ANY Verilog IP

Uses MCP Sampling to request LLM completions from the client (agent).
No API key required - leverages the client's LLM capabilities.

Works for: CPUs, Controllers, Switches, SoCs, FPGAs, anything!
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any

from mcp.server import Server
from mcp.types import (
    SamplingMessage,
    TextContent as SamplingTextContent,
    CreateMessageRequestParams,
    CreateMessageResult,
)

from .rtl_parser import ModuleInstance

# Vibrant color palette for functional groups
GROUP_COLORS = [
    ('#E3F2FD', '#1565C0'),  # Blue (IF)
    ('#E8F5E9', '#2E7D32'),  # Green (ID)
    ('#FFF3E0', '#EF6C00'),  # Orange (EX)
    ('#FCE4EC', '#C2185B'),  # Pink (MEM)
    ('#F3E5F5', '#7B1FA2'),  # Purple (WB)
    ('#E0F7FA', '#00838F'),  # Cyan
    ('#FFF8E1', '#FF8F00'),  # Amber
    ('#FFEBEE', '#C62828'),  # Red
    ('#E8EAF6', '#5C6BC0'),  # Indigo (Latches)
    ('#F1F8E9', '#558B2F'),  # Light Green
]

# CPU Pipeline stage specific colors
CPU_STAGE_COLORS = {
    'IF': ('#E3F2FD', '#1976D2'),
    'IF_ID': ('#E8EAF6', '#5C6BC0'),
    'ID': ('#E8F5E9', '#388E3C'),
    'ID_EX': ('#E8EAF6', '#5C6BC0'),
    'EX': ('#FFF3E0', '#F57C00'),
    'EX_MEM': ('#E8EAF6', '#5C6BC0'),
    'MEM': ('#FCE4EC', '#C2185B'),
    'MEM_WB': ('#E8EAF6', '#5C6BC0'),
    'WB': ('#F3E5F5', '#7B1FA2'),
}


async def request_sampling(server: Server, prompt: str, max_tokens: int = 800) -> Optional[str]:
    """
    Request LLM completion from the MCP client via sampling.
    
    Args:
        server: The MCP Server instance
        prompt: The prompt to send
        max_tokens: Maximum tokens for response
        
    Returns:
        The LLM response text, or None if sampling fails
    """
    try:
        # Create the sampling request
        result: CreateMessageResult = await server.request_context.session.create_message(
            messages=[
                SamplingMessage(
                    role="user",
                    content=SamplingTextContent(type="text", text=prompt)
                )
            ],
            max_tokens=max_tokens,
        )
        
        # Extract text from response
        if result and result.content:
            if hasattr(result.content, 'text'):
                return result.content.text
            elif isinstance(result.content, dict) and 'text' in result.content:
                return result.content['text']
        
        return None
        
    except Exception as e:
        print(f"MCP Sampling failed: {e}")
        return None


async def analyze_design(server: Server, top_module_code: str, instance_list: List[str]) -> Dict:
    """
    Holistic analysis of entire design using MCP Sampling.
    
    Args:
        server: The MCP Server instance
        top_module_code: Source code of top module (first 3000 chars)
        instance_list: List of instance names and types
        
    Returns:
        Dict with: design_type, functional_groups (with assigned instances)
    """
    # Build instance summary
    instances_text = "\n".join(instance_list[:30])  # Limit to 30 for token efficiency
    
    prompt = f"""Analyze this Verilog design and identify functional groups for a block diagram.

TOP MODULE CODE:
```verilog
{top_module_code[:3000]}
```

INSTANCES:
{instances_text}

IMPORTANT RULES:

1. For CPU/Processor designs: Use STANDARD PIPELINE STAGES as groups:
   - IF (Instruction Fetch): PC, Instruction Memory, PC adders
   - IF_ID (IF/ID Latch): Pipeline register between IF and ID
   - ID (Instruction Decode): Control, Registers, Sign Extend
   - ID_EX (ID/EX Latch): Pipeline register between ID and EX
   - EX (Execute): ALU, ALU Control, MUX, Forwarding
   - EX_MEM (EX/MEM Latch): Pipeline register
   - MEM (Memory Access): Data Memory
   - MEM_WB (MEM/WB Latch): Pipeline register
   - WB (Write Back): MemToReg MUX

2. For non-CPU designs: Use functional groups like:
   - Interface, Buffer, Parser, Control, Datapath, Memory, Queue, etc.

3. Keep group names SHORT (1-3 words max).

Return ONLY valid JSON:
{{
    "design_type": "<short description, e.g. '5-Stage RISC-V CPU' or '6-Port Ethernet Switch'>",
    "is_cpu": <true if this is a CPU/processor, false otherwise>,
    "groups": [
        {{"name": "<Group Name>", "instances": ["inst1", "inst2"]}},
        ...
    ]
}}

IMPORTANT: Every instance must be assigned to exactly one group."""

    result_text = await request_sampling(server, prompt, max_tokens=800)
    
    if result_text:
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                is_cpu = result.get("is_cpu", False)
                
                # Assign colors to groups
                for i, group in enumerate(result.get("groups", [])):
                    group_name = group.get("name", "")
                    
                    # Use CPU stage colors if applicable
                    if is_cpu and group_name in CPU_STAGE_COLORS:
                        fill, border = CPU_STAGE_COLORS[group_name]
                    else:
                        color_idx = i % len(GROUP_COLORS)
                        fill, border = GROUP_COLORS[color_idx]
                    
                    group["fill_color"] = fill
                    group["border_color"] = border
                return result
        except json.JSONDecodeError:
            pass
    
    return _fallback_design_analysis(instance_list)


def _fallback_design_analysis(instance_list: List[str]) -> Dict:
    """Fallback when sampling not available - simple pattern grouping."""
    groups = {}
    
    for item in instance_list:
        parts = item.split(" : ")
        inst_name = parts[0] if parts else item
        
        # Simple pattern-based grouping
        name_lower = inst_name.lower()
        if any(x in name_lower for x in ['mux', 'select']):
            group = 'Multiplexers'
        elif any(x in name_lower for x in ['reg', 'latch', 'ff']):
            group = 'Registers'
        elif any(x in name_lower for x in ['mem', 'ram', 'rom', 'fifo']):
            group = 'Memory'
        elif any(x in name_lower for x in ['ctrl', 'control', 'fsm', 'state']):
            group = 'Control'
        elif any(x in name_lower for x in ['alu', 'add', 'mult', 'div']):
            group = 'Datapath'
        else:
            group = 'Logic'
        
        if group not in groups:
            groups[group] = []
        groups[group].append(inst_name)
    
    # Convert to expected format
    result_groups = []
    for i, (name, instances) in enumerate(groups.items()):
        color_idx = i % len(GROUP_COLORS)
        result_groups.append({
            "name": name,
            "instances": instances,
            "fill_color": GROUP_COLORS[color_idx][0],
            "border_color": GROUP_COLORS[color_idx][1]
        })
    
    return {
        "design_type": "RTL Design",
        "groups": result_groups
    }


async def classify_instance_with_context(
    server: Server,
    instance: ModuleInstance,
    module_code: str,
    design_context: str
) -> Dict:
    """
    Classify a single instance with design context using MCP Sampling.
    
    Args:
        server: The MCP Server instance
        instance: The module instance
        module_code: Source code of the module (first 1000 chars)
        design_context: What type of design this is
        
    Returns:
        Dict with semantic_type, description
    """
    prompt = f"""Classify this Verilog module for a block diagram.

DESIGN: {design_context}
MODULE: {instance.module_type}
INSTANCE: {instance.instance_name}

Classify by FUNCTION, matching these semantic types:
- alu: Arithmetic/Logic Unit, ALU, adders, arithmetic operations
- mux: Multiplexers, selectors (2:1, 4:1 MUX, etc.)  
- memory: RAM, ROM, Data Memory, Instruction Memory
- register: Register file, pipeline registers (IF_ID, ID_EX, etc.)
- control: Control units, FSM, decoders
- compare: Comparators, hazard detection, forwarding units
- adder: Simple adders (PC+4, branch target)
- transform: Sign extend, shift left, data width conversion

Return ONLY JSON:
{{"semantic_type": "<alu|mux|memory|register|control|compare|adder|transform|logic>", "description": "<Module Type>\\n[{instance.instance_name}]"}}"""

    result_text = await request_sampling(server, prompt, max_tokens=80)
    
    if result_text:
        try:
            json_match = re.search(r'\{[^{}]+\}', result_text)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    return _simple_classify(instance)


def _simple_classify(instance: ModuleInstance) -> Dict:
    """Simple classification based on name."""
    name = instance.module_type.lower()
    
    if 'mux' in name:
        return {"semantic_type": "mux", "description": "Multiplexer"}
    elif any(x in name for x in ['mem', 'ram', 'rom']):
        return {"semantic_type": "memory", "description": "Memory"}
    elif any(x in name for x in ['reg', 'latch']):
        return {"semantic_type": "register", "description": "Register"}
    elif any(x in name for x in ['alu', 'add']):
        return {"semantic_type": "datapath", "description": "ALU"}
    elif 'ctrl' in name or 'control' in name:
        return {"semantic_type": "control", "description": "Controller"}
    else:
        return {"semantic_type": "logic", "description": instance.module_type}


async def enhance_instances_holistic(
    server: Server,
    instances: list,
    modules: Dict,
    top_module_code: str = "",
    use_llm: bool = True
) -> Tuple[Dict, str]:
    """
    Enhanced instance analysis with holistic design understanding.
    
    Args:
        server: The MCP Server instance
        instances: List of ModuleInstance objects
        modules: Dict of parsed modules
        top_module_code: Source code of top module
        use_llm: Whether to use LLM (via sampling)
        
    Returns:
        Tuple of (group_assignments dict, design_type string)
    """
    # Build instance list for analysis
    instance_list = [f"{inst.instance_name} : {inst.module_type}" for inst in instances]
    
    # Step 1: Analyze entire design holistically
    if use_llm:
        design_analysis = await analyze_design(server, top_module_code, instance_list)
    else:
        design_analysis = _fallback_design_analysis(instance_list)
    
    design_type = design_analysis.get("design_type", "RTL Design")
    groups = design_analysis.get("groups", [])
    
    # Build instance->group mapping
    instance_to_group = {}
    for group in groups:
        group_name = group.get("name", "Logic")
        for inst_name in group.get("instances", []):
            # Handle both "inst_name" and "inst_name : type" formats
            clean_name = inst_name.split(" : ")[0].strip()
            instance_to_group[clean_name] = {
                "group": group_name,
                "fill_color": group.get("fill_color", "#ECEFF1"),
                "border_color": group.get("border_color", "#607D8B")
            }
    
    # Step 2: Enhance each instance
    for inst in instances:
        # Get group assignment
        group_info = instance_to_group.get(inst.instance_name, {
            "group": "Logic",
            "fill_color": "#F5F5F5",
            "border_color": "#424242"
        })
        
        inst.pipeline_stage = group_info["group"]
        inst.cluster_fill_color = group_info["fill_color"]
        inst.cluster_border_color = group_info["border_color"]
        
        # Don't set inst.fill_color - let dot_generator use component style defaults
        # unless specifically needed for generic logic blocks.
        if inst.semantic_type == 'logic' and not use_llm:
             inst.fill_color = group_info["fill_color"]
        
        # Get module code for detailed classification
        module_info = modules.get(inst.module_type)
        module_code = ""
        if module_info and hasattr(module_info, 'raw_code'):
            module_code = module_info.raw_code
        
        # Classify instance
        if use_llm:
            classification = await classify_instance_with_context(server, inst, module_code, design_type)
        else:
            classification = _simple_classify(inst)
        
        inst.semantic_type = classification.get("semantic_type", "logic")
        inst.description = classification.get("description", inst.module_type)
    
    return instance_to_group, design_type


# Keep old function for backward compatibility (now async)
async def enhance_instances(
    server: Server,
    instances: list,
    modules: Dict,
    use_llm: bool = True
) -> None:
    """Legacy function - wraps new holistic approach."""
    # Get top module code if available
    top_code = ""
    for mod in modules.values():
        if hasattr(mod, 'raw_code'):
            top_code = mod.raw_code
            break
    
    await enhance_instances_holistic(server, instances, modules, top_code, use_llm)
