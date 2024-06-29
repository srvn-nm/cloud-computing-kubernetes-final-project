from kubernetes import client, config

def get_all_deployments_status():
    config.load_kube_config()  # Load kube config from the default location

    api_instance = client.AppsV1Api()
    deployments = api_instance.list_namespaced_deployment(namespace='default')
    
    all_deployments_status = []

    for deployment in deployments.items:
        status = {
            "DeploymentName": deployment.metadata.name,
            "Replicas": deployment.spec.replicas,
            "ReadyReplicas": deployment.status.ready_replicas,
            "PodStatuses": []
        }

        pod_api = client.CoreV1Api()
        pods = pod_api.list_namespaced_pod(namespace='default', label_selector=f"app={deployment.metadata.name}")

        for pod in pods.items:
            pod_info = {
                "Name": pod.metadata.name,
                "Phase": pod.status.phase,
                "HostIP": pod.status.host_ip,
                "PodIP": pod.status.pod_ip,
                "StartTime": pod.status.start_time
            }
            status["PodStatuses"].append(pod_info)

        all_deployments_status.append(status)

    return all_deployments_status

all_statuses = get_all_deployments_status()
print(all_statuses)
