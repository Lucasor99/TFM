import os
import subprocess
import sys
import argparse
from kubernetes import client, config
import time

# Kubernetes access configuration
config.load_kube_config()

def run_command(command):
    """Run a shell command and return the output."""
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode().strip()

def label_nodes_with_ip():
    """Label nodes with their internal IPs if not already labeled."""
    nodes = run_command("kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}={.status.addresses[?(@.type==\"InternalIP\")].address} {end}'")
    node_array = nodes.split()

    for node_info in node_array:
        node_name, node_ip = node_info.split("=")
        # Check if the node is already labeled with the IP
        labels = run_command(f"kubectl get node {node_name} --show-labels")
        if f"ip={node_ip}" not in labels:
            # Label the node with its IP
            run_command(f"kubectl label node {node_name} ip={node_ip}")

def create_deployment(replicas):
    # Label nodes with their IPs if necessary
    label_nodes_with_ip()

    # Get the names of the nodes in the Kubernetes cluster
    nodes = run_command("kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\" \"}{end}'")
    node_array = nodes.split()

    # Check that the number of nodes matches the number of replicas
    if len(node_array) < replicas:
        print("Error: the number of available nodes is less than the number of replicas")
        sys.exit(1)

    # Generate PersistentVolumes
    with open('DeployFiles/cassandra-pv-template.yaml', 'r') as f:
        cassandra_pv_template = f.read()

    for i in range(replicas):
        pv = cassandra_pv_template.replace('${ID}', str(i)).replace('${NODE}', node_array[i])
        run_command(f"echo '{pv}' | kubectl apply -f -")

    # Generate StatefulSet and Service
    with open('DeployFiles/cassandra-statefulset-template.yaml', 'r') as f:
        cassandra_statefulset_template = f.read()
    
    cassandra_statefulset = cassandra_statefulset_template.replace('${REPLICAS}', str(replicas))
    run_command(f"echo '{cassandra_statefulset}' | kubectl apply -f -")

    # Wait for Cassandra pods to be in Running state
    print("Waiting for Cassandra pods to be in Running state...")
    while True:
        pods_status = run_command("kubectl get pods -l app=cassandra -o jsonpath='{.items[*].status.phase}'")
        if all(status == 'Running' for status in pods_status.split()):
            break
        time.sleep(5)
    
    print("All Cassandra pods are in Running state.")

    # Deploy the web service
    run_command("kubectl apply -f DeployFiles/web.yaml")
    
    # Wait for the web pod to be in Running state
    print("Waiting for the web pod to be in Running state...")
    while True:
        web_status = run_command("kubectl get pods -l app=web -o jsonpath='{.items[*].status.phase}'")
        if 'Running' in web_status.split():
            break
        time.sleep(5)
    
    print("The web pod is running. Access the service at http://localhost:30000")

    # Deploy the asn1scc service
    run_command("kubectl apply -f DeployFiles/asn1scc.yaml")

def copy_to_pod(files, pod_prefix, dest_dir):
    pod = run_command(f"kubectl get pods -l app={pod_prefix} -o jsonpath='{{.items[0].metadata.name}}'")
    for file in files:
        run_command(f"kubectl cp {file} {pod}:{dest_dir}")

def open_console(pod_prefix):
    pod = run_command(f"kubectl get pods -l app={pod_prefix} -o jsonpath='{{.items[0].metadata.name}}'")
    os.system(f"kubectl exec -it {pod} -- /bin/bash")

def main():
    parser = argparse.ArgumentParser(description="Manage deployments and file copies in Kubernetes.")
    parser.add_argument('-create', type=int, help="Create Auto Ground Station deployment with the specified number of replicas")
    parser.add_argument('-cpCSV', nargs='+', help="Copy one or more files to the asn1scc pod in the folder src/filesCSV/")
    parser.add_argument('-cpASN', nargs='+', help="Copy one or more files to the asn1scc pod in the folder src/filesASN/")
    parser.add_argument('-web', action='store_true', help="Open a console in the pod web")
    parser.add_argument('-asn', action='store_true', help="Open a console in the pod asn1scc")
    
    args = parser.parse_args()
    
    if args.create:
        create_deployment(args.create)
    
    if args.cpCSV:
        copy_to_pod(args.cpCSV, 'asn1scc', '/dmt/filesCSV/')
    
    if args.cpASN:
        copy_to_pod(args.cpASN, 'asn1scc', '/dmt/filesASN1/')
    
    if args.web:
        open_console('web')

    if args.asn:
        open_console('asn1scc')

if __name__ == '__main__':
    main()
