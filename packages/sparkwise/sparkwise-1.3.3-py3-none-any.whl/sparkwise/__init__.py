"""
sparkwise - The automated technical fellow for your Fabric Spark workloads.

Provides intelligent configuration analysis, error diagnosis, and optimization
recommendations for Apache Spark on Microsoft Fabric.
"""

__version__ = "1.3.3"
__author__ = "Santhosh Ravindran"
__all__ = ["FabricAdvisor", "diagnose", "ask", "profile", "profile_executors", 
           "profile_jobs", "profile_resources", "predict_scalability", 
           "show_timeline", "analyze_efficiency", "detect_skew", "analyze_query"]

# Lazy imports to avoid PySpark initialization issues
_diagnose = None
_ask = None
_profile = None
_profile_executors = None
_profile_jobs = None
_profile_resources = None
_predict_scalability = None
_show_timeline = None
_analyze_efficiency = None
_detect_skew = None
_analyze_query = None


def __getattr__(name):
    """Lazy load modules to avoid early PySpark initialization."""
    global _diagnose, _ask, _profile, _profile_executors, _profile_jobs, _profile_resources
    global _predict_scalability, _show_timeline, _analyze_efficiency, _detect_skew, _analyze_query
    
    if name == "diagnose":
        if _diagnose is None:
            from sparkwise.core.advisor import FabricAdvisor
            _diagnose = FabricAdvisor()
        return _diagnose
    
    elif name == "ask":
        if _ask is None:
            from sparkwise import config_qa as ask_module
            _ask = ask_module.ask
        return _ask
    
    elif name == "profile":
        if _profile is None:
            from sparkwise.profiling.session_profiler import SessionProfiler
            _profile = SessionProfiler()
        return _profile
    
    elif name == "profile_executors":
        if _profile_executors is None:
            from sparkwise.profiling.executor_profiler import ExecutorProfiler
            _profile_executors = ExecutorProfiler()
        return _profile_executors
    
    elif name == "profile_jobs":
        if _profile_jobs is None:
            from sparkwise.profiling.job_profiler import JobProfiler
            _profile_jobs = JobProfiler()
        return _profile_jobs
    
    elif name == "profile_resources":
        if _profile_resources is None:
            from sparkwise.profiling.resource_profiler import ResourceProfiler
            _profile_resources = ResourceProfiler()
        return _profile_resources
    
    elif name == "predict_scalability":
        if _predict_scalability is None:
            from sparkwise.profiling.scalability_predictor import predict_scalability as pred_func
            _predict_scalability = pred_func
        return _predict_scalability
    
    elif name == "show_timeline":
        if _show_timeline is None:
            from sparkwise.profiling.stage_timeline import show_timeline as timeline_func
            _show_timeline = timeline_func
        return _show_timeline
    
    elif name == "analyze_efficiency":
        if _analyze_efficiency is None:
            from sparkwise.profiling.efficiency_analyzer import analyze_efficiency as eff_func
            _analyze_efficiency = eff_func
        return _analyze_efficiency
    
    elif name == "detect_skew":
        if _detect_skew is None:
            from sparkwise.core.advanced_skew_detector import detect_skew as skew_func
            _detect_skew = skew_func
        return _detect_skew
    
    elif name == "analyze_query":
        if _analyze_query is None:
            from sparkwise.core.query_plan_analyzer import analyze_query as query_func
            _analyze_query = query_func
        return _analyze_query
    
    elif name == "FabricAdvisor":
        from sparkwise.core.advisor import FabricAdvisor
        return FabricAdvisor
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__():
    """Make all exports appear in dir() for discoverability."""
    return ['__name__', '__doc__', '__version__', '__author__', '__all__', 
            'FabricAdvisor', 'diagnose', 'ask', 'profile', 'profile_executors',
            'profile_jobs', 'profile_resources', 'predict_scalability',
            'show_timeline', 'analyze_efficiency', 'detect_skew', 'analyze_query']
