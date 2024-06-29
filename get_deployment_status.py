from kubernetes import client, config

def get_deployment_status(deployment_name):
    config.load_kube_config()  # Load kube config from the default location

    api_instance = client.AppsV1Api()
    deployment = api_instance.read_namespaced_deployment(name=deployment_name, namespace='default')

    status = {
        "DeploymentName": deployment.metadata.name,
        "Replicas": deployment.spec.replicas,
        "ReadyReplicas": deployment.status.ready_replicas,
        "PodStatuses": []
    }

    pod_api = client.CoreV1Api()
    pods = pod_api.list_namespaced_pod(namespace='default', label_selector=f"app={deployment_name}")

    for pod in pods.items:
        pod_info = {
            "Name": pod.metadata.name,
            "Phase": pod.status.phase,
            "HostIP": pod.status.host_ip,
            "PodIP": pod.status.pod_ip,
            "StartTime": pod.status.start_time
        }
        status["PodStatuses"].append(pod_info)

    return status

status = get_deployment_status("my-app")
print(status)
