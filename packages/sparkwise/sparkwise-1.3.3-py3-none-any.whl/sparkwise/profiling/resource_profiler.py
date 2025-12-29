"""
Resource Profiler

Compares actual vs configured resources and identifies resource utilization issues.
"""

from typing import Dict, Any, Optional, List
from pyspark.sql import SparkSession
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn


class ResourceProfiler:
    """
    Profiles resource allocation and utilization.
    
    Provides insights into:
    - Actual vs configured resources
    - Resource utilization efficiency
    - Over/under-provisioning detection
    - Cost optimization opportunities
    """
    
    def __init__(self, spark: Optional[SparkSession] = None) -> None:
        """
        Initialize the resource profiler.
        
        Args:
            spark: SparkSession instance. If None, uses active session.
        """
        self.spark = spark or SparkSession.builder.getOrCreate()
        self.sc = self.spark.sparkContext
        self.conf = self.spark.conf
        self.console = Console()
    
    def profile(self) -> Dict[str, Any]:
        """
        Profile resource allocation and utilization.
        
        Returns:
            Dictionary containing resource profile data
        """
        profile_data = {
            "configured_resources": self._get_configured_resources(),
            "actual_resources": self._get_actual_resources(),
            "utilization_analysis": self._analyze_utilization(),
            "recommendations": self._generate_recommendations()
        }
        
        # Display profile
        self._display_profile(profile_data)
        
        return profile_data
    
    def _get_configured_resources(self) -> Dict[str, Any]:
        """Get configured resource settings."""
        return {
            "executor": {
                "instances": self.conf.get("spark.executor.instances", "dynamic"),
                "memory": self.conf.get("spark.executor.memory", "N/A"),
                "cores": self.conf.get("spark.executor.cores", "N/A"),
                "memory_overhead": self.conf.get("spark.executor.memoryOverhead", "auto")
            },
            "driver": {
                "memory": self.conf.get("spark.driver.memory", "N/A"),
                "cores": self.conf.get("spark.driver.cores", "N/A"),
                "max_result_size": self.conf.get("spark.driver.maxResultSize", "1g")
            },
            "dynamic_allocation": {
                "enabled": self.conf.get("spark.dynamicAllocation.enabled", "false"),
                "min_executors": self.conf.get("spark.dynamicAllocation.minExecutors", "0"),
                "max_executors": self.conf.get("spark.dynamicAllocation.maxExecutors", "infinity"),
                "initial_executors": self.conf.get("spark.dynamicAllocation.initialExecutors", "min")
            }
        }
    
    def _get_actual_resources(self) -> Dict[str, Any]:
        """Get actual allocated resources from runtime."""
        try:
            status_tracker = self.sc.statusTracker()
            
            # Try to get actual executor count
            try:
                executor_info = status_tracker.getExecutorInfos()
                active_executors = len([e for e in executor_info if e.isActive()])
                
                # Calculate total resources
                cores_per_exec = int(self.conf.get("spark.executor.cores", "1"))
                total_cores = active_executors * cores_per_exec
                
                mem_per_exec = self.conf.get("spark.executor.memory", "1g")
                # Parse memory (simplified)
                mem_value = mem_per_exec.lower().replace("g", "").replace("m", "")
                try:
                    mem_gb = float(mem_value)
                    if "m" in mem_per_exec.lower():
                        mem_gb = mem_gb / 1024
                    total_memory_gb = active_executors * mem_gb
                except:
                    total_memory_gb = 0
                
                return {
                    "executors": active_executors,
                    "total_cores": total_cores,
                    "total_memory_gb": round(total_memory_gb, 2),
                    "available": True
                }
            except:
                return {
                    "available": False,
                    "note": "Runtime metrics not available in Fabric",
                    "guidance": "Check Fabric workspace capacity settings"
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization efficiency."""
        analysis = {
            "findings": [],
            "efficiency_score": 0.0
        }
        
        try:
            # Check executor configuration
            executor_instances = self.conf.get("spark.executor.instances", "dynamic")
            dynamic_enabled = self.conf.get("spark.dynamicAllocation.enabled", "false")
            
            if executor_instances != "dynamic" and dynamic_enabled.lower() == "false":
                analysis["findings"].append({
                    "type": "Static Allocation",
                    "severity": "warning",
                    "message": "Using static executor allocation. Consider enabling dynamic allocation for better resource efficiency.",
                    "impact": "May waste resources during low activity or starve during high demand"
                })
            
            # Check memory configuration
            executor_memory = self.conf.get("spark.executor.memory", "N/A")
            executor_cores = self.conf.get("spark.executor.cores", "N/A")
            
            if executor_memory != "N/A" and executor_cores != "N/A":
                try:
                    mem_gb = float(executor_memory.lower().replace("g", "").replace("m", ""))
                    if "m" in executor_memory.lower():
                        mem_gb = mem_gb / 1024
                    
                    cores = int(executor_cores)
                    
                    # Calculate memory per core
                    mem_per_core = mem_gb / cores if cores > 0 else 0
                    
                    if mem_per_core < 2:
                        analysis["findings"].append({
                            "type": "Low Memory per Core",
                            "severity": "warning",
                            "message": f"Only {mem_per_core:.1f}GB per core. May cause memory pressure.",
                            "recommendation": "Consider increasing executor memory or reducing cores"
                        })
                    elif mem_per_core > 16:
                        analysis["findings"].append({
                            "type": "Excessive Memory per Core",
                            "severity": "info",
                            "message": f"{mem_per_core:.1f}GB per core. May indicate over-provisioning.",
                            "recommendation": "Consider using more executors with less memory each"
                        })
                except:
                    pass
            
            # Calculate efficiency score
            if not analysis["findings"]:
                analysis["efficiency_score"] = 1.0
            else:
                warnings = len([f for f in analysis["findings"] if f["severity"] == "warning"])
                analysis["efficiency_score"] = max(0.5, 1.0 - (warnings * 0.2))
        
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate resource optimization recommendations."""
        recommendations = []
        
        try:
            # Check if using Starter Pool
            pool_name = self.conf.get("spark.fabric.pool.name", "N/A")
            
            if "starter" in pool_name.lower():
                recommendations.append({
                    "priority": "info",
                    "category": "Pooling",
                    "recommendation": "Using Starter Pool - optimal for dev/test with instant startup",
                    "benefit": "No cold-start delay (3-5min savings per run)"
                })
            
            # Check dynamic allocation
            dynamic_enabled = self.conf.get("spark.dynamicAllocation.enabled", "false")
            
            if dynamic_enabled.lower() == "false":
                recommendations.append({
                    "priority": "medium",
                    "category": "Dynamic Allocation",
                    "recommendation": "Enable dynamic allocation for auto-scaling",
                    "benefit": "Automatically scales executors based on workload demand",
                    "config": "spark.dynamicAllocation.enabled=true"
                })
            
            # Check AQE
            aqe_enabled = self.conf.get("spark.sql.adaptive.enabled", "false")
            
            if aqe_enabled.lower() == "false":
                recommendations.append({
                    "priority": "high",
                    "category": "Query Optimization",
                    "recommendation": "Enable Adaptive Query Execution (AQE)",
                    "benefit": "Dynamic optimization of partition sizes and join strategies",
                    "config": "spark.sql.adaptive.enabled=true"
                })
            
            # Check partition sizing
            max_partition_bytes = self.conf.get("spark.sql.files.maxPartitionBytes", "134217728")
            executor_memory = self.conf.get("spark.executor.memory", "N/A")
            
            if executor_memory != "N/A":
                try:
                    mem_gb = float(executor_memory.lower().replace("g", ""))
                    partition_mb = int(max_partition_bytes) / (1024 * 1024)
                    
                    if mem_gb > 32 and partition_mb < 200:
                        recommendations.append({
                            "priority": "low",
                            "category": "Partition Sizing",
                            "recommendation": f"Increase partition size from {partition_mb:.0f}MB to 256-512MB",
                            "benefit": "Reduce task overhead for large-memory executors",
                            "config": "spark.sql.files.maxPartitionBytes=268435456 (256MB)"
                        })
                except:
                    pass
        
        except Exception as e:
            recommendations.append({
                "priority": "error",
                "category": "Analysis",
                "recommendation": f"Error generating recommendations: {str(e)}"
            })
        
        return recommendations
    
    def _display_profile(self, profile_data: Dict[str, Any]) -> None:
        """Display resource profile in formatted tables."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold cyan]💎 Resource Utilization Profile[/bold cyan]",
            border_style="cyan"
        ))
        
        # Configured Resources
        configured = profile_data.get("configured_resources", {})
        self.console.print("\n[bold]⚙️  Configured Resources[/bold]")
        
        config_table = Table(show_header=True, header_style="bold magenta")
        config_table.add_column("Resource Type", style="cyan")
        config_table.add_column("Configuration")
        config_table.add_column("Value")
        
        # Executor config
        executor = configured.get("executor", {})
        config_table.add_row("Executor", "Instances", executor.get("instances", "N/A"))
        config_table.add_row("", "Memory", executor.get("memory", "N/A"))
        config_table.add_row("", "Cores", executor.get("cores", "N/A"))
        config_table.add_row("", "Memory Overhead", executor.get("memory_overhead", "N/A"))
        
        # Driver config
        driver = configured.get("driver", {})
        config_table.add_row("Driver", "Memory", driver.get("memory", "N/A"))
        config_table.add_row("", "Cores", driver.get("cores", "N/A"))
        
        # Dynamic allocation
        dynamic = configured.get("dynamic_allocation", {})
        dyn_enabled = dynamic.get("enabled", "false")
        config_table.add_row("Dynamic Allocation", "Enabled", 
                            "[green]✓ Yes[/green]" if dyn_enabled.lower() == "true" else "[yellow]✗ No[/yellow]")
        
        if dyn_enabled.lower() == "true":
            config_table.add_row("", "Min Executors", dynamic.get("min_executors", "N/A"))
            config_table.add_row("", "Max Executors", dynamic.get("max_executors", "N/A"))
        
        self.console.print(config_table)
        
        # Actual Resources
        actual = profile_data.get("actual_resources", {})
        if actual.get("available", False):
            self.console.print("\n[bold]📊 Actual Allocated Resources[/bold]")
            
            actual_table = Table(show_header=False, box=None)
            actual_table.add_column("Metric", style="cyan")
            actual_table.add_column("Value", justify="right")
            
            actual_table.add_row("Active Executors", str(actual.get("executors", "N/A")))
            actual_table.add_row("Total CPU Cores", str(actual.get("total_cores", "N/A")))
            actual_table.add_row("Total Memory", f"{actual.get('total_memory_gb', 0):.2f} GB")
            
            self.console.print(actual_table)
        else:
            self.console.print(f"\n[dim]ℹ️  {actual.get('note', 'Actual resource metrics not available')}[/dim]")
            if "guidance" in actual:
                self.console.print(f"[dim]   {actual['guidance']}[/dim]")
        
        # Utilization Analysis
        utilization = profile_data.get("utilization_analysis", {})
        findings = utilization.get("findings", [])
        
        if findings:
            self.console.print("\n[bold]🔍 Utilization Analysis[/bold]")
            
            for finding in findings:
                severity = finding.get("severity", "info")
                if severity == "warning":
                    icon = "[yellow]⚠️ [/yellow]"
                    style = "yellow"
                elif severity == "error":
                    icon = "[red]❌[/red]"
                    style = "red"
                else:
                    icon = "[blue]ℹ️ [/blue]"
                    style = "blue"
                
                self.console.print(f"\n{icon} [{style}]{finding.get('type', 'Finding')}[/{style}]")
                self.console.print(f"   {finding.get('message', '')}")
                
                if "recommendation" in finding:
                    self.console.print(f"   💡 {finding['recommendation']}")
        
        # Efficiency Score
        efficiency = utilization.get("efficiency_score", 0)
        if efficiency > 0:
            self.console.print("\n[bold]📈 Resource Efficiency Score[/bold]")
            
            # Create a simple progress bar for efficiency
            efficiency_pct = int(efficiency * 100)
            
            if efficiency >= 0.8:
                bar_color = "green"
                status = "Excellent"
            elif efficiency >= 0.6:
                bar_color = "yellow"
                status = "Good"
            else:
                bar_color = "red"
                status = "Needs Improvement"
            
            self.console.print(f"  [{bar_color}]{'█' * efficiency_pct}{'░' * (100 - efficiency_pct)}[/{bar_color}] {efficiency_pct}% - {status}")
        
        # Recommendations
        recommendations = profile_data.get("recommendations", [])
        if recommendations:
            self.console.print("\n[bold]💡 Optimization Recommendations[/bold]")
            
            for rec in recommendations:
                priority = rec.get("priority", "info")
                
                if priority == "high":
                    icon = "🔴"
                elif priority == "medium":
                    icon = "🟡"
                else:
                    icon = "🔵"
                
                self.console.print(f"\n{icon} [cyan]{rec.get('category', 'General')}[/cyan]")
                self.console.print(f"   {rec.get('recommendation', '')}")
                
                if "benefit" in rec:
                    self.console.print(f"   ✓ Benefit: {rec['benefit']}")
                
                if "config" in rec:
                    self.console.print(f"   [dim]Config: {rec['config']}[/dim]")
