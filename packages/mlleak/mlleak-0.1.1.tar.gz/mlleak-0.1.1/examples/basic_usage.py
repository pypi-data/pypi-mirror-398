"""
Basic usage examples for mlleak package.

This script demonstrates various leakage detection scenarios.
"""

import pandas as pd
import numpy as np
import mlleak


def example_clean_split():
    """Example 1: Clean split with no leakage."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Clean Split (No Issues)")
    print("="*60)
    
    # Create clean train/test split
    np.random.seed(42)
    train_df = pd.DataFrame({
        'user_id': range(100, 200),
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'date': pd.date_range('2024-01-01', periods=100),
        'target': np.random.randint(0, 2, 100)
    })
    
    test_df = pd.DataFrame({
        'user_id': range(200, 250),
        'feature1': np.random.randn(50),
        'feature2': np.random.randn(50),
        'date': pd.date_range('2024-04-11', periods=50),
        'target': np.random.randint(0, 2, 50)
    })
    
    mlleak.report(train_df, test_df, target='target', 
                  group_cols=['user_id'], time_col='date')


def example_duplicate_leakage():
    """Example 2: Duplicate rows in train and test."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Duplicate Row Leakage")
    print("="*60)
    
    np.random.seed(42)
    train_df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'target': np.random.randint(0, 2, 100)
    })
    
    # Test set contains some duplicates from training
    test_df = pd.concat([
        train_df.sample(10),  # 10 duplicates!
        pd.DataFrame({
            'feature1': np.random.randn(40),
            'feature2': np.random.randn(40),
            'target': np.random.randint(0, 2, 40)
        })
    ]).reset_index(drop=True)
    
    mlleak.report(train_df, test_df, target='target')


def example_time_leakage():
    """Example 3: Time leakage (test before train)."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Time Leakage")
    print("="*60)
    
    np.random.seed(42)
    
    # Training data from Jan-March
    train_df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'date': pd.date_range('2024-01-01', periods=100),
        'target': np.random.randint(0, 2, 100)
    })
    
    # Test data has some dates BEFORE training! (leakage)
    test_dates = list(pd.date_range('2023-12-01', periods=20)) + \
                 list(pd.date_range('2024-04-11', periods=30))
    
    test_df = pd.DataFrame({
        'feature1': np.random.randn(50),
        'date': test_dates,
        'target': np.random.randint(0, 2, 50)
    })
    
    mlleak.report(train_df, test_df, target='target', time_col='date')


def example_group_leakage():
    """Example 4: Group leakage (same user_id in both splits)."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Group Leakage")
    print("="*60)
    
    np.random.seed(42)
    
    # Training data with users 1-100
    train_df = pd.DataFrame({
        'user_id': np.random.randint(1, 101, 200),
        'session_id': range(1000, 1200),
        'feature1': np.random.randn(200),
        'target': np.random.randint(0, 2, 200)
    })
    
    # Test data with users 90-120 (overlap with train!)
    test_df = pd.DataFrame({
        'user_id': np.random.randint(90, 121, 100),
        'session_id': range(2000, 2100),
        'feature1': np.random.randn(100),
        'target': np.random.randint(0, 2, 100)
    })
    
    mlleak.report(train_df, test_df, target='target', 
                  group_cols=['user_id', 'session_id'])


def example_multiple_issues():
    """Example 5: Multiple types of leakage."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Multiple Leakage Issues (Worst Case!)")
    print("="*60)
    
    np.random.seed(42)
    
    # Training data
    train_df = pd.DataFrame({
        'user_id': np.random.randint(1, 51, 100),
        'feature1': np.random.randn(100),
        'date': pd.date_range('2024-01-01', periods=100),
        'target': np.random.randint(0, 2, 100)
    })
    
    # Test data with ALL types of leakage
    test_df = pd.concat([
        train_df.sample(5),  # Duplicate rows
        pd.DataFrame({
            'user_id': np.random.randint(40, 61, 45),  # Overlapping user_ids
            'feature1': np.random.randn(45),
            'date': pd.concat([
                pd.Series(pd.date_range('2023-11-01', periods=15)),  # Time leakage
                pd.Series(pd.date_range('2024-04-11', periods=30))
            ]).reset_index(drop=True),
            'target': np.random.randint(0, 2, 45)
        })
    ]).reset_index(drop=True)
    
    mlleak.report(train_df, test_df, target='target',
                  group_cols=['user_id'], time_col='date')


if __name__ == "__main__":
    print("\nmlleak - ML Data Leakage Detection Examples\n")
    
    # Run all examples
    example_clean_split()
    example_duplicate_leakage()
    example_time_leakage()
    example_group_leakage()
    example_multiple_issues()
    
    print("\n" + "="*60)
    print("Examples completed! Check the reports above.")
    print("="*60)
