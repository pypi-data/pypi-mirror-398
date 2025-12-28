"""Report formatting and display utilities."""

from typing import Dict, Any


def get_risk_level(risk_score: int) -> tuple:
    """
    Get risk level description and symbol based on score.
    
    Args:
        risk_score: Risk score from 0-100
    
    Returns:
        Tuple of (level_name, symbol)
    """
    if risk_score >= 70:
        return "HIGH RISK", "(!)"
    elif risk_score >= 40:
        return "MEDIUM RISK", "(*)"
    elif risk_score > 0:
        return "LOW RISK", "(i)"
    else:
        return "NO RISK", "(+)"


def format_report(results: Dict[str, Any]) -> str:
    """
    Format detection results into a human-readable report.
    
    Args:
        results: Results dictionary from report() function
    
    Returns:
        Formatted report string
    """
    lines = []
    
    # Header
    lines.append("=" * 50)
    lines.append("         ML DATA LEAKAGE REPORT")
    lines.append("=" * 50)
    lines.append("")
    
    # Dataset info
    summary = results.get("summary", {})
    lines.append("DATASET INFO:")
    lines.append(f"  Train samples: {summary.get('train_samples', 'N/A')}")
    lines.append(f"  Test samples:  {summary.get('test_samples', 'N/A')}")
    lines.append(f"  Total features: {summary.get('total_features', 'N/A')}")
    lines.append("")
    
    # Leakage checks
    lines.append("LEAKAGE CHECKS:")
    lines.append("-" * 50)
    lines.append("")
    
    # Duplicate check
    dup_result = results.get("duplicate_check", {})
    if dup_result.get("passed") is True:
        lines.append("[PASS] Duplicate Rows: PASS")
        lines.append("  No duplicate rows found between splits")
    elif dup_result.get("passed") is False:
        lines.append("[FAIL] Duplicate Rows: FAIL")
        lines.append(f"  Found {dup_result.get('duplicate_count', 0)} duplicate rows")
        dup_pct = (dup_result.get('duplicate_count', 0) / dup_result.get('total_test', 1)) * 100
        lines.append(f"  {dup_pct:.2f}% of test data is duplicated from training")
    elif "error" in dup_result:
        lines.append("[ERROR] Duplicate Rows: ERROR")
        lines.append(f"  {dup_result.get('error')}")
    lines.append("")
    
    # Time check
    time_result = results.get("time_check")
    if time_result:
        if time_result.get("passed") is True:
            lines.append("[PASS] Time Leakage: PASS")
            lines.append("  Test data is properly sequenced after training data")
        elif time_result.get("passed") is False:
            lines.append("[FAIL] Time Leakage: FAIL")
            lines.append(f"  Found {time_result.get('leakage_count', 0)} test samples with timestamps before training data")
            lines.append(f"  Latest train date: {time_result.get('train_max', 'N/A')}")
            lines.append(f"  Earliest test date: {time_result.get('test_min', 'N/A')}")
        elif "error" in time_result:
            lines.append("[ERROR] Time Leakage: ERROR")
            lines.append(f"  {time_result.get('error')}")
        lines.append("")
    
    # Group check
    group_result = results.get("group_check")
    if group_result:
        group_results = group_result.get("group_results", {})
        
        for group_col, gr in group_results.items():
            if gr.get("passed") is True:
                lines.append(f"[PASS] Group Leakage ({group_col}): PASS")
                lines.append(f"  No overlapping groups found")
            elif gr.get("passed") is False:
                lines.append(f"[FAIL] Group Leakage ({group_col}): FAIL")
                lines.append(f"  Found {gr.get('overlap_count', 0)} overlapping groups ({gr.get('overlap_percentage', 0):.1f}%)")
                lines.append(f"  This means same {group_col} values appear in both train and test")
            elif "error" in gr:
                lines.append(f"[ERROR] Group Leakage ({group_col}): ERROR")
                lines.append(f"  {gr.get('error')}")
            lines.append("")
    
    # Risk score
    risk_score = results.get("risk_score", 0)
    risk_level, risk_symbol = get_risk_level(risk_score)
    lines.append(f"OVERALL RISK SCORE: {risk_score}/100 ({risk_level} {risk_symbol})")
    lines.append("")
    
    # Recommendations
    if risk_score > 0:
        lines.append("RECOMMENDATIONS:")
        
        # Duplicate recommendations
        if not dup_result.get("passed", True):
            lines.append("  - Remove duplicate rows from test set")
        
        # Time recommendations
        if time_result and not time_result.get("passed", True):
            lines.append("  - Ensure test data is strictly after training data")
            lines.append("  - Consider using time-based split with proper cutoff")
        
        # Group recommendations
        if group_result and not group_result.get("passed", True):
            for group_col, gr in group_results.items():
                if not gr.get("passed", True):
                    lines.append(f"  - Remove overlapping {group_col} groups from test set")
                    lines.append(f"  - Use group-based split to ensure no {group_col} overlap")
        
        lines.append("")
    
    # Footer
    lines.append("=" * 50)
    
    return "\n".join(lines)
