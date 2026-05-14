# Lesson: OOMKilled Detection in Troubleshooting

**Date:** 2024-01-16
**Category:** Kubernetes

## Issue

Users with crashing pods weren't able to quickly identify if pods were OOMKilled (Out of Memory Killed). The issue was buried in pod status and required multiple commands to diagnose.

## Solution

Add comprehensive OOMKilled detection as part of standard troubleshooting workflow. Check both:
1. Termination reason contains "OOMKilled"
2. Exit code is 137 (128 + 9 = SIGKILL, commonly OOM)

## Code Pattern

```python
def check_oomkilled(pod_name, namespace):
    # Check termination reason
    reason_cmd = f"kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.reason}}'"
    stdout, _, _ = run_cmd(reason_cmd)
    
    if 'OOMKilled' in stdout:
        return True, "Pod was OOMKilled"
    
    # Check exit code 137
    exit_cmd = f"kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.exitCode}}'"
    stdout, _, _ = run_cmd(exit_cmd)
    
    if stdout.strip() == '137':
        return True, "Exit code 137 indicates OOMKill"
    
    return False, "Not OOMKilled"
```

## Troubleshooting Steps

1. Get pod phase: `kubectl get pod <name> -n <ns> -o jsonpath='{.status.phase}'`
2. Check restart count: `kubectl get pod <name> -n <ns> -o jsonpath='{.status.containerStatuses[*].restartCount}'`
3. Check termination reason: `kubectl get pod <name> -n <ns> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'`
4. Get previous logs: `kubectl logs <name> -n <ns> --previous`
5. Check events: `kubectl get events -n <ns> --field-selector involvedObject.name=<name>`

## Recommendations

If OOMKilled:
- Increase memory limits in deployment
- Check for memory leaks in application
- Review actual memory usage vs limits
- Consider scaling replicas if single pod memory spikes