"""
Delta Lake and storage optimization checker.

Verifies optimal configurations for:
- V-Order (Fabric-specific Parquet optimization)
- Deletion Vectors (efficient MERGE operations)
- Optimize Write (small file prevention)
- Auto Compaction
"""

from typing import Dict, Any
from pyspark.sql import SparkSession


class DeltaOptimizationChecker:
    """Checks Delta Lake and storage optimizations for Fabric."""
    
    def __init__(self, spark: SparkSession) -> None:
        """Initialize with SparkSession."""
        self.spark = spark
        self.conf = spark.conf
    
    def check(self) -> Dict[str, Any]:
        """
        Check Delta and storage optimization settings.
        
        Returns:
            Dictionary with optimization check results
        """
        result = {
            "v_order_enabled": False,
            "deletion_vectors_enabled": False,
            "optimize_write_enabled": False,
            "optimize_write_bin_size": None,
            "optimize_write_partitioned": False,
            "driver_mode_snapshot": False,
            "fast_optimize": False,
            "adaptive_file_size": False,
            "file_level_target": False,
            "issues": [],
            "recommendations": [],
            "critical_count": 0,
            "recommendation_count": 0
        }
        
        # Check 1: V-Order (Critical for Fabric)
        v_order = self._check_v_order()
        result["v_order_enabled"] = v_order
        
        if not v_order:
            # Context-aware V-Order messaging
            result["recommendations"].append({
                "config": "spark.sql.parquet.vorder.enabled",
                "action": "Enable for read-heavy workloads only",
                "impact": "3-10x faster reads for Power BI/Direct Lake. 15-20% slower writes if enabled.",
                "priority": "medium",
                "fabric_specific": True
            })
            result["recommendation_count"] += 1
            
            print("ℹ️ V-Order is DISABLED (optimal for write-heavy workloads)")
            print("   Benefit: 2x faster writes vs V-Order enabled")
            print("   💡 Enable only for read-heavy workloads (Power BI/analytics)")
            print("      Trade-off: 3-10x faster reads, but 15-20% slower writes")
        else:
            print("✅ V-Order is ENABLED - optimized for Power BI/Direct Lake")
            print("   Note: Adds 15-20% write overhead. Use writeHeavy profile if needed")
        
        # Check 2: Deletion Vectors
        deletion_vectors = self._check_deletion_vectors()
        result["deletion_vectors_enabled"] = deletion_vectors
        
        if not deletion_vectors:
            result["recommendations"].append({
                "config": "spark.databricks.delta.properties.defaults.enableDeletionVectors",
                "action": "Set to 'true'",
                "impact": "Faster MERGE/UPDATE operations (no full file rewrites)",
                "priority": "medium"
            })
            result["recommendation_count"] += 1
            
            print("ℹ️ Deletion Vectors are DISABLED")
            print("   💡 Enable for faster MERGE/UPDATE operations")
        else:
            print("✅ Deletion Vectors are ENABLED")
        
        # Check 3: Optimize Write
        optimize_write = self._check_optimize_write()
        result["optimize_write_enabled"] = optimize_write
        
        if not optimize_write:
            result["recommendations"].append({
                "config": "spark.microsoft.delta.optimizeWrite.enabled",
                "action": "Consider enabling for read-heavy or streaming workloads",
                "impact": "Prevents small file problem. Note: writeHeavy profile (default) disables this for maximum write throughput. Enable for readHeavyForSpark/readHeavyForPBI profiles or streaming workloads.",
                "priority": "low",
                "fabric_specific": True
            })
            result["recommendation_count"] += 1
            
            print("ℹ️ Optimize Write is DISABLED (optimal for writeHeavy profile - default)")
            print("   Benefit: Maximum write throughput for ETL and data ingestion")
            print("   💡 Enable only for read-heavy or streaming workloads")
            print("      - readHeavyForSpark: spark.fabric.resourceProfile=readHeavyForSpark")
            print("      - readHeavyForPBI: spark.fabric.resourceProfile=readHeavyForPBI")
        else:
            print("✅ Optimize Write is ENABLED - optimized for read-heavy workloads")
            print("   Note: Adds write overhead. Use writeHeavy profile for pure ingestion")
        
        # Check 4: Auto Compaction
        auto_compact = self._check_auto_compaction()
        if auto_compact:
            print("✅ Auto Compaction is ENABLED")
        else:
            print("ℹ️ Auto Compaction is DISABLED")
            print("   💡 Consider enabling or run manual OPTIMIZE commands regularly")
        
        # Check 5: Optimize Write Bin Size
        bin_size = self._check_optimize_write_bin_size()
        result["optimize_write_bin_size"] = bin_size
        if bin_size and optimize_write:
            print(f"ℹ️ Optimize Write Bin Size: {bin_size}")
            if bin_size != "128" and bin_size != "128MB":
                print(f"   💡 Consider using 128MB for partitioned tables")
        
        # Check 6: Optimize Write Partitioned
        partitioned = self._check_optimize_write_partitioned()
        result["optimize_write_partitioned"] = partitioned
        if partitioned:
            print("✅ Optimize Write Partitioned is ENABLED - optimized for partitioned tables")
        
        # Check 7: Driver Mode Snapshot
        driver_mode = self._check_driver_mode_snapshot()
        result["driver_mode_snapshot"] = driver_mode
        if driver_mode:
            print("✅ Driver Mode Snapshot is ENABLED - faster metadata operations")
        else:
            result["recommendations"].append({
                "config": "spark.microsoft.delta.snapshot.driverMode.enabled",
                "action": "Set to 'true' for large tables",
                "impact": "Faster snapshot loading and metadata operations",
                "priority": "low",
                "fabric_specific": True
            })
            result["recommendation_count"] += 1
        
        # Check 8: Fast Optimize
        fast_optimize = self._check_fast_optimize()
        result["fast_optimize"] = fast_optimize
        if fast_optimize:
            print("✅ Fast Optimize is ENABLED - 2-5x faster OPTIMIZE operations")
        else:
            result["recommendations"].append({
                "config": "spark.microsoft.delta.optimize.fast.enabled",
                "action": "Set to 'true' for faster compaction",
                "impact": "2-5x faster OPTIMIZE operations",
                "priority": "low",
                "fabric_specific": True
            })
            result["recommendation_count"] += 1
        
        # Check 9: Adaptive File Size
        adaptive = self._check_adaptive_file_size()
        result["adaptive_file_size"] = adaptive
        if adaptive:
            print("✅ Adaptive File Sizing is ENABLED - intelligent file size tuning")
        
        # Check 10: File Level Target
        file_level = self._check_file_level_target()
        result["file_level_target"] = file_level
        if file_level:
            print("✅ File Level Targeting is ENABLED - selective OPTIMIZE")
        
        return result
    
    def _check_v_order(self) -> bool:
        """Check if V-Order is enabled (Fabric-specific optimization)."""
        try:
            v_order = self.conf.get("spark.sql.parquet.vorder.enabled", "false")
            return v_order.lower() == "true"
        except Exception:
            return False
    
    def _check_deletion_vectors(self) -> bool:
        """Check if Deletion Vectors are enabled."""
        try:
            # Check both Databricks and standard Delta configs
            dv_databricks = self.conf.get(
                "spark.databricks.delta.properties.defaults.enableDeletionVectors", 
                "false"
            )
            dv_standard = self.conf.get(
                "spark.databricks.delta.deletionVectors.enabled",
                "false"
            )
            
            return (dv_databricks.lower() == "true" or 
                    dv_standard.lower() == "true")
        except Exception:
            return False
    
    def _check_optimize_write(self) -> bool:
        """Check if Optimize Write is enabled."""
        try:
            # Check Fabric-specific config first
            opt_write_fabric = self.conf.get(
                "spark.microsoft.delta.optimizeWrite.enabled",
                "false"
            )
            
            # Fallback to standard Delta config
            opt_write_delta = self.conf.get(
                "spark.databricks.delta.optimizeWrite.enabled",
                "false"
            )
            
            return (opt_write_fabric.lower() == "true" or 
                    opt_write_delta.lower() == "true")
        except Exception:
            return False
    
    def _check_auto_compaction(self) -> bool:
        """Check if Auto Compaction is enabled."""
        try:
            auto_compact = self.conf.get(
                "spark.databricks.delta.autoCompact.enabled",
                "false"
            )
            return auto_compact.lower() == "true"
        except Exception:
            return False
    
    def _check_optimize_write_bin_size(self) -> str:
        """Check Optimize Write bin size configuration."""
        try:
            return self.conf.get("spark.databricks.delta.optimizeWrite.binSize", None)
        except Exception:
            return None
    
    def _check_optimize_write_partitioned(self) -> bool:
        """Check if Optimize Write Partitioned is enabled."""
        try:
            partitioned = self.conf.get(
                "spark.databricks.delta.optimizeWrite.partitioned.enabled",
                "false"
            )
            return partitioned.lower() == "true"
        except Exception:
            return False
    
    def _check_driver_mode_snapshot(self) -> bool:
        """Check if Driver Mode Snapshot is enabled."""
        try:
            driver_mode = self.conf.get(
                "spark.microsoft.delta.snapshot.driverMode.enabled",
                "false"
            )
            return driver_mode.lower() == "true"
        except Exception:
            return False
    
    def _check_fast_optimize(self) -> bool:
        """Check if Fast Optimize is enabled."""
        try:
            fast_opt = self.conf.get(
                "spark.microsoft.delta.optimize.fast.enabled",
                "false"
            )
            return fast_opt.lower() == "true"
        except Exception:
            return False
    
    def _check_adaptive_file_size(self) -> bool:
        """Check if Adaptive File Size is enabled."""
        try:
            adaptive = self.conf.get(
                "spark.microsoft.delta.targetFileSize.adaptive.enabled",
                "false"
            )
            return adaptive.lower() == "true"
        except Exception:
            return False
    
    def _check_file_level_target(self) -> bool:
        """Check if File Level Target is enabled."""
        try:
            file_level = self.conf.get(
                "spark.microsoft.delta.optimize.fileLevelTarget.enabled",
                "false"
            )
            return file_level.lower() == "true"
        except Exception:
            return False
    
    def get_table_stats(self, table_path: str) -> Dict[str, Any]:
        """
        Get statistics for a Delta table (file count, size, etc.).
        
        Args:
            table_path: Path to Delta table
            
        Returns:
            Dictionary with table statistics
        """
        try:
            from delta.tables import DeltaTable
            
            delta_table = DeltaTable.forPath(self.spark, table_path)
            detail = delta_table.detail().collect()[0]
            
            stats = {
                "num_files": detail["numFiles"],
                "size_bytes": detail["sizeInBytes"],
                "num_files_warning": detail["numFiles"] > 1000,
                "small_files_warning": (detail["sizeInBytes"] / detail["numFiles"]) < 10_000_000  # < 10MB avg
            }
            
            if stats["num_files_warning"]:
                print(f"⚠️ Table has {stats['num_files']} files - consider running OPTIMIZE")
            
            if stats["small_files_warning"]:
                avg_size_mb = (stats["size_bytes"] / stats["num_files"]) / 1_000_000
                print(f"⚠️ Average file size is {avg_size_mb:.1f}MB - small file problem detected")
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
