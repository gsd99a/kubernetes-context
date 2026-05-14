# AKS Workflow Agent

A context-aware Kubernetes operations tool for Azure AKS with multi-config support, interactive setup, and comprehensive resource management.

## Features

- **Multi-config support** - Create/manage config files per app (`config_<appname>.yaml`)
- **Interactive setup** - Guided wizard for new users to configure AKS access
- **Context switching** - Switch between Kubernetes contexts easily
- **Comprehensive resources** - Query pods, deployments, services, secrets, configmaps, events
- **Troubleshooting** - Pod diagnostics, logs, thread/heap dumps
- **Secret search** - Search secret usage across all Kubernetes resources
- **Azure KeyVault** - Integrated KeyVault operations (if configured)

---

## Quick Start

### For New Users

```bash
# Run interactive setup
python aks-workflow-agent.py --setup

# Follow the prompts to enter:
# - Azure Subscription ID
# - Resource Group
# - AKS Cluster Name
# - Default Namespace (optional)
# - App name (for config file naming)
# - Azure KeyVault (optional)
```

### For Existing Users

```bash
# Use existing config file
python aks-workflow-agent.py --config config_myapp.yaml

# Or pass config path with namespace
python aks-workflow-agent.py --config config_prod.yaml -n production -r pods
```

---

## Usage

### Configuration Setup

```bash
# Create new config (interactive wizard)
python aks-workflow-agent.py --setup

# Use existing config file
python aks-workflow-agent.py --config config_<app>.yaml

# Config files are named: config_<appname>.yaml
```

### List Resources in Namespace

```bash
# List all resource types
python aks-workflow-agent.py --config config_prod.yaml -n production -r all

# List specific resources
python aks-workflow-agent.py --config config_prod.yaml -n production -r pods
python aks-workflow-agent.py --config config_prod.yaml -n production -r deployments
python aks-workflow-agent.py --config config_prod.yaml -n production -r services
python aks-workflow-agent.py --config config_prod.yaml -n production -r secrets
python aks-workflow-agent.py --config config_prod.yaml -n production -r configmaps
python aks-workflow-agent.py --config config_prod.yaml -n production -r events
```

### Pod Operations

```bash
# Get all pods with details
python aks-workflow-agent.py --config config_prod.yaml -n production -r pods

# Get logs
python aks-workflow-agent.py --config config_prod.yaml -n production -l mypod

# Get previous logs (crashed container)
python aks-workflow-agent.py --config config_prod.yaml -n production -l mypod --previous

# Get logs from specific container
python aks-workflow-agent.py --config config_prod.yaml -n production -l mypod -c mycontainer

# Describe pod
python aks-workflow-agent.py --config config_prod.yaml --describe pod/mypod

# Troubleshoot crashing pod
python aks-workflow-agent.py --config config_prod.yaml -n production -t mypod
```

### Secrets

```bash
# List secrets
python aks-workflow-agent.py --config config_prod.yaml -n production -r secrets

# Search for secret string usage
python aks-workflow-agent.py --config config_prod.yaml -n production -s "db-password"

# Search across all resources
python aks-workflow-agent.py --config config_prod.yaml -n production -s "api-key"
```

### Java Diagnostics

```bash
# Generate thread dump
python aks-workflow-agent.py --config config_prod.yaml -n production --thread-dump myjava-pod

# Generate thread dump for specific container
python aks-workflow-agent.py --config config_prod.yaml -n production --thread-dump mypod -c java-container

# Generate heap dump
python aks-workflow-agent.py --config config_prod.yaml -n production --heap-dump myjava-pod

# Copy from pod to local machine
kubectl cp production/mypod:/tmp/heapdump-*.hprof ./heapdump.hprof
```

### Context Management

```bash
# List available contexts
python aks-workflow-agent.py --list-contexts

# Switch to specific context
python aks-workflow-agent.py --switch-context prod-cluster

# Use context with namespace
python aks-workflow-agent.py --switch-context dev-cluster -n dev -r pods
```

### KeyVault Operations

```bash
# List KeyVault contents (requires keyvault in config)
python aks-workflow-agent.py --config config_prod.yaml --keyvault list

# Search in KeyVault
python aks-workflow-agent.py --config config_prod.yaml --keyvault search --keyvault-search "connection"
```

---

## Config File Format

```yaml
subscription: "your-subscription-id-or-name"
resource_group: "your-resource-group"
cluster_name: "your-aks-cluster-name"
namespace: "default-namespace"
app_name: "myapp"
keyvault: "your-keyvault-name"
created_at: "2024-01-15T10:30:00"
```

---

## Config File Naming Convention

The config file is named based on the app name you provide:

- App name `production` → `config_production.yaml`
- App name `webapp` → `config_webapp.yaml`
- App name `api-service` → `config_api-service.yaml`

---

## Workflow Examples

### Example 1: New User First-Time Setup

```bash
# 1. Clone repository
git clone https://github.com/yourrepo/aks-workflow-agent.git
cd aks-workflow-agent

# 2. Run setup wizard
python aks-workflow-agent.py --setup

# 3. Enter your details:
#    Azure Subscription ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
#    Resource Group: my-rg
#    AKS Cluster Name: my-aks-cluster
#    Default Namespace: production
#    App/Service Name: production-app
#    Azure KeyVault: my-keyvault (optional)

# 4. Config file created: config_production-app.yaml

# 5. Now use it
python aks-workflow-agent.py --config config_production-app.yaml -r pods
```

### Example 2: Existing Config User

```bash
# User already has config_production.yaml

# Query resources
python aks-workflow-agent.py --config config_production.yaml -n production -r pods

# Troubleshoot pod
python aks-workflow-agent.py --config config_production.yaml -n production -t mypod-xyz

# Search for secret
python aks-workflow-agent.py --config config_production.yaml -n production -s "db-connection"
```

### Example 3: Multi-Environment Workflow

```bash
# Dev environment
python aks-workflow-agent.py --config config_dev.yaml -n dev -r all

# Staging environment
python aks-workflow-agent.py --config config_staging.yaml -n staging -r all

# Production environment
python aks-workflow-agent.py --config config_prod.yaml -n production -r all
```

---

## Error Handling

### Common Issues

| Error | Solution |
|-------|----------|
| `No namespace configured` | Use `-n <namespace>` or set `namespace` in config file |
| `Config file not found` | Use `--setup` to create a new config |
| `kubectl not found` | Install kubectl: https://kubernetes.io/docs/tasks/tools/ |
| `az CLI error` | Run `az login` to authenticate |
| `Permission denied` | Check RBAC permissions for namespace |

### Prerequisites

- Python 3.7+
- `kubectl` configured
- `azure-cli` (for KeyVault features)
- `jq` (for JSON parsing)

### Install Prerequisites

```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl

# Azure CLI
curl -sL https://aka.ms/installazureclizyb | bash

# jq
apt-get install jq  # Ubuntu
brew install jq     # macOS
```

---

## Command Reference

| Command | Description |
|---------|-------------|
| `--setup` | Run interactive setup wizard |
| `--config <path>` | Use specific config file |
| `--list-contexts` | List kubectl contexts |
| `--switch-context <ctx>` | Switch kubectl context |
| `--namespace, -n` | Target namespace |
| `--resource, -r` | Resource type to query |
| `--describe, -d` | Describe resource (type/name) |
| `--logs, -l` | Get pod logs |
| `--troubleshoot, -t` | Troubleshoot pod issues |
| `--search-secret, -s` | Search secret usage |
| `--thread-dump` | Generate thread dump |
| `--heap-dump` | Generate heap dump |
| `--keyvault` | KeyVault operations |

---

## Files

| File | Description |
|------|-------------|
| `aks-workflow-agent.py` | Main agent script |
| `config_*.yaml` | Config files (per app) |
| `skills/` | Agent skill definitions |
| `agents/` | Agent behavior definitions |
| `lessons/` | Lessons learned |

---

## License

MIT