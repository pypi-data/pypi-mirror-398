# 🔥 Sparkwise

> **Achieve optimal Fabric Spark price-performance with automated insights - simplifies tuning, makes optimization fun**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

sparkwise is an automated Data Engineering specialist for Apache Spark on Microsoft Fabric. It provides intelligent diagnostics, configuration recommendations, and comprehensive session profiling to help you achieve the best price-performance for your workloads - all while making Spark tuning simple and enjoyable.

## 🎯 Why sparkwise?

Spark tuning on Microsoft Fabric doesn't have to be complex or expensive. sparkwise helps you:
- 💰 **Optimize costs** - Detect configurations that waste capacity and increase runtime
- ⚡ **Maximize performance** - Enable Fabric-specific optimizations (Native Engine, V-Order, resource profiles)
- 🎓 **Simplify learning** - Interactive Q&A for 133 Spark/Delta/Fabric configurations
- 🔍 **Understand workloads** - Comprehensive profiling of sessions, executors, jobs, and resources
- ⏱️ **Save time** - Avoid 3-5min cold-starts by detecting Starter Pool blockers
- 📊 **Make data-driven decisions** - Priority-ranked recommendations with impact analysis

## ✨ Key Features

### 🔬 **Automated Diagnostics**
- **Native Execution Engine** - Verifies Velox usage, detects fallbacks to row-based processing
- **Spark Compute** - Analyzes Starter vs Custom Pool usage, warns about immutable configs
- **Data Skew Detection** - Identifies imbalanced task distributions
- **Delta Optimizations** - Checks V-Order, Deletion Vectors, Optimize Write, Auto Compaction
- **Runtime Tuning** - Validates AQE, partition sizing, scheduler mode

### 📊 **Comprehensive Profiling**
- **Session Profiling** - Application metadata, resource allocation, memory breakdown
- **Executor Profiling** - Executor status, memory utilization, task distribution
- **Job Profiling** - Job/stage/task metrics, bottleneck detection
- **Resource Profiling** - Efficiency scoring, utilization analysis, optimization recommendations

### 🚀 **Advanced Performance Analysis** (NEW!)
- **Real Metrics Collection** - Uses actual Spark stage/task data instead of estimates
- **Scalability Prediction** - Compare Starter vs Custom Pool with real VCore-hour calculations
- **Stage Timeline** - Visualize execution patterns with parallel/sequential analysis
- **Efficiency Analysis** - Quantify wasted compute in VCore-hours with actionable recommendations

### 🔍 **Advanced Skew Detection** (NEW!)
- **Task Duration Analysis** - Detect stragglers and long-running tasks with variance detection
- **Partition-Level Analysis** - Identify data distribution imbalances with statistical metrics
- **Skewed Join Detection** - Analyze join patterns and recommend broadcast vs salting strategies
- **Automatic Mitigation** - Get code examples for salting, AQE, and broadcast optimizations

### 🎯 **SQL Query Plan Analysis** (NEW!)
- **Anti-Pattern Detection** - Identify cartesian products, full scans, and excessive shuffles
- **Native Engine Compatibility** - Check if queries use Fabric Native Engine (3-8x faster)
- **Z-Order Recommendations** - Suggest best columns for Delta optimization based on cardinality
- **Caching Opportunities** - Detect repeated table scans that benefit from caching
- **Fabric Best Practices** - V-Order, broadcast joins, AQE, and partition recommendations

### 💡 **Interactive Configuration Assistant**
- **133 documented configurations** - Spark, Delta Lake, Fabric-specific, and Runtime 1.2 configs
- **Context-aware guidance** - Workload-specific recommendations with impact analysis
- **Resource profile support** - Understand writeHeavy, readHeavyForSpark, readHeavyForPBI profiles
- **Search capabilities** - Find configs by keyword or partial name

### 📈 **Priority-Based Recommendations**
- **Color-coded priorities** - Critical (red) → High (yellow) → Medium (blue) → Low (dim)
- **Formatted tables** - Clean, readable output with impact explanations
- **Actionable guidance** - Specific commands and configuration values

## 🚀 Quick Start

### Installation

```bash
pip install sparkwise
```

Or install the wheel file directly in Fabric:

```python
%pip install sparkwise-0.1.0-py3-none-any.whl
```

### Basic Usage

```python
from sparkwise import diagnose, ask

# Run comprehensive analysis on current session
diagnose.analyze()

# Ask about any configuration
ask.config('spark.native.enabled')

# Search for configurations
ask.search('optimize')
```

### Session Profiling

```python
from sparkwise import (profile, profile_executors, profile_jobs, profile_resources,
                       predict_scalability, show_timeline, analyze_efficiency)

# Profile complete session
profile()

# Profile executor metrics
profile_executors()

# Analyze job performance
profile_jobs()

# Check resource efficiency
profile_resources()

# Advanced profiling features
predict_scalability()  # Compare pool configurations
show_timeline()        # Visualize stage execution
analyze_efficiency()   # Quantify compute waste
```

### Advanced Analysis

```python
from sparkwise import detect_skew, analyze_query

# Detect data skew
skew_results = detect_skew()  # Analyze task-level skew

# Analyze specific DataFrame for partition skew
from sparkwise.core.advanced_skew_detector import AdvancedSkewDetector
detector = AdvancedSkewDetector()
detector.analyze_partition_skew(your_df, ["key_column"])

# Detect skewed joins
detector.detect_skewed_joins(large_df, small_df, "join_key")

# Analyze SQL query plans
query_results = analyze_query(your_df)

# Get Z-Order recommendations
from sparkwise.core.query_plan_analyzer import QueryPlanAnalyzer
analyzer = QueryPlanAnalyzer()
zorder_cols = analyzer.suggest_zorder_columns(delta_df, ["filtered_col"])

# Detect caching opportunities
analyzer.detect_repeated_subqueries(your_df)
```

## 📊 Sample Output

### Diagnostic Analysis

```
🔥 sparkwise Analysis 🔥

🔎 Native Execution Engine
──────────────────────────────────────────────
⚠️ Warning: Native keywords not found in physical plan
   💡 Check for unsupported operators or complex UDFs

⚡ Spark Compute
──────────────────────────────────────────────
✅ Your job uses 1 executors - fits in Starter Pool
   💡 Ensure 'Starter Pool' is selected in workspace settings

💾 Storage & Delta Optimizations
──────────────────────────────────────────────
ℹ️ V-Order is DISABLED (optimal for write-heavy workloads)
   Benefit: 2x faster writes vs V-Order enabled
   💡 Enable only for read-heavy workloads (Power BI/analytics)
      Trade-off: 3-10x faster reads, but 15-20% slower writes

ℹ️ Optimize Write is DISABLED (optimal for writeHeavy profile - default)
   Benefit: Maximum write throughput for ETL and data ingestion
   💡 Enable only for read-heavy or streaming workloads
      - readHeavyForSpark: spark.fabric.resourceProfile=readHeavyForSpark
      - readHeavyForPBI: spark.fabric.resourceProfile=readHeavyForPBI

⚙️ Runtime Tuning
──────────────────────────────────────────────
⛔ CRITICAL: Adaptive Query Execution (AQE) is DISABLED
   💡 Enable immediately: spark.sql.adaptive.enabled=true
      Benefits: Dynamic coalescing, skew joins, better parallelism

📋 Summary of Findings
┌─────────────────────┬────────┬─────────────────┬─────────────────┐
│ Category            │ Status │ Critical Issues │ Recommendations │
├─────────────────────┼────────┼─────────────────┼─────────────────┤
│ Native Execution    │ ⚠️     │ 1               │ 1               │
│ Spark Compute       │ ✅     │ 0               │ 1               │
│ Data Skew           │ ✅     │ 0               │ 0               │
│ Delta               │ ✅     │ 0               │ 3               │
│ Runtime             │ ⚠️     │ 1               │ 2               │
└─────────────────────┴────────┴─────────────────┴─────────────────┘

🔧 Configuration Recommendations
Total recommendations: 7

┌──────────┬─────────────────────────────────┬────────────────┬──────────────┐
│ Priority │ Configuration                   │ Action         │ Impact       │
├──────────┼─────────────────────────────────┼────────────────┼──────────────┤
│ CRITICAL │ spark.sql.adaptive.enabled      │ Set to 'true'  │ Enable       │
│          │                                 │                │ dynamic      │
│          │                                 │                │ partition    │
│          │                                 │                │ coalescing   │
├──────────┼─────────────────────────────────┼────────────────┼──────────────┤
│ MEDIUM   │ spark.sql.parquet.vorder.enabled│ Enable for     │ 3-10x faster │
│          │                                 │ read-heavy     │ reads for    │
│          │                                 │ workloads only │ Power BI     │
└──────────┴─────────────────────────────────┴────────────────┴──────────────┘

✨ Analysis complete!
```

### Interactive Q&A

```python
ask.config('spark.fabric.resourceProfile')
```

**Output:**
```
📚 spark.fabric.resourceProfile

──────────────────────────────────────────────────────────────────────

Default: writeHeavy
Scope: session

What it does:
FABRIC CRITICAL: Selects predefined Spark resource profiles optimized 
for specific workload patterns. Simplifies configuration tuning.

Recommendations for your workload:
  • etl_ingestion: writeHeavy - optimized for ETL and data ingestion
  • analytics_spark: readHeavyForSpark - optimized for analytical queries
  • power_bi: readHeavyForPBI - optimized for Power BI Direct Lake
  • custom_needs: custom - user-defined configuration

Fabric-specific notes:
Microsoft Fabric resource profiles provide workload-optimized settings:

**writeHeavy (DEFAULT):**
- V-Order: DISABLED for faster writes
- Optimize Write: NULL/DISABLED for maximum throughput
- Use Case: ETL pipelines, data ingestion, batch transformations

**readHeavyForSpark:**
- Optimize Write: ENABLED with 128MB bins
- Use Case: Interactive Spark queries, analytical workloads

**readHeavyForPBI:**
- V-Order: ENABLED for Power BI optimization
- Optimize Write: ENABLED with 1GB bins
- Use Case: Power BI dashboards, Direct Lake scenarios

Related configurations:
  • spark.sql.parquet.vorder.enabled
  • spark.databricks.delta.optimizeWrite.enabled
  • spark.microsoft.delta.optimizeWrite.enabled

Examples:
  spark.conf.set('spark.fabric.resourceProfile', 'readHeavyForSpark')
  spark.conf.set('spark.fabric.resourceProfile', 'writeHeavy')

──────────────────────────────────────────────────────────────────────
```

## 📦 What's Included

### Core Modules
- `diagnose` - Main diagnostic engine with 5 check categories
- `ask` - Interactive configuration Q&A system
- `profile` - Session profiling
- `profile_executors` - Executor-level metrics
- `profile_jobs` - Job/stage/task analysis
- `profile_resources` - Resource efficiency scoring

### Knowledge Base (133 Configurations)
- **33 Spark configs** - Core settings for shuffle, memory, AQE, serialization
- **45 Delta configs** - Delta Lake optimizations, V-Order, Deletion Vectors
- **10 Fabric configs** - Native Engine, resource profiles, OneLake storage
- **45 Runtime 1.2 configs** - Latest Fabric Runtime 1.2 features

### Latest Features
- ✅ Fabric resource profiles (writeHeavy, readHeavyForSpark, readHeavyForPBI)
- ✅ Advanced Delta optimizations (Fast Optimize, Adaptive File Size, File Level Target)
- ✅ Driver Mode Snapshot for faster metadata operations
- ✅ Comprehensive session profiling tools
- ✅ Priority-based recommendation tables
- ✅ Color-coded terminal output with Rich library

## 🎯 Use Cases

### Data Engineers
- **Optimize ETL pipelines** - Detect bottlenecks, tune parallelism, reduce costs
- **Validate configurations** - Ensure proper resource profiles and pool usage
- **Debug job failures** - Understand errors with plain English explanations

### Data Scientists
- **Improve notebook performance** - Enable Native Engine, optimize memory usage
- **Understand Spark behavior** - Learn configurations through interactive Q&A
- **Profile experiments** - Track resource usage and efficiency

### Platform Admins
- **Standardize best practices** - Share optimal configurations across teams
- **Monitor capacity usage** - Identify jobs forcing Custom Pool usage
- **Cost optimization** - Detect over-provisioned or misconfigured workloads

## 📚 CLI Usage

```bash
# Run diagnostics
sparkwise analyze

# Profile session
sparkwise profile session

# Profile executors
sparkwise profile executors

# Profile jobs
sparkwise profile jobs --max-jobs 5

# Profile resources
sparkwise profile resources

# Analyze bottlenecks
sparkwise profile bottlenecks

# Ask about configuration
sparkwise ask spark.sql.shuffle.partitions

# Search configurations
sparkwise search "adaptive"
```

## 🏗️ Architecture

```
sparkwise/
├── core/
│   ├── advisor.py          # Main diagnostic orchestrator
│   ├── native_check.py     # Velox/Native execution verification
│   ├── pool_check.py       # Starter vs Custom Pool analysis
│   ├── skew_check.py       # Data skew detection
│   ├── delta_check.py      # Delta Lake optimizations
│   └── runtime_check.py    # Runtime configuration tuning
├── profiling/
│   ├── session_profiler.py    # Complete session analysis
│   ├── executor_profiler.py   # Executor metrics
│   ├── job_profiler.py        # Job/stage/task profiling
│   └── resource_profiler.py   # Resource efficiency analysis
├── knowledge_base/
│   ├── spark_configs.yaml     # Core Spark configurations
│   ├── delta_configs.yaml     # Delta Lake configurations
│   ├── fabric_configs.yaml    # Fabric-specific configs
│   └── fabric_runtime_1.2_configs.yaml  # Runtime 1.2 features
├── cli.py                     # Command-line interface
└── config_qa.py              # Interactive Q&A assistant
```

## 🎓 Examples

Check out the [examples](examples/) directory:
- [basic_analysis.py](examples/basic_analysis.py) - Basic diagnostic workflow
- [config_qa_demo.py](examples/config_qa_demo.py) - Configuration Q&A usage
- [profiling_demo.py](examples/profiling_demo.py) - Comprehensive profiling examples
- [knowledge_base_demo.py](examples/knowledge_base_demo.py) - Knowledge base exploration
- [immutable_configs_demo.py](examples/immutable_configs_demo.py) - Starter Pool optimization

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=sparkwise --cov-report=html

# Run specific test file
pytest tests/test_advisor.py
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/santhoshravindran7/sparkwise.git
cd sparkwise

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with ❤️ for the Microsoft Fabric Data Engineering and Data Science community.

## 📬 Contact & Support

- **Author**: Santhosh Ravindran
- **GitHub**: [@santhoshravindran7](https://github.com/santhoshravindran7)
- **Issues**: [Report bugs or request features](https://github.com/santhoshravindran7/sparkwise/issues)

## 🎉 What's New in v0.1.0

- ✨ Complete profiling suite (session, executor, job, resource profilers)
- 🎨 Rich terminal output with color-coded priorities
- 📊 Priority-based recommendation tables
- 🔧 Fabric resource profile support (writeHeavy, readHeavy profiles)
- ⚡ 4 new advanced Delta optimizations
- 📚 133 documented configurations (up from 100)
- 🎯 Context-aware Optimize Write recommendations
- 🚀 CLI support for all profiling operations

---

Make Spark tuning fun again! 🚀✨
