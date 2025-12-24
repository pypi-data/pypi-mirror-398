# Trustable AI - Quick Start Guide

Get up and running with Trustable AI in 5 minutes.

## Installation

```bash
pip install trustable-ai
```

## Azure DevOps Setup (3 Steps)

### 1. Generate PAT Token

Visit: `https://dev.azure.com/{your-org}/_usersSettings/tokens`

Create token with permissions:
- Work Items: Read, Write, & Manage  
- Code: Read

### 2. Set Environment Variable

```bash
# Linux/Mac
export AZURE_DEVOPS_EXT_PAT="your-token-here"

# Windows PowerShell  
$env:AZURE_DEVOPS_EXT_PAT="your-token-here"
```

### 3. Configure Project

Create `.claude/config.yaml`:

```yaml
work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/your-organization"
  project: "Your Project Name"
  credentials_source: "env:AZURE_DEVOPS_EXT_PAT"
```

## Verify Setup

```bash
python3 -c "
import sys
sys.path.insert(0, '.claude/skills')
from work_tracking import get_adapter
adapter = get_adapter()
print(f'Connected! Found {len(adapter.list_sprints())} sprints')
"
```

See **docs/AZURE_DEVOPS_SETUP.md** for complete setup guide.
