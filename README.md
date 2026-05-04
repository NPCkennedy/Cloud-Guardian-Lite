# Cloud Guardian Lite

An Azure compliance scanner that detects untagged cloud resources and sends real-time alerts via Microsoft Teams.

Built to address **MAS TRM 2021 Section 9.1.2** — financial institutions must maintain a cloud asset inventory with clearly defined ownership and accountability. Untagged resources create a direct compliance gap.

---

## What It Does

1. Connects to Azure using `DefaultAzureCredential`
2. Scans a resource group for resources missing required governance tags
3. Writes a timestamped JSON compliance report
4. Sends a Microsoft Teams alert with violation details
5. Runs automatically on every push and daily at 9am SGT via GitHub Actions

**Required tags checked:**
- `Owner` — who is responsible for this resource
- `Environment` — dev, staging, or production
- `CostCenter` — internal billing code for chargeback

---

## Demo

Push a commit to trigger the pipeline. Within 60 seconds:

1. GitHub Actions spins up a fresh runner
2. Scanner authenticates to Azure via Service Principal
3. Detects untagged resources in the resource group
4. Writes `violations.json` — downloadable as a pipeline artifact
5. Sends Teams alert with violation details

![Demo flow]

```
git push
      ↓
GitHub Actions triggered
      ↓
Authenticated via Service Principal (Reader role only)
      ↓
Scanned resource group — violations detected
      ↓
violations.json uploaded as artifact
      ↓
Teams alert sent
```

---

## Sample Output

**Terminal / Pipeline logs:**
```
INFO  — Successfully authenticated with Azure
INFO  — Scanning resource group: cloud-guardian-rg
INFO  — Found 2 resources
WARNING — Violation: test-nsg-1 missing ['Owner', 'Environment', 'CostCenter']
WARNING — Violation: test-nsg-2 missing ['Owner', 'Environment', 'CostCenter']
INFO  — scan complete. 2 violations found.
INFO  — Report written to violations.json
WARNING — Scan complete. 2 violations found. Review violations.json
```

**violations.json:**
```json
{
  "scan_timestamp": "2026-05-04T14:59:36.816977+00:00",
  "total_violations": 2,
  "violations": [
    {
      "resource_name": "test-nsg-1",
      "resource_type": "Microsoft.Network/networkSecurityGroups",
      "missing_tags": ["Owner", "Environment", "CostCenter"]
    },
    {
      "resource_name": "test-nsg-2",
      "resource_type": "Microsoft.Network/networkSecurityGroups",
      "missing_tags": ["Owner", "Environment", "CostCenter"]
    }
  ]
}
```

**Teams alert:**
```
⚠️ Cloud Guardian Alert — 2 violation(s) found
• test-nsg-1 (Microsoft.Network/networkSecurityGroups): missing Owner, Environment, CostCenter
• test-nsg-2 (Microsoft.Network/networkSecurityGroups): missing Owner, Environment, CostCenter
```

---

## Prerequisites

- Python 3.11+
- Azure CLI installed — [install guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- Azure account with a resource group
- Microsoft Teams channel with Incoming Webhook configured
- GitHub account

---

## Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/NPCkennedy/Cloud-Guardian-Lite.git
cd Cloud-Guardian-Lite
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Authenticate to Azure**
```bash
az login
az account set --subscription "your-subscription-id"
```

**4. Configure environment variables**

Create a `.env` file in the repo root — never commit this file:
```
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group-name
TEAMS_WEBHOOK_URL=your-teams-webhook-url
```

**5. Run the scanner**
```bash
python -m src.scanner
```

---

## GitHub Actions Setup (Automated)

**1. Create a Service Principal**
```bash
az ad sp create-for-rbac \
  --name "cloud-guardian-sp" \
  --role "Reader" \
  --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP"
```

Note the output — `appId`, `password`, `tenant`. The password is shown only once.

**2. Add GitHub Secrets**

Go to your repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | appId from Service Principal |
| `AZURE_CLIENT_SECRET` | password from Service Principal |
| `AZURE_TENANT_ID` | tenant from Service Principal |
| `AZURE_SUBSCRIPTION_ID` | your Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | your resource group name |
| `TEAMS_WEBHOOK_URL` | your Teams incoming webhook URL |

**3. Push to trigger the pipeline**
```bash
git push
```

The scanner runs automatically on every push and daily at 9am SGT (1am UTC).

---

## Project Structure

```
cloud-guardian/
    src/
        __init__.py       — marks src/ as a Python package
        scanner.py        — connects to Azure, checks tags, orchestrates scan
        report.py         — writes timestamped violations.json
        notifier.py       — sends Teams alert via webhook
    tests/
        test_scanner.py   — unit tests
    .github/workflows/
        scanner.yml       — GitHub Actions pipeline
    .env.example        — environment variable template
    requirements.txt    — pinned dependencies
    README.md
```

---

## How It Works

**Authentication:**
Uses `DefaultAzureCredential` which tries a credential chain:
- Locally: falls through to `AzureCliCredential` — your `az login` session
- In GitHub Actions: uses `EnvironmentCredential` — GitHub Secrets injected as env vars

Same code. Different credential. No hardcoded secrets anywhere.

**Tag checking logic:**
```python
REQUIRED_TAGS = ["Owner", "Environment", "CostCenter"]

for resource in resources:
    if resource.tags is None:
        # all tags missing
    else:
        # check which required tags are absent
```

**Exit codes:**
- `exit(0)` — scan complete, no violations
- `exit(1)` — violations found OR script error

GitHub Actions marks the pipeline as failed on `exit(1)` — making violations immediately visible in the Actions tab.

---

## MAS TRM Context

MAS Technology Risk Management Guidelines 2021 Section 9.1.2 requires Singapore financial institutions to maintain an inventory of cloud assets with clearly defined ownership and accountability.

Cloud Guardian addresses this by:
- Detecting resources missing `Owner` attribution
- Detecting resources missing `Environment` classification
- Detecting resources missing `CostCenter` for billing accountability
- Producing a timestamped audit trail in `violations.json`
- Alerting the responsible team in real time via Teams

---

## Security

- Zero hardcoded credentials — all secrets via environment variables
- Service Principal scoped to `Reader` role on the resource group only — least privilege
- `.env` file excluded from git via `.gitignore`
- GitHub Secrets encrypted at rest — never visible in logs


---

## Tech Stack

- Python 3.11
- Azure SDK (`azure-identity`, `azure-mgmt-resource`)
- GitHub Actions
- Microsoft Teams (Incoming Webhook)
- `requests`, `python-dotenv`
