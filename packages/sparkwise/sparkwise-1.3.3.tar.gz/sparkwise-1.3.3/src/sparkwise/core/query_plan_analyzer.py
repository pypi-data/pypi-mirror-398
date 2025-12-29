"""
SQL Query Plan Analysis for Fabric Spark Workloads

Parses physical plans to detect anti-patterns, missing optimizations,
and provides recommendations for Z-Order, partitioning, and materialized views.
"""

from typing import Dict, List, Optional, Set, Tuple
from pyspark.sql import SparkSession, DataFrame
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box
import re

console = Console()


class QueryPlanAnalyzer:
    """Analyzes SQL query plans for optimization opportunities."""
    
    # Anti-pattern detection patterns
    FULL_SCAN_PATTERN = r'FileScan|TableScan.*\bPartitionFilters: \[\]'
    SHUFFLE_PATTERN = r'Exchange|ShuffleExchange'
    SORT_PATTERN = r'Sort\['
    CARTESIAN_PRODUCT_PATTERN = r'CartesianProduct|BroadcastNestedLoopJoin'
    
    # Fabric-specific patterns
    NATIVE_ENGINE_PATTERN = r'NativeFileScan|VeloxFileScan'
    DELTA_SCAN_PATTERN = r'Delta|DeltaTableScan'
    
    # Size thresholds
    LARGE_TABLE_ROWS = 10_000_000  # 10M rows
    BROADCAST_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize the query plan analyzer with optional SparkSession."""
        self.spark = spark or SparkSession.getActiveSession()
        if not self.spark:
            raise RuntimeError("No active Spark session found")
    
    def analyze_query_plan(self, df: DataFrame, explain_mode: str = "extended") -> Dict:
        """
        Analyze query plan for a DataFrame and detect anti-patterns.
        
        Args:
            df: DataFrame to analyze
            explain_mode: "simple", "extended", "codegen", or "formatted"
        
        Returns:
            Dict with analysis results and recommendations
        """
        console.print("\n[bold cyan]🔍 Query Plan Analysis[/bold cyan]\n")
        
        try:
            # Get the physical plan
            plan_str = df._jdf.queryExecution().toString()
            
            # Parse and analyze
            issues = []
            
            # 1. Check for full table scans
            full_scans = self._detect_full_table_scans(plan_str)
            if full_scans:
                issues.extend(full_scans)
            
            # 2. Check for excessive shuffles
            shuffle_count = self._count_shuffles(plan_str)
            if shuffle_count > 3:
                issues.append({
                    'type': 'EXCESSIVE_SHUFFLES',
                    'severity': 'HIGH',
                    'description': f'Query has {shuffle_count} shuffle operations',
                    'recommendation': 'Consider reducing joins/aggregations or enabling AQE'
                })
            
            # 3. Check for cartesian products
            if re.search(self.CARTESIAN_PRODUCT_PATTERN, plan_str):
                issues.append({
                    'type': 'CARTESIAN_PRODUCT',
                    'severity': 'CRITICAL',
                    'description': 'Cartesian product detected (missing join condition)',
                    'recommendation': 'Add proper join condition to avoid O(n²) complexity'
                })
            
            # 4. Check for sorts without partitioning
            if re.search(self.SORT_PATTERN, plan_str) and shuffle_count < 2:
                issues.append({
                    'type': 'GLOBAL_SORT',
                    'severity': 'MODERATE',
                    'description': 'Global sort detected',
                    'recommendation': 'Consider partitioning data before sorting or use window functions'
                })
            
            # 5. Check if Native Engine is being used
            using_native = bool(re.search(self.NATIVE_ENGINE_PATTERN, plan_str))
            if not using_native:
                issues.append({
                    'type': 'NO_NATIVE_ENGINE',
                    'severity': 'MODERATE',
                    'description': 'Query not using Fabric Native Engine',
                    'recommendation': 'Remove UDFs and use built-in Spark functions for 3-8x speedup'
                })
            
            # 6. Check for Delta table scans
            using_delta = bool(re.search(self.DELTA_SCAN_PATTERN, plan_str))
            
            # Display results
            self._display_plan_analysis(plan_str, issues, shuffle_count, using_native, using_delta)
            
            return {
                'issues': issues,
                'shuffle_count': shuffle_count,
                'using_native_engine': using_native,
                'using_delta': using_delta,
                'severity_counts': self._count_severities(issues),
                'plan': plan_str,
            }
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing query plan: {e}[/red]")
            return {'error': str(e)}
    
    def _detect_full_table_scans(self, plan_str: str) -> List[Dict]:
        """Detect full table scans without partition filters."""
        issues = []
        
        # Look for file scans without partition filters
        scan_matches = re.finditer(r'(FileScan|Scan)\s+.*?(?:PartitionFilters: \[(.*?)\])?', plan_str, re.DOTALL)
        
        for match in scan_matches:
            filters = match.group(2) if match.group(2) else ""
            if not filters or filters.strip() == "":
                # No partition filters - full scan
                issues.append({
                    'type': 'FULL_TABLE_SCAN',
                    'severity': 'HIGH',
                    'description': 'Full table scan detected without partition filtering',
                    'recommendation': 'Add partition filters or consider Z-Order clustering'
                })
        
        return issues
    
    def _count_shuffles(self, plan_str: str) -> int:
        """Count number of shuffle operations in plan."""
        return len(re.findall(self.SHUFFLE_PATTERN, plan_str))
    
    def _count_severities(self, issues: List[Dict]) -> Dict:
        """Count issues by severity."""
        counts = {'CRITICAL': 0, 'HIGH': 0, 'MODERATE': 0, 'LOW': 0}
        for issue in issues:
            severity = issue.get('severity', 'LOW')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _display_plan_analysis(
        self, 
        plan_str: str, 
        issues: List[Dict], 
        shuffle_count: int,
        using_native: bool,
        using_delta: bool
    ) -> None:
        """Display query plan analysis results."""
        
        # Summary panel
        summary_lines = [
            f"[bold]Query Characteristics:[/bold]\n",
            f"Shuffle Operations: {shuffle_count}",
            f"Native Engine: {'[green]✅ Enabled[/]' if using_native else '[yellow]⚠️ Not Used[/]'}",
            f"Delta Format: {'[green]✅ Yes[/]' if using_delta else '[blue]ℹ️ No[/]'}",
            f"\n[bold]Issues Found:[/bold] {len(issues)}",
        ]
        
        if issues:
            severity_counts = self._count_severities(issues)
            if severity_counts['CRITICAL'] > 0:
                summary_lines.append(f"  🔴 Critical: {severity_counts['CRITICAL']}")
            if severity_counts['HIGH'] > 0:
                summary_lines.append(f"  🟡 High: {severity_counts['HIGH']}")
            if severity_counts['MODERATE'] > 0:
                summary_lines.append(f"  🔵 Moderate: {severity_counts['MODERATE']}")
        else:
            summary_lines.append("  [green]✅ No major issues detected![/]")
        
        console.print(Panel(
            "\n".join(summary_lines),
            title="📊 Query Plan Summary",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # Issues table
        if issues:
            self._display_issues_table(issues)
            self._display_recommendations(issues, shuffle_count, using_native)
    
    def _display_issues_table(self, issues: List[Dict]) -> None:
        """Display issues in a formatted table."""
        
        table = Table(
            title="⚠️ Detected Issues",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Severity", width=12)
        table.add_column("Issue Type", width=25)
        table.add_column("Description", width=50)
        
        for issue in sorted(issues, key=lambda x: ['CRITICAL', 'HIGH', 'MODERATE', 'LOW'].index(x['severity'])):
            severity = issue['severity']
            
            if severity == 'CRITICAL':
                severity_display = "[red]🔴 CRITICAL[/]"
            elif severity == 'HIGH':
                severity_display = "[yellow]🟡 HIGH[/]"
            elif severity == 'MODERATE':
                severity_display = "[blue]🔵 MODERATE[/]"
            else:
                severity_display = "[dim]⚪ LOW[/]"
            
            table.add_row(
                severity_display,
                issue['type'].replace('_', ' ').title(),
                issue['description']
            )
        
        console.print(table)
    
    def _display_recommendations(self, issues: List[Dict], shuffle_count: int, using_native: bool) -> None:
        """Display optimization recommendations."""
        
        rec_lines = ["🎯 **Optimization Recommendations:**\n"]
        
        # Group recommendations by priority
        critical_issues = [i for i in issues if i['severity'] == 'CRITICAL']
        high_issues = [i for i in issues if i['severity'] == 'HIGH']
        
        if critical_issues:
            rec_lines.append("**🔴 CRITICAL - Fix Immediately:**\n")
            for i, issue in enumerate(critical_issues, 1):
                rec_lines.append(f"{i}. {issue['recommendation']}")
            rec_lines.append("")
        
        if high_issues:
            rec_lines.append("**🟡 HIGH PRIORITY:**\n")
            for i, issue in enumerate(high_issues, 1):
                rec_lines.append(f"{i}. {issue['recommendation']}")
            rec_lines.append("")
        
        # General Fabric-specific recommendations
        rec_lines.append("**💡 Fabric Best Practices:**\n")
        
        if shuffle_count > 3:
            rec_lines.append("• **Enable Adaptive Query Execution:**")
            rec_lines.append("  ```python")
            rec_lines.append("  spark.conf.set('spark.sql.adaptive.enabled', 'true')")
            rec_lines.append("  ```\n")
        
        if not using_native:
            rec_lines.append("• **Enable Native Engine (3-8x faster):**")
            rec_lines.append("  - Remove Python UDFs")
            rec_lines.append("  - Use built-in Spark SQL functions")
            rec_lines.append("  - Enable: `spark.conf.set('spark.native.enabled', 'true')`\n")
        
        # Add Z-Order recommendation for full scans
        if any(i['type'] == 'FULL_TABLE_SCAN' for i in issues):
            rec_lines.append("• **Optimize Delta Tables with Z-Order:**")
            rec_lines.append("  ```python")
            rec_lines.append("  from delta.tables import DeltaTable")
            rec_lines.append("  DeltaTable.forPath(spark, '/path/to/table').optimize().executeZOrderBy('frequently_filtered_column')")
            rec_lines.append("  ```\n")
        
        # V-Order recommendation with context
        if not self.analysis_result.get('is_delta', False):
            rec_lines.append("• **Use V-Order for Parquet (Read-Heavy Workloads):**")
            rec_lines.append("  ```python")
            rec_lines.append("  # Enable for analytics/reporting tables (read >> write)")
            rec_lines.append("  df.write.format('parquet').option('parquet.vorder.enabled', 'true').save('/path')")
            rec_lines.append("  ```")
            rec_lines.append("  ⚠️ Note: V-Order adds 5-15% write overhead. Avoid for write-heavy/streaming scenarios.\n")
        
        panel = Panel(
            "\n".join(rec_lines),
            title="💡 Action Plan",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(panel)
    
    def suggest_zorder_columns(self, df: DataFrame, query_filters: List[str]) -> List[str]:
        """
        Suggest columns for Z-Order optimization based on query patterns.
        
        Args:
            df: DataFrame (Delta table)
            query_filters: List of commonly filtered columns
        
        Returns:
            List of recommended Z-Order columns
        """
        console.print("\n[bold cyan]🎯 Z-Order Column Recommendations[/bold cyan]\n")
        
        try:
            # Analyze column statistics
            recommendations = []
            
            for col_name in query_filters:
                # Check if column exists
                if col_name not in df.columns:
                    console.print(f"[yellow]⚠️ Column '{col_name}' not found in DataFrame[/yellow]")
                    continue
                
                # Get distinct count (cardinality)
                distinct_count = df.select(col_name).distinct().count()
                total_count = df.count()
                cardinality_ratio = distinct_count / total_count if total_count > 0 else 0
                
                # High cardinality columns benefit most from Z-Order
                if cardinality_ratio > 0.1:  # > 10% distinct values
                    score = "HIGH"
                    icon = "⭐⭐⭐"
                elif cardinality_ratio > 0.01:  # > 1% distinct values
                    score = "MEDIUM"
                    icon = "⭐⭐"
                else:
                    score = "LOW"
                    icon = "⭐"
                
                recommendations.append({
                    'column': col_name,
                    'distinct_count': distinct_count,
                    'cardinality_ratio': cardinality_ratio,
                    'score': score,
                    'icon': icon,
                })
            
            # Sort by score
            recommendations.sort(key=lambda x: x['cardinality_ratio'], reverse=True)
            
            # Display recommendations
            if recommendations:
                table = Table(
                    title="🎯 Z-Order Column Candidates",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold cyan"
                )
                
                table.add_column("Column", style="bold", width=20)
                table.add_column("Distinct Values", justify="right", width=18)
                table.add_column("Cardinality", justify="right", width=15)
                table.add_column("Z-Order Benefit", width=18)
                
                for rec in recommendations:
                    table.add_row(
                        rec['column'],
                        f"{rec['distinct_count']:,}",
                        f"{rec['cardinality_ratio']:.2%}",
                        f"{rec['icon']} {rec['score']}"
                    )
                
                console.print(table)
                
                # Implementation example
                top_columns = [r['column'] for r in recommendations[:3]]
                
                example = f"""
**Implementation Example:**

```python
from delta.tables import DeltaTable

# Optimize with top recommended columns
delta_table = DeltaTable.forPath(spark, '/path/to/your/table')
delta_table.optimize().executeZOrderBy({', '.join(repr(c) for c in top_columns)})

# Expected benefits:
# - Faster queries with filters on these columns
# - Improved data skipping (fewer files scanned)
# - Better compression ratios
```

**Note:** Z-Order is most effective for:
- High cardinality columns (many distinct values)
- Frequently filtered columns in WHERE clauses
- Columns used in JOIN conditions
"""
                
                console.print(Panel(
                    example.strip(),
                    title="💡 Implementation Guide",
                    border_style="green",
                    padding=(1, 2)
                ))
            else:
                console.print("[yellow]No suitable columns found for Z-Order optimization.[/yellow]")
            
            return [r['column'] for r in recommendations if r['score'] in ['HIGH', 'MEDIUM']]
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing Z-Order candidates: {e}[/red]")
            return []
    
    def detect_repeated_subqueries(self, df: DataFrame) -> List[str]:
        """
        Detect repeated subqueries that could benefit from caching/materialized views.
        
        Args:
            df: DataFrame to analyze
        
        Returns:
            List of recommendations for caching
        """
        console.print("\n[bold cyan]🔄 Caching Opportunity Analysis[/bold cyan]\n")
        
        try:
            plan_str = df._jdf.queryExecution().toString()
            
            # Look for repeated table scans
            table_scan_pattern = r'Scan.*?\[(.*?)\]'
            scans = re.findall(table_scan_pattern, plan_str)
            
            # Count occurrences
            scan_counts = {}
            for scan in scans:
                scan_counts[scan] = scan_counts.get(scan, 0) + 1
            
            # Find tables scanned multiple times
            repeated_scans = {table: count for table, count in scan_counts.items() if count > 1}
            
            if repeated_scans:
                recommendations = []
                
                table = Table(
                    title="🔄 Repeated Table Scans",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold cyan"
                )
                
                table.add_column("Table/Source", width=40)
                table.add_column("Scan Count", justify="right", width=15)
                table.add_column("Recommendation", width=30)
                
                for table_name, count in sorted(repeated_scans.items(), key=lambda x: x[1], reverse=True):
                    table.add_row(
                        table_name[:40],
                        str(count),
                        "[green]✓ Cache recommended[/]"
                    )
                    
                    recommendations.append(f"Consider caching: {table_name}")
                
                console.print(table)
                
                # Caching examples
                cache_example = """
**Caching Strategy:**

```python
# For intermediate DataFrames used multiple times:
df_cached = df.cache()
result1 = df_cached.filter(...)
result2 = df_cached.groupBy(...)

# For complex transformations:
df_materialized = df.checkpoint()  # Creates a physical copy

# Monitor cache usage:
spark.catalog.clearCache()  # Clear when done
```

**When to cache:**
- DataFrame used in multiple actions (count, write, show)
- Complex transformations reused across queries
- Iterative algorithms (ML training)

**When NOT to cache:**
- Single-use DataFrames
- Very large DataFrames that don't fit in memory
- Simple transformations (filter, select)
"""
                
                console.print(Panel(
                    cache_example.strip(),
                    title="💡 Caching Best Practices",
                    border_style="green",
                    padding=(1, 2)
                ))
                
                return recommendations
            else:
                console.print("[green]✅ No repeated table scans detected. Caching not needed.[/green]")
                return []
            
        except Exception as e:
            console.print(f"[red]❌ Error detecting repeated subqueries: {e}[/red]")
            return []


def analyze_query(df: DataFrame, spark: Optional[SparkSession] = None) -> Dict:
    """
    Main entry point for query plan analysis.
    
    Args:
        df: DataFrame to analyze
        spark: Optional SparkSession (uses active session if not provided)
    
    Returns:
        Dict with analysis results
    """
    analyzer = QueryPlanAnalyzer(spark)
    return analyzer.analyze_query_plan(df)
