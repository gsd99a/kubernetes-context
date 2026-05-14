# Lesson: Azure Authentication Handling

**Date:** 2024-01-17
**Category:** Azure

## Issue

Agent would fail completely if Azure CLI was not authenticated, even for operations that only needed kubectl (like viewing pods). This frustrated users who didn't need KeyVault features.

## Solution

Implement graceful degradation:
1. Check Azure CLI availability at startup (optional warning)
2. Only require `az login` for KeyVault operations
3. Continue with kubectl-only operations regardless of Azure auth status
4. Provide clear messaging about which features are available

## Code Pattern

```python
def check_az_availability():
    _, az_err, az_rc = run_cmd("az version", show_cmd=False)
    
    if az_rc != 0:
        print(f"{Colors.YELLOW}⚠ Azure CLI not found or not logged in{Colors.ENDC}")
        print(f"  KeyVault features will be unavailable")
        print(f"  Run 'az login' to authenticate")
        return False
    return True

def keyvault_operation():
    if not check_az_availability():
        print(f"{Colors.RED}Cannot perform KeyVault operation{Colors.ENDC}")
        return
    # ... proceed with KeyVault operations
```

## Available Without Azure Auth

- List pods/deployments/services
- Get pod logs
- Describe resources
- Troubleshoot pods
- Thread/heap dumps

## Requires Azure Auth

- KeyVault operations
- Azure-specific resource queries
- Subscription/cluster info via az CLI

## Best Practice

Always provide informative messages:
- What's working
- What's not working
- How to fix it