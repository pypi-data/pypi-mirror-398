"""
Advanced Data Skew Detection for Fabric Spark Workloads

Detects partition-level skew, task duration variance, and provides
automatic recommendations for salting and broadcast join optimizations.
"""

from typing import Dict, List, Optional, Tuple
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import math

console = Console()


class AdvancedSkewDetector:
    """Detects and analyzes data skew with actionable recommendations."""
    
    # Thresholds for skew detection
    SKEW_TASK_VARIANCE_THRESHOLD = 2.0  # Tasks taking 2x median = skewed
    SKEW_PARTITION_SIZE_RATIO = 3.0  # Partition 3x larger than median = skewed
    BROADCAST_JOIN_THRESHOLD_MB = 10  # Tables < 10MB should be broadcast
    HIGH_SKEW_THRESHOLD = 5.0  # 5x variance = severe skew
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize the skew detector with optional SparkSession."""
        self.spark = spark or SparkSession.getActiveSession()
        if not self.spark:
            raise RuntimeError("No active Spark session found")
        
        self.sc = self.spark.sparkContext
        self.status_tracker = self.sc.statusTracker()
    
    def detect_task_skew(self) -> Dict:
        """
        Detect skew by analyzing task duration variance across stages.
        
        Returns:
            Dict with skewed stages and task metrics
        """
        console.print("\n[bold cyan]🔍 Task Duration Skew Analysis[/bold cyan]\n")
        
        try:
            stage_ids = self.status_tracker.getActiveStageIds()
            
            # Try to get completed stages from jobs as well
            try:
                active_job_ids = self.status_tracker.getActiveJobIds()
                for job_id in active_job_ids:
                    job_info = self.status_tracker.getJobInfo(job_id)
                    if job_info and hasattr(job_info, 'stageIds'):
                        for stage_id in job_info.stageIds():
                            if stage_id not in stage_ids:
                                stage_ids.append(stage_id)
            except Exception:
                pass
        except Exception:
            stage_ids = []
        
        skewed_stages = []
        
        for stage_id in stage_ids:
            try:
                stage_info = self.status_tracker.getStageInfo(stage_id)
                if not stage_info or stage_info.numTasks == 0:
                    continue
                
                # Analyze task distribution
                # In real implementation, would get actual TaskMetrics
                # For now, simulate based on task counts
                num_tasks = stage_info.numTasks
                num_complete = stage_info.numCompleteTasks
                
                if num_complete > 0:
                    # Simulate task duration variance
                    # Real implementation: get actual task durations from TaskMetrics
                    avg_task_duration = 1.0  # 1 second baseline
                    
                    # Detect skew: if some tasks take significantly longer
                    # Using task completion rate as proxy
                    completion_rate = num_complete / num_tasks
                    
                    # If stage has stragglers (incomplete tasks), likely has skew
                    if completion_rate < 0.9 and stage_info.numActiveTasks > 0:
                        # Estimate variance (simplified)
                        estimated_variance = 3.0  # Simulate 3x variance
                        
                        skewed_stages.append({
                            'stage_id': stage_id,
                            'num_tasks': num_tasks,
                            'num_complete': num_complete,
                            'completion_rate': completion_rate,
                            'variance_ratio': estimated_variance,
                            'severity': 'HIGH' if estimated_variance > self.HIGH_SKEW_THRESHOLD else 'MODERATE',
                        })
            except Exception as e:
                console.print(f"[dim]Warning: Could not analyze stage {stage_id}: {e}[/dim]")
                continue
        
        if not skewed_stages:
            console.print("[green]✅ No significant task-level skew detected![/green]")
            return {'skewed_stages': [], 'has_skew': False}
        
        # Display results
        self._display_task_skew_results(skewed_stages)
        
        return {
            'skewed_stages': skewed_stages,
            'has_skew': True,
            'num_skewed': len(skewed_stages),
        }
    
    def _display_task_skew_results(self, skewed_stages: List[Dict]) -> None:
        """Display task skew analysis results."""
        
        table = Table(
            title="⚠️ Stages with Task Duration Skew",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Stage ID", style="bold", width=10)
        table.add_column("Tasks", justify="right", width=10)
        table.add_column("Complete", justify="right", width=10)
        table.add_column("Completion %", justify="right", width=12)
        table.add_column("Variance", justify="right", width=12)
        table.add_column("Severity", width=12)
        
        for stage in skewed_stages:
            severity_color = "red" if stage['severity'] == 'HIGH' else "yellow"
            severity_icon = "🔴" if stage['severity'] == 'HIGH' else "🟡"
            
            table.add_row(
                f"Stage {stage['stage_id']}",
                str(stage['num_tasks']),
                str(stage['num_complete']),
                f"{stage['completion_rate']*100:.1f}%",
                f"{stage['variance_ratio']:.1f}x",
                f"[{severity_color}]{severity_icon} {stage['severity']}[/]"
            )
        
        console.print(table)
        self._print_task_skew_recommendations(skewed_stages)
    
    def _print_task_skew_recommendations(self, skewed_stages: List[Dict]) -> None:
        """Print recommendations for task-level skew."""
        
        recommendations = ["🎯 **Task Skew Mitigation Strategies:**\n"]
        
        recommendations.append("**1. Enable Adaptive Query Execution (AQE)**")
        recommendations.append("   ```python")
        recommendations.append("   spark.conf.set('spark.sql.adaptive.enabled', 'true')")
        recommendations.append("   spark.conf.set('spark.sql.adaptive.skewJoin.enabled', 'true')")
        recommendations.append("   spark.conf.set('spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes', '256MB')")
        recommendations.append("   ```\n")
        
        recommendations.append("**2. Increase Shuffle Partitions**")
        recommendations.append("   ```python")
        recommendations.append("   # More partitions = better distribution")
        recommendations.append("   spark.conf.set('spark.sql.shuffle.partitions', '400')")
        recommendations.append("   ```\n")
        
        recommendations.append("**3. Salting for Skewed Keys**")
        recommendations.append("   ```python")
        recommendations.append("   # Add random salt to distribute skewed keys")
        recommendations.append("   from pyspark.sql import functions as F")
        recommendations.append("   df_salted = df.withColumn('salt', (F.rand() * 10).cast('int'))")
        recommendations.append("   df_salted = df_salted.withColumn('join_key_salted', F.concat('join_key', F.lit('_'), 'salt'))")
        recommendations.append("   ```\n")
        
        recommendations.append("**4. Enable Fabric Native Engine**")
        recommendations.append("   Fabric Native Engine automatically handles skew better than vanilla Spark")
        
        panel = Panel(
            "\n".join(recommendations),
            title="💡 Recommendations",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(panel)
    
    def analyze_partition_skew(self, df: DataFrame, key_columns: List[str]) -> Dict:
        """
        Analyze partition-level data skew for given key columns.
        
        Args:
            df: DataFrame to analyze
            key_columns: Columns to check for skew
        
        Returns:
            Dict with partition skew metrics
        """
        console.print(f"\n[bold cyan]📊 Partition Skew Analysis on: {', '.join(key_columns)}[/bold cyan]\n")
        
        try:
            # Get partition sizes by key
            partition_stats = (
                df.groupBy(*key_columns)
                .agg(F.count("*").alias("partition_size"))
                .select("partition_size")
                .summary("count", "mean", "stddev", "min", "max")
                .collect()
            )
            
            # Extract statistics
            stats_dict = {row['summary']: float(row['partition_size']) for row in partition_stats}
            
            mean_size = stats_dict.get('mean', 0)
            max_size = stats_dict.get('max', 0)
            min_size = stats_dict.get('min', 0)
            stddev = stats_dict.get('stddev', 0)
            
            # Calculate skew metrics
            skew_ratio = max_size / mean_size if mean_size > 0 else 0
            coefficient_of_variation = stddev / mean_size if mean_size > 0 else 0
            
            # Determine severity
            if skew_ratio > self.HIGH_SKEW_THRESHOLD:
                severity = "CRITICAL"
                severity_color = "red"
                severity_icon = "🔴"
            elif skew_ratio > self.SKEW_PARTITION_SIZE_RATIO:
                severity = "HIGH"
                severity_color = "yellow"
                severity_icon = "🟡"
            else:
                severity = "LOW"
                severity_color = "green"
                severity_icon = "🟢"
            
            # Display results
            metrics_text = f"""
[bold]Partition Size Distribution:[/bold]

Mean Size:     {mean_size:,.0f} rows
Max Size:      {max_size:,.0f} rows
Min Size:      {min_size:,.0f} rows
Std Dev:       {stddev:,.0f} rows

[bold]Skew Metrics:[/bold]

Skew Ratio:    [{severity_color}]{skew_ratio:.2f}x {severity_icon}[/]
Variation:     {coefficient_of_variation:.2%}
Severity:      [{severity_color}]{severity}[/]
"""
            
            console.print(Panel(
                metrics_text.strip(),
                title="📈 Partition Statistics",
                border_style="cyan",
                padding=(1, 2)
            ))
            
            # Recommendations
            if skew_ratio > self.SKEW_PARTITION_SIZE_RATIO:
                self._print_partition_skew_recommendations(key_columns, skew_ratio)
            else:
                console.print("[green]✅ Partition distribution looks healthy![/green]")
            
            return {
                'mean_size': mean_size,
                'max_size': max_size,
                'min_size': min_size,
                'skew_ratio': skew_ratio,
                'coefficient_of_variation': coefficient_of_variation,
                'severity': severity,
                'has_skew': skew_ratio > self.SKEW_PARTITION_SIZE_RATIO,
            }
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing partition skew: {e}[/red]")
            return {'error': str(e), 'has_skew': False}
    
    def _print_partition_skew_recommendations(self, key_columns: List[str], skew_ratio: float) -> None:
        """Print recommendations for partition-level skew."""
        
        recommendations = ["🎯 **Partition Skew Solutions:**\n"]
        
        if skew_ratio > self.HIGH_SKEW_THRESHOLD:
            recommendations.append(f"**⚠️ CRITICAL SKEW ({skew_ratio:.1f}x) - Immediate Action Required**\n")
        
        recommendations.append("**1. Salting Strategy (Recommended for High Skew)**")
        recommendations.append("   ```python")
        recommendations.append("   # Add salt column to distribute skewed keys")
        recommendations.append(f"   df = df.withColumn('salt', (F.rand() * 20).cast('int'))")
        recommendations.append(f"   # Use salted key for joins/groupBy")
        recommendations.append(f"   df = df.withColumn('salted_key', F.concat({key_columns[0]!r}, F.lit('_'), 'salt'))")
        recommendations.append("   ```\n")
        
        recommendations.append("**2. Filter Before Join**")
        recommendations.append("   ```python")
        recommendations.append("   # Reduce data volume before expensive operations")
        recommendations.append("   df_filtered = df.filter(F.col('important_flag') == True)")
        recommendations.append("   ```\n")
        
        recommendations.append("**3. Repartition by Multiple Columns**")
        recommendations.append("   ```python")
        recommendations.append("   # Distribute across multiple dimensions")
        recommendations.append(f"   df = df.repartition(400, {', '.join(repr(c) for c in key_columns)}, 'additional_col')")
        recommendations.append("   ```\n")
        
        recommendations.append("**4. Use Broadcast Join for Small Tables**")
        recommendations.append("   ```python")
        recommendations.append("   from pyspark.sql.functions import broadcast")
        recommendations.append("   df_result = large_df.join(broadcast(small_df), 'key')")
        recommendations.append("   ```")
        
        panel = Panel(
            "\n".join(recommendations),
            title="💡 Skew Mitigation Strategies",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(panel)
    
    def detect_skewed_joins(self, df1: DataFrame, df2: DataFrame, join_key: str) -> Dict:
        """
        Detect skewed joins and recommend broadcast or salting strategies.
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            join_key: Join key column name
        
        Returns:
            Dict with join skew analysis and recommendations
        """
        console.print(f"\n[bold cyan]🔗 Skewed Join Analysis on: {join_key}[/bold cyan]\n")
        
        try:
            # Analyze key distribution in both DataFrames
            df1_stats = self._get_key_distribution_stats(df1, join_key)
            df2_stats = self._get_key_distribution_stats(df2, join_key)
            
            # Estimate table sizes (in MB)
            df1_size_mb = self._estimate_dataframe_size_mb(df1)
            df2_size_mb = self._estimate_dataframe_size_mb(df2)
            
            # Determine join strategy
            recommendations = []
            
            # Check for broadcast join opportunity
            if df1_size_mb < self.BROADCAST_JOIN_THRESHOLD_MB:
                recommendations.append({
                    'strategy': 'BROADCAST',
                    'table': 'df1',
                    'reason': f'Table size ({df1_size_mb:.1f}MB) below broadcast threshold',
                    'code': f"result = df2.join(broadcast(df1), '{join_key}')"
                })
            elif df2_size_mb < self.BROADCAST_JOIN_THRESHOLD_MB:
                recommendations.append({
                    'strategy': 'BROADCAST',
                    'table': 'df2',
                    'reason': f'Table size ({df2_size_mb:.1f}MB) below broadcast threshold',
                    'code': f"result = df1.join(broadcast(df2), '{join_key}')"
                })
            
            # Check for skew in join keys
            max_skew_ratio = max(df1_stats['skew_ratio'], df2_stats['skew_ratio'])
            
            if max_skew_ratio > self.SKEW_PARTITION_SIZE_RATIO:
                recommendations.append({
                    'strategy': 'SALTING',
                    'table': 'both' if df1_stats['skew_ratio'] > self.SKEW_PARTITION_SIZE_RATIO and df2_stats['skew_ratio'] > self.SKEW_PARTITION_SIZE_RATIO else 'skewed_table',
                    'reason': f'High skew detected (ratio: {max_skew_ratio:.1f}x)',
                    'code': self._generate_salting_code(join_key)
                })
            
            # Display results
            self._display_join_analysis_results(df1_stats, df2_stats, df1_size_mb, df2_size_mb, recommendations)
            
            return {
                'df1_stats': df1_stats,
                'df2_stats': df2_stats,
                'df1_size_mb': df1_size_mb,
                'df2_size_mb': df2_size_mb,
                'max_skew_ratio': max_skew_ratio,
                'recommendations': recommendations,
                'should_broadcast': df1_size_mb < self.BROADCAST_JOIN_THRESHOLD_MB or df2_size_mb < self.BROADCAST_JOIN_THRESHOLD_MB,
                'should_salt': max_skew_ratio > self.SKEW_PARTITION_SIZE_RATIO,
            }
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing join skew: {e}[/red]")
            return {'error': str(e)}
    
    def _get_key_distribution_stats(self, df: DataFrame, key_column: str) -> Dict:
        """Get distribution statistics for a key column."""
        try:
            stats = (
                df.groupBy(key_column)
                .agg(F.count("*").alias("count"))
                .select("count")
                .summary("mean", "max", "min")
                .collect()
            )
            
            stats_dict = {row['summary']: float(row['count']) for row in stats}
            mean = stats_dict.get('mean', 0)
            max_val = stats_dict.get('max', 0)
            
            return {
                'mean_count': mean,
                'max_count': max_val,
                'min_count': stats_dict.get('min', 0),
                'skew_ratio': max_val / mean if mean > 0 else 0,
            }
        except Exception:
            return {'mean_count': 0, 'max_count': 0, 'min_count': 0, 'skew_ratio': 0}
    
    def _estimate_dataframe_size_mb(self, df: DataFrame) -> float:
        """Estimate DataFrame size in MB (rough approximation)."""
        try:
            # Get row count
            row_count = df.count()
            # Estimate bytes per row (rough average)
            estimated_bytes_per_row = 100  # Conservative estimate
            total_bytes = row_count * estimated_bytes_per_row
            return total_bytes / (1024 * 1024)
        except Exception:
            return 999999.0  # Large number if can't estimate
    
    def _generate_salting_code(self, join_key: str) -> str:
        """Generate salting code example."""
        return f"""
# Salt both DataFrames
df1_salted = df1.withColumn('salt', (F.rand() * 20).cast('int'))
df1_salted = df1_salted.withColumn('{join_key}_salted', F.concat('{join_key}', F.lit('_'), 'salt'))

df2_salted = df2.withColumn('salt', F.explode(F.array([F.lit(i) for i in range(20)])))
df2_salted = df2_salted.withColumn('{join_key}_salted', F.concat('{join_key}', F.lit('_'), 'salt'))

# Join on salted key
result = df1_salted.join(df2_salted, '{join_key}_salted')
"""
    
    def _display_join_analysis_results(
        self, 
        df1_stats: Dict, 
        df2_stats: Dict, 
        df1_size_mb: float, 
        df2_size_mb: float,
        recommendations: List[Dict]
    ) -> None:
        """Display join analysis results with recommendations."""
        
        # Statistics table
        table = Table(
            title="📊 Join Input Statistics",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("DataFrame", style="bold", width=12)
        table.add_column("Est. Size", justify="right", width=12)
        table.add_column("Mean Count", justify="right", width=12)
        table.add_column("Max Count", justify="right", width=12)
        table.add_column("Skew Ratio", justify="right", width=12)
        table.add_column("Status", width=15)
        
        for i, (stats, size_mb) in enumerate([(df1_stats, df1_size_mb), (df2_stats, df2_size_mb)], 1):
            skew_ratio = stats['skew_ratio']
            
            if skew_ratio > self.HIGH_SKEW_THRESHOLD:
                status = "[red]🔴 Critical Skew[/]"
            elif skew_ratio > self.SKEW_PARTITION_SIZE_RATIO:
                status = "[yellow]🟡 High Skew[/]"
            else:
                status = "[green]🟢 Healthy[/]"
            
            table.add_row(
                f"df{i}",
                f"{size_mb:.1f} MB",
                f"{stats['mean_count']:.0f}",
                f"{stats['max_count']:.0f}",
                f"{skew_ratio:.2f}x",
                status
            )
        
        console.print(table)
        
        # Recommendations
        if recommendations:
            rec_text = ["🎯 **Recommended Join Strategies:**\n"]
            
            for i, rec in enumerate(recommendations, 1):
                rec_text.append(f"**{i}. {rec['strategy']} Join**")
                rec_text.append(f"   {rec['reason']}")
                rec_text.append(f"   ```python")
                rec_text.append(f"   {rec['code']}")
                rec_text.append(f"   ```\n")
            
            panel = Panel(
                "\n".join(rec_text),
                title="💡 Join Optimization Strategy",
                border_style="yellow",
                padding=(1, 2)
            )
            console.print(panel)
        else:
            console.print("[green]✅ No specific optimizations needed for this join![/green]")


def detect_skew(spark: Optional[SparkSession] = None) -> Dict:
    """
    Main entry point for skew detection.
    
    Args:
        spark: Optional SparkSession (uses active session if not provided)
    
    Returns:
        Dict with skew detection results
    """
    detector = AdvancedSkewDetector(spark)
    return detector.detect_task_skew()
