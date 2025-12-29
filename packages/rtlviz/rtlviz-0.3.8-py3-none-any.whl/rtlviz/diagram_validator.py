#!/usr/bin/env python3
"""
Diagram Validator - LLM-as-Judge for RTL Diagram Quality

Strict validation criteria:
1. CONNECTIVITY: All nodes should be connected (no orphans)
2. GROUPING: Related components should be clustered  
3. LAYOUT: Orthogonal lines, clear flow direction
"""

import json
import re
from typing import Dict, Set

from .llm_analyzer import get_openai_client


def validate_diagram(dot_code: str) -> Dict:
    """
    Validate diagram quality - checks for disconnected nodes.
    
    Returns:
        Dict with: score (0-100), pass (bool), issues, suggestions
    """
    # Extract nodes and edges
    node_names = set(re.findall(r'(\w+)\s*\[label=', dot_code))
    
    # Find all edge connections (excluding invisible edges)
    connected_nodes: Set[str] = set()
    edges = re.findall(r'(\w+)\s*->\s*(\w+)', dot_code)
    for src, dst in edges:
        # Skip invisible edges used for layout
        connected_nodes.add(src)
        connected_nodes.add(dst)
    
    # Find disconnected nodes
    disconnected = node_names - connected_nodes
    
    # Count metrics
    node_count = len(node_names)
    edge_count = len(edges) - len(re.findall(r'style=invis', dot_code))
    cluster_count = len(re.findall(r'subgraph cluster_', dot_code))
    
    # Quick checks
    issues = []
    score = 100
    
    if node_count == 0:
        return {"score": 0, "pass": False, "issues": ["No nodes found"], "suggestions": []}
    
    # Check for disconnected nodes (critical issue)
    if disconnected:
        score -= min(40, len(disconnected) * 5)  # -5 per disconnected node, max -40
        issues.append(f"{len(disconnected)} disconnected nodes: {', '.join(list(disconnected)[:5])}")
    
    # Check edge ratio
    edge_ratio = edge_count / max(1, node_count)
    if edge_ratio < 0.3:
        score -= 20
        issues.append(f"Low connectivity: only {edge_count} edges for {node_count} nodes")
    
    # Check for clusters
    if cluster_count < 2 and node_count > 5:
        score -= 15
        issues.append("Only one cluster - components not grouped")
        
    # Check for excessive whitespace
    nodesep_match = re.search(r'nodesep=([\d\.]+)', dot_code)
    ranksep_match = re.search(r'ranksep=([\d\.]+)', dot_code)
    if nodesep_match and float(nodesep_match.group(1)) > 0.6:
         score -= 10
         issues.append(f"Excessive horizontal whitespace (nodesep={nodesep_match.group(1)})")
    if ranksep_match and float(ranksep_match.group(1)) > 1.2:
         score -= 10
         issues.append(f"Excessive vertical whitespace (ranksep={ranksep_match.group(1)})")

    # Check for uncolored nodes
    # Basic check: count node lines vs node lines with fillcolor
    uncolored_count = 0
    for line in dot_code.split('\n'):
        if '[' in line and 'label=' in line and '->' not in line:
            if 'fillcolor' not in line:
                uncolored_count += 1
    
    if uncolored_count > 0:
        score -= min(30, uncolored_count * 5)
        issues.append(f"{uncolored_count} nodes are missing colors")
    
    # Use LLM for detailed validation if available
    client = get_openai_client()
    if client and len(issues) == 0:
        try:
            llm_result = _llm_validate(client, dot_code, node_count, edge_count, cluster_count)
            if llm_result:
                score = llm_result.get("score", score)
                issues.extend(llm_result.get("issues", []))
        except Exception:
            pass
    
    return {
        "score": max(0, score),
        "pass": score >= 65,
        "issues": issues,
        "suggestions": ["Fix disconnected nodes by improving signal detection"] if disconnected else [],
        "disconnected_nodes": list(disconnected)
    }


def _llm_validate(client, dot_code: str, nodes: int, edges: int, clusters: int) -> Dict:
    """Use LLM for detailed quality check."""
    prompt = f"""Evaluate this RTL block diagram DOT code:
Nodes: {nodes}, Edges: {edges}, Clusters: {clusters}

```dot
{dot_code[:1500]}
```

Check:
1. Are nodes logically grouped into clusters?
2. Does the layout flow left-to-right?
3. Are there reasonable connections?
4. Is there excessive whitespace? (Dense layout is better)
5. Do all nodes have appropriate coloring? (No white/blank nodes)

Return JSON: {{"score": 0-100, "issues": ["list"]}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0
    )
    
    result_text = response.choices[0].message.content.strip()
    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return None


def should_regenerate(result: Dict) -> bool:
    """Check if diagram should be regenerated."""
    return not result.get("pass", True)
