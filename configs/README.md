# Example Config Files

This directory contains sample and template config files for the AKS Workflow Agent.

## Config File Format

```yaml
subscription: "your-subscription-id"
resource_group: "your-resource-group"
cluster_name: "your-aks-cluster-name"
namespace: "default"
app_name: "example"
keyvault: "your-keyvault-name"
created_at: "2024-01-01T00:00:00"
```

## Usage

1. Copy `config_example.yaml` to `config_<yourapp>.yaml`
2. Edit with your values
3. Use with: `python aks-workflow-agent.py --config configs/config_yourapp.yaml`

## Naming Convention

Config files should be named: `config_<appname>.yaml`

Examples:
- `config_production.yaml`
- `config_staging.yaml`
- `config_dev.yaml`
- `config_webapp.yaml`