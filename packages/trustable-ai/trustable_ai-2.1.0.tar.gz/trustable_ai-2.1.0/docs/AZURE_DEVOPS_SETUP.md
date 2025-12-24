# Azure DevOps Setup Guide - PAT Token Authentication

This guide explains how to configure Azure DevOps REST API authentication for Trustable AI using Personal Access Tokens (PAT).

## Overview

Trustable AI uses **Azure DevOps REST API v7.1** with **PAT (Personal Access Token)** authentication. This provides:
- ✅ Secure, programmatic access (no passwords)
- ✅ Scoped permissions (work items, repos, pipelines)
- ✅ Revocable tokens for security
- ✅ Works in CI/CD and automation
- ✅ No Azure CLI dependency

## Quick Start (3 Steps)

### 1. Generate a PAT Token

**Navigate to Azure DevOps PAT Settings:**
```
https://dev.azure.com/{your-organization}/_usersSettings/tokens
```

**Create a New Token:**
1. Click "+ New Token"
2. Name: `Trustable AI Development`
3. Organization: Select your organization
4. Expiration: 90 days (or custom)
5. Scopes: **Select these permissions:**
   - ✅ **Work Items**: Read, Write, & Manage
   - ✅ **Code**: Read
   - ✅ **Build**: Read & Execute
   - ✅ **Release**: Read
   - ✅ **Project and Team**: Read

6. Click "Create"
7. **IMPORTANT**: Copy the token immediately (you won't see it again!)

**Token Format:**
```
abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmnopqrstuvwxyz
```

### 2. Configure the Token

**Option A: Environment Variable (Recommended)**

**Linux/Mac:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export AZURE_DEVOPS_EXT_PAT="your-token-here"

# Reload shell
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
# Add to PowerShell profile
$env:AZURE_DEVOPS_EXT_PAT="your-token-here"

# Or set permanently (requires admin)
[System.Environment]::SetEnvironmentVariable(
    'AZURE_DEVOPS_EXT_PAT',
    'your-token-here',
    [System.EnvironmentVariableTarget]::User
)
```

**Windows (Command Prompt):**
```cmd
setx AZURE_DEVOPS_EXT_PAT "your-token-here"
# Restart terminal for changes to take effect
```

**Option B: Configuration File**

Edit `.claude/config.yaml`:
```yaml
work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/your-organization"
  project: "Your Project Name"
  credentials_source: "env:AZURE_DEVOPS_EXT_PAT"  # Use environment variable
```

**Or with token directly in config (NOT recommended for production):**
```yaml
work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/your-organization"
  project: "Your Project Name"
  credentials_source: "token:your-token-here"  # ⚠️ Less secure, use env instead
```

### 3. Verify Setup

**Test the connection:**

```bash
python3 -c "
import sys
sys.path.insert(0, '.claude/skills')
from work_tracking import get_adapter

adapter = get_adapter()
sprints = adapter.list_sprints()
print(f'✅ Connected! Found {len(sprints)} sprint(s)')
for sprint in sprints[:3]:
    print(f'  - {sprint[\"name\"]}')
"
```

**Expected output:**
```
✅ Connected! Found 7 sprint(s)
  - Sprint 1
  - Sprint 2
  - Sprint 3
```

**If authentication fails:**
```
AuthenticationError: Azure DevOps PAT token not found or invalid.
Set AZURE_DEVOPS_EXT_PAT environment variable or configure credentials_source in .claude/config.yaml.
Generate a PAT at: https://dev.azure.com/your-org/_usersSettings/tokens
```

## Configuration Details

### Required Settings

Edit `.claude/config.yaml`:

```yaml
work_tracking:
  # Platform type
  platform: "azure-devops"

  # Organization URL (must start with https://dev.azure.com/)
  organization: "https://dev.azure.com/your-organization"

  # Project name (exact match, case-sensitive)
  project: "Your Project Name"

  # Credentials source (environment variable or direct token)
  credentials_source: "env:AZURE_DEVOPS_EXT_PAT"

  # Optional: Work item type mappings
  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"
    bug: "Bug"

  # Optional: Custom field mappings
  custom_fields:
    business_value: "Custom.BusinessValueScore"
    technical_risk: "Custom.TechnicalRisk"
```

### Credential Sources

**Environment Variable (Recommended):**
```yaml
credentials_source: "env:AZURE_DEVOPS_EXT_PAT"
```
- Most secure (token not in config file)
- Works in CI/CD environments
- Easy to rotate tokens

**Direct Token (Not Recommended):**
```yaml
credentials_source: "token:abcd1234..."
```
- ⚠️ Token visible in config file
- ⚠️ Can be accidentally committed to git
- ✅ Use only for local testing

**Environment Variable with Custom Name:**
```yaml
credentials_source: "env:MY_CUSTOM_PAT_VAR"
```
Then set:
```bash
export MY_CUSTOM_PAT_VAR="your-token-here"
```

## Security Best Practices

### 1. Keep Tokens Secret

**Add to .gitignore:**
```
# .gitignore
.env
.env.local
*.secrets
config.local.yaml
```

**Never commit tokens:**
```bash
# ❌ WRONG - token in config file that's committed
git add .claude/config.yaml  # Contains credentials_source: "token:abc123"

# ✅ CORRECT - token in environment variable
export AZURE_DEVOPS_EXT_PAT="abc123"
git add .claude/config.yaml  # Contains credentials_source: "env:AZURE_DEVOPS_EXT_PAT"
```

### 2. Use Scoped Permissions

**Minimum required scopes:**
- Work Items: Read, Write, & Manage
- Code: Read (for PR operations)

**Avoid:**
- Full access
- Delete permissions (unless needed)
- Admin permissions

### 3. Rotate Tokens Regularly

**Set expiration:**
- Development: 30-90 days
- Production: 30 days
- CI/CD: 90 days with monitoring

**Rotate before expiration:**
1. Generate new token
2. Update environment variable
3. Test connection
4. Revoke old token

### 4. Monitor Token Usage

**Check Azure DevOps audit logs:**
```
https://dev.azure.com/{organization}/_settings/tokens
```

Look for:
- Unexpected usage patterns
- Failed authentication attempts
- Tokens used from unknown IPs

## Troubleshooting

### Error: "PAT token not found or invalid"

**Check environment variable:**
```bash
# Linux/Mac
echo $AZURE_DEVOPS_EXT_PAT

# Windows PowerShell
echo $env:AZURE_DEVOPS_EXT_PAT

# Should output your token (not empty)
```

**Verify token is valid:**
```bash
curl -u :$AZURE_DEVOPS_EXT_PAT \
  https://dev.azure.com/{organization}/_apis/projects?api-version=7.1

# Should return JSON with your projects, not 401 Unauthorized
```

**Check token hasn't expired:**
- Navigate to https://dev.azure.com/{organization}/_usersSettings/tokens
- Look for your token in the list
- Check expiration date

### Error: "Invalid Azure DevOps organization URL"

**Check organization URL format:**
```yaml
# ✅ CORRECT
organization: "https://dev.azure.com/myorg"

# ❌ WRONG - missing https://
organization: "dev.azure.com/myorg"

# ❌ WRONG - has trailing slash
organization: "https://dev.azure.com/myorg/"

# ❌ WRONG - includes project
organization: "https://dev.azure.com/myorg/MyProject"
```

### Error: "Azure DevOps project not configured"

**Check project name is exact match:**
```yaml
# Project names are case-sensitive
project: "Trusted AI Development Workbench"  # ✅ Exact match

# ❌ WRONG - case mismatch
project: "trusted ai development workbench"
```

**Verify project exists:**
```bash
python3 -c "
import requests
import os
import base64

token = os.environ.get('AZURE_DEVOPS_EXT_PAT')
org = 'https://dev.azure.com/your-org'

auth = base64.b64encode(f':{token}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}'}

response = requests.get(f'{org}/_apis/projects?api-version=7.1', headers=headers)
projects = response.json()['value']

print('Available projects:')
for p in projects:
    print(f'  - {p[\"name\"]}')
"
```

### Error: "Authentication failed (401)"

**Causes:**
1. Token expired
2. Token revoked
3. Incorrect token format
4. Token lacks required scopes

**Fix:**
1. Generate new token with correct scopes
2. Update AZURE_DEVOPS_EXT_PAT
3. Test connection

### Error: "Permission denied (403)"

**Causes:**
- Token has insufficient permissions
- Project access restricted

**Fix:**
1. Regenerate token with correct scopes:
   - Work Items: Read, Write, & Manage
   - Code: Read
2. Verify project membership
3. Check project permissions

## CI/CD Setup

### GitHub Actions

**.github/workflows/trustable-ai.yml:**
```yaml
name: Trustable AI Workflows

on: [push]

jobs:
  sprint-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Trustable AI
        run: pip install trustable-ai

      - name: Run Sprint Review
        env:
          AZURE_DEVOPS_EXT_PAT: ${{ secrets.AZURE_DEVOPS_PAT }}
        run: |
          python3 scripts/sprint_review_v2.py --sprint "Sprint 7"
```

**GitHub Secrets:**
1. Go to repo Settings → Secrets → Actions
2. Add secret: `AZURE_DEVOPS_PAT`
3. Paste your PAT token

### GitLab CI

**.gitlab-ci.yml:**
```yaml
sprint-review:
  stage: test
  image: python:3.11
  variables:
    AZURE_DEVOPS_EXT_PAT: $CI_AZURE_PAT
  script:
    - pip install trustable-ai
    - python3 scripts/sprint_review_v2.py --sprint "Sprint 7"
```

**GitLab CI/CD Variables:**
1. Go to Settings → CI/CD → Variables
2. Add variable: `CI_AZURE_PAT`
3. Paste your PAT token
4. Check "Mask variable"

### Azure DevOps Pipeline

**azure-pipelines.yml:**
```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: |
    pip install trustable-ai
  displayName: 'Install Trustable AI'

- script: |
    python3 scripts/sprint_review_v2.py --sprint "Sprint 7"
  displayName: 'Run Sprint Review'
  env:
    AZURE_DEVOPS_EXT_PAT: $(AzurePAT)
```

**Pipeline Variables:**
1. Edit pipeline → Variables
2. Add variable: `AzurePAT`
3. Paste PAT token
4. Check "Keep this value secret"

## Advanced Configuration

### Multiple Organizations

**Use different tokens per organization:**

```bash
# Organization 1
export AZURE_DEVOPS_EXT_PAT_ORG1="token1"

# Organization 2
export AZURE_DEVOPS_EXT_PAT_ORG2="token2"
```

**.claude/config.yaml:**
```yaml
work_tracking:
  organization: "https://dev.azure.com/org1"
  project: "Project1"
  credentials_source: "env:AZURE_DEVOPS_EXT_PAT_ORG1"
```

### Token Refresh Automation

**Script to check token expiration:**

```python
import os
import requests
import base64
from datetime import datetime

def check_token_expiration():
    """Check if Azure DevOps PAT token is expiring soon."""
    token = os.environ.get('AZURE_DEVOPS_EXT_PAT')
    org = "https://dev.azure.com/your-org"

    # Test token validity
    auth = base64.b64encode(f':{token}'.encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}

    response = requests.get(f'{org}/_apis/projects?api-version=7.1', headers=headers)

    if response.status_code == 401:
        print("⚠️  Token expired or invalid - please regenerate")
        return False
    elif response.status_code == 200:
        print("✅ Token valid")
        return True
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
        return False

if __name__ == '__main__':
    check_token_expiration()
```

## Summary

**Setup Checklist:**
- [ ] Generate PAT token with Work Items permissions
- [ ] Set AZURE_DEVOPS_EXT_PAT environment variable
- [ ] Configure .claude/config.yaml with organization and project
- [ ] Test connection with get_adapter()
- [ ] Add .env to .gitignore
- [ ] Set token expiration reminder (30-90 days)

**Security Checklist:**
- [ ] Never commit tokens to git
- [ ] Use environment variables for tokens
- [ ] Set minimum required scopes
- [ ] Enable token expiration
- [ ] Monitor token usage in Azure DevOps
- [ ] Rotate tokens regularly

**You're ready to use Trustable AI with Azure DevOps!** 🎉
