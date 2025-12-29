"""
Data skew detection module.

Identifies when tasks have significantly imbalanced execution times,
indicating data distribution problems.
"""

from typing import Dict, Any, List, Optional
from pyspark.sql import SparkSession
import statistics


class SkewDetector:
    """Detects data skew by analyzing task execution metrics."""
    
    # Threshold: Task is skewed if max > threshold * median
    SKEW_THRESHOLD_MULTIPLIER = 2.0
    
    # Minimum stage duration to analyze (milliseconds)
    MIN_STAGE_DURATION_MS = 5000
    
    def __init__(self, spark: SparkSession) -> None:
        """Initialize with SparkSession."""
        self.spark = spark
        self.sc = spark.sparkContext
    
    def check(self) -> Dict[str, Any]:
        """
        Detect data skew in recent job execution.
        
        Returns:
            Dictionary with skew analysis results
        """
        result = {
            "skew_detected": False,
            "skewed_stages": [],
            "issues": [],
            "recommendations": [],
            "critical_count": 0,
            "recommendation_count": 0
        }
        
        try:
            # Get recent job IDs - method may not be available in Fabric
            status_tracker = self.sc.statusTracker()
            
            # Check if method exists (not available in Fabric/Synapse)
            if not hasattr(status_tracker, 'getActiveJobIds'):
                print("ℹ️ Skew detection not available in this Spark environment")
                print("   💡 Use Fabric Monitoring Hub -> Spark History UI for skew analysis")
                print("      Look for: Task duration skew, partition size distribution")
                result["note"] = "Use Fabric Monitoring Hub for detailed skew analysis"
                return result
            
            active_jobs = status_tracker.getActiveJobIds()
            
            if not active_jobs:
                print("ℹ️ No active jobs to analyze for skew")
                print("   Run this analysis after completing a Spark job")
                return result
            
            # Analyze each active job
            for job_id in active_jobs:
                job_info = self.sc.statusTracker().getJobInfo(job_id)
                if job_info and job_info.stageIds:
                    for stage_id in job_info.stageIds:
                        stage_result = self._analyze_stage(stage_id)
                        
                        if stage_result and stage_result["is_skewed"]:
                            result["skew_detected"] = True
                            result["skewed_stages"].append(stage_result)
                            
                            result["issues"].append({
                                "severity": "warning",
                                "message": f"Stage {stage_id}: Skewed task execution detected"
                            })
                            
                            self._print_skew_details(stage_result)
            
            if result["skew_detected"]:
                # Add general recommendations
                result["recommendations"].extend([
                    {
                        "action": "Add salt column to join/groupBy keys",
                        "impact": "Distribute load evenly across tasks",
                        "priority": "medium",
                        "example": "df.withColumn('salt', (rand() * 10).cast('int'))"
                    },
                    {
                        "action": "Enable AQE skew join optimization",
                        "impact": "Automatic skew handling for joins",
                        "priority": "high",
                        "config": "spark.sql.adaptive.skewJoin.enabled=true"
                    },
                    {
                        "action": "Repartition data before expensive operations",
                        "impact": "Better data distribution",
                        "priority": "medium",
                        "example": "df.repartition(200, 'key_column')"
                    }
                ])
                result["recommendation_count"] = len(result["recommendations"])
            else:
                print("✅ No significant data skew detected")
                print("   Task execution times are well-balanced")
        
        except Exception as e:
            print(f"⚠️ Could not analyze skew: {str(e)}")
            result["error"] = str(e)
        
        return result
    
    def _analyze_stage(self, stage_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single stage for skew.
        
        Args:
            stage_id: Stage ID to analyze
            
        Returns:
            Dictionary with stage skew analysis or None
        """
        try:
            stage_info = self.sc.statusTracker().getStageInfo(stage_id)
            
            if not stage_info:
                return None
            
            # Get task metrics (simplified - in real implementation would use UI data)
            num_tasks = stage_info.numTasks
            num_completed = stage_info.numCompletedTasks
            
            # Only analyze completed stages
            if num_completed < num_tasks * 0.8:  # At least 80% complete
                return None
            
            # In a real implementation, we would fetch actual task durations
            # from Spark UI or History Server
            # For MVP, we use a simplified heuristic
            
            # Placeholder: Would fetch actual task metrics here
            # task_durations = self._get_task_durations(stage_id)
            
            return None  # Simplified for MVP
            
        except Exception as e:
            return None
    
    def _get_task_durations(self, stage_id: int) -> List[float]:
        """
        Get task execution durations for a stage.
        
        Note: This is a placeholder. Real implementation would query
        Spark UI REST API or History Server.
        
        Args:
            stage_id: Stage ID
            
        Returns:
            List of task durations in seconds
        """
        # Placeholder implementation
        return []
    
    def _print_skew_details(self, stage_result: Dict[str, Any]) -> None:
        """Print detailed skew information."""
        stage_id = stage_result.get("stage_id", "unknown")
        max_duration = stage_result.get("max_task_duration", 0)
        median_duration = stage_result.get("median_task_duration", 0)
        
        print(f"⚠️ Data Skew Detected in Stage {stage_id}")
        print(f"   Max task: {max_duration:.1f}s | Median task: {median_duration:.1f}s")
        print(f"   Ratio: {max_duration / median_duration:.1f}x slower")
        print("   💡 This indicates uneven data distribution across partitions")
    
    def analyze_dataframe(self, df, key_columns: List[str]) -> Dict[str, Any]:
        """
        Analyze a DataFrame for potential skew in specified columns.
        
        Args:
            df: DataFrame to analyze
            key_columns: Columns to check for skew
            
        Returns:
            Dictionary with skew analysis per column
        """
        result = {
            "columns": {},
            "recommendations": []
        }
        
        for col in key_columns:
            try:
                # Count distinct values and get distribution
                value_counts = df.groupBy(col).count()
                stats = value_counts.select("count").describe().collect()
                
                max_count = value_counts.agg({"count": "max"}).collect()[0][0]
                min_count = value_counts.agg({"count": "min"}).collect()[0][0]
                
                skew_ratio = max_count / min_count if min_count > 0 else float('inf')
                
                result["columns"][col] = {
                    "max_count": max_count,
                    "min_count": min_count,
                    "skew_ratio": skew_ratio,
                    "is_skewed": skew_ratio > 10  # 10x difference indicates skew
                }
                
                if skew_ratio > 10:
                    result["recommendations"].append({
                        "column": col,
                        "action": f"Column '{col}' has significant skew (ratio: {skew_ratio:.1f}x)",
                        "solution": "Consider salting this key or using broadcast join if other side is small"
                    })
            
            except Exception as e:
                result["columns"][col] = {"error": str(e)}
        
        return result
