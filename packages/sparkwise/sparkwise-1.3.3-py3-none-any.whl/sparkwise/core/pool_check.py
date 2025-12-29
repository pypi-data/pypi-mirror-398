"""
Pooling strategy analysis module.

Determines if workload can fit in Starter Pool vs Custom Pool
to optimize for startup time and cost.
"""

from typing import Dict, Any
from pyspark.sql import SparkSession


class PoolingChecker:
    """Analyzes pooling strategy for Fabric Spark workloads."""
    
    # Fabric Starter Pool limits (approximate)
    STARTER_POOL_LIMITS = {
        "F2": {"max_nodes": 1, "max_vcores": 2},
        "F4": {"max_nodes": 1, "max_vcores": 4},
        "F8": {"max_nodes": 2, "max_vcores": 8},
        "F16": {"max_nodes": 4, "max_vcores": 16},
        "F32": {"max_nodes": 8, "max_vcores": 32},
        "F64": {"max_nodes": 12, "max_vcores": 64},
        "F128": {"max_nodes": 24, "max_vcores": 128}
    }
    
    # Threshold for recommending Starter Pool
    STARTER_POOL_NODE_THRESHOLD = 12
    
    # Session-immutable configs that force Custom Pool
    # These are common configs users accidentally set
    IMMUTABLE_CONFIGS = {
        "spark.executor.cores",
        "spark.executor.memory",
        "spark.executor.instances",
        "spark.driver.memory",
        "spark.driver.cores",
        "spark.dynamicAllocation.enabled",
        "spark.dynamicAllocation.minExecutors",
        "spark.dynamicAllocation.maxExecutors",
        "spark.serializer",
        "spark.master",
        "spark.app.name",
        "spark.local.dir",
        "spark.cores.max",
        "spark.memory.fraction",
        "spark.memory.storageFraction",
        "spark.sql.shuffle.partitions",  # If explicitly set at session start
    }
    
    def __init__(self, spark: SparkSession) -> None:
        """Initialize with SparkSession."""
        self.spark = spark
        self.sc = spark.sparkContext
        self.conf = spark.conf
    
    def check(self) -> Dict[str, Any]:
        """
        Check pooling strategy and provide recommendations.
        
        Returns:
            Dictionary with pooling analysis results
        """
        result = {
            "executor_count": 0,
            "pool_type": "unknown",
            "can_use_starter": False,
            "startup_savings": None,
            "immutable_configs_set": [],
            "issues": [],
            "recommendations": [],
            "critical_count": 0,
            "recommendation_count": 0
        }
        
        # CRITICAL: Check for immutable configs that force Custom Pool
        self._check_immutable_configs(result)
        
        # Get executor count
        executor_count = self._get_executor_count()
        result["executor_count"] = executor_count
        
        # Determine current pool type (heuristic)
        pool_type = self._detect_pool_type()
        result["pool_type"] = pool_type
        
        # Check if workload fits in Starter Pool
        if executor_count <= self.STARTER_POOL_NODE_THRESHOLD:
            result["can_use_starter"] = True
            result["startup_savings"] = "3-5 minutes"
            
            print(f"✅ Your job uses {executor_count} executors - fits in Starter Pool")
            
            if pool_type == "custom":
                result["issues"].append({
                    "severity": "warning",
                    "message": f"Using Custom Pool for small workload ({executor_count} nodes)"
                })
                result["recommendations"].append({
                    "action": "Switch to Starter Pool",
                    "impact": "Save 3-5 minutes of cold-start time per run",
                    "priority": "medium",
                    "how": "In Fabric workspace settings, select 'Starter Pool' instead of Custom Pool"
                })
                result["recommendation_count"] += 1
                
                print("   💡 [Optimization] Switch to Starter Pool to eliminate cold-start delays")
                print("      Savings: ~3-5 minutes per job run")
            else:
                print("   💡 Ensure 'Starter Pool' is selected in workspace settings")
        else:
            result["can_use_starter"] = False
            print(f"ℹ️ Large workload detected ({executor_count} executors)")
            print("   Custom Pool is appropriate for this scale")
            
            # Check if the pool size is appropriately configured
            self._check_pool_sizing(result, executor_count)
        
        # Check for over-provisioning patterns
        self._check_overprovisioning(result, executor_count)
        
        return result
    
    def _check_immutable_configs(self, result: Dict[str, Any]) -> None:
        """
        Check if user has set any session-immutable configs.
        
        These configs force Custom Pool usage even if workload is small.
        """
        immutable_set = []
        
        try:
            # Get all Spark configurations
            all_configs = dict(self.conf.getAll())
            
            # Check which immutable configs are set
            for config in self.IMMUTABLE_CONFIGS:
                if config in all_configs:
                    # Check if it differs from default (heuristic)
                    value = all_configs[config]
                    immutable_set.append({"config": config, "value": value})
            
            if immutable_set:
                result["immutable_configs_set"] = immutable_set
                result["issues"].append({
                    "severity": "critical",
                    "message": f"⚠️ CRITICAL: {len(immutable_set)} session-immutable config(s) detected"
                })
                result["critical_count"] += 1
                
                print("\n🔴 CRITICAL: Session-Immutable Configs Detected")
                print("=" * 70)
                print("The following configs FORCE Custom Pool usage (3-5min cold-start):")
                print()
                
                for item in immutable_set[:5]:  # Show first 5
                    print(f"   • {item['config']} = {item['value']}")
                
                if len(immutable_set) > 5:
                    print(f"   ... and {len(immutable_set) - 5} more")
                
                print()
                print("💡 Impact:")
                print("   ❌ Cannot use Starter Pool (instant startup)")
                print("   ❌ Forced to Custom Pool (3-5 minute cold-start)")
                print("   ❌ Additional capacity consumption")
                print()
                print("✅ Solution:")
                print("   1. Remove these spark.conf.set() calls from your notebook")
                print("   2. Use Starter Pool defaults (auto-configured by Fabric)")
                print("   3. Only set these if you truly need Custom Pool")
                print()
                print("   Learn more: sparkwise.ask.config('fabric.starter.pool.immutable.configs')")
                print("=" * 70)
                
                result["recommendations"].append({
                    "action": "Remove session-immutable config settings",
                    "impact": "Enable Starter Pool for 3-5min faster startup",
                    "priority": "critical",
                    "configs_to_remove": [item["config"] for item in immutable_set]
                })
                result["recommendation_count"] += 1
                
        except Exception as e:
            # Silent failure - this is best-effort detection
            pass
    
    def _get_executor_count(self) -> int:
        """Get the number of active executors."""
        try:
            # Try to get executor count from status tracker
            executor_infos = self.sc.statusTracker().getExecutorInfos()
            # Subtract 1 for driver
            return max(0, len(executor_infos) - 1)
        except Exception:
            # Fallback to default parallelism / cores per executor
            try:
                parallelism = self.sc.defaultParallelism
                cores_per_exec = int(self.conf.get("spark.executor.cores", "4"))
                return max(1, parallelism // cores_per_exec)
            except Exception:
                return 0
    
    def _detect_pool_type(self) -> str:
        """Detect if using Starter or Custom Pool (heuristic)."""
        try:
            # Check for Fabric-specific configuration hints
            pool_name = self.conf.get("spark.fabric.pool.name", "")
            
            if "starter" in pool_name.lower():
                return "starter"
            elif "custom" in pool_name.lower():
                return "custom"
            
            # Heuristic: Check if pool was recently started
            # (Custom pools have longer startup times)
            # This is a simplified check
            return "unknown"
        except Exception:
            return "unknown"
    
    def _check_pool_sizing(self, result: Dict[str, Any], executor_count: int) -> None:
        """Check if Custom Pool is appropriately sized."""
        try:
            # Get configured vs actual executors
            max_executors = self.conf.get("spark.dynamicAllocation.maxExecutors", None)
            
            if max_executors:
                max_executors = int(max_executors)
                if executor_count < max_executors * 0.3:  # Using < 30% of capacity
                    result["recommendations"].append({
                        "action": f"Reduce maxExecutors from {max_executors} to ~{executor_count * 2}",
                        "impact": "Reduce cost by right-sizing Custom Pool",
                        "priority": "low"
                    })
                    result["recommendation_count"] += 1
                    
                    print(f"   ℹ️ Pool capacity: {max_executors} executors, using only {executor_count}")
                    print("      Consider reducing max capacity to optimize cost")
        except Exception:
            pass
    
    def _check_overprovisioning(self, result: Dict[str, Any], executor_count: int) -> None:
        """Detect potential over-provisioning patterns."""
        try:
            # Check executor memory vs typical workload
            executor_memory = self.conf.get("spark.executor.memory", "4g")
            
            # Parse memory (simplified)
            memory_gb = int(''.join(filter(str.isdigit, executor_memory)))
            
            # If using very large executors (>32GB) with small node count
            if memory_gb > 32 and executor_count <= 4:
                result["recommendations"].append({
                    "action": "Consider using more executors with less memory each",
                    "impact": "Better parallelism and resource utilization",
                    "priority": "low",
                    "detail": f"Current: {executor_count} × {memory_gb}GB"
                })
                result["recommendation_count"] += 1
        except Exception:
            pass
