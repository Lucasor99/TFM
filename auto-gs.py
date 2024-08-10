import os
import subprocess
import sys
import argparse
from kubernetes import client, config
import time

# Kubernetes access configuration
config.load_kube_config()

def run_command(command):
    """Run a shell command and return the output, error, and exit code."""
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode().strip() if result.stdout else ''
        stderr = result.stderr.decode().strip() if result.stderr else ''
        return stdout, stderr, result.returncode
    except Exception as e:
        return '', str(e), 1

def label_nodes_with_ip():
    """Label nodes with their internal IPs if not already labeled."""
    nodes, _, _ = run_command("kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}={.status.addresses[?(@.type==\"InternalIP\")].address} {end}'")
    node_array = nodes.split()

    for node_info in node_array:
        node_name, node_ip = node_info.split("=")
        # Check if the node is already labeled with the IP
        labels, _, _ = run_command(f"kubectl get node {node_name} --show-labels")
        if f"ip={node_ip}" not in labels:
            # Label the node with its IP
            run_command(f"kubectl label node {node_name} ip={node_ip}")

def create_deployment(replicas, rf):
    # Label nodes with their IPs if necessary
    label_nodes_with_ip()

    # Get the names of the nodes in the Kubernetes cluster
    nodes, _, _ = run_command("kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\" \"}{end}'")
    node_array = nodes.split()
    print(f"Number of available nodes is {len(node_array)}")

    # Check that the number of nodes matches the number of replicas
    if len(node_array) < replicas:
        print("Error: the number of available nodes is less than the number of replicas")
        sys.exit(1)

    # Create the secrets
    run_command("kubectl apply -f DeployFiles/secrets.yaml")
    print("Creating secrets...")

    # Create the network policies
    run_command("kubectl apply -f DeployFiles/networkPolicies.yaml")
    print("Creating network policies...")


    # Generate PersistentVolumes
    with open('DeployFiles/cassandra-pv-template.yaml', 'r') as f:
        cassandra_pv_template = f.read()

    for i in range(replicas):
        pv = cassandra_pv_template.replace('${ID}', str(i)).replace('${NODE}', node_array[i])
        run_command(f"echo '{pv}' | kubectl apply -f -")

    # Generate StatefulSet and Service
    with open('DeployFiles/cassandra-statefulset-template.yaml', 'r') as f:
        cassandra_statefulset_template = f.read()
    
    cassandra_statefulset = cassandra_statefulset_template.replace('${REPLICAS}', str(replicas)).replace('${RF}', str(rf))
    run_command(f"echo '{cassandra_statefulset}' | kubectl apply -f -")

    # Wait for Cassandra pods to be in Running state
    print("Waiting for Cassandra pods to be in Running state...")
    while True:
        pods_status, _, _ = run_command("kubectl get pods -l app=cassandra -o jsonpath='{.items[*].status.phase}'")
        if all(status == 'Running' for status in pods_status.split()):
            break
        time.sleep(5)
    
    print("All Cassandra pods are in Running state.")

    # Deploy the mysql deployment
    run_command("kubectl apply -f DeployFiles/mysql.yaml")

    # Create the keyspace with the specified replication factor
    create_keyspace(rf)

    # Deploy the web service
    run_command("kubectl apply -f DeployFiles/web.yaml")
    
    # Wait for the web pod to be in Running state
    print("Waiting for the web pod to be in Running state...")
    while True:
        web_status, _, _ = run_command("kubectl get pods -l app=web -o jsonpath='{.items[*].status.phase}'")
        if 'Running' in web_status.split():
            break
        time.sleep(5)
    
    print("The web pod is running. Access on-premise the service at http://localhost:30000")

    # Deploy the asn1scc service
    run_command("kubectl apply -f DeployFiles/asn1scc.yaml")
    print("Deploying asn1scc service...")

    # Create nginx service
    run_command("kubectl apply -f DeployFiles/nginx.yaml")
    print("Deploying nginx service...")

def create_keyspace(rf):
    """Create the Cassandra keyspace with the given replication factor."""
    # Get one of the Cassandra pods
    pod, _, _ = run_command("kubectl get pods -l app=cassandra -o jsonpath='{.items[0].metadata.name}'")

    # Create the keyspace with the specified replication factor
    print(f"Creating keyspace 'tfm' with replication factor {rf}.")
    time.sleep(20)
    # Try to create the keyspace with the specified replication factor during Timeout seconds
    start_time = time.time()
    while True:
        stdout, stderr, returncode = run_command(f"kubectl exec -it {pod} -- cqlsh -e \"CREATE KEYSPACE IF NOT EXISTS tfm WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': {rf}}};\"")
        if returncode == 0:
            print("Keyspace 'tfm' created successfully.")
            break
        else:
            print(f"Failed to create keyspace: {stderr}")
        if time.time() - start_time > 120:  # Timeout after 2 minutes
            print(f"Error: Failed to create keyspace 'tfm' within 2 minutes. Last error: {stderr}")
            sys.exit(1)
        print("Retrying to create keyspace...")
        time.sleep(5)

def copy_to_pod(files, pod_prefix, dest_dir):
    pod, _, _ = run_command(f"kubectl get pods -l app={pod_prefix} -o jsonpath='{{.items[0].metadata.name}}'")
    for file in files:
        run_command(f"kubectl cp {file} {pod}:{dest_dir}")

def open_console(pod_prefix):
    pod, _, _ = run_command(f"kubectl get pods -l app={pod_prefix} -o jsonpath='{{.items[0].metadata.name}}'")
    os.system(f"kubectl exec -it {pod} -- /bin/bash")

def main():
    parser = argparse.ArgumentParser(description="Manage deployments and file copies in Kubernetes.")
    parser.add_argument('-create', type=int, help="Create Auto Ground Station deployment with the specified number of replicas")
    parser.add_argument('-rf', type=int, help="Replication factor for Cassandra keyspace", default=3)
    parser.add_argument('-cpCSV', nargs='+', help="Copy one or more files to the asn1scc pod in the folder src/filesCSV/")
    parser.add_argument('-cpASN', nargs='+', help="Copy one or more files to the asn1scc pod in the folder src/filesASN/")
    parser.add_argument('-web', action='store_true', help="Open a console in the pod web")
    parser.add_argument('-asn', action='store_true', help="Open a console in the pod asn1scc")
    
    args = parser.parse_args()
    
    if args.create:
        create_deployment(args.create, args.rf)
    
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
