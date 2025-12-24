# ForgeFlow

[![PyPI version](https://badge.fury.io/py/forge-flow.svg)](https://pypi.org/project/forge-flow/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/YOUR-USERNAME/forge-flow/workflows/CI/badge.svg)](https://github.com/YOUR-USERNAME/forge-flow/actions)

**Production-grade ML library for building reliable, type-safe machine learning pipelines.**

ForgeFlow is designed for engineering teams who need robust data validation, reproducible feature engineering, and production-ready ML infrastructure. Built with strict type safety, immutability, and defensive programming principles.

## Why ForgeFlow?

Modern ML systems fail in production due to data quality issues, schema drift, and unreliable pipelines. ForgeFlow addresses these challenges with:

- **Strict Schema Validation** - Pydantic-based contracts that fail fast on invalid data
- **Immutable Operations** - Pure functions that prevent side effects and ensure reproducibility
- **Quality Gates** - Automated checks that prevent bad data from reaching production
- **Drift Detection** - Statistical monitoring to catch distribution shifts early
- **Type Safety** - 100% type-hinted codebase for better IDE support and fewer runtime errors

## Installation

```bash
pip install forge-flow
```

Optional dependencies:
```bash
pip install forge-flow[serving]    # Redis-based feature store
pip install forge-flow[database]   # SQL database connectors
pip install forge-flow[all]        # Everything
```

## Quick Start

ForgeFlow follows a simple pipeline pattern: **Ingest → Validate → Transform → Serve**

### 1. Define Your Schema

Schemas enforce data contracts and catch issues early:

```python
from forge_flow.schemas import StrictSchema
from pydantic import Field

class Transaction(StrictSchema):
    user_id: int = Field(gt=0)
    amount: float = Field(gt=0, le=1000000)
    timestamp: datetime
```

### 2. Validate Data

Automatic validation with Dead Letter Queue for invalid records:

```python
from forge_flow.schemas import SchemaValidator

validator = SchemaValidator(Transaction)
clean_data = validator.validate(raw_data, raise_on_error=False)
```

### 3. Engineer Features

Immutable transformations with built-in quality checks:

```python
from forge_flow.features import DataCleaner, FeatureEngineer

cleaner = DataCleaner()
cleaned = cleaner.handle_nulls(clean_data)

engineer = FeatureEngineer()
features = engineer.add_rolling_features(
    cleaned,
    group_col='user_id',
    value_col='amount',
    windows=[7, 30]
)
```

### 4. Quality Gates

Prevent bad data from reaching production:

```python
from forge_flow.features import QualityGate

gate = QualityGate(max_null_rate=0.05, min_rows=1000)
gate.validate(features)  # Raises error if quality fails
```

## Core Features

### Data Ingestion
- **File Connectors** - Read from local, S3, GCS, Azure (Parquet, CSV, JSON)
- **API Connectors** - Resilient HTTP clients with retries and rate limiting
- **Database Connectors** - SQLAlchemy-based with incremental loading

### Feature Engineering
- **Data Cleaning** - Null handling, outlier detection, type casting
- **Transformations** - Rolling windows, lag features, encoding, normalization
- **Pipelines** - Reproducible workflows with Pydantic configuration

### Production Features
- **Online Store** - Redis-based sub-millisecond feature serving
- **Drift Detection** - KS test for numeric, PSI for categorical features
- **Structured Logging** - Full observability with structlog

## Design Principles

ForgeFlow is built for production systems, not notebooks:

1. **Fail Fast** - Validate early, catch errors at ingestion boundaries
2. **Immutability** - Operations return new objects, preventing side effects
3. **Type Safety** - Comprehensive type hints for better tooling and fewer bugs
4. **Explicit Over Implicit** - No magic, clear data flows
5. **Testability** - Pure functions and dependency injection throughout

## Documentation

- **[Examples](examples/)** - Practical usage patterns and integration guides
- **[Contributing](CONTRIBUTING.md)** - Development workflow and standards

## Use Cases

ForgeFlow excels at:

- **Fraud Detection** - Real-time feature serving with drift monitoring
- **Recommendation Systems** - Reproducible feature pipelines at scale
- **Credit Risk** - Audit trails and regulatory compliance
- **Predictive Maintenance** - Time-series feature engineering

## Requirements

- Python 3.10+
- Core: pandas, numpy, pydantic, structlog
- Optional: redis (serving), sqlalchemy (database)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/YOUR-USERNAME/forge-flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR-USERNAME/forge-flow/discussions)

---

Built with ❤️ for production ML teams who value reliability over convenience.
