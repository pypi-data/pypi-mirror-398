"""
Native Execution Engine verification module.

Checks if Fabric's Velox-based Native Execution Engine is active
and detects fallbacks to row-based processing.
"""

from typing import Dict, Any, Optional
from pyspark.sql import SparkSession, DataFrame
import re


class NativeExecutionChecker:
    """Verifies Native Execution Engine (Velox) usage in Fabric Spark."""
    
    # Patterns indicating native execution
    NATIVE_INDICATORS = [
        "Velox", "VeloxColumnarToRowExec", "NativeFileScan", 
        "Gluten", "VeloxAppendColumnsExec"
    ]
    
    # Patterns indicating fallback to row-based execution
    FALLBACK_INDICATORS = [
        "RowToColumnar", "BatchEvalPython", "PythonUDF"
    ]
    
    def __init__(self, spark: SparkSession) -> None:
        """Initialize with SparkSession."""
        self.spark = spark
        self.conf = spark.conf
    
    def check(self, df: Optional[DataFrame] = None) -> Dict[str, Any]:
        """
        Check Native Execution Engine status.
        
        Args:
            df: Optional DataFrame for physical plan analysis
            
        Returns:
            Dictionary with check results and recommendations
        """
        result = {
            "status": "unknown",
            "native_enabled": False,
            "plan_analysis": None,
            "issues": [],
            "recommendations": [],
            "critical_count": 0,
            "recommendation_count": 0
        }
        
        # Check 1: Configuration setting
        native_config_enabled = self._check_native_config()
        result["native_enabled"] = native_config_enabled
        
        if not native_config_enabled:
            result["status"] = "disabled"
            result["issues"].append({
                "severity": "critical",
                "message": "Native Engine is explicitly DISABLED in configuration"
            })
            result["recommendations"].append({
                "config": "spark.native.enabled",
                "action": "Set to 'true'",
                "impact": "~3-5x performance improvement for vectorized operations",
                "priority": "high"
            })
            result["critical_count"] += 1
            result["recommendation_count"] += 1
            
            print("❌ Native Engine is explicitly DISABLED (spark.native.enabled=false)")
            print("   💡 Set spark.native.enabled=true to unlock Velox acceleration")
            return result
        
        # Check 2: Physical plan analysis (if DataFrame provided)
        if df is not None:
            plan_result = self._analyze_physical_plan(df)
            result["plan_analysis"] = plan_result
            
            if plan_result["has_native"]:
                result["status"] = "active"
                print("✅ Native Execution Engine is ACTIVE (Velox detected in query plan)")
                
                if plan_result["has_fallback"]:
                    result["issues"].append({
                        "severity": "warning",
                        "message": f"Partial fallback detected: {', '.join(plan_result['fallback_reasons'])}"
                    })
                    result["recommendations"].append({
                        "action": "Replace Python UDFs with native SQL functions",
                        "impact": "Eliminate fallback to row-based processing",
                        "priority": "medium"
                    })
                    result["recommendation_count"] += 1
                    
                    print(f"   ⚠️ Partial Fallback: {', '.join(plan_result['fallback_reasons'])}")
                    print("   💡 Replace Python UDFs with pyspark.sql.functions for full vectorization")
            else:
                result["status"] = "inactive"
                result["issues"].append({
                    "severity": "critical",
                    "message": "Native engine enabled but not used in query plan"
                })
                result["recommendations"].append({
                    "action": "Check for unsupported operators or UDFs in your query",
                    "impact": "Enable full Velox acceleration",
                    "priority": "high"
                })
                result["critical_count"] += 1
                result["recommendation_count"] += 1
                
                print("⚠️ Warning: Native keywords not found in physical plan")
                print("   💡 Check for unsupported operators or complex UDFs")
        else:
            result["status"] = "enabled"
            print("✅ Native Engine is ENABLED in configuration")
            print("   ℹ️ Pass a DataFrame to analyze() for deep query plan inspection")
        
        return result
    
    def _check_native_config(self) -> bool:
        """Check if native execution is enabled in Spark config."""
        try:
            native_enabled = self.conf.get("spark.native.enabled", "false")
            return native_enabled.lower() == "true"
        except Exception:
            return False
    
    def _analyze_physical_plan(self, df: DataFrame) -> Dict[str, Any]:
        """
        Analyze the physical plan for native execution indicators.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with plan analysis results
        """
        try:
            # Get the physical plan as string
            plan = df._jdf.queryExecution().executedPlan().toString()
            
            # Check for native indicators
            has_native = any(indicator in plan for indicator in self.NATIVE_INDICATORS)
            
            # Check for fallback indicators
            fallback_reasons = [
                indicator for indicator in self.FALLBACK_INDICATORS 
                if indicator in plan
            ]
            has_fallback = len(fallback_reasons) > 0
            
            return {
                "has_native": has_native,
                "has_fallback": has_fallback,
                "fallback_reasons": fallback_reasons,
                "plan_snippet": plan[:500]  # First 500 chars for reference
            }
        except Exception as e:
            return {
                "has_native": False,
                "has_fallback": False,
                "fallback_reasons": [],
                "error": str(e)
            }
