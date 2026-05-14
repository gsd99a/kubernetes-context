#!/usr/bin/env python3
"""
AKS Workflow Agent - Context-aware Kubernetes operations tool
Manages AKS operations with multi-context support and config file management
"""

import argparse
import json
import os
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class AKSWorkflowAgent:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.namespace = None
        self.subscription = None
        self.cluster_name = None
        self.resource_group = None

    def run_cmd(self, cmd: str, capture: bool = True, show_cmd: bool = True) -> tuple:
        if show_cmd:
            print(f"\n{Colors.CYAN}>>> {cmd}{Colors.ENDC}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=capture, text=True, timeout=60
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", 1
        except Exception as e:
            return "", str(e), 1

    def check_prerequisites(self) -> bool:
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}Checking Prerequisites...{Colors.ENDC}")
        _, kubectl_err, kubectl_rc = self.run_cmd("kubectl version --client", show_cmd=False)
        _, az_err, az_rc = self.run_cmd("az version", show_cmd=False)
        if kubectl_rc != 0:
            print(f"{Colors.RED}✗ kubectl not found!{Colors.ENDC}")
            print("  Install: https://kubernetes.io/docs/tasks/tools/")
            return False
        if az_rc == 0:
            print(f"{Colors.GREEN}✓ Azure CLI installed{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}⚠ Azure CLI not found (KeyVault features limited){Colors.ENDC}")
        print(f"{Colors.GREEN}✓ kubectl installed{Colors.ENDC}")
        return True

    def interactive_setup(self) -> bool:
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}AKS Workflow Agent - Setup Wizard{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")

        self.subscription = input(f"{Colors.CYAN}Azure Subscription ID or Name: {Colors.ENDC}").strip()
        if not self.subscription:
            print(f"{Colors.RED}Subscription is required!{Colors.ENDC}")
            return False

        self.resource_group = input(f"{Colors.CYAN}Resource Group Name: {Colors.ENDC}").strip()
        if not self.resource_group:
            print(f"{Colors.RED}Resource Group is required!{Colors.ENDC}")
            return False

        self.cluster_name = input(f"{Colors.CYAN}AKS Cluster Name: {Colors.ENDC}").strip()
        if not self.cluster_name:
            print(f"{Colors.RED}Cluster Name is required!{Colors.ENDC}")
            return False

        self.namespace = input(f"{Colors.CYAN}Default Namespace (optional, press Enter to skip): {Colors.ENDC}").strip()

        app_name = input(f"{Colors.CYAN}App/Service Name (for config naming): {Colors.ENDC}").strip()
        if not app_name:
            app_name = "default"

        keyvault = input(f"{Colors.CYAN}Azure KeyVault Name (optional): {Colors.ENDC}").strip()
        
        config_data = {
            'subscription': self.subscription,
            'resource_group': self.resource_group,
            'cluster_name': self.cluster_name,
            'namespace': self.namespace,
            'app_name': app_name,
            'keyvault': keyvault if keyvault else None,
            'created_at': datetime.now().isoformat()
        }

        config_file = f"config_{app_name}.yaml"
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            print(f"\n{Colors.GREEN}✓ Config saved to {config_file}{Colors.ENDC}")
            self.config_path = config_file
            self.config = config_data
        except Exception as e:
            print(f"{Colors.RED}Failed to save config: {e}{Colors.ENDC}")
            return False

        return self.configure_aks_context()

    def configure_aks_context(self) -> bool:
        print(f"\n{Colors.HEADER}Configuring AKS Context...{Colors.ENDC}")
        
        stdout, _, rc = self.run_cmd(
            f"az aks get-credentials --resource-group {self.resource_group} "
            f"--name {self.cluster_name} --overwrite-existing"
        )
        
        if rc != 0:
            print(f"{Colors.RED}Failed to configure kubectl context{Colors.ENDC}")
            return False
        
        current_ctx, _, _ = self.run_cmd("kubectl config current-context")
        print(f"{Colors.GREEN}✓ Context set to: {current_ctx.strip()}{Colors.ENDC}")
        return True

    def load_config(self, path: str) -> bool:
        try:
            with open(path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            self.subscription = self.config.get('subscription')
            self.resource_group = self.config.get('resource_group')
            self.cluster_name = self.config.get('cluster_name')
            self.namespace = self.config.get('namespace')
            self.config_path = path
            
            if not all([self.subscription, self.resource_group, self.cluster_name]):
                print(f"{Colors.RED}Config file missing required fields{Colors.ENDC}")
                return False
            
            print(f"{Colors.GREEN}✓ Config loaded from {path}{Colors.ENDC}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to load config: {e}{Colors.ENDC}")
            return False

    def get_resources(self, resource_type: str = "all") -> str:
        if not self.namespace:
            return "No namespace configured"
        
        if resource_type == "pods" or resource_type == "all":
            return self._get_pods()
        elif resource_type == "deployments":
            return self._get_deployments()
        elif resource_type == "services":
            return self._get_services()
        elif resource_type == "secrets":
            return self._get_secrets()
        elif resource_type == "configmaps":
            return self._get_configmaps()
        elif resource_type == "events":
            return self._get_events()
        elif resource_type == "all":
            return self._get_all_resources()
        return "Unknown resource type"

    def _get_pods(self) -> str:
        print(f"\n{Colors.HEADER}[ PODS ]{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl get pods -n {self.namespace} -o wide")
        return stdout if rc == 0 else f"Error: {stdout}"

    def _get_deployments(self) -> str:
        print(f"\n{Colors.HEADER}[ DEPLOYMENTS ]{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl get deployments -n {self.namespace}")
        return stdout if rc == 0 else f"Error: {stdout}"

    def _get_services(self) -> str:
        print(f"\n{Colors.HEADER}[ SERVICES ]{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl get svc -n {self.namespace}")
        return stdout if rc == 0 else f"Error: {stdout}"

    def _get_secrets(self) -> str:
        print(f"\n{Colors.HEADER}[ SECRETS ]{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl get secrets -n {self.namespace}")
        return stdout if rc == 0 else f"Error: {stdout}"

    def _get_configmaps(self) -> str:
        print(f"\n{Colors.HEADER}[ CONFIGMAPS ]{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl get configmap -n {self.namespace}")
        return stdout if rc == 0 else f"Error: {stdout}"

    def _get_events(self) -> str:
        print(f"\n{Colors.HEADER}[ EVENTS ]{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(
            f"kubectl get events -n {self.namespace} --sort-by='.lastTimestamp'"
        )
        return stdout if rc == 0 else f"Error: {stdout}"

    def _get_all_resources(self) -> str:
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}All Resources in Namespace: {self.namespace}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        
        self._get_pods()
        self._get_deployments()
        self._get_services()
        self._get_secrets()
        self._get_configmaps()
        self._get_events()
        return "Complete"

    def describe_resource(self, resource_type: str, name: str) -> str:
        if not self.namespace:
            return "No namespace configured"
        
        print(f"\n{Colors.HEADER}[ {resource_type.upper()}: {name} ]{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(
            f"kubectl describe {resource_type} {name} -n {self.namespace}"
        )
        return stdout if rc == 0 else f"Error: {rc}"

    def get_pod_logs(self, pod_name: str, previous: bool = False, 
                     container: str = "", tail: int = 100) -> str:
        if not self.namespace:
            return "No namespace configured"
        
        print(f"\n{Colors.HEADER}[ LOGS: {pod_name} ]{Colors.ENDC}")
        cmd = f"kubectl logs {pod_name} -n {self.namespace}"
        if previous:
            cmd += " --previous"
        if container:
            cmd += f" -c {container}"
        if tail:
            cmd += f" --tail={tail}"
        
        stdout, stderr, rc = self.run_cmd(cmd)
        return stdout + stderr if rc == 0 else f"Error: {stderr}"

    def troubleshoot_pod(self, pod_name: str) -> str:
        if not self.namespace:
            return "No namespace configured"
        
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}Troubleshooting Pod: {pod_name}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        
        checks = [
            ("Pod Status", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.phase}}'"),
            ("Restart Count", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.containerStatuses[*].restartCount}}'"),
            ("Container States", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.containerStatuses}}'"),
            ("Last Termination Reason", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.reason}}'"),
            ("Exit Code", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.exitCode}}'"),
            ("OOMKilled Check", f"kubectl get pod {pod_name} -n {self.namespace} -o json | grep -i oomkilled"),
        ]
        
        for name, cmd in checks:
            print(f"\n{Colors.YELLOW}{name}:{Colors.ENDC}")
            stdout, _, _ = self.run_cmd(cmd)
            if stdout.strip():
                print(stdout)
        
        print(f"\n{Colors.YELLOW}Describing Pod:{Colors.ENDC}")
        self.run_cmd(f"kubectl describe pod {pod_name} -n {self.namespace}")
        
        print(f"\n{Colors.YELLOW}Pod Events:{Colors.ENDC}")
        self.run_cmd(f"kubectl get events -n {self.namespace} --field-selector involvedObject.name={pod_name} --sort-by='.lastTimestamp'")
        
        return "Troubleshooting complete"

    def search_secret_usage(self, search_string: str) -> str:
        if not self.namespace:
            return "No namespace configured"
        
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}Searching for: '{search_string}' in namespace: {self.namespace}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        
        searches = [
            ("Kubernetes Secrets", f"kubectl get secrets -n {self.namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.data | tojson | @base64d | contains($s)) | .metadata.name'"),
            ("ConfigMaps", f"kubectl get configmap -n {self.namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.data | tojson | contains($s)) | .metadata.name'"),
            ("Deployments/Pods", f"kubectl get deployment,statefulset,daemonset,pod -n {self.namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.spec | tojson | contains($s)) | \"{{\\\"kind\\\": .kind, \\\"name\\\": .metadata.name}}\"'"),
        ]
        
        for name, cmd in searches:
            print(f"\n{Colors.YELLOW}{name}:{Colors.ENDC}")
            self.run_cmd(cmd)
        
        return "Search complete"

    def thread_dump(self, pod_name: str, container: str = "") -> str:
        if not self.namespace:
            return "No namespace configured"
        
        print(f"\n{Colors.HEADER}[ THREAD DUMP: {pod_name} ]{Colors.ENDC}")
        
        pid_cmd = f"kubectl exec {pod_name} -n {self.namespace}"
        if container:
            pid_cmd += f" -c {container}"
        pid_cmd += " -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print $1}'"
        
        stdout, _, _ = self.run_cmd(pid_cmd)
        java_pid = stdout.strip()
        
        if not java_pid:
            print(f"{Colors.RED}No Java process found!{Colors.ENDC}")
            return "No Java process found"
        
        print(f"Java PID: {java_pid}")
        
        dump_cmd = f"kubectl exec {pod_name} -n {self.namespace}"
        if container:
            dump_cmd += f" -c {container}"
        dump_cmd += f" -- jstack -l {java_pid}"
        
        stdout, stderr, rc = self.run_cmd(dump_cmd)
        if rc == 0:
            print(stdout)
            return "Thread dump successful"
        return f"Error: {stderr}"

    def heap_dump(self, pod_name: str, container: str = "") -> str:
        if not self.namespace:
            return "No namespace configured"
        
        print(f"\n{Colors.HEADER}[ HEAP DUMP: {pod_name} ]{Colors.ENDC}")
        
        pid_cmd = f"kubectl exec {pod_name} -n {self.namespace}"
        if container:
            pid_cmd += f" -c {container}"
        pid_cmd += " -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print $1}'"
        
        stdout, _, _ = self.run_cmd(pid_cmd)
        java_pid = stdout.strip()
        
        if not java_pid:
            return "No Java process found"
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"/tmp/heapdump-{timestamp}.hprof"
        
        dump_cmd = f"kubectl exec {pod_name} -n {self.namespace}"
        if container:
            dump_cmd += f" -c {container}"
        dump_cmd += f" -- jmap -dump:format=b,file={filename} {java_pid}"
        
        stdout, stderr, rc = self.run_cmd(dump_cmd)
        if rc == 0:
            self.run_cmd(f"kubectl cp {self.namespace}/{pod_name}:{filename} ./heapdump-{timestamp}.hprof")
            return f"Heap dump saved to heapdump-{timestamp}.hprof"
        return f"Error: {stderr}"

    def keyvault_operations(self, operation: str, name: str = "") -> str:
        keyvault = self.config.get('keyvault')
        if not keyvault:
            return "No KeyVault configured in config"
        
        if operation == "list":
            print(f"\n{Colors.HEADER}[ KEYVAULT: {keyvault} ]{Colors.ENDC}")
            self.run_cmd(f"az keyvault secret list --vault-name {keyvault} --output table 2>/dev/null")
            self.run_cmd(f"az keyvault certificate list --vault-name {keyvault} --output table 2>/dev/null")
            return "KeyVault listing complete"
        elif operation == "search" and name:
            self.run_cmd(f"az keyvault secret list --vault-name {keyvault} --output json 2>/dev/null | jq -r --arg s '{name}' '.[] | select(.id | test($s; \"i\")) | .id'")
            return "Search complete"
        return "Unknown operation"


def main():
    parser = argparse.ArgumentParser(description="AKS Workflow Agent - Context-aware Kubernetes operations")
    
    parser.add_argument("--config", "-c", help="Path to config.yaml file")
    parser.add_argument("--namespace", "-n", help="Kubernetes namespace")
    parser.add_argument("--resource", "-r", choices=[
        'pods', 'deployments', 'services', 'secrets', 'configmaps', 'events', 'all'
    ], help="Resource type to query")
    parser.add_argument("--describe", "-d", help="Describe specific resource (format: type/name)")
    parser.add_argument("--logs", "-l", help="Get logs for pod name")
    parser.add_argument("--previous", "-p", action="store_true", help="Get previous logs")
    parser.add_argument("--container", help="Container name for multi-container pods")
    parser.add_argument("--troubleshoot", "-t", help="Troubleshoot pod")
    parser.add_argument("--search-secret", "-s", help="Search for secret string")
    parser.add_argument("--thread-dump", help="Generate thread dump for pod")
    parser.add_argument("--heap-dump", help="Generate heap dump for pod")
    parser.add_argument("--keyvault", "-kv", choices=['list', 'search'], help="KeyVault operation")
    parser.add_argument("--keyvault-search", help="Search string in KeyVault")
    parser.add_argument("--setup", action="store_true", help="Run interactive setup")
    parser.add_argument("--list-contexts", action="store_true", help="List available kube contexts")
    parser.add_argument("--switch-context", help="Switch to context")
    
    args = parser.parse_args()
    agent = AKSWorkflowAgent(args.config)
    
    if args.setup:
        if not agent.interactive_setup():
            sys.exit(1)
        return
    
    if args.config:
        if not agent.load_config(args.config):
            sys.exit(1)
    else:
        config_files = list(Path(".").glob("config_*.yaml"))
        if config_files:
            print(f"{Colors.YELLOW}Found config files: {config_files}{Colors.ENDC}")
            print(f"{Colors.YELLOW}Use --config to specify which to use{Colors.ENDC}")
            print(f"{Colors.YELLOW}Or use --setup to create a new one{Colors.ENDC}")
    
    if not agent.check_prerequisites():
        sys.exit(1)
    
    if args.list_contexts:
        agent.run_cmd("kubectl config get-contexts")
        return
    
    if args.switch_context:
        agent.run_cmd(f"kubectl config use-context {args.switch_context}")
        return
    
    if args.namespace:
        agent.namespace = args.namespace
    
    if not agent.namespace:
        print(f"{Colors.YELLOW}No namespace specified. Use -n <namespace> or configure in config file{Colors.ENDC}")
    
    if args.resource:
        agent.get_resources(args.resource)
    
    if args.describe:
        parts = args.describe.split('/')
        if len(parts) == 2:
            agent.describe_resource(parts[0], parts[1])
    
    if args.logs:
        agent.get_pod_logs(args.logs, args.previous, args.container)
    
    if args.troubleshoot:
        agent.troubleshoot_pod(args.troubleshoot)
    
    if args.search_secret:
        agent.search_secret_usage(args.search_secret)
    
    if args.thread_dump:
        agent.thread_dump(args.thread_dump, args.container)
    
    if args.heap_dump:
        agent.heap_dump(args.heap_dump, args.container)
    
    if args.keyvault:
        agent.keyvault_operations(args.keyvault, args.keyvault_search)


if __name__ == "__main__":
    main()