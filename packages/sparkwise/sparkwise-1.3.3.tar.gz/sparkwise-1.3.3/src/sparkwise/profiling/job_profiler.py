"""
Job Profiler

Analyzes job, stage, and task execution metrics to identify performance bottlenecks.
"""

from typing import Dict, Any, List, Optional
from pyspark.sql import SparkSession
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime, timedelta


class JobProfiler:
    """
    Profiles Spark job execution metrics and identifies bottlenecks.
    
    Provides insights into:
    - Job execution history and status
    - Stage-level performance metrics
    - Task execution times and failures
    - Bottleneck identification
    - Shuffle metrics
    """
    
    def __init__(self, spark: Optional[SparkSession] = None) -> None:
        """
        Initialize the job profiler.
        
        Args:
            spark: SparkSession instance. If None, uses active session.
        """
        self.spark = spark or SparkSession.builder.getOrCreate()
        self.sc = self.spark.sparkContext
        self.console = Console()
    
    def profile(self, include_completed: bool = True, max_jobs: int = 10) -> Dict[str, Any]:
        """
        Profile job execution metrics and display results.
        
        Args:
            include_completed: Whether to include completed jobs
            max_jobs: Maximum number of jobs to analyze
            
        Returns:
            Dictionary containing job profile data
        """
        profile_data = {
            "job_summary": self._get_job_summary(),
            "recent_jobs": self._get_recent_jobs(max_jobs, include_completed),
            "shuffle_metrics": self._get_shuffle_metrics(),
            "recommendations": self._generate_recommendations()
        }
        
        # Display profile
        self._display_profile(profile_data)
        
        return profile_data
    
    def _get_job_summary(self) -> Dict[str, Any]:
        """Get overall job execution summary."""
        try:
            status_tracker = self.sc.statusTracker()
            
            # Try to get active and completed jobs
            try:
                active_job_ids = status_tracker.getActiveJobIds() if hasattr(status_tracker, 'getActiveJobIds') else []
                active_stage_ids = status_tracker.getActiveStageIds()
                
                return {
                    "active_jobs": len(active_job_ids),
                    "active_stages": len(active_stage_ids),
                    "available": True
                }
            except:
                return {
                    "available": False,
                    "note": "Job metrics not available in Fabric runtime",
                    "guidance": "Use Fabric Monitoring Hub for detailed job analysis"
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_recent_jobs(self, max_jobs: int, include_completed: bool) -> List[Dict[str, Any]]:
        """Get recent job execution details."""
        try:
            status_tracker = self.sc.statusTracker()
            
            if not hasattr(status_tracker, 'getActiveJobIds'):
                return []
            
            job_ids = list(status_tracker.getActiveJobIds())
            jobs = []
            
            for job_id in job_ids[:max_jobs]:
                try:
                    job_info = status_tracker.getJobInfo(job_id)
                    if job_info:
                        stage_ids = job_info.stageIds()
                        
                        # Aggregate stage metrics
                        total_tasks = 0
                        completed_tasks = 0
                        failed_tasks = 0
                        
                        for stage_id in stage_ids:
                            stage_info = status_tracker.getStageInfo(stage_id)
                            if stage_info:
                                total_tasks += stage_info.numTasks()
                                completed_tasks += stage_info.numCompletedTasks()
                                failed_tasks += stage_info.numFailedTasks()
                        
                        jobs.append({
                            "job_id": job_id,
                            "num_stages": len(stage_ids),
                            "total_tasks": total_tasks,
                            "completed_tasks": completed_tasks,
                            "failed_tasks": failed_tasks,
                            "status": job_info.status().toString() if hasattr(job_info, 'status') else "RUNNING"
                        })
                except:
                    continue
            
            return jobs
        except Exception:
            return []
    
    def _get_shuffle_metrics(self) -> Dict[str, Any]:
        """Get shuffle read/write metrics."""
        try:
            # Get shuffle metrics from storage status
            storage_status = self.sc._jsc.sc().getExecutorStorageStatus()
            
            total_shuffle_read = 0
            total_shuffle_write = 0
            
            # Note: Direct shuffle metrics require accessing RDD info
            # which may not be available in all contexts
            
            return {
                "available": False,
                "note": "Shuffle metrics require completed jobs",
                "guidance": "Run a query with shuffles and check Fabric Monitoring Hub"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on job profiles."""
        recommendations = []
        
        try:
            status_tracker = self.sc.statusTracker()
            
            if hasattr(status_tracker, 'getActiveJobIds'):
                active_jobs = status_tracker.getActiveJobIds()
                
                if len(active_jobs) > 5:
                    recommendations.append(
                        "High number of concurrent jobs detected. Consider serializing some jobs for better resource utilization."
                    )
                
                # Check for failed tasks
                for job_id in active_jobs[:5]:
                    job_info = status_tracker.getJobInfo(job_id)
                    if job_info:
                        stage_ids = job_info.stageIds()
                        for stage_id in stage_ids:
                            stage_info = status_tracker.getStageInfo(stage_id)
                            if stage_info and stage_info.numFailedTasks() > 0:
                                recommendations.append(
                                    f"Job {job_id} has failed tasks. Check for data skew or executor failures."
                                )
                                break
        except:
            pass
        
        if not recommendations:
            recommendations.append("Job execution appears healthy. Continue monitoring for changes.")
        
        return recommendations
    
    def _display_profile(self, profile_data: Dict[str, Any]) -> None:
        """Display job profile in formatted tables."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold cyan]🏃 Job Execution Profile[/bold cyan]",
            border_style="cyan"
        ))
        
        # Job Summary
        summary = profile_data.get("job_summary", {})
        
        if summary.get("available", False):
            self.console.print("\n[bold]📊 Job Summary[/bold]")
            
            summary_table = Table(show_header=False, box=None)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Count", justify="right")
            
            active_jobs = summary.get("active_jobs", 0)
            active_stages = summary.get("active_stages", 0)
            
            job_status = f"[green]{active_jobs}[/green]" if active_jobs > 0 else str(active_jobs)
            stage_status = f"[green]{active_stages}[/green]" if active_stages > 0 else str(active_stages)
            
            summary_table.add_row("Active Jobs", job_status)
            summary_table.add_row("Active Stages", stage_status)
            
            self.console.print(summary_table)
        else:
            self.console.print("\n[dim]ℹ️  Job metrics not available in Fabric runtime[/dim]")
            self.console.print(f"[dim]   {summary.get('guidance', 'Use Fabric Monitoring Hub for job details')}[/dim]")
        
        # Recent Jobs
        jobs = profile_data.get("recent_jobs", [])
        if jobs:
            self.console.print("\n[bold]📋 Recent Jobs[/bold]")
            
            job_table = Table(show_header=True, header_style="bold magenta")
            job_table.add_column("Job ID", style="cyan")
            job_table.add_column("Stages", justify="center")
            job_table.add_column("Tasks", justify="center")
            job_table.add_column("Completed", justify="center")
            job_table.add_column("Failed", justify="center")
            job_table.add_column("Status")
            
            for job in jobs:
                failed = job.get("failed_tasks", 0)
                failed_str = f"[red]{failed}[/red]" if failed > 0 else str(failed)
                
                status = job.get("status", "RUNNING")
                if status == "SUCCEEDED":
                    status_str = "[green]✓ Success[/green]"
                elif status == "FAILED":
                    status_str = "[red]✗ Failed[/red]"
                elif status == "RUNNING":
                    status_str = "[yellow]⟳ Running[/yellow]"
                else:
                    status_str = status
                
                job_table.add_row(
                    str(job.get("job_id", "N/A")),
                    str(job.get("num_stages", 0)),
                    str(job.get("total_tasks", 0)),
                    str(job.get("completed_tasks", 0)),
                    failed_str,
                    status_str
                )
            
            self.console.print(job_table)
        
        # Shuffle Metrics
        shuffle = profile_data.get("shuffle_metrics", {})
        if shuffle.get("available", False):
            self.console.print("\n[bold]🔀 Shuffle Metrics[/bold]")
            
            shuffle_table = Table(show_header=False, box=None)
            shuffle_table.add_column("Metric", style="cyan")
            shuffle_table.add_column("Value", justify="right")
            
            shuffle_table.add_row("Total Shuffle Read", shuffle.get("total_read", "N/A"))
            shuffle_table.add_row("Total Shuffle Write", shuffle.get("total_write", "N/A"))
            
            self.console.print(shuffle_table)
        elif "note" in shuffle:
            self.console.print(f"\n[dim]ℹ️  {shuffle['note']}[/dim]")
            self.console.print(f"[dim]   {shuffle.get('guidance', '')}[/dim]")
        
        # Recommendations
        recommendations = profile_data.get("recommendations", [])
        if recommendations:
            self.console.print("\n[bold]💡 Recommendations[/bold]")
            for i, rec in enumerate(recommendations, 1):
                self.console.print(f"  {i}. {rec}")
        
        # Fabric guidance
        self.console.print("\n[bold cyan]📊 Fabric Monitoring Hub[/bold cyan]")
        self.console.print("[dim]For detailed job metrics, stages, and task-level analysis:[/dim]")
        self.console.print("[dim]  1. Navigate to Fabric workspace[/dim]")
        self.console.print("[dim]  2. Select your notebook/lakehouse[/dim]")
        self.console.print("[dim]  3. Click 'Monitoring Hub' in the menu[/dim]")
        self.console.print("[dim]  4. View detailed execution metrics and timelines[/dim]")
    
    def analyze_bottlenecks(self) -> Dict[str, Any]:
        """
        Analyze and identify performance bottlenecks.
        
        Returns:
            Dictionary with bottleneck analysis
        """
        self.console.print("\n[bold cyan]🔍 Bottleneck Analysis[/bold cyan]\n")
        
        bottlenecks = {
            "detected": [],
            "potential": [],
            "recommendations": []
        }
        
        try:
            status_tracker = self.sc.statusTracker()
            
            if hasattr(status_tracker, 'getActiveStageIds'):
                active_stages = status_tracker.getActiveStageIds()
                
                if len(active_stages) > 10:
                    bottlenecks["potential"].append({
                        "type": "Many Active Stages",
                        "description": f"{len(active_stages)} stages running concurrently",
                        "impact": "May indicate excessive parallelism or resource contention",
                        "recommendation": "Review job structure and consider stage consolidation"
                    })
                
                # Check individual stages for issues
                for stage_id in active_stages[:5]:  # Check first 5 stages
                    stage_info = status_tracker.getStageInfo(stage_id)
                    if stage_info:
                        num_tasks = stage_info.numTasks()
                        completed = stage_info.numCompletedTasks()
                        failed = stage_info.numFailedTasks()
                        
                        if failed > num_tasks * 0.1:  # More than 10% failed
                            bottlenecks["detected"].append({
                                "type": "High Task Failure Rate",
                                "stage_id": stage_id,
                                "failed_tasks": failed,
                                "total_tasks": num_tasks,
                                "recommendation": "Check for data skew, memory issues, or executor failures"
                            })
        except:
            self.console.print("[dim]ℹ️  Bottleneck analysis not available in Fabric runtime[/dim]")
            self.console.print("[dim]   Use Fabric Monitoring Hub for detailed bottleneck identification[/dim]")
        
        # Display results
        if bottlenecks["detected"]:
            self.console.print("[bold red]⚠️  Detected Bottlenecks:[/bold red]")
            for bn in bottlenecks["detected"]:
                self.console.print(f"\n  • [red]{bn['type']}[/red]")
                for key, value in bn.items():
                    if key != "type":
                        self.console.print(f"    {key}: {value}")
        
        if bottlenecks["potential"]:
            self.console.print("\n[bold yellow]⚡ Potential Bottlenecks:[/bold yellow]")
            for bn in bottlenecks["potential"]:
                self.console.print(f"\n  • [yellow]{bn['type']}[/yellow]")
                self.console.print(f"    {bn['description']}")
                self.console.print(f"    💡 {bn['recommendation']}")
        
        if not bottlenecks["detected"] and not bottlenecks["potential"]:
            self.console.print("[green]✓ No obvious bottlenecks detected[/green]")
            self.console.print("[dim]  Performance appears nominal[/dim]")
        
        return bottlenecks
