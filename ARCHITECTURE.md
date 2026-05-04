# Cloud Guardian Lite — Architecture

## Overview

Cloud Guardian Lite is a scheduled compliance scanner built on GitHub Actions and the Azure SDK. It runs automatically on every push and daily at 9am SGT, scanning an Azure resource group for missing governance tags and alerting the team via Microsoft Teams.

---

## Full Pipeline Flow

```
Developer pushes code
        │
        ▼
┌─────────────────────┐
│      GitHub         │
│  Detects push or    │
│  cron schedule      │
│  (1am UTC / 9am SGT)│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   GitHub Actions    │
│   Runner (Ubuntu)   │
│                     │
│  1. Checkout code   │
│  2. Install Python  │
│  3. pip install     │
│  4. Run scanner     │
└────────┬────────────┘
         │
         │  Injects GitHub Secrets as env vars:
         │  AZURE_CLIENT_ID
         │  AZURE_CLIENT_SECRET
         │  AZURE_TENANT_ID
         │  AZURE_SUBSCRIPTION_ID
         │  AZURE_RESOURCE_GROUP
         │  TEAMS_WEBHOOK_URL
         │
         ▼
┌─────────────────────┐
│     scanner.py      │
│                     │
│  DefaultAzureCredential
│  → EnvironmentCredential
│  → authenticates as │
│    Service Principal│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│       Azure         │
│  Resource Manager   │
│       API           │
│                     │
│  Lists all resources│
│  in resource group  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│     scanner.py      │
│                     │
│  Checks each resource
│  for required tags: │
│  • Owner            │
│  • Environment      │
│  • CostCenter       │
└────────┬────────────┘
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐    ┌───────────────────┐
│  No violations  │    │  Violations found  │
│                 │    │                   │
│  exit(0)        │    │  report.py        │
│  Pipeline: ✅   │    │  → violations.json │
└─────────────────┘    │                   │
                       │  notifier.py      │
                       │  → Teams alert    │
                       │                   │
                       │  exit(1)          │
                       │  Pipeline: ❌     │
                       └────────┬──────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
         ┌──────────────────┐   ┌──────────────────┐
         │  GitHub Actions  │   │  Microsoft Teams  │
         │  Artifact        │   │  Channel          │
         │                  │   │                   │
         │  violations.json │   │  ⚠️ Alert message │
         │  downloadable    │   │  with violation   │
         │  from Actions tab│   │  details          │
         └──────────────────┘   └──────────────────┘
```

---

## Component Breakdown

### GitHub Actions — `scanner.yml`
The orchestration layer. Defines when the pipeline runs and what steps execute on the runner. Two triggers: push to master branch, and daily cron schedule.

### GitHub Secrets
Encrypted storage for all credentials. Injected as environment variables at runtime — never visible in logs or code. Six secrets configured:
- `AZURE_CLIENT_ID` — Service Principal identity
- `AZURE_CLIENT_SECRET` — Service Principal password
- `AZURE_TENANT_ID` — Azure directory
- `AZURE_SUBSCRIPTION_ID` — Azure account
- `AZURE_RESOURCE_GROUP` — target resource group
- `TEAMS_WEBHOOK_URL` — Teams incoming webhook

### `scanner.py`
Core logic. Authenticates to Azure, lists resources, checks tags, orchestrates report and alert.

### `report.py`
Writes `violations.json` with UTC timestamp, total violation count, and per-resource details.

### `notifier.py`
Sends HTTP POST to Teams incoming webhook with formatted violation summary.

### Azure Resource Manager API
Microsoft's management plane API. Returns all resources in the target resource group including their tag dictionaries.

### Azure Service Principal
Non-human identity used by GitHub Actions to authenticate to Azure. Scoped to `Reader` role on the resource group only — least privilege. Cannot create, modify, or delete resources.

---

## Authentication Flow

```
GitHub Actions Runner
        │
        │  Reads env vars:
        │  AZURE_CLIENT_ID
        │  AZURE_CLIENT_SECRET  
        │  AZURE_TENANT_ID
        │
        ▼
DefaultAzureCredential
        │
        │  Tries credential chain:
        │  1. EnvironmentCredential ✅ (finds the env vars)
        │  2. (stops here — no need to continue)
        │
        ▼
Azure AD issues access token
        │
        ▼
ResourceManagementClient uses token
to call Azure Resource Manager API
```

**Locally (development):**
```
DefaultAzureCredential
        │
        │  Tries credential chain:
        │  1. EnvironmentCredential ❌ (no env vars set)
        │  2. ManagedIdentityCredential ❌ (not in Azure)
        │  3. AzureCliCredential ✅ (az login session found)
        │
        ▼
Authenticated via az login session
```

Same code. Different credential. No changes needed between environments.

---

## Exit Code Design

| Scenario | Exit Code | Pipeline Status |
|---|---|---|
| No violations found | `0` | ✅ Pass |
| Violations found | `1` | ❌ Fail |
| Authentication error | `1` | ❌ Fail |
| Azure API error | `1` | ❌ Fail |
| Report write error | `1` | ❌ Fail |
| Teams alert error | `1` | ❌ Fail |

Pipeline failure on violations is intentional — it makes compliance issues immediately visible in the GitHub Actions tab and can trigger notifications to the on-call engineer.

---

## Security Design

```
Principle: Least Privilege

Service Principal
  └── Reader role only
  └── Scoped to resource group only
  └── Cannot modify or delete anything
  └── If credentials leak → read-only blast radius

GitHub Secrets
  └── Encrypted at rest
  └── Never visible in logs (shown as ***)
  └── Not accessible to forked repos

.env file
  └── Local development only
  └── In .gitignore — never committed
  └── .env.example shows required variables without real values
```

---

## Data Flow

```
Azure Resource Manager API
        │
        │  Returns resource objects:
        │  resource.name
        │  resource.type
        │  resource.tags  ← dict or None
        │
        ▼
Tag checker
        │
        │  For each resource:
        │  if tags is None → all 3 tags missing
        │  else → check Owner, Environment, CostCenter
        │
        ▼
Violations list
[
  {
    "resource_name": "test-nsg-1",
    "resource_type": "Microsoft.Network/networkSecurityGroups",
    "missing_tags": ["Owner", "Environment", "CostCenter"]
  }
]
        │
        ├──────────────────┐
        ▼                  ▼
violations.json      Teams webhook
(audit trail)        (real-time alert)
```

---

## Production Considerations

This project uses GitHub Actions managed runners and a basic Teams webhook. In a production environment you would consider:

| Current | Production equivalent |
|---|---|
| GitHub Actions runners | Self-hosted runners inside VNet |
| Teams webhook | Azure Monitor + PagerDuty integration |
| violations.json artifact | Azure Blob Storage for long-term audit trail |
| Single resource group scan | Multi-subscription scan |
| Scheduled detection | Azure Policy for real-time enforcement |
| Reader SP on resource group | Managed Identity on Azure Function App |
