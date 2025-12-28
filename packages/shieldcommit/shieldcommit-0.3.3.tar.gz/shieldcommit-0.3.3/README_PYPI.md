🛡️ ShieldCommit v0.3.0

Lightweight pre-commit secret scanner CLI with comprehensive infrastructure version warnings across AWS, Azure, and Google Cloud.

## Features

✅ **Secret Detection** (v0.1)
- 40+ regex patterns for cloud/API keys, tokens, private keys
- Real-time scanning of staged files
- Support for multiple secret types (AWS, GCP, Azure, GitHub, etc.)

✨ **Infrastructure Version Warnings** (v0.2-v0.3)

### Kubernetes/Container Orchestration
- **AWS EKS** - Kubernetes version detection (deprecated/extended support)
- **Azure AKS** - Kubernetes version detection with EOL tracking
- **Google Cloud GKE** - Kubernetes versions + release channel recommendations (RAPID/REGULAR/STABLE)

### Database Engines
- **AWS RDS** - PostgreSQL, MySQL, MariaDB version detection
- **Azure Database** - SQL Server, MySQL, PostgreSQL version detection
- **Google Cloud SQL** - MySQL, PostgreSQL, SQL Server version detection

### Additional Features
- Non-blocking warnings (safe for beta)
- Zero cloud API calls required
- End-of-life (EOL) date tracking
- Extended support period detection
- Actionable upgrade guidance
- Consistent warning format across all platforms
- Works with Terraform, CloudFormation, and IaC files

## Installation

```bash
pip install shieldcommit==0.3.3