"""Core leakage detection functionality."""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from .reporter import format_report


def detect_duplicate_rows(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    exclude_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Detect exact row duplicates between train and test sets.
    
    Args:
        train_df: Training DataFrame
        test_df: Test DataFrame
        exclude_cols: Columns to exclude from duplicate check (e.g., target column)
    
    Returns:
        Dictionary with detection results
    """
    # Get columns to check
    check_cols = list(train_df.columns)
    if exclude_cols:
        check_cols = [col for col in check_cols if col not in exclude_cols]
    
    # Find common columns
    common_cols = [col for col in check_cols if col in test_df.columns]
    
    if not common_cols:
        return {
            "passed": True,
            "duplicate_count": 0,
            "details": "No common columns to check"
        }
    
    # Create subsets with only common columns
    train_subset = train_df[common_cols].copy()
    test_subset = test_df[common_cols].copy()
    
    # Find duplicates by merging
    merged = train_subset.merge(
        test_subset,
        on=common_cols,
        how='inner',
        indicator=False
    )
    
    duplicate_count = len(merged)
    
    return {
        "passed": duplicate_count == 0,
        "duplicate_count": duplicate_count,
        "total_train": len(train_df),
        "total_test": len(test_df),
        "checked_columns": len(common_cols),
        "details": f"Found {duplicate_count} duplicate rows" if duplicate_count > 0 else "No duplicates found"
    }


def detect_time_leakage(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    time_col: str
) -> Dict[str, Any]:
    """
    Detect time leakage (test data before training data).
    
    Args:
        train_df: Training DataFrame
        test_df: Test DataFrame
        time_col: Name of the time/date column
    
    Returns:
        Dictionary with detection results
    """
    if time_col not in train_df.columns:
        return {
            "passed": None,
            "error": f"Time column '{time_col}' not found in training data"
        }
    
    if time_col not in test_df.columns:
        return {
            "passed": None,
            "error": f"Time column '{time_col}' not found in test data"
        }
    
    try:
        # Convert to datetime if not already
        train_times = pd.to_datetime(train_df[time_col])
        test_times = pd.to_datetime(test_df[time_col])
        
        # Get min/max dates
        train_min = train_times.min()
        train_max = train_times.max()
        test_min = test_times.min()
        test_max = test_times.max()
        
        # Check for leakage (test data before training data)
        leakage_count = (test_times < train_max).sum()
        
        return {
            "passed": leakage_count == 0,
            "leakage_count": int(leakage_count),
            "train_min": str(train_min),
            "train_max": str(train_max),
            "test_min": str(test_min),
            "test_max": str(test_max),
            "details": f"Found {leakage_count} test samples with timestamps before latest training data" if leakage_count > 0 else "No time leakage detected"
        }
    except Exception as e:
        return {
            "passed": None,
            "error": f"Error processing time column: {str(e)}"
        }


def detect_group_leakage(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    group_cols: List[str]
) -> Dict[str, Any]:
    """
    Detect group leakage (same group IDs in both train and test).
    
    Args:
        train_df: Training DataFrame
        test_df: Test DataFrame
        group_cols: List of column names representing groups
    
    Returns:
        Dictionary with detection results
    """
    results = {}
    overall_passed = True
    
    for group_col in group_cols:
        if group_col not in train_df.columns:
            results[group_col] = {
                "passed": None,
                "error": f"Group column '{group_col}' not found in training data"
            }
            continue
        
        if group_col not in test_df.columns:
            results[group_col] = {
                "passed": None,
                "error": f"Group column '{group_col}' not found in test data"
            }
            continue
        
        # Find overlapping groups
        train_groups = set(train_df[group_col].dropna().unique())
        test_groups = set(test_df[group_col].dropna().unique())
        overlap = train_groups.intersection(test_groups)
        
        passed = len(overlap) == 0
        overall_passed = overall_passed and passed
        
        results[group_col] = {
            "passed": passed,
            "overlap_count": len(overlap),
            "train_unique": len(train_groups),
            "test_unique": len(test_groups),
            "overlap_percentage": round(len(overlap) / len(train_groups) * 100, 2) if len(train_groups) > 0 else 0,
            "details": f"Found {len(overlap)} overlapping groups" if len(overlap) > 0 else "No overlapping groups"
        }
    
    return {
        "passed": overall_passed,
        "group_results": results,
        "total_groups_checked": len(group_cols)
    }


def calculate_risk_score(
    duplicate_result: Dict[str, Any],
    time_result: Optional[Dict[str, Any]],
    group_result: Optional[Dict[str, Any]]
) -> int:
    """
    Calculate overall risk score (0-100).
    
    Higher score = higher risk of data leakage
    
    Args:
        duplicate_result: Results from duplicate detection
        time_result: Results from time leakage detection
        group_result: Results from group leakage detection
    
    Returns:
        Risk score from 0 (no risk) to 100 (critical risk)
    """
    risk_score = 0
    
    # Duplicate risk (0-40 points)
    if not duplicate_result.get("passed", True):
        duplicate_pct = (duplicate_result.get("duplicate_count", 0) / 
                        duplicate_result.get("total_test", 1)) * 100
        risk_score += min(40, duplicate_pct * 4)  # Scale to max 40 points
    
    # Time leakage risk (0-30 points)
    if time_result and not time_result.get("passed", True):
        leakage_pct = (time_result.get("leakage_count", 0) / 
                      len(time_result)) * 100 if isinstance(time_result, dict) else 0
        risk_score += min(30, leakage_pct * 3)  # Scale to max 30 points
    
    # Group leakage risk (0-30 points)
    if group_result and not group_result.get("passed", True):
        group_results = group_result.get("group_results", {})
        max_overlap = 0
        for gr in group_results.values():
            if isinstance(gr, dict) and "overlap_percentage" in gr:
                max_overlap = max(max_overlap, gr["overlap_percentage"])
        risk_score += min(30, max_overlap * 3)  # Scale to max 30 points
    
    return min(100, int(risk_score))


def report(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target: Optional[str] = None,
    group_cols: Optional[List[str]] = None,
    time_col: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Generate a comprehensive data leakage report.
    
    Args:
        train_df: Training DataFrame
        test_df: Test DataFrame
        target: Optional target column name to exclude from duplicate checks
        group_cols: Optional list of group column names (e.g., user_id)
        time_col: Optional time/date column name
        verbose: If True, print formatted report to console
    
    Returns:
        Dictionary containing all detection results and risk score
    """
    # Validate inputs
    if not isinstance(train_df, pd.DataFrame):
        raise ValueError("train_df must be a pandas DataFrame")
    if not isinstance(test_df, pd.DataFrame):
        raise ValueError("test_df must be a pandas DataFrame")
    
    if len(train_df) == 0:
        raise ValueError("train_df is empty")
    if len(test_df) == 0:
        raise ValueError("test_df is empty")
    
    # Run detections
    exclude_cols = [target] if target else None
    duplicate_result = detect_duplicate_rows(train_df, test_df, exclude_cols)
    
    time_result = None
    if time_col:
        time_result = detect_time_leakage(train_df, test_df, time_col)
    
    group_result = None
    if group_cols:
        group_result = detect_group_leakage(train_df, test_df, group_cols)
    
    # Calculate risk score
    risk_score = calculate_risk_score(duplicate_result, time_result, group_result)
    
    # Compile results
    results = {
        "summary": {
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "total_features": len(train_df.columns),
            "risk_score": risk_score
        },
        "duplicate_check": duplicate_result,
        "time_check": time_result,
        "group_check": group_result,
        "risk_score": risk_score
    }
    
    # Print formatted report if verbose
    if verbose:
        print(format_report(results))
    
    return results
