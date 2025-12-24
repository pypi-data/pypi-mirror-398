"""
Expression profiling tool for Polars analysis classes.

Profiles the performance of Polars expressions from analysis classes
by executing them on progressively larger slices of a LazyFrame.
"""
# state:READONLY
from __future__ import annotations

import time
from typing import List, Type, Optional
from dataclasses import dataclass
from pathlib import Path

import polars as pl
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .polars_analysis_management import PolarsAnalysis, polars_select_expressions


@dataclass
class ExpressionProfile:
    """Profile result for a single expression execution."""
    analysis_class_name: str
    expression_index: int
    expression_name: str
    column_name: str
    row_count: int
    execution_time_secs: float
    success: bool
    error_message: Optional[str] = None


def profile_expressions(
    analysis_klasses: List[Type[PolarsAnalysis]],
    ldf: pl.LazyFrame,
    test_columns: Optional[List[str]] = None,
    max_rows: Optional[int] = None,
    row_counts: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Profile Polars expressions from analysis classes by timing their execution
    on progressively larger slices of a LazyFrame.
    
    Args:
        analysis_klasses: List of PolarsAnalysis classes to profile
        ldf: LazyFrame to profile against
        test_columns: Optional list of column names to test. If None, uses all columns.
        max_rows: Maximum number of rows to test. If None, uses all rows in LazyFrame.
        row_counts: Optional list of specific row counts to test. If None, uses base-10 sizes (10, 100, 1000, ...)
    
    Returns:
        DataFrame with columns:
        - analysis_class_name: Name of the analysis class
        - expression_index: Index of expression in select_clauses
        - expression_name: Name/description of the expression
        - column_name: Column being tested
        - row_count: Number of rows in the test slice
        - execution_time_secs: Time taken to execute
        - success: Whether execution succeeded
        - error_message: Error message if execution failed
    """
    # Get all expressions from analysis classes
    all_expressions = polars_select_expressions(analysis_klasses)
    
    if not all_expressions:
        return pd.DataFrame()
    
    # Determine which columns to test
    all_cols = ldf.collect_schema().names()
    if test_columns is None:
        test_columns = all_cols
    else:
        # Filter to only columns that exist
        test_columns = [c for c in test_columns if c in all_cols]
    
    if not test_columns:
        return pd.DataFrame()
    
    # Determine row counts to test
    if row_counts is None:
        # Get total row count
        if max_rows is None:
            try:
                total_rows = ldf.select(pl.len().alias("__len")).collect().item()
            except Exception:
                total_rows = 10000  # Default fallback
        else:
            total_rows = max_rows
        
        # Generate base-10 row counts: 10, 100, 1000, ... up to total_rows
        row_counts = []
        current = 10
        while current <= total_rows:
            row_counts.append(current)
            current *= 10
        # Always include total_rows if it's not already in the list
        if total_rows not in row_counts:
            row_counts.append(total_rows)
    else:
        row_counts = sorted(row_counts)
    
    # Map expressions back to their analysis classes
    # This is approximate - we'll use the order they appear
    expr_to_analysis = {}
    expr_index = 0
    for analysis_class in analysis_klasses:
        for _ in analysis_class.select_clauses:
            expr_to_analysis[expr_index] = analysis_class.__name__
            expr_index += 1
    
    # Profile each expression at each row count
    # Note: Expressions may operate on all columns (using selectors), so we execute
    # them on the full sliced LazyFrame, but we'll attribute the time to each test column
    profiles: List[ExpressionProfile] = []
    
    for row_count in row_counts:
        # Create a slice of the LazyFrame with only test columns
        sliced_ldf = ldf.select(test_columns).head(row_count)
        
        for expr_idx, expr in enumerate(all_expressions):
            analysis_name = expr_to_analysis.get(expr_idx, "Unknown")
            
            # Try to get expression name from the expression itself
            # Expressions from analysis classes often have names via json_postfix
            expr_name = f"expr_{expr_idx}"
            try:
                # Try to extract name if expression has one
                if hasattr(expr, 'meta'):
                    meta = expr.meta
                    if hasattr(meta, 'output_name'):
                        name = meta.output_name()
                        if name:
                            expr_name = name
                    elif hasattr(meta, 'output_names'):
                        names = meta.output_names()
                        if names and len(names) > 0:
                            expr_name = names[0]
            except Exception:
                pass
            
            # Also try to get a string representation as fallback
            if expr_name == f"expr_{expr_idx}":
                try:
                    expr_str = str(expr)
                    # Extract meaningful part (first 50 chars)
                    if len(expr_str) > 50:
                        expr_name = expr_str[:50] + "..."
                    else:
                        expr_name = expr_str
                except Exception:
                    pass
            
            # Execute and time the expression on the full sliced LazyFrame
            # Expressions may operate on multiple columns via selectors
            start_time = time.time()
            success = True
            error_msg = None
            
            try:
                _ = sliced_ldf.select(expr).collect()  # Execute expression to measure time
                execution_time = time.time() - start_time
            except Exception as e:
                execution_time = time.time() - start_time
                success = False
                error_msg = str(e)
            
            # Create a profile entry for each test column
            # This allows per-column analysis even though expression runs on all columns
            for col_name in test_columns:
                profile = ExpressionProfile(
                    analysis_class_name=analysis_name,
                    expression_index=expr_idx,
                    expression_name=expr_name,
                    column_name=col_name,
                    row_count=row_count,
                    execution_time_secs=execution_time,  # Same time for all columns (expression runs once)
                    success=success,
                    error_message=error_msg,
                )
                profiles.append(profile)
    
    # Convert to DataFrame
    profile_dicts = [
        {
            'analysis_class_name': p.analysis_class_name,
            'expression_index': p.expression_index,
            'expression_name': p.expression_name,
            'column_name': p.column_name,
            'row_count': p.row_count,
            'execution_time_secs': p.execution_time_secs,
            'success': p.success,
            'error_message': p.error_message,
        }
        for p in profiles
    ]
    
    return pd.DataFrame(profile_dicts)


def plot_expression_performance(
    profile_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    show_plot: bool = False,
) -> None:
    """
    Create matplotlib plots showing expression performance across different row counts.
    
    Args:
        profile_df: DataFrame from profile_expressions()
        output_path: Optional path to save the plot. If None, plot is shown or saved to default location.
        show_plot: Whether to display the plot (requires interactive backend)
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")
    
    if profile_df.empty:
        print("No profile data to plot")
        return
    
    # Filter to only successful executions
    success_df = profile_df[profile_df['success']].copy()
    
    if success_df.empty:
        print("No successful executions to plot")
        return
    
    # Create subplots - one per analysis class
    analysis_classes = success_df['analysis_class_name'].unique()
    n_analyses = len(analysis_classes)
    
    if n_analyses == 0:
        return
    
    # Create figure with subplots
    fig, axes = plt.subplots(n_analyses, 1, figsize=(12, 6 * n_analyses))
    if n_analyses == 1:
        axes = [axes]
    
    for ax_idx, analysis_name in enumerate(analysis_classes):
        ax = axes[ax_idx]
        
        # Get data for this analysis class
        analysis_df = success_df[success_df['analysis_class_name'] == analysis_name]
        
        # Plot each expression as a line
        for (expr_name, col_name), group in analysis_df.groupby(['expression_name', 'column_name']):
            group_sorted = group.sort_values('row_count')
            label = f"{expr_name} ({col_name})"
            ax.plot(
                group_sorted['row_count'],
                group_sorted['execution_time_secs'],
                marker='o',
                label=label,
                linewidth=2,
            )
        
        ax.set_xlabel('Row Count (log scale)')
        ax.set_ylabel('Execution Time (seconds)')
        ax.set_title(f'Expression Performance: {analysis_name}')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {output_path}")
    
    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_expression_comparison(
    profile_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    show_plot: bool = False,
) -> None:
    """
    Create a comparison plot showing all expressions on the same axes.
    
    Args:
        profile_df: DataFrame from profile_expressions()
        output_path: Optional path to save the plot
        show_plot: Whether to display the plot
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")
    
    if profile_df.empty:
        print("No profile data to plot")
        return
    
    # Filter to only successful executions
    success_df = profile_df[profile_df['success']].copy()
    
    if success_df.empty:
        print("No successful executions to plot")
        return
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each expression as a line
    for (analysis_name, expr_name, col_name), group in success_df.groupby(['analysis_class_name', 'expression_name', 'column_name']):
        group_sorted = group.sort_values('row_count')
        label = f"{analysis_name}.{expr_name} ({col_name})"
        ax.plot(
            group_sorted['row_count'],
            group_sorted['execution_time_secs'],
            marker='o',
            label=label,
            linewidth=2,
            markersize=4,
        )
    
    ax.set_xlabel('Row Count (log scale)')
    ax.set_ylabel('Execution Time (seconds, log scale)')
    ax.set_title('Expression Performance Comparison')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {output_path}")
    
    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_per_column_performance(
    profile_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    show_plot: bool = False,
) -> None:
    """
    Create plots showing performance per column, grouped by expression.
    
    Args:
        profile_df: DataFrame from profile_expressions()
        output_path: Optional path to save the plot
        show_plot: Whether to display the plot
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")
    
    if profile_df.empty:
        print("No profile data to plot")
        return
    
    # Filter to only successful executions
    success_df = profile_df[profile_df['success']].copy()
    
    if success_df.empty:
        print("No successful executions to plot")
        return
    
    # Get unique expressions
    expressions = success_df.groupby(['analysis_class_name', 'expression_name']).groups.keys()
    n_exprs = len(list(expressions))
    
    if n_exprs == 0:
        return
    
    # Create subplots - one per expression
    fig, axes = plt.subplots(n_exprs, 1, figsize=(12, 6 * n_exprs))
    if n_exprs == 1:
        axes = [axes]
    
    for ax_idx, (analysis_name, expr_name) in enumerate(expressions):
        ax = axes[ax_idx]
        
        # Get data for this expression
        expr_df = success_df[
            (success_df['analysis_class_name'] == analysis_name) &
            (success_df['expression_name'] == expr_name)
        ]
        
        # Plot each column as a line
        for col_name, group in expr_df.groupby('column_name'):
            group_sorted = group.sort_values('row_count')
            ax.plot(
                group_sorted['row_count'],
                group_sorted['execution_time_secs'],
                marker='o',
                label=col_name,
                linewidth=2,
            )
        
        ax.set_xlabel('Row Count (log scale)')
        ax.set_ylabel('Execution Time (seconds, log scale)')
        ax.set_title(f'{analysis_name}.{expr_name}')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {output_path}")
    
    if show_plot:
        plt.show()
    else:
        plt.close()







