from kubernetes import client, config

def create_deployment(app_name, replicas, image_address, image_tag, domain_address, service_port):
    config.load_kube_config()  # Load kube config from the default location

    # Define container
    container = client.V1Container(
        name=app_name,
        image=f"{image_address}:{image_tag}",
        ports=[client.V1ContainerPort(container_port=service_port)]
    )

    # Define template
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": app_name}),
        spec=client.V1PodSpec(containers=[container])
    )

    # Define spec
    spec = client.V1DeploymentSpec(
        replicas=replicas,
        template=template,
        selector={'matchLabels': {'app': app_name}}
    )

    # Define deployment
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=app_name),
        spec=spec
    )

    # Create deployment
    api_instance = client.AppsV1Api()
    api_instance.create_namespaced_deployment(
        namespace="default",
        body=deployment
    )

create_deployment("my-app", 3, "nginx", "latest", "my-app.example.local", 80)
