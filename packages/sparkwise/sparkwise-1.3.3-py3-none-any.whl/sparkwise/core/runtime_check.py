"""
Runtime configuration tuning checker.

Validates runtime settings for:
- Adaptive Query Execution (AQE)
- Partition sizing
- Scheduler mode
- Speculation
- Memory configurations
"""

from typing import Dict, Any
from pyspark.sql import SparkSession


class RuntimeTuningChecker:
    """Checks runtime configuration for optimal performance."""
    
    def __init__(self, spark: SparkSession) -> None:
        """Initialize with SparkSession."""
        self.spark = spark
        self.conf = spark.conf
    
    def check(self) -> Dict[str, Any]:
        """
        Check runtime tuning configurations.
        
        Returns:
            Dictionary with runtime check results
        """
        result = {
            "aqe_enabled": False,
            "partition_size_optimal": False,
            "issues": [],
            "recommendations": [],
            "critical_count": 0,
            "recommendation_count": 0
        }
        
        # Check 1: Adaptive Query Execution (CRITICAL)
        aqe_result = self._check_aqe()
        result["aqe_enabled"] = aqe_result["enabled"]
        
        if not aqe_result["enabled"]:
            result["issues"].append({
                "severity": "critical",
                "message": "Adaptive Query Execution (AQE) is DISABLED"
            })
            result["recommendations"].append({
                "config": "spark.sql.adaptive.enabled",
                "action": "Set to 'true'",
                "impact": "Enable dynamic partition coalescing and skew join optimization",
                "priority": "critical"
            })
            result["critical_count"] += 1
            result["recommendation_count"] += 1
            
            print("⛔ CRITICAL: Adaptive Query Execution (AQE) is DISABLED")
            print("   💡 Enable immediately: spark.sql.adaptive.enabled=true")
            print("      Benefits: Dynamic coalescing, skew joins, better parallelism")
        else:
            print("✅ Adaptive Query Execution (AQE) is ACTIVE")
            
            # Check AQE sub-features
            if not aqe_result.get("coalesce_partitions", False):
                result["recommendations"].append({
                    "config": "spark.sql.adaptive.coalescePartitions.enabled",
                    "action": "Set to 'true'",
                    "impact": "Reduce shuffle partition count dynamically",
                    "priority": "medium"
                })
                result["recommendation_count"] += 1
                print("   ℹ️ Enable partition coalescing for better performance")
        
        # Check 2: Partition sizing
        partition_result = self._check_partition_sizing()
        result["partition_size_optimal"] = partition_result["optimal"]
        
        if not partition_result["optimal"]:
            result["recommendations"].extend(partition_result["recommendations"])
            result["recommendation_count"] += len(partition_result["recommendations"])
        
        # Check 3: Shuffle partitions
        shuffle_result = self._check_shuffle_partitions()
        if shuffle_result["recommendations"]:
            result["recommendations"].extend(shuffle_result["recommendations"])
            result["recommendation_count"] += len(shuffle_result["recommendations"])
        
        # Check 4: Scheduler mode
        scheduler_result = self._check_scheduler_mode()
        if scheduler_result["recommendations"]:
            result["recommendations"].extend(scheduler_result["recommendations"])
            result["recommendation_count"] += len(scheduler_result["recommendations"])
        
        # Check 5: Speculation
        speculation_result = self._check_speculation()
        if speculation_result["warnings"]:
            result["recommendations"].extend(speculation_result["warnings"])
            result["recommendation_count"] += len(speculation_result["warnings"])
        
        return result
    
    def _check_aqe(self) -> Dict[str, Any]:
        """Check Adaptive Query Execution settings."""
        try:
            aqe_enabled = self.conf.get("spark.sql.adaptive.enabled", "false")
            coalesce = self.conf.get("spark.sql.adaptive.coalescePartitions.enabled", "false")
            skew_join = self.conf.get("spark.sql.adaptive.skewJoin.enabled", "false")
            
            return {
                "enabled": aqe_enabled.lower() == "true",
                "coalesce_partitions": coalesce.lower() == "true",
                "skew_join": skew_join.lower() == "true"
            }
        except Exception:
            return {"enabled": False}
    
    def _check_partition_sizing(self) -> Dict[str, Any]:
        """Check if partition sizes are appropriate for the cluster."""
        result = {
            "optimal": True,
            "recommendations": []
        }
        
        try:
            # Get partition size setting
            partition_bytes = self.conf.get("spark.sql.files.maxPartitionBytes", "134217728")
            partition_mb = int(partition_bytes) / (1024 * 1024)
            
            # Get executor memory
            executor_memory = self.conf.get("spark.executor.memory", "4g")
            memory_gb = int(''.join(filter(str.isdigit, executor_memory)))
            
            # Heuristic: Large executors should use larger partitions
            if memory_gb >= 32 and partition_mb < 256:
                result["optimal"] = False
                result["recommendations"].append({
                    "config": "spark.sql.files.maxPartitionBytes",
                    "action": f"Increase from {partition_mb:.0f}MB to 256-512MB",
                    "impact": "Reduce task overhead for large-memory executors",
                    "priority": "low",
                    "detail": f"Your executors have {memory_gb}GB RAM but use {partition_mb:.0f}MB partitions"
                })
                
                print(f"   ℹ️ Partition size: {partition_mb:.0f}MB (small for {memory_gb}GB executors)")
                print("      Consider increasing to 256-512MB for better throughput")
            else:
                print(f"✅ Partition sizing is appropriate ({partition_mb:.0f}MB)")
        
        except Exception as e:
            pass
        
        return result
    
    def _check_shuffle_partitions(self) -> Dict[str, Any]:
        """Check shuffle partition configuration."""
        result = {"recommendations": []}
        
        try:
            shuffle_partitions = int(self.conf.get("spark.sql.shuffle.partitions", "200"))
            
            # Get cluster size
            executor_count = len(self.spark.sparkContext.statusTracker().getExecutorInfos()) - 1
            executor_cores = int(self.conf.get("spark.executor.cores", "4"))
            total_cores = executor_count * executor_cores
            
            # Heuristic: shuffle partitions should be 2-3x total cores
            optimal_min = total_cores * 2
            optimal_max = total_cores * 4
            
            if shuffle_partitions < optimal_min:
                result["recommendations"].append({
                    "config": "spark.sql.shuffle.partitions",
                    "action": f"Increase from {shuffle_partitions} to {optimal_min}-{optimal_max}",
                    "impact": "Better parallelism for shuffles",
                    "priority": "medium",
                    "detail": f"Current: {shuffle_partitions}, Optimal range: {optimal_min}-{optimal_max} (based on {total_cores} cores)"
                })
                
                print(f"   ℹ️ Shuffle partitions: {shuffle_partitions} (low for {total_cores} cores)")
                print(f"      Recommended: {optimal_min}-{optimal_max}")
            elif shuffle_partitions > optimal_max * 2:
                result["recommendations"].append({
                    "config": "spark.sql.shuffle.partitions",
                    "action": f"Decrease from {shuffle_partitions} to {optimal_min}-{optimal_max}",
                    "impact": "Reduce scheduling overhead",
                    "priority": "low",
                    "detail": f"Too many partitions for cluster size ({total_cores} cores)"
                })
                
                print(f"   ℹ️ Shuffle partitions: {shuffle_partitions} (high for {total_cores} cores)")
                print(f"      Recommended: {optimal_min}-{optimal_max}")
            else:
                print(f"✅ Shuffle partitions configured appropriately ({shuffle_partitions})")
        
        except Exception as e:
            pass
        
        return result
    
    def _check_scheduler_mode(self) -> Dict[str, Any]:
        """Check scheduler mode setting."""
        result = {"recommendations": []}
        
        try:
            scheduler_mode = self.conf.get("spark.scheduler.mode", "FIFO")
            
            if scheduler_mode == "FIFO":
                result["recommendations"].append({
                    "config": "spark.scheduler.mode",
                    "action": "Consider 'FAIR' for interactive workloads",
                    "impact": "Better responsiveness when running multiple queries",
                    "priority": "low",
                    "note": "Only change if running concurrent queries in same session"
                })
                
                print(f"   ℹ️ Scheduler: {scheduler_mode} (default)")
                print("      Consider FAIR mode for interactive/concurrent queries")
            else:
                print(f"✅ Scheduler mode: {scheduler_mode}")
        
        except Exception:
            pass
        
        return result
    
    def _check_speculation(self) -> Dict[str, Any]:
        """Check speculation settings."""
        result = {"warnings": []}
        
        try:
            speculation = self.conf.get("spark.speculation", "false")
            native_enabled = self.conf.get("spark.native.enabled", "false")
            
            if speculation.lower() == "true" and native_enabled.lower() == "true":
                result["warnings"].append({
                    "config": "spark.speculation",
                    "action": "Review if speculation is needed with Native Execution",
                    "impact": "Speculation may cause duplicate expensive Velox operations",
                    "priority": "low",
                    "note": "Only enable speculation if you have frequent stragglers"
                })
                
                print("   ℹ️ Speculation enabled with Native Execution")
                print("      Monitor for duplicate expensive operations")
        
        except Exception:
            pass
        
        return result
