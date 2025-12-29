"""
Executor Profiler

Analyzes executor-level metrics including memory usage, task distribution, and performance.
"""

from typing import Dict, Any, List, Optional
from pyspark.sql import SparkSession
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class ExecutorProfiler:
    """
    Profiles Spark executor metrics and resource utilization.
    
    Provides insights into:
    - Active executor count and distribution
    - Memory usage per executor
    - Task distribution across executors
    - Executor failures and removals
    - Storage memory utilization
    """
    
    def __init__(self, spark: Optional[SparkSession] = None) -> None:
        """
        Initialize the executor profiler.
        
        Args:
            spark: SparkSession instance. If None, uses active session.
        """
        self.spark = spark or SparkSession.builder.getOrCreate()
        self.sc = self.spark.sparkContext
        self.console = Console()
    
    def profile(self) -> Dict[str, Any]:
        """
        Profile executor metrics and display results.
        
        Returns:
            Dictionary containing executor profile data
        """
        profile_data = {
            "executor_summary": self._get_executor_summary(),
            "executor_details": self._get_executor_details(),
            "memory_utilization": self._get_memory_utilization(),
            "task_distribution": self._get_task_distribution()
        }
        
        # Display profile
        self._display_profile(profile_data)
        
        return profile_data
    
    def _get_executor_summary(self) -> Dict[str, Any]:
        """Get summary of executor configuration and state."""
        try:
            status_tracker = self.sc.statusTracker()
            
            # Try to get executor info (may not be available in all modes)
            try:
                executor_info = status_tracker.getExecutorInfos()
                active_executors = len([e for e in executor_info if e.isActive()])
                total_executors = len(executor_info)
            except:
                active_executors = "N/A"
                total_executors = "N/A"
            
            return {
                "active_executors": active_executors,
                "total_executors": total_executors,
                "configured_instances": self.spark.conf.get("spark.executor.instances", "dynamic"),
                "configured_memory": self.spark.conf.get("spark.executor.memory", "N/A"),
                "configured_cores": self.spark.conf.get("spark.executor.cores", "N/A"),
                "dynamic_allocation": self.spark.conf.get("spark.dynamicAllocation.enabled", "false")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_executor_details(self) -> List[Dict[str, Any]]:
        """Get detailed information about each executor."""
        try:
            status_tracker = self.sc.statusTracker()
            executor_info = status_tracker.getExecutorInfos()
            
            executors = []
            for executor in executor_info:
                executors.append({
                    "executor_id": executor.id(),
                    "host": executor.host(),
                    "port": executor.port(),
                    "is_active": executor.isActive(),
                    "total_cores": executor.totalCores(),
                    "max_tasks": executor.maxTasks(),
                    "max_memory": executor.maxMemory()
                })
            
            return executors
        except AttributeError:
            # getExecutorInfos not available in this Spark version/mode
            return []
        except Exception as e:
            return [{"error": str(e)}]
    
    def _get_memory_utilization(self) -> Dict[str, Any]:
        """Get memory utilization metrics."""
        try:
            # Get storage status for memory info
            storage_status = self.sc._jsc.sc().getExecutorStorageStatus()
            
            total_memory = 0
            used_memory = 0
            remaining_memory = 0
            
            for status in storage_status:
                max_mem = status.maxMem()
                mem_used = status.memUsed()
                mem_remaining = status.memRemaining()
                
                total_memory += max_mem
                used_memory += mem_used
                remaining_memory += mem_remaining
            
            # Convert to GB
            total_gb = total_memory / (1024 ** 3)
            used_gb = used_memory / (1024 ** 3)
            remaining_gb = remaining_memory / (1024 ** 3)
            
            utilization_pct = (used_memory / total_memory * 100) if total_memory > 0 else 0
            
            return {
                "total_memory_gb": round(total_gb, 2),
                "used_memory_gb": round(used_gb, 2),
                "remaining_memory_gb": round(remaining_gb, 2),
                "utilization_percent": round(utilization_pct, 2)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_task_distribution(self) -> Dict[str, Any]:
        """Get task distribution metrics across executors."""
        try:
            status_tracker = self.sc.statusTracker()
            
            # Get active job IDs
            if hasattr(status_tracker, 'getActiveJobIds'):
                active_jobs = status_tracker.getActiveJobIds()
                
                total_tasks = 0
                completed_tasks = 0
                failed_tasks = 0
                
                for job_id in active_jobs:
                    job_info = status_tracker.getJobInfo(job_id)
                    if job_info:
                        stage_ids = job_info.stageIds()
                        for stage_id in stage_ids:
                            stage_info = status_tracker.getStageInfo(stage_id)
                            if stage_info:
                                total_tasks += stage_info.numTasks()
                                completed_tasks += stage_info.numCompletedTasks()
                                failed_tasks += stage_info.numFailedTasks()
                
                return {
                    "active_jobs": len(active_jobs),
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "running_tasks": total_tasks - completed_tasks - failed_tasks
                }
            else:
                return {
                    "note": "Task distribution not available in Fabric (use Monitoring Hub)",
                    "guidance": "Navigate to Fabric Monitoring Hub for detailed task metrics"
                }
        except Exception as e:
            return {
                "note": "Task distribution not available in Fabric (use Monitoring Hub)",
                "guidance": "Navigate to Fabric Monitoring Hub for detailed task metrics"
            }
    
    def _display_profile(self, profile_data: Dict[str, Any]) -> None:
        """Display executor profile in formatted tables."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold cyan]⚡ Executor Profile[/bold cyan]",
            border_style="cyan"
        ))
        
        # Executor Summary
        summary = profile_data.get("executor_summary", {})
        if "error" not in summary:
            self.console.print("\n[bold]📊 Executor Summary[/bold]")
            
            summary_table = Table(show_header=False, box=None)
            summary_table.add_column("Property", style="cyan")
            summary_table.add_column("Value")
            
            active_exec = summary.get("active_executors", "N/A")
            total_exec = summary.get("total_executors", "N/A")
            
            if active_exec != "N/A" and total_exec != "N/A":
                executor_status = f"{active_exec}/{total_exec} active"
                if active_exec == total_exec and active_exec > 0:
                    executor_status = f"[green]{executor_status}[/green]"
                elif active_exec < total_exec:
                    executor_status = f"[yellow]{executor_status}[/yellow]"
            else:
                executor_status = "N/A (check Fabric Monitoring Hub)"
            
            summary_table.add_row("Executor Status", executor_status)
            summary_table.add_row("Configured Instances", summary.get("configured_instances", "N/A"))
            summary_table.add_row("Memory per Executor", summary.get("configured_memory", "N/A"))
            summary_table.add_row("Cores per Executor", summary.get("configured_cores", "N/A"))
            
            dynamic_alloc = summary.get("dynamic_allocation", "false")
            if dynamic_alloc.lower() == "true":
                dynamic_str = "[green]✓ Enabled[/green]"
            else:
                dynamic_str = "[yellow]✗ Disabled[/yellow]"
            summary_table.add_row("Dynamic Allocation", dynamic_str)
            
            self.console.print(summary_table)
        
        # Executor Details
        details = profile_data.get("executor_details", [])
        if details and not any("error" in d for d in details):
            self.console.print("\n[bold]🔷 Executor Details[/bold]")
            
            exec_table = Table(show_header=True, header_style="bold magenta")
            exec_table.add_column("Executor ID", style="cyan")
            exec_table.add_column("Host")
            exec_table.add_column("Cores")
            exec_table.add_column("Max Tasks")
            exec_table.add_column("Max Memory")
            exec_table.add_column("Status")
            
            for executor in details:
                status = "[green]Active[/green]" if executor.get("is_active") else "[red]Inactive[/red]"
                max_mem_gb = executor.get("max_memory", 0) / (1024 ** 3)
                
                exec_table.add_row(
                    executor.get("executor_id", "N/A"),
                    executor.get("host", "N/A"),
                    str(executor.get("total_cores", "N/A")),
                    str(executor.get("max_tasks", "N/A")),
                    f"{max_mem_gb:.2f} GB",
                    status
                )
            
            self.console.print(exec_table)
        elif not details:
            self.console.print("\n[dim]ℹ️  Detailed executor metrics not available in Fabric.[/dim]")
            self.console.print("[dim]   Use Fabric Monitoring Hub for executor-level details.[/dim]")
        
        # Memory Utilization
        memory = profile_data.get("memory_utilization", {})
        if "error" not in memory and "total_memory_gb" in memory:
            self.console.print("\n[bold]🧠 Memory Utilization[/bold]")
            
            mem_table = Table(show_header=True, header_style="bold magenta")
            mem_table.add_column("Metric", style="cyan")
            mem_table.add_column("Value", justify="right")
            
            total_mem = memory.get("total_memory_gb", 0)
            used_mem = memory.get("used_memory_gb", 0)
            remaining_mem = memory.get("remaining_memory_gb", 0)
            utilization = memory.get("utilization_percent", 0)
            
            mem_table.add_row("Total Storage Memory", f"{total_mem:.2f} GB")
            mem_table.add_row("Used Memory", f"{used_mem:.2f} GB")
            mem_table.add_row("Remaining Memory", f"{remaining_mem:.2f} GB")
            
            # Color-code utilization
            if utilization > 80:
                util_str = f"[red]{utilization:.1f}%[/red] ⚠️  High"
            elif utilization > 60:
                util_str = f"[yellow]{utilization:.1f}%[/yellow]"
            else:
                util_str = f"[green]{utilization:.1f}%[/green]"
            
            mem_table.add_row("Utilization", util_str)
            
            self.console.print(mem_table)
            
            if utilization > 80:
                self.console.print("\n[yellow]💡 High memory utilization detected. Consider:[/yellow]")
                self.console.print("   - Unpersist unused DataFrames: df.unpersist()")
                self.console.print("   - Reduce cached data")
                self.console.print("   - Increase executor memory if needed")
        
        # Task Distribution
        tasks = profile_data.get("task_distribution", {})
        if tasks:
            self.console.print("\n[bold]📋 Task Distribution[/bold]")
            
            if "note" in tasks:
                self.console.print(f"[dim]ℹ️  {tasks['note']}[/dim]")
                self.console.print(f"[dim]   {tasks['guidance']}[/dim]")
            else:
                task_table = Table(show_header=False, box=None)
                task_table.add_column("Metric", style="cyan")
                task_table.add_column("Count", justify="right")
                
                task_table.add_row("Active Jobs", str(tasks.get("active_jobs", 0)))
                task_table.add_row("Total Tasks", str(tasks.get("total_tasks", 0)))
                task_table.add_row("Completed Tasks", f"[green]{tasks.get('completed_tasks', 0)}[/green]")
                task_table.add_row("Running Tasks", f"[yellow]{tasks.get('running_tasks', 0)}[/yellow]")
                
                failed = tasks.get("failed_tasks", 0)
                if failed > 0:
                    task_table.add_row("Failed Tasks", f"[red]{failed}[/red] ⚠️")
                else:
                    task_table.add_row("Failed Tasks", str(failed))
                
                self.console.print(task_table)
