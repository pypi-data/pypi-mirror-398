"""
Scalability Prediction for Fabric Spark Workloads

Predicts performance with different executor counts and Fabric capacity sizes.
Provides ROI analysis for Starter Pool vs Custom Pool decisions.
"""

from typing import Dict, List, Tuple, Optional
from pyspark.sql import SparkSession
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import math

console = Console()


class ScalabilityPredictor:
    """Predicts application scalability for Fabric Spark workloads."""
    
    # Fabric capacity specifications (Spark VCores available)
    # Note: These are capacity SKUs, NOT pool types
    # Both Starter and Custom pools can run on any capacity
    FABRIC_CAPACITIES = {
        'F2': {'spark_vcores': 4, 'burst_vcores': 20},
        'F4': {'spark_vcores': 8, 'burst_vcores': 24},
        'F8': {'spark_vcores': 16, 'burst_vcores': 48},
        'F16': {'spark_vcores': 32, 'burst_vcores': 96},
        'F32': {'spark_vcores': 64, 'burst_vcores': 192},
        'F64': {'spark_vcores': 128, 'burst_vcores': 384},
        'F128': {'spark_vcores': 256, 'burst_vcores': 768},
        'F256': {'spark_vcores': 512, 'burst_vcores': 1536},
        'F512': {'spark_vcores': 1024, 'burst_vcores': 3072},
        'F1024': {'spark_vcores': 2048, 'burst_vcores': 6144},
        'F2048': {'spark_vcores': 4096, 'burst_vcores': 12288},
    }
    
    # Starter Pool defaults (Medium node - available on ALL capacities)
    STARTER_POOL = {
        'node_size': 'Medium',
        'executors': 2,
        'cores_per_executor': 4,
        'memory_per_executor_gb': 28,
        'startup_time_sec': 0,  # Instant (pre-warmed)
    }
    
    # Custom Pool characteristics
    CUSTOM_POOL = {
        'startup_time_sec': 180,  # 3-5 minutes average (cold start)
        'configurable': True,  # Can be sized based on capacity limits
    }
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize the predictor with optional SparkSession."""
        self.spark = spark or SparkSession.getActiveSession()
        if not self.spark:
            raise RuntimeError("No active Spark session found")
        
        self.app_id = self.spark.sparkContext.applicationId
        self.sc = self.spark.sparkContext
    
    def _get_current_metrics(self) -> Dict:
        """Extract current application metrics from real Spark data."""
        try:
            status_tracker = self.sc.statusTracker()
            
            # Get active and completed stage IDs
            stage_ids = []
            try:
                stage_ids.extend(status_tracker.getActiveStageIds())
            except Exception:
                pass
            
            # Try to get completed stages from jobs
            try:
                active_job_ids = status_tracker.getActiveJobIds()
                for job_id in active_job_ids:
                    job_info = status_tracker.getJobInfo(job_id)
                    if job_info and hasattr(job_info, 'stageIds'):
                        for stage_id in job_info.stageIds():
                            if stage_id not in stage_ids:
                                stage_ids.append(stage_id)
            except Exception:
                pass
            
            total_task_time = 0
            total_tasks = 0
            completed_tasks = 0
            max_parallel_tasks = 0
            stage_count = 0
            actual_stage_duration = 0
            
            for stage_id in stage_ids:
                try:
                    stage_info = status_tracker.getStageInfo(stage_id)
                    if stage_info:
                        stage_count += 1
                        total_tasks += stage_info.numTasks
                        completed_tasks += stage_info.numCompleteTasks
                        max_parallel_tasks = max(max_parallel_tasks, stage_info.numActiveTasks)
                        
                        # Calculate actual stage duration if available
                        if hasattr(stage_info, 'submissionTime') and hasattr(stage_info, 'completionTime'):
                            submit_time = stage_info.submissionTime()
                            complete_time = stage_info.completionTime()
                            if submit_time and complete_time and complete_time >= 0:
                                duration_ms = complete_time - submit_time
                                actual_stage_duration += duration_ms / 1000.0  # Convert to seconds
                        
                        # Estimate task execution time based on completed tasks
                        if stage_info.numCompleteTasks > 0:
                            # Use real duration if available, else estimate 100ms per task (fast jobs)
                            if actual_stage_duration > 0:
                                total_task_time = actual_stage_duration * completed_tasks / total_tasks if total_tasks > 0 else actual_stage_duration
                            else:
                                total_task_time += stage_info.numCompleteTasks * 0.1  # 100ms for fast ops
                except Exception:
                    continue
            
            # Get REAL executor info
            try:
                executor_info = self.sc._jvm.org.apache.spark.SparkEnv.get().blockManager().master().getStorageStatus()
                num_executors = len(executor_info) - 1  # Exclude driver
            except Exception:
                num_executors = 1
            
            # Get REAL configuration
            conf = self.spark.sparkContext.getConf()
            cores_per_executor = int(conf.get('spark.executor.cores', '4'))
            
            # Calculate wall clock time estimate
            # For running jobs: based on stage completion
            # For completed jobs: would come from applicationEnd - applicationStart
            if stage_count > 0 and total_tasks > 0:
                completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
                # Estimate wall clock as task time / available parallelism
                available_cores = num_executors * cores_per_executor
                if available_cores > 0 and total_task_time > 0:
                    wall_clock_time_sec = total_task_time / available_cores
                    # Add safety check for unrealistic values
                    wall_clock_time_sec = min(wall_clock_time_sec, 3600 * 24)  # Cap at 24 hours
                elif actual_stage_duration > 0:
                    # Use real stage duration for fast jobs
                    wall_clock_time_sec = actual_stage_duration
                else:
                    wall_clock_time_sec = stage_count * 5  # 5 sec per stage for fast jobs
            else:
                wall_clock_time_sec = 5  # 5 second fallback for very fast operations
            
            # Ensure non-zero, non-infinity value (minimum 0.1s for sub-second ops)
            wall_clock_time_sec = max(0.1, min(wall_clock_time_sec, 3600 * 24))
            
            return {
                'num_executors': max(num_executors, 1),
                'cores_per_executor': cores_per_executor,
                'total_cores': num_executors * cores_per_executor,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'total_task_time_sec': total_task_time,
                'max_parallel_tasks': max_parallel_tasks,
                'wall_clock_time_sec': wall_clock_time_sec,
                'stage_count': stage_count,
            }
        except Exception as e:
            console.print(f"[dim]Warning: Could not extract metrics: {e}. Using defaults.[/dim]")
            # Fallback to sensible defaults
            conf = self.spark.sparkContext.getConf()
            cores = int(conf.get('spark.executor.cores', '4'))
            return {
                'num_executors': 2,
                'cores_per_executor': cores,
                'total_cores': 2 * cores,
                'total_tasks': 100,
                'completed_tasks': 100,
                'total_task_time_sec': 40,
                'max_parallel_tasks': 8,
                'wall_clock_time_sec': 60,
                'stage_count': 2,
            }
        except Exception:
            # Return defaults if metrics unavailable
            return {
                'num_executors': 2,
                'cores_per_executor': 4,
                'total_cores': 8,
                'total_tasks': 100,
                'total_task_time_sec': 1000,
                'max_parallel_tasks': 8,
                'wall_clock_time_sec': 300,
            }
    
    def _estimate_completion_time(
        self, 
        total_task_time: float, 
        num_executors: int, 
        cores_per_executor: int,
        max_parallelism: int
    ) -> Tuple[float, float]:
        """
        Estimate completion time and cluster utilization.
        
        Returns:
            (estimated_time_sec, utilization_percent)
        """
        available_cores = num_executors * cores_per_executor
        effective_cores = min(available_cores, max_parallelism)
        
        # Estimate completion time
        estimated_time = total_task_time / effective_cores if effective_cores > 0 else float('inf')
        
        # Calculate utilization
        utilization = (effective_cores / available_cores * 100) if available_cores > 0 else 0
        
        return estimated_time, utilization
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable time."""
        # Handle infinity and NaN
        if not isinstance(seconds, (int, float)) or seconds != seconds:  # NaN check
            return "N/A"
        if seconds == float('inf'):
            return "∞"
        if seconds <= 0:
            return "0s"
        
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def predict_with_custom_pool(self, capacity_sku: str = 'F64', custom_pool_vcores: Optional[int] = None) -> Dict:
        """
        Predict performance with Custom Pool on specified Fabric capacity.
        
        Args:
            capacity_sku: Your Fabric capacity SKU (F2 through F2048)
            custom_pool_vcores: Custom pool size in VCores (defaults to 50% of capacity)
        
        Returns:
            Dictionary with prediction results
        """
        if capacity_sku not in self.FABRIC_CAPACITIES:
            raise ValueError(f"Invalid capacity SKU. Choose from: {list(self.FABRIC_CAPACITIES.keys())}")
        
        metrics = self._get_current_metrics()
        capacity = self.FABRIC_CAPACITIES[capacity_sku]
        
        # Custom pool can use any amount up to capacity limit
        # Default to 50% of available Spark VCores
        if custom_pool_vcores is None:
            available_cores = capacity['spark_vcores']
        else:
            available_cores = min(custom_pool_vcores, capacity['spark_vcores'])
        
        # Estimate executors (leave cores for driver)
        available_cores = available_cores - 4  # Reserve for driver
        num_executors = available_cores // 4  # 4 cores per executor
        
        estimated_time, utilization = self._estimate_completion_time(
            metrics['total_task_time_sec'],
            num_executors,
            4,  # Standard cores per executor
            metrics['max_parallel_tasks']
        )
        
        # Add cold start time
        total_time = estimated_time + self.CUSTOM_POOL['startup_time_sec']
        
        return {
            'capacity_sku': capacity_sku,
            'num_executors': num_executors,
            'total_cores': num_executors * 4,
            'custom_pool_vcores': available_cores + 4,  # Including driver
            'estimated_execution_time': estimated_time,
            'cold_start_time': self.CUSTOM_POOL['startup_time_sec'],
            'total_time': total_time,
            'utilization_percent': utilization,
            'compute_hours': (num_executors * 4 * total_time) / 3600,  # VCore-hours
        }
    
    def compare_pool_options(self) -> None:
        """Compare Starter Pool vs Custom Pool options with rich visualization."""
        console.print("\n[bold cyan]🔮 Fabric Spark Scalability Prediction[/bold cyan]\n")
        
        metrics = self._get_current_metrics()
        
        # Current configuration (likely Starter Pool)
        current_time, current_util = self._estimate_completion_time(
            metrics['total_task_time_sec'],
            metrics['num_executors'],
            metrics['cores_per_executor'],
            metrics['max_parallel_tasks']
        )
        
        # Create comparison table
        table = Table(
            title="⚡ Pool Performance Comparison",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Configuration", style="bold")
        table.add_column("Executors", justify="right")
        table.add_column("VCores", justify="right")
        table.add_column("Cold Start", justify="right")
        table.add_column("Execution", justify="right")
        table.add_column("Total Time", justify="right")
        table.add_column("Utilization", justify="right")
        table.add_column("Compute (VCore-h)", justify="right")
        table.add_column("ROI", style="bold")
        
        # Starter Pool (Medium node)
        starter_total = current_time
        starter_vcores = self.STARTER_POOL['executors'] * self.STARTER_POOL['cores_per_executor']
        starter_compute_hours = (starter_vcores * starter_total) / 3600
        
        table.add_row(
            "🟢 Starter Pool (Medium)",
            str(self.STARTER_POOL['executors']),
            str(starter_vcores),
            "0s",
            self._format_time(current_time),
            self._format_time(starter_total),
            f"{current_util:.1f}%",
            f"{starter_compute_hours:.2f}",
            "Baseline",
            style="green"
        )
        
        # Custom Pool predictions with different VCore allocations
        # Assuming user has at least F64 capacity for meaningful comparison
        predictions = []
        custom_pool_options = [
            ('Small Custom Pool', 16),   # 4 executors
            ('Medium Custom Pool', 32),  # 8 executors  
            ('Large Custom Pool', 64),   # 16 executors
        ]
        
        for pool_name, vcores in custom_pool_options:
            pred = self.predict_with_custom_pool('F64', custom_pool_vcores=vcores)
            pred['pool_name'] = pool_name
            predictions.append(pred)
            
            time_savings = starter_total - pred['total_time']
            speedup = starter_total / pred['total_time'] if pred['total_time'] > 0 else 0
            
            # Determine ROI rating
            if speedup >= 2.0 and pred['utilization_percent'] >= 70:
                roi = "⭐⭐⭐ Excellent"
                style = "bold green"
            elif speedup >= 1.5 and pred['utilization_percent'] >= 60:
                roi = "⭐⭐ Good"
                style = "yellow"
            elif speedup >= 1.2:
                roi = "⭐ Moderate"
                style = "dim yellow"
            else:
                roi = "❌ Poor"
                style = "red"
            
            table.add_row(
                f"🔵 {pred['pool_name']}",
                str(pred['num_executors']),
                str(pred['total_cores']),
                self._format_time(pred['cold_start_time']),
                self._format_time(pred['estimated_execution_time']),
                self._format_time(pred['total_time']),
                f"{pred['utilization_percent']:.1f}%",
                f"{pred['compute_hours']:.2f}",
                roi,
                style=style
            )
        
        console.print(table)
        
        # Recommendations panel
        self._print_recommendations(predictions, starter_total, current_util)
    
    def _print_recommendations(self, predictions: List[Dict], starter_time: float, starter_util: float) -> None:
        """Print actionable recommendations based on predictions."""
        
        # Find best ROI
        best_pred = max(
            predictions,
            key=lambda p: (starter_time / p['total_time']) * (p['utilization_percent'] / 100)
        )
        
        speedup = starter_time / best_pred['total_time'] if best_pred['total_time'] > 0 else 0
        time_savings = starter_time - best_pred['total_time']
        
        recommendations = []
        
        if speedup >= 1.5 and best_pred['utilization_percent'] >= 60:
            recommendations.append(
                f"💡 **Consider {best_pred['pool_name']}** for {speedup:.1f}x speedup"
            )
            recommendations.append(
                f"   Saves {self._format_time(time_savings)} per run with {best_pred['utilization_percent']:.0f}% utilization"
            )
            recommendations.append(
                f"   Uses {best_pred['custom_pool_vcores']} VCores ({best_pred['num_executors']} executors)"
            )
            recommendations.append(
                f"   Break-even: Run this job frequently to offset 3min cold-start"
            )
        elif speedup < 1.2:
            recommendations.append(
                "✅ **Stay on Starter Pool (Medium)** - Custom Pool provides minimal benefit"
            )
            recommendations.append(
                "   Your workload scales efficiently with available resources"
            )
            recommendations.append(
                "   Cold-start overhead (3-5min) would negate any gains"
            )
        else:
            recommendations.append(
                f"⚖️ **Evaluate {best_pred['pool_name']} for production** - Moderate speedup ({speedup:.1f}x)"
            )
            recommendations.append(
                "   Consider if time savings justify cold-start overhead for frequent jobs"
            )
        
        # Capacity and billing context
        recommendations.append("\n📊 **Fabric Capacity & Billing Context:**")
        recommendations.append("   • Starter Pool (Medium node): Available on ALL capacity SKUs (F2-F2048)")
        recommendations.append("   • Custom Pool: Sized based on your capacity's available VCores")
        recommendations.append("   • Capacity-based billing: Fixed cost based on F SKU")
        recommendations.append("   • Autoscale billing: Pay-as-you-go for Spark workloads (Spark offloaded)")
        recommendations.append("     - Default quota: Up to 2,048 CUs (can be increased via quota limit request)")
        recommendations.append("     - Example: F2 base capacity + 2,048 CU autoscale limit")
        recommendations.append("   • Pricing varies by region and reservation vs on-demand")
        
        panel = Panel(
            "\n".join(recommendations),
            title="📊 Scalability Recommendations",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(panel)
    
    def predict_capacity_upgrade(self, runs_per_month: int = 100) -> None:
        """
        Predict compute utilization based on job frequency.
        
        Args:
            runs_per_month: Expected number of job runs per month
        """
        console.print(f"\n[bold cyan]💡 Compute Utilization Analysis ({runs_per_month} runs/month)[/bold cyan]\n")
        
        metrics = self._get_current_metrics()
        
        # Current (Starter Pool) baseline
        current_time, _ = self._estimate_completion_time(
            metrics['total_task_time_sec'],
            self.STARTER_POOL['executors'],
            self.STARTER_POOL['cores_per_executor'],
            metrics['max_parallel_tasks']
        )
        
        # Monthly compute hours
        starter_vcores = self.STARTER_POOL['executors'] * self.STARTER_POOL['cores_per_executor']
        current_monthly_vcore_hours = (starter_vcores * current_time / 3600) * runs_per_month
        
        table = Table(
            title="⏱️ Monthly Compute Analysis",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Configuration", style="bold")
        table.add_column("Time/Run", justify="right")
        table.add_column("Monthly Time", justify="right")
        table.add_column("Time Saved", justify="right")
        table.add_column("VCore-Hours/Month", justify="right")
        table.add_column("Efficiency", justify="right")
        table.add_column("Verdict", style="bold")
        
        # Starter Pool
        starter_hours = (current_time / 3600) * runs_per_month
        table.add_row(
            "Starter Pool (Medium)",
            self._format_time(current_time),
            f"{starter_hours:.1f}h",
            "-",
            f"{current_monthly_vcore_hours:.1f}",
            "Baseline",
            "Baseline",
            style="green"
        )
        
        # Custom pool options
        custom_pool_options = [
            ('Small Custom', 16),
            ('Medium Custom', 32),
            ('Large Custom', 64),
            ('XL Custom', 128),
        ]
        
        for pool_name, vcores in custom_pool_options:
            pred = self.predict_with_custom_pool('F128', custom_pool_vcores=vcores)
            
            monthly_hours = (pred['total_time'] / 3600) * runs_per_month
            hours_saved = starter_hours - monthly_hours
            monthly_vcore_hours = pred['compute_hours'] * runs_per_month
            
            # Efficiency gain
            efficiency_gain = (current_monthly_vcore_hours / monthly_vcore_hours) if monthly_vcore_hours > 0 else 0
            
            # Verdict
            if hours_saved > 10 and efficiency_gain > 1.5:
                verdict = "⭐⭐⭐ Excellent"
                style = "bold green"
            elif hours_saved > 5 and efficiency_gain > 1.2:
                verdict = "⭐⭐ Good"
                style = "yellow"
            elif hours_saved > 0:
                verdict = "⭐ Consider"
                style = "dim yellow"
            else:
                verdict = "❌ Not Worth"
                style = "red"
            
            table.add_row(
                f"{pool_name} ({vcores}v)",
                self._format_time(pred['total_time']),
                f"{monthly_hours:.1f}h",
                f"{hours_saved:.1f}h",
                f"{monthly_vcore_hours:.1f}",
                f"{efficiency_gain:.2f}x" if efficiency_gain > 0 else "N/A",
                verdict,
                style=style
            )
        
        console.print(table)
        
        console.print("\n[dim]Note: Compute shown in VCore-hours. Actual costs depend on capacity SKU, region, and billing model (capacity vs autoscale).[/dim]")


def predict_scalability(df_or_spark=None, runs_per_month: int = 100) -> None:
    """
    Main entry point for scalability prediction.
    
    Args:
        df_or_spark: DataFrame or SparkSession (optional, uses active session if not provided)
        runs_per_month: Expected job frequency for ROI calculation
    """
    # Extract SparkSession from DataFrame or use directly
    if df_or_spark is None:
        spark = SparkSession.getActiveSession()
        if spark is None:
            raise RuntimeError("No active Spark session found")
    elif hasattr(df_or_spark, 'sparkSession'):
        # It's a DataFrame
        spark = df_or_spark.sparkSession
    else:
        # It's a SparkSession
        spark = df_or_spark
    
    predictor = ScalabilityPredictor(spark)
    predictor.compare_pool_options()
    console.print("\n" + "="*80 + "\n")
    predictor.predict_capacity_upgrade(runs_per_month)
