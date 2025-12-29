"""
Main Fabric Advisor class - orchestrates all diagnostic checks.
"""

from typing import Optional, Dict, Any
from pyspark.sql import SparkSession, DataFrame
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sparkwise.core.native_check import NativeExecutionChecker
from sparkwise.core.pool_check import PoolingChecker
from sparkwise.core.skew_check import SkewDetector
from sparkwise.core.delta_check import DeltaOptimizationChecker
from sparkwise.core.runtime_check import RuntimeTuningChecker


class FabricAdvisor:
    """
    The main diagnostic engine for Fabric Spark workloads.
    
    Performs comprehensive analysis of:
    - Native Execution Engine compliance
    - Pooling strategy efficiency
    - Data skew detection
    - Delta/Storage optimizations
    - Runtime configuration tuning
    - Resource allocation balance
    """
    
    def __init__(self) -> None:
        """Initialize the Fabric Advisor with current SparkSession."""
        try:
            self.spark = SparkSession.builder.getOrCreate()
            self.sc = self.spark.sparkContext
            self.conf = self.spark.conf
            self.console = Console()
            
            # Initialize all checker modules
            self.native_checker = NativeExecutionChecker(self.spark)
            self.pool_checker = PoolingChecker(self.spark)
            self.skew_detector = SkewDetector(self.spark)
            self.delta_checker = DeltaOptimizationChecker(self.spark)
            self.runtime_checker = RuntimeTuningChecker(self.spark)
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize sparkwise: {e}")
    
    def analyze_last_run(self, export_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the last Spark run and provide optimization recommendations.
        
        Args:
            export_path: Optional path to export the analysis report as JSON
            
        Returns:
            Dictionary containing analysis results from all modules
        """
        return self.analyze(df=None, export_path=export_path)
    
    def analyze(
        self, 
        df: Optional[DataFrame] = None, 
        export_path: Optional[str] = None,
        return_dict: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Run comprehensive Fabric Spark analysis.
        
        Args:
            df: Optional DataFrame for deep query plan analysis
            export_path: Optional path to export the analysis report
            return_dict: If True, return results dictionary; if False (default), return None
            
        Returns:
            Dictionary containing all analysis results if return_dict=True, otherwise None
        """
        self.console.print("\n")
        self.console.print(
            Panel.fit(
                "🔥 [bold cyan]sparkwise Analysis[/bold cyan] 🔥",
                border_style="cyan"
            )
        )
        
        results = {}
        
        # Run all diagnostic checks
        results["native_execution"] = self._run_check(
            "🔎 Native Execution Engine",
            lambda: self.native_checker.check(df)
        )
        
        results["pooling"] = self._run_check(
            "⚡ Spark Compute",
            lambda: self.pool_checker.check()
        )
        
        results["skew"] = self._run_check(
            "📊 Data Skew Detection",
            lambda: self.skew_detector.check()
        )
        
        results["delta"] = self._run_check(
            "💾 Storage & Delta Optimizations",
            lambda: self.delta_checker.check()
        )
        
        results["runtime"] = self._run_check(
            "⚙️ Runtime Tuning",
            lambda: self.runtime_checker.check()
        )
        
        # Print summary
        self._print_summary(results)
        
        # Print formatted recommendations table
        self._print_recommendations_table(results)
        
        # Export if requested
        if export_path:
            self._export_results(results, export_path)
        
        self.console.print("\n✨ [bold green]Analysis complete![/bold green]\n")
        
        # Only return dict if explicitly requested
        # Returning None suppresses notebook output completely
        if return_dict:
            return results
        
        # Suppress IPython/Jupyter auto-display by returning None
        try:
            # If in IPython/Jupyter, suppress the Out[X] display
            from IPython.display import clear_output
            pass  # We don't clear, just detect we're in IPython
        except ImportError:
            pass
        
        return None
    
    def _run_check(self, title: str, check_func: callable) -> Dict[str, Any]:
        """
        Run a diagnostic check and handle errors gracefully.
        
        Args:
            title: Display title for the check
            check_func: Function to execute for the check
            
        Returns:
            Results dictionary from the check
        """
        self.console.print(f"\n[bold]{title}[/bold]")
        self.console.print("─" * 60)
        
        try:
            result = check_func()
            return result
        except Exception as e:
            self.console.print(f"[red]Error during {title}: {str(e)}[/red]")
            return {"status": "error", "message": str(e)}
    
    def _print_summary(self, results: Dict[str, Any]) -> None:
        """Print a summary table of all findings."""
        self.console.print("\n")
        self.console.print("[bold cyan]📋 Summary of Findings[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Critical Issues", justify="center")
        table.add_column("Recommendations", justify="center")
        
        for category, result in results.items():
            if result.get("status") == "error":
                table.add_row(
                    category.replace("_", " ").title(),
                    "❌ Error",
                    "-",
                    "-"
                )
            else:
                critical = result.get("critical_count", 0)
                recommendations = result.get("recommendation_count", 0)
                
                status = "✅ Good" if critical == 0 else f"⚠️ Issues"
                
                table.add_row(
                    category.replace("_", " ").title(),
                    status,
                    str(critical),
                    str(recommendations)
                )
        
        self.console.print(table)
        
        # Print detailed recommendations table
        self._print_recommendations_table(results)
    
    def _print_recommendations_table(self, results: Dict[str, Any]) -> None:
        """Print detailed configuration recommendations in a formatted table."""
        all_recommendations = []
        
        # Collect all recommendations from all checks
        for category, result in results.items():
            if result.get("status") == "error":
                continue
                
            recommendations = result.get("recommendations", [])
            for rec in recommendations:
                all_recommendations.append({
                    "category": category.replace("_", " ").title(),
                    "config": rec.get("config", "N/A"),
                    "action": rec.get("action", "N/A"),
                    "impact": rec.get("impact", "N/A"),
                    "priority": rec.get("priority", "medium"),
                    "detail": rec.get("detail", "")
                })
        
        if not all_recommendations:
            self.console.print("\n✅ [bold green]No configuration changes recommended - your setup is optimal![/bold green]")
            return
        
        # Sort by priority: critical > high > medium > low
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_recommendations.sort(key=lambda x: priority_order.get(x["priority"], 2))
        
        self.console.print("\n")
        self.console.print("[bold cyan]🔧 Configuration Recommendations[/bold cyan]")
        self.console.print(f"[dim]Total recommendations: {len(all_recommendations)}[/dim]\n")
        
        # Create table without fixed widths to auto-fit content
        table = Table(show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("Priority", style="bold", no_wrap=True)
        table.add_column("Configuration", style="cyan")
        table.add_column("Recommended Action")
        table.add_column("Impact & Details")
        
        for rec in all_recommendations:
            # Color priority based on severity
            priority = rec["priority"].upper()
            if rec["priority"] == "critical":
                priority_str = f"[red bold]{priority}[/red bold]"
            elif rec["priority"] == "high":
                priority_str = f"[yellow bold]{priority}[/yellow bold]"
            elif rec["priority"] == "medium":
                priority_str = f"[blue]{priority}[/blue]"
            else:
                priority_str = f"[dim]{priority}[/dim]"
            
            # Add detail if available
            impact_text = rec["impact"]
            if rec.get("detail"):
                impact_text += f"\n[dim]└─ {rec['detail']}[/dim]"
            
            table.add_row(
                priority_str,
                rec["config"],
                rec["action"],
                impact_text
            )
        
        self.console.print(table)
    
    def _export_results(self, results: Dict[str, Any], path: str) -> None:
        """Export analysis results to JSON file."""
        import json
        from datetime import datetime
        
        export_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "spark_version": self.spark.version,
            "user": self.sc.sparkUser(),
            "results": results
        }
        
        with open(path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.console.print(f"\n💾 Results exported to: {path}")
    
    def quick_check(self) -> None:
        """
        Run a quick health check (native execution + pooling only).
        Useful for fast validation during development.
        """
        self.console.print("\n[bold]⚡ Quick Health Check[/bold]\n")
        
        native_result = self.native_checker.check()
        pool_result = self.pool_checker.check()
        
        if native_result.get("critical_count", 0) == 0 and pool_result.get("critical_count", 0) == 0:
            self.console.print("[bold green]✅ All systems optimal![/bold green]\n")
        else:
            self.console.print("[yellow]⚠️ Some optimizations available. Run full analysis for details.[/yellow]\n")
