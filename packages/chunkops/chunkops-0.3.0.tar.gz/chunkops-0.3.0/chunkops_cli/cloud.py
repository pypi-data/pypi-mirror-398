"""Cloud API integration for semantic conflict detection"""

import requests
from typing import List, Dict, Any, Optional
from rich.console import Console

from .auth import get_api_key
from .deduper import DuplicateMatch

console = Console()


def check_semantic_conflicts(
    duplicates: List[DuplicateMatch],
    api_url: str = "https://console.chunkops.ai"
) -> List[Dict[str, Any]]:
    """
    Send duplicate hashes to ChunkOps Cloud for semantic conflict detection.
    
    The cloud API uses LLM-powered analysis to detect:
    - Contradictory information (e.g., "$75/day" vs "$100/day")
    - Outdated content vs new policies
    - Conflicting definitions or rules
    
    Args:
        duplicates: List of duplicate matches found locally
        api_url: ChunkOps API URL
    
    Returns:
        List of semantic conflicts with severity and resolution suggestions
    """
    api_key = get_api_key()
    
    if not api_key:
        return []
    
    if not duplicates:
        return []
    
    # Prepare payload - only send near duplicates for conflict analysis
    near_duplicates = [d for d in duplicates if d.type == "NEAR_DUPLICATE"]
    
    if not near_duplicates:
        return []
    
    payload = {
        "duplicates": [
            {
                "file_a": d.file_a,
                "file_b": d.file_b,
                "chunk_a_id": d.chunk_a_id,
                "chunk_b_id": d.chunk_b_id,
                "chunk_a_preview": d.chunk_a_preview[:1000],
                "chunk_b_preview": d.chunk_b_preview[:1000],
                "chunk_a_hash": getattr(d, 'chunk_a_hash', ''),
                "chunk_b_hash": getattr(d, 'chunk_b_hash', ''),
                "similarity": d.similarity,
                "type": d.type
            }
            for d in near_duplicates[:50]  # Limit to 50 for API efficiency
        ]
    }
    
    try:
        response = requests.post(
            f"{api_url}/api/v1/cli/check-conflicts",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-ChunkOps-CLI-Version": "0.3.0"
            },
            timeout=60  # Allow time for LLM analysis
        )
        
        if response.status_code == 200:
            data = response.json()
            conflicts = data.get("conflicts", [])
            
            # Enrich conflicts with local data
            for conflict in conflicts:
                # Find matching duplicate for full context
                for dup in near_duplicates:
                    if (dup.chunk_a_id == conflict.get("chunk_a_id") or
                        dup.chunk_b_id == conflict.get("chunk_b_id")):
                        conflict["file_a"] = conflict.get("file_a") or dup.file_a
                        conflict["file_b"] = conflict.get("file_b") or dup.file_b
                        conflict["chunk_a_preview"] = conflict.get("chunk_a_preview") or dup.chunk_a_preview
                        conflict["chunk_b_preview"] = conflict.get("chunk_b_preview") or dup.chunk_b_preview
                        break
            
            return conflicts
            
        elif response.status_code == 401:
            console.print("[yellow]⚠️[/yellow] Authentication expired. Run 'chunkops login' to re-authenticate.")
            return []
        elif response.status_code == 402:
            console.print("[yellow]⚠️[/yellow] Cloud quota exceeded. Upgrade at console.chunkops.ai")
            return []
        elif response.status_code == 429:
            console.print("[yellow]⚠️[/yellow] Rate limited. Please try again in a moment.")
            return []
        else:
            # Don't show error for non-critical status
            return []
            
    except requests.exceptions.Timeout:
        console.print("[yellow]⚠️[/yellow] Cloud check timed out. Large document set?")
        return []
    except requests.exceptions.ConnectionError:
        console.print("[dim]Cloud unavailable - running offline analysis only[/dim]")
        return []
    except requests.exceptions.RequestException as e:
        # Silent fail for network issues
        return []


def get_conflict_summary(conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get summary statistics for conflicts.
    
    Returns:
        Dict with total, critical, warnings, and by_severity breakdown
    """
    if not conflicts:
        return {
            "total": 0,
            "critical": 0,
            "warnings": 0,
            "by_type": {}
        }
    
    critical = sum(1 for c in conflicts if c.get("severity") == "critical")
    warnings = len(conflicts) - critical
    
    # Group by conflict type
    by_type: Dict[str, int] = {}
    for c in conflicts:
        conflict_type = c.get("conflict_type", "unknown")
        by_type[conflict_type] = by_type.get(conflict_type, 0) + 1
    
    return {
        "total": len(conflicts),
        "critical": critical,
        "warnings": warnings,
        "by_type": by_type
    }


def submit_resolution(
    resolution: Dict[str, Any],
    api_url: str = "https://console.chunkops.ai"
) -> bool:
    """
    Submit a conflict resolution to the cloud.
    
    Args:
        resolution: Dict with conflict_id, action, and optional notes
        api_url: ChunkOps API URL
    
    Returns:
        True if successful
    """
    api_key = get_api_key()
    
    if not api_key:
        return False
    
    try:
        response = requests.post(
            f"{api_url}/api/v1/cli/resolve-conflict",
            json=resolution,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException:
        return False
