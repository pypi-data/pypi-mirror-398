"""
Spark Session Profiler

Analyzes current Spark session configuration, resources, and runtime information.
"""

from typing import Dict, Any, Optional
from pyspark.sql import SparkSession
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime


class SessionProfiler:
    """
    Profiles the current Spark session configuration and runtime state.
    
    Provides insights into:
    - Application metadata (name, ID, user)
    - Spark version and runtime info
    - Driver and executor configuration
    - Memory allocation breakdown
    - Key configuration settings
    - Session uptime and state
    """
    
    def __init__(self, spark: Optional[SparkSession] = None) -> None:
        """
        Initialize the session profiler.
        
        Args:
            spark: SparkSession instance. If None, uses active session.
        """
        self.spark = spark or SparkSession.builder.getOrCreate()
        self.sc = self.spark.sparkContext
        self.conf = self.spark.conf
        self.console = Console()
    
    def profile(self, export_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Profile the current Spark session and display results.
        
        Args:
            export_path: Optional path to export profile as JSON
            
        Returns:
            Dictionary containing session profile data
        """
        profile_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "application": self._get_application_info(),
            "resources": self._get_resource_info(),
            "memory": self._get_memory_breakdown(),
            "configurations": self._get_key_configs(),
            "runtime": self._get_runtime_info()
        }
        
        # Display profile
        self._display_profile(profile_data)
        
        # Export if requested
        if export_path:
            self._export_profile(profile_data, export_path)
        
        return profile_data
    
    def _get_application_info(self) -> Dict[str, Any]:
        """Get application metadata."""
        try:
            return {
                "name": self.sc.appName,
                "id": self.sc.applicationId,
                "user": self.sc.sparkUser(),
                "spark_version": self.sc.version,
                "master": self.sc.master,
                "deploy_mode": self.conf.get("spark.submit.deployMode", "client")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_resource_info(self) -> Dict[str, Any]:
        """Get driver and executor resource configuration."""
        try:
            return {
                "driver": {
                    "memory": self.conf.get("spark.driver.memory", "N/A"),
                    "cores": self.conf.get("spark.driver.cores", "N/A"),
                    "max_result_size": self.conf.get("spark.driver.maxResultSize", "1g")
                },
                "executor": {
                    "instances": self.conf.get("spark.executor.instances", "dynamic"),
                    "memory": self.conf.get("spark.executor.memory", "N/A"),
                    "cores": self.conf.get("spark.executor.cores", "N/A"),
                    "memory_overhead": self.conf.get("spark.executor.memoryOverhead", "auto"),
                    "off_heap_memory": self.conf.get("spark.memory.offHeap.size", "0")
                },
                "dynamic_allocation": {
                    "enabled": self.conf.get("spark.dynamicAllocation.enabled", "false"),
                    "min_executors": self.conf.get("spark.dynamicAllocation.minExecutors", "0"),
                    "max_executors": self.conf.get("spark.dynamicAllocation.maxExecutors", "infinity"),
                    "initial_executors": self.conf.get("spark.dynamicAllocation.initialExecutors", "min")
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_memory_breakdown(self) -> Dict[str, Any]:
        """Get memory allocation breakdown."""
        try:
            executor_memory = self.conf.get("spark.executor.memory", "1g")
            
            # Parse memory value
            mem_value = executor_memory.lower().replace("g", "").replace("m", "").replace("k", "")
            try:
                mem_gb = float(mem_value)
                if "m" in executor_memory.lower():
                    mem_gb = mem_gb / 1024
                elif "k" in executor_memory.lower():
                    mem_gb = mem_gb / (1024 * 1024)
            except:
                mem_gb = 0
            
            # Calculate memory fractions
            storage_fraction = float(self.conf.get("spark.memory.storageFraction", "0.5"))
            memory_fraction = float(self.conf.get("spark.memory.fraction", "0.6"))
            
            return {
                "total_executor_memory": executor_memory,
                "memory_fraction": memory_fraction,
                "storage_fraction": storage_fraction,
                "estimated_breakdown": {
                    "execution_memory": f"{mem_gb * memory_fraction * (1 - storage_fraction):.2f}GB",
                    "storage_memory": f"{mem_gb * memory_fraction * storage_fraction:.2f}GB",
                    "user_memory": f"{mem_gb * (1 - memory_fraction):.2f}GB"
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_key_configs(self) -> Dict[str, str]:
        """Get important configuration settings."""
        key_configs = {
            "spark.sql.adaptive.enabled": "AQE Status",
            "spark.sql.shuffle.partitions": "Shuffle Partitions",
            "spark.sql.files.maxPartitionBytes": "Max Partition Bytes",
            "spark.native.enabled": "Native Execution (Velox)",
            "spark.sql.parquet.vorder.enabled": "V-Order (Fabric)",
            "spark.databricks.delta.optimizeWrite.enabled": "Delta Optimize Write",
            "spark.serializer": "Serializer",
            "spark.locality.wait": "Locality Wait",
            "spark.speculation": "Speculation"
        }
        
        configs = {}
        for config_key, display_name in key_configs.items():
            try:
                value = self.conf.get(config_key, "not set")
                configs[display_name] = value
            except:
                configs[display_name] = "not set"
        
        return configs
    
    def _get_runtime_info(self) -> Dict[str, Any]:
        """Get runtime information."""
        try:
            # Get status tracker for metrics
            status_tracker = self.sc.statusTracker()
            
            return {
                "default_parallelism": self.sc.defaultParallelism,
                "default_min_partitions": self.sc.defaultMinPartitions,
                "is_stopped": self.sc._jsc.sc().isStopped() if hasattr(self.sc, '_jsc') else False,
                "pool_name": self.conf.get("spark.fabric.pool.name", "N/A")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _display_profile(self, profile_data: Dict[str, Any]) -> None:
        """Display session profile in formatted tables."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold cyan]📊 Spark Session Profile[/bold cyan]\n"
            f"[dim]{profile_data['timestamp']}[/dim]",
            border_style="cyan"
        ))
        
        # Application Info
        app_info = profile_data.get("application", {})
        if "error" not in app_info:
            self.console.print("\n[bold]🔷 Application Information[/bold]")
            app_table = Table(show_header=False, box=None)
            app_table.add_column("Property", style="cyan")
            app_table.add_column("Value")
            
            app_table.add_row("Application Name", app_info.get("name", "N/A"))
            app_table.add_row("Application ID", app_info.get("id", "N/A"))
            app_table.add_row("User", app_info.get("user", "N/A"))
            app_table.add_row("Spark Version", app_info.get("spark_version", "N/A"))
            app_table.add_row("Master", app_info.get("master", "N/A"))
            app_table.add_row("Deploy Mode", app_info.get("deploy_mode", "N/A"))
            
            self.console.print(app_table)
        
        # Resource Info
        resources = profile_data.get("resources", {})
        if "error" not in resources:
            self.console.print("\n[bold]💎 Resource Configuration[/bold]")
            
            # Driver resources
            driver = resources.get("driver", {})
            self.console.print("\n[cyan]Driver:[/cyan]")
            self.console.print(f"  Memory: {driver.get('memory', 'N/A')}")
            self.console.print(f"  Cores: {driver.get('cores', 'N/A')}")
            self.console.print(f"  Max Result Size: {driver.get('max_result_size', 'N/A')}")
            
            # Executor resources
            executor = resources.get("executor", {})
            self.console.print("\n[cyan]Executor:[/cyan]")
            self.console.print(f"  Instances: {executor.get('instances', 'N/A')}")
            self.console.print(f"  Memory: {executor.get('memory', 'N/A')}")
            self.console.print(f"  Cores: {executor.get('cores', 'N/A')}")
            self.console.print(f"  Memory Overhead: {executor.get('memory_overhead', 'N/A')}")
            self.console.print(f"  Off-Heap Memory: {executor.get('off_heap_memory', 'N/A')}")
            
            # Dynamic allocation
            dynamic = resources.get("dynamic_allocation", {})
            self.console.print("\n[cyan]Dynamic Allocation:[/cyan]")
            self.console.print(f"  Enabled: {dynamic.get('enabled', 'N/A')}")
            if dynamic.get('enabled', 'false').lower() == 'true':
                self.console.print(f"  Min Executors: {dynamic.get('min_executors', 'N/A')}")
                self.console.print(f"  Max Executors: {dynamic.get('max_executors', 'N/A')}")
                self.console.print(f"  Initial Executors: {dynamic.get('initial_executors', 'N/A')}")
        
        # Memory Breakdown
        memory = profile_data.get("memory", {})
        if "error" not in memory:
            self.console.print("\n[bold]🧠 Memory Allocation Breakdown[/bold]")
            mem_table = Table(show_header=True, header_style="bold magenta")
            mem_table.add_column("Memory Type", style="cyan")
            mem_table.add_column("Allocation")
            mem_table.add_column("Description")
            
            breakdown = memory.get("estimated_breakdown", {})
            mem_table.add_row(
                "Execution Memory",
                breakdown.get("execution_memory", "N/A"),
                "For shuffles, joins, sorts, aggregations"
            )
            mem_table.add_row(
                "Storage Memory",
                breakdown.get("storage_memory", "N/A"),
                "For caching RDDs/DataFrames"
            )
            mem_table.add_row(
                "User Memory",
                breakdown.get("user_memory", "N/A"),
                "For user data structures and UDFs"
            )
            
            self.console.print(mem_table)
            self.console.print(f"\n[dim]Total Executor Memory: {memory.get('total_executor_memory', 'N/A')}[/dim]")
            self.console.print(f"[dim]Memory Fraction: {memory.get('memory_fraction', 'N/A')} | Storage Fraction: {memory.get('storage_fraction', 'N/A')}[/dim]")
        
        # Key Configurations
        configs = profile_data.get("configurations", {})
        if configs:
            self.console.print("\n[bold]⚙️ Key Configuration Settings[/bold]")
            config_table = Table(show_header=True, header_style="bold magenta")
            config_table.add_column("Configuration", style="cyan")
            config_table.add_column("Value")
            
            for config_name, value in configs.items():
                # Highlight important values
                if value == "true":
                    value_str = "[green]✓ enabled[/green]"
                elif value == "false":
                    value_str = "[yellow]✗ disabled[/yellow]"
                elif value == "not set":
                    value_str = "[dim]not set[/dim]"
                else:
                    value_str = value
                
                config_table.add_row(config_name, value_str)
            
            self.console.print(config_table)
        
        # Runtime Info
        runtime = profile_data.get("runtime", {})
        if "error" not in runtime:
            self.console.print("\n[bold]⚡ Runtime Information[/bold]")
            self.console.print(f"  Default Parallelism: {runtime.get('default_parallelism', 'N/A')}")
            self.console.print(f"  Default Min Partitions: {runtime.get('default_min_partitions', 'N/A')}")
            
            pool_name = runtime.get('pool_name', 'N/A')
            if pool_name != 'N/A':
                if 'starter' in pool_name.lower():
                    pool_str = f"[green]{pool_name}[/green] (instant startup)"
                else:
                    pool_str = f"[yellow]{pool_name}[/yellow] (3-5min cold start)"
                self.console.print(f"  Fabric Pool: {pool_str}")
    
    def _export_profile(self, profile_data: Dict[str, Any], path: str) -> None:
        """Export profile data to JSON file."""
        import json
        
        with open(path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        self.console.print(f"\n💾 Profile exported to: {path}")
