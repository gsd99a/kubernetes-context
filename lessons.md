# AKS Workflow Agent - Lessons Learned

This document tracks lessons learned, common pitfalls, and best practices discovered while building and using the AKS Workflow Agent.

---

## Configuration Management

### Lesson 1: Always Validate Config Before Use

**Issue:** Users forgetting to pass config file or using wrong path.

**Solution:**
- Scan for existing `config_*.yaml` files on startup
- Provide clear error message with setup instructions
- Support both relative and absolute paths

**Code Pattern:**
```python
config_files = list(Path(".").glob("config_*.yaml"))
if not config_files:
    print("No config files found. Use --setup to create one.")
```

---

### Lesson 2: Namespace Configuration Priority

**Issue:** Confusion about which namespace to use (config vs CLI).

**Solution:**
- CLI argument takes precedence over config
- Clear messaging about which namespace is active
- Error if no namespace specified anywhere

**Code Pattern:**
```python
if args.namespace:
    agent.namespace = args.namespace  # CLI takes precedence
# Otherwise use config namespace or error
```

---

## Azure Authentication

### Lesson 3: Handle Azure Auth Failures Gracefully

**Issue:** `az login` required but not always obvious to users.

**Solution:**
- Check `az account show` before KeyVault operations
- Provide clear instructions when auth fails
- Continue with kubectl-only operations even if Azure CLI fails

---

### Lesson 4: AKS Context Configuration

**Issue:** kubectl context not set correctly after config creation.

**Solution:**
- Always run `az aks get-credentials` during setup
- Verify context is set with `kubectl config current-context`
- Show user which context is active

**Code Pattern:**
```bash
az aks get-credentials --resource-group <rg> --name <cluster> --overwrite-existing
kubectl config current-context
```

---

## Kubernetes Operations

### Lesson 5: Multi-Container Pods

**Issue:** Users forgetting to specify container when pods have multiple containers.

**Solution:**
- Always prompt for or accept container name
- Document multi-container patterns clearly
- Show container names in pod listing

**Commands:**
```bash
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].name}'
kubectl logs <pod> -n <ns> -c <container>
```

---

### Lesson 6: Previous Logs for Crashed Containers

**Issue:** Users only checking current logs and missing crash information.

**Solution:**
- Always mention `--previous` flag when troubleshooting
- Show both current and previous logs in troubleshooting mode
- Check termination reason and exit code

**Key Insight:** Previous logs are only available if container restarted. After container is recreated, previous logs are lost.

---

### Lesson 7: OOMKilled Detection

**Issue:** OOMKilled pods not immediately obvious.

**Solution:**
- Check for OOMKilled in termination reason
- Check exit code 137 (128 + 9 = SIGKILL, often OOM)
- Include memory limits in troubleshooting output

**Commands:**
```bash
kubectl get pod <pod> -n <ns> -o json | jq '.status.containerStatuses[] | select(.lastState.terminated.reason == "OOMKilled")'
```

---

## Secret Management

### Lesson 8: Secret Search is Case-Sensitive

**Issue:** Search for "DB_PASSWORD" doesn't find "db_password".

**Solution:**
- Use case-insensitive search with `test($s; "i")`
- Document this behavior in search results
- Consider providing case-insensitive option

**Commands:**
```bash
kubectl get secrets -n <ns> -o json | jq -r --arg s "<string>" '.items[] | select(.data | tojson | @base64d | test($s; "i"))'
```

---

### Lesson 9: Secret Values are Base64 Encoded

**Issue:** Users trying to search decoded values without knowing encoding.

**Solution:**
- Always decode before searching
- Use `@base64d` filter in jq
- Document encoding in search results

---

## Java Diagnostics

### Lesson 10: Java Process Detection

**Issue:** No Java process found when trying thread/heap dump.

**Solution:**
- Check for `jps` command availability
- Fall back to `ps aux | grep java`
- Check if Java is running at all first
- Verify container has JDK (not just JRE)

**Commands:**
```bash
kubectl exec <pod> -n <ns> -c <container> -- which jstack jmap jps
kubectl exec <pod> -n <ns> -c <container> -- ps aux | grep java
```

---

### Lesson 11: Thread Dump Timing

**Issue:** Single thread dump may not capture intermittent issues.

**Solution:**
- Take multiple dumps (3) with 5-second intervals
- Compare to find patterns
- Use `-l` flag for lock information

**Pattern:**
```bash
for i in 1 2 3; do
  jstack -l <pid> >> /tmp/threaddump-$i.log
  [ $i -lt 3 ] && sleep 5
done
```

---

### Lesson 12: Heap Dump Size

**Issue:** Large heap dumps may not fit in `/tmp` or take too long.

**Solution:**
- Check available space before dump
- Consider heap histogram as alternative
- Use `live=true` option to only dump live objects
- Monitor pod resource usage during dump

---

## Best Practices

### Practice 1: Always Check Prerequisites First

```python
def check_prerequisites():
    # Check kubectl
    # Check az (if needed)
    # Provide install instructions if missing
```

---

### Practice 2: Use Timeouts for Long Operations

```python
subprocess.run(cmd, timeout=60)  # Don't hang forever
```

---

### Practice 3: Handle Errors at Each Step

```python
stdout, stderr, rc = run_cmd(cmd)
if rc != 0:
    print(f"Error: {stderr}")
    return None
```

---

### Practice 4: Clear Visual Feedback

```python
print(f"{Colors.HEADER}[ SECTION ]{Colors.ENDC}")
print(f"{Colors.GREEN}✓ Success{Colors.ENDC}")
print(f"{Colors.RED}✗ Error{Colors.ENDC}")
```

---

### Practice 5: Context Switching Safety

**Issue:** Users accidentally running commands in wrong cluster.

**Solution:**
- Always show current context before operations
- Require confirmation for production contexts
- Use context naming conventions (dev/staging/prod)

---

## Troubleshooting Flow

```
User Request
    ↓
Check Config → [No Config] → Run --setup
    ↓
Check Namespace → [No NS] → Prompt for namespace
    ↓
Check Prerequisites → [Missing] → Show install instructions
    ↓
Execute Operation
    ↓
Handle Errors → [Error] → Provide resolution
    ↓
Display Results
    ↓
Suggest Next Actions
```

---

## Security Considerations

### Consideration 1: Secret Values in Logs

**Risk:** Secret values may appear in logs if not careful.

**Practice:** Never log decoded secret values. Use `jq` with explicit field selection.

---

### Consideration 2: Config File Permissions

**Risk:** Config files may contain sensitive subscription IDs.

**Practice:** Set restrictive permissions on config files:
```bash
chmod 600 config_*.yaml
```

---

### Consideration 3: KeyVault Access

**Risk:** Unintended access to KeyVault secrets.

**Practice:**
- Only access KeyVault if explicitly configured
- Require user confirmation for sensitive operations
- Log all KeyVault access

---

## Performance Tips

### Tip 1: Use JSONPath for Specific Data

Instead of full YAML output:
```bash
# Fast - single field
kubectl get pod <pod> -n <ns> -o jsonpath='{.status.phase}'

# Slow - full YAML
kubectl get pod <pod> -n <ns> -o yaml
```

---

### Tip 2: Watch vs Get

```bash
# Continuous monitoring
kubectl get pods -n <ns> -w

# Single snapshot
kubectl get pods -n <ns>
```

---

### Tip 3: Label Selectors

```bash
# Only pods with specific label
kubectl get pods -n <ns> -l app=webapp

# Exclude completed jobs
kubectl get pods -n <ns> --field-selector=status.phase!=Succeeded
```

---

## Testing Checklist

- [ ] New user setup flow works
- [ ] Existing config file loads correctly
- [ ] Namespace from CLI overrides config
- [ ] All resource types return data
- [ ] Pod logs work (current and previous)
- [ ] Troubleshooting detects OOMKilled
- [ ] Secret search finds matches
- [ ] Thread dump generates file
- [ ] Heap dump copies to local
- [ ] KeyVault operations work (if configured)
- [ ] Error messages are helpful
- [ ] Color coding displays correctly

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Initial | Basic setup, config management, resource query |
| 1.1 | - | Added troubleshooting, thread/heap dumps |
| 1.2 | - | Added KeyVault support, secret search |