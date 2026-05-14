# AKS Workflow Agent - Skills

## Overview

This document defines the skills and capabilities for the AKS Workflow Agent. When invoked, the agent should use these skills to assist users with Kubernetes/AKS operations.

---

## Core Skills

### Skill 1: Config Management

**Trigger Phrases:**
- "setup agent"
- "configure aks"
- "new config"
- "create config"
- "initialize"
- "first time setup"

**Actions:**
1. If user is new → Run interactive setup wizard
2. Collect: subscription, resource_group, cluster_name, namespace, app_name, keyvault
3. Save config to `config_<appname>.yaml`
4. Configure kubectl context using `az aks get-credentials`

**Commands:**
```bash
# Check if kubectl and az are available
kubectl version --client
az version

# Run setup
python aks-workflow-agent.py --setup

# Use existing config
python aks-workflow-agent.py --config config_<app>.yaml
```

---

### Skill 2: Resource Query (Namespace-based)

**Trigger Phrases:**
- "get pods"
- "list deployments"
- "show services"
- "check resources"
- "namespace status"
- "what's running"
- "all resources"

**Actions:**
1. Verify namespace is configured
2. Query specified resource type (or all)
3. Display results with clear headers

**Commands:**
```bash
# All resources
kubectl get all -n <namespace>

# Specific resources
kubectl get pods -n <namespace> -o wide
kubectl get deployments -n <namespace>
kubectl get svc -n <namespace>
kubectl get secrets -n <namespace>
kubectl get configmap -n <namespace>
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

---

### Skill 3: Pod Operations

**Trigger Phrases:**
- "pod logs"
- "describe pod"
- "get pod details"
- "pod status"
- "check pod"
- "pod info"

**Actions:**
1. Get pod status and details
2. Retrieve logs (current and previous if crashed)
3. Check events related to pod

**Commands:**
```bash
# Get pods
kubectl get pods -n <namespace>

# Describe pod
kubectl describe pod <pod-name> -n <namespace>

# Logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous
kubectl logs <pod-name> -c <container> -n <namespace>

# Events
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name> --sort-by='.lastTimestamp'
```

---

### Skill 4: Troubleshooting

**Trigger Phrases:**
- "troubleshoot"
- "debug pod"
- "crashing"
- "restarting"
- "failed"
- "pod issues"
- "OOMKilled"
- "evicted"

**Actions:**
1. Check pod status and phase
2. Check restart count
3. Check container states
4. Check termination reason and exit code
5. Check for OOMKilled
6. Get events

**Commands:**
```bash
# Pod status
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.phase}'

# Restart count
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].restartCount}'

# Termination reason
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'

# Exit code
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}'

# Previous logs
kubectl logs <pod-name> -n <namespace> --previous

# OOMKilled check
kubectl get pod <pod-name> -n <namespace> -o json | jq '.status.containerStatuses[] | select(.lastState.terminated.reason == "OOMKilled")'
```

---

### Skill 5: Secret Management

**Trigger Phrases:**
- "list secrets"
- "get secret"
- "search secret"
- "where is secret"
- "secret usage"
- "find secret"

**Actions:**
1. List secrets in namespace
2. Search secret string across secrets, configmaps, deployments
3. Report all matches

**Commands:**
```bash
# List secrets
kubectl get secrets -n <namespace>

# Get secret value
kubectl get secret <secret-name> -n <namespace> -o jsonpath='{.data}' | jq -r 'to_entries[] | @base64d'

# Search secret string
kubectl get secrets -n <namespace> -o json | jq -r --arg s "<string>" '.items[] | select(.data | tojson | @base64d | contains($s)) | .metadata.name'

kubectl get configmap -n <namespace> -o json | jq -r --arg s "<string>" '.items[] | select(.data | tojson | contains($s)) | .metadata.name'

kubectl get deployment,statefulset,daemonset,pod -n <namespace> -o json | jq -r --arg s "<string>" '.items[] | select(.spec | tojson | contains($s)) | {type: .kind, name: .metadata.name}'
```

---

### Skill 6: Java Diagnostics

**Trigger Phrases:**
- "thread dump"
- "heap dump"
- "memory dump"
- "jstack"
- "jmap"
- "java diagnostics"
- "analyze memory"
- "deadlock"

**Actions:**
1. Find Java PID in container
2. Generate thread dump with jstack
3. Generate heap dump with jmap
4. Copy dumps to local machine

**Commands:**
```bash
# Find Java PID
kubectl exec <pod> -n <namespace> -c <container> -- jps -l

# Thread dump
kubectl exec <pod> -n <namespace> -c <container> -- jstack -l <pid>

# Heap dump
kubectl exec <pod> -n <namespace> -c <container> -- jmap -dump:format=b,file=/tmp/heapdump.hprof <pid>

# Copy dump
kubectl cp <namespace>/<pod>:/tmp/heapdump.hprof ./heapdump.hprof

# Heap histogram
kubectl exec <pod> -n <namespace> -c <container> -- jmap -histo <pid>
```

---

### Skill 7: KeyVault Operations

**Trigger Phrases:**
- "keyvault"
- "azure vault"
- "list vault"
- "search vault"
- "get vault secret"

**Actions:**
1. Verify KeyVault name in config
2. List secrets, certificates, keys
3. Search for string in KeyVault

**Commands:**
```bash
# List secrets
az keyvault secret list --vault-name <keyvault-name> --output table

# Get secret
az keyvault secret show --name <secret-name> --vault-name <keyvault-name>

# List certificates
az keyvault certificate list --vault-name <keyvault-name> --output table

# List keys
az keyvault key list --vault-name <keyvault-name> --output table

# Search
az keyvault secret list --vault-name <keyvault-name> --output json | jq -r --arg s "<string>" '.[] | select(.id | test($s; "i"))'
```

---

## Workflow Guidelines

### First-Time User Workflow

1. **Greet user** and identify if new or existing
2. **If new user:**
   - Run `--setup` wizard
   - Collect all required inputs
   - Save config to `config_<appname>.yaml`
   - Configure AKS context
3. **If existing user:**
   - Prompt for config file path
   - Load and validate config

### Resource Query Workflow

1. **Confirm namespace** from config or CLI argument
2. **Determine resource type** from request
3. **Execute kubectl commands**
4. **Format and display results**
5. **Suggest next actions** if issues found

### Troubleshooting Workflow

1. **Identify problem** from user description
2. **Check pod status** and restart counts
3. **Get logs** (current and previous if crashed)
4. **Check events** related to pod
5. **Identify root cause** from termination reason/exit code
6. **Provide recommendations**

---

## Error Handling Patterns

| Error Type | Detection | Resolution |
|------------|-----------|------------|
| No namespace | `namespace` is None | Prompt for namespace or use config default |
| No config file | File not found | Suggest `--setup` or provide path |
| Auth failure | kubectl returns error | Suggest `az login` and context check |
| Pod not found | Resource doesn't exist | List available pods |
| Permission denied | Forbidden error | Check RBAC bindings |
| OOMKilled | Exit code 137 or OOMKilled reason | Suggest increasing memory limits |

---

## Response Formatting

When responding to user requests, follow this format:

```
[ SECTION HEADER ]

<command output>

[ SECTION HEADER ]

<command output>
```

Or for simple queries:
```
<formatted output with clear spacing>
```

Always include:
- Clear headers for each section
- Actionable summary at the end
- Next steps if issues found