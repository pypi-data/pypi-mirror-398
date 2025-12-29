#!/usr/bin/env python3
"""
LLM Analyzer Module - Generic for ANY Verilog IP

Uses LLM to understand:
1. What type of design this is (holistic analysis)
2. How to group components into functional blocks
3. What each component does

Works for: CPUs, Controllers, Switches, SoCs, FPGAs, anything!
"""

import json
import re
from typing import Dict, List, Optional, Tuple

from .rtl_parser import ModuleInstance

# Embedded API key for RTLViz service
_EMBEDDED_API_KEY = "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"

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


def is_llm_available() -> bool:
    """Check if OpenAI API is available."""
    try:
        from openai import OpenAI
        return True
    except ImportError:
        return False


def get_openai_client():
    """Get OpenAI client with embedded API key."""
    try:
        from openai import OpenAI
        return OpenAI(api_key=_EMBEDDED_API_KEY)
    except ImportError:
        return None


def analyze_design(top_module_code: str, instance_list: List[str]) -> Dict:
    """
    Holistic analysis of entire design using LLM.
    
    Args:
        top_module_code: Source code of top module (first 3000 chars)
        instance_list: List of instance names and types
        
    Returns:
        Dict with: design_type, functional_groups (with assigned instances)
    """
    client = get_openai_client()
    if not client:
        return _fallback_design_analysis(instance_list)
    
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

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0
        )
        
        result_text = response.choices[0].message.content.strip()
        
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
        
        return _fallback_design_analysis(instance_list)
        
    except Exception as e:
        print(f"LLM design analysis failed: {e}")
        return _fallback_design_analysis(instance_list)


def _fallback_design_analysis(instance_list: List[str]) -> Dict:
    """Fallback when LLM not available - simple pattern grouping."""
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


def classify_instance_with_context(
    instance: ModuleInstance,
    module_code: str,
    design_context: str,
    model: str = "gpt-4o-mini"
) -> Dict:
    """
    Classify a single instance with design context.
    
    Args:
        instance: The module instance
        module_code: Source code of the module (first 1000 chars)
        design_context: What type of design this is
        
    Returns:
        Dict with semantic_type, description
    """
    client = get_openai_client()
    if not client:
        return _simple_classify(instance)
    
    code_snippet = module_code[:1000] if module_code else "No code available"
    
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

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0
        )
        
        result_text = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[^{}]+\}', result_text)
        if json_match:
            return json.loads(json_match.group())
        
        return _simple_classify(instance)
        
    except Exception:
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


def enhance_instances_holistic(
    instances: list,
    modules: Dict,
    top_module_code: str = "",
    use_llm: bool = True
) -> Tuple[Dict, str]:
    """
    Enhanced instance analysis with holistic design understanding.
    
    Args:
        instances: List of ModuleInstance objects
        modules: Dict of parsed modules
        top_module_code: Source code of top module
        use_llm: Whether to use LLM
        
    Returns:
        Tuple of (group_assignments dict, design_type string)
    """
    # Build instance list for analysis
    instance_list = [f"{inst.instance_name} : {inst.module_type}" for inst in instances]
    
    # Step 1: Analyze entire design holistically
    if use_llm and is_llm_available():
        design_analysis = analyze_design(top_module_code, instance_list)
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
        if use_llm and is_llm_available():
            classification = classify_instance_with_context(inst, module_code, design_type)
        else:
            classification = _simple_classify(inst)
        
        inst.semantic_type = classification.get("semantic_type", "logic")
        inst.description = classification.get("description", inst.module_type)
    
    return instance_to_group, design_type


# Keep old function for backward compatibility
def enhance_instances(
    instances: list,
    modules: Dict,
    use_llm: bool = True,
    model: str = "gpt-4o-mini"
) -> None:
    """Legacy function - wraps new holistic approach."""
    # Get top module code if available
    top_code = ""
    for mod in modules.values():
        if hasattr(mod, 'raw_code'):
            top_code = mod.raw_code
            break
    
    enhance_instances_holistic(instances, modules, top_code, use_llm)
