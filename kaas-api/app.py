from flask import Flask, request, jsonify
from kubernetes import client, config
from utils.postgres_utils import postgres_image,postgres_port, postgres_replicas
import datetime
from prometheus_client import Counter
from kubernetes.client import V1CronJob, V1CronJobSpec, V1JobTemplateSpec, V1ObjectMeta, V1PodTemplateSpec, V1PodSpec, V1Container, V1EnvVar, V1VolumeMount, V1SecretVolumeSource, V1Volume


app = Flask(__name__)
config.load_kube_config()

#CoreV1Api: This is the primary API group in Kubernetes ,It provides access to most of the fundamental Kubernetes resources 
v1 = client.CoreV1Api()
#AppsV1Api: This API group is part of the "apps" API, which provides access to more complex, higher-level objects that manage applications.
apps_v1 = client.AppsV1Api()

apps_version = "apps/v1"

@app.route('/deploy', methods=['POST'])
def deploy_app():
    data = request.get_json()
    app_name = data.get('appName')
    replicas = data.get('replicas', 1)
    image_address = data.get('imageAddress')
    image_tag = data.get('imageTag', 'latest')
    service_port = data.get('servicePort', 80)
    resources = data.get('resources', {})
    envs = data.get('envs', [])
    secrets = data.get('secrets', [])
    external_access = data.get('externalAccess', False)
    domain_address = data.get('domainAddress')

    # Define environment variables
    env_vars = []
    for env in envs:
        env_vars.append(client.V1EnvVar(name=env['name'], value=env['value']))

    # Define secrets (if any)
    secret_volumes = []
    for secret in secrets:
        secret_volumes.append(client.V1VolumeMount(name=secret['name'], mount_path=secret['mountPath']))


    # Define the container spec
    container = client.V1Container(
        name=app_name,
        image=f"{image_address}:{image_tag}",
        ports=[client.V1ContainerPort(container_port=service_port)],
        resources=client.V1ResourceRequirements(
            requests=resources.get('requests', {}),
            limits=resources.get('limits', {})
        )
    )

    # Create the deployment spec
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": app_name}),
        spec=client.V1PodSpec(
            containers=[container],
            volumes=[client.V1Volume(name=secret['name'], secret=client.V1SecretVolumeSource(secret_name=secret['name'])) for secret in secrets]
        )
    )

    spec = client.V1DeploymentSpec(
        replicas=replicas,
        template=template,
        selector={'matchLabels': {"app": app_name}}
    )

    deployment = client.V1Deployment(
        api_version=apps_version,
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=app_name),
        spec=spec
    )

    # Create the deployment
    apps_v1 = client.AppsV1Api()
    try:
        apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
    except client.ApiException as e:
        return jsonify({"error": str(e)}), 500

    # Optionally create a service
    if external_access:
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=app_name),
            spec=client.V1ServiceSpec(
                selector={"app": app_name},
                ports=[client.V1ServicePort(port=80, target_port=service_port)],
                type="NodePort"
            )
        )
        core_v1 = client.CoreV1Api()
        try:
            core_v1.create_namespaced_service(namespace="default", body=service)
        except client.ApiException as e:
            return jsonify({"error": str(e)}), 500

    # # Optionally create an Ingress
    # if domain_address:
    #     ingress = client.NetworkingV1Api(
    #         api_version="networking.k8s.io/v1",
    #         kind="Ingress",
    #         metadata=client.V1ObjectMeta(name=app_name),
    #         spec=client.NetworkingV1IngressSpec(
    #             rules=[
    #                 client.NetworkingV1IngressRule(
    #                     host=f"{app_name}.{domain_address}",
    #                     http=client.NetworkingV1HTTPIngressRuleValue(
    #                         paths=[
    #                             client.NetworkingV1HTTPIngressPath(
    #                                 path="/",
    #                                 backend=client.NetworkingV1IngressBackend(
    #                                     service_name=app_name,
    #                                     service_port=client.IntOrString(int_value=service_port)
    #                                 )
    #                             )
    #                         ]
    #                     )
    #                 )
    #             ]
    #         )
    #     )
    #     try:
    #         networking_v1.create_namespaced_ingress(namespace="default", body=ingress)
    #     except client.ApiException as e:
    #         return jsonify({"error": str(e)}), 500

    return jsonify({"message": "App deployed successfully"})

@app.route('/status/<string:app_name>', methods=['GET'])
def get_app_status(app_name):
    # Get deployment status
    deployment = apps_v1.read_namespaced_deployment(name=app_name, namespace="default")
    pods = v1.list_namespaced_pod(namespace="default", label_selector=f"app={app_name}")
    
    pod_statuses = []
    for pod in pods.items:
        pod_statuses.append({
            "name": pod.metadata.name,
            "phase": pod.status.phase,
            "hostIP": pod.status.host_ip,
            "podIP": pod.status.pod_ip,
            "startTime": pod.status.start_time
        })

    response = {
        "deploymentName": deployment.metadata.name,
        "replicas": deployment.spec.replicas,
        "readyReplicas": deployment.status.ready_replicas,
        "podStatuses": pod_statuses
    }

    return jsonify(response)

@app.route('/statuses', methods=['GET'])
def get_all_app_statuses():
    deployments = apps_v1.list_namespaced_deployment(namespace="default")
    all_statuses = []

    for deployment in deployments.items:
        app_name = deployment.metadata.name
        pods = v1.list_namespaced_pod(namespace="default", label_selector=f"app={app_name}")
        
        pod_statuses = []
        for pod in pods.items:
            pod_statuses.append({
                "name": pod.metadata.name,
                "phase": pod.status.phase,
                "hostIP": pod.status.host_ip,
                "podIP": pod.status.pod_ip,
                "startTime": pod.status.start_time
            })

        all_statuses.append({
            "deploymentName": deployment.metadata.name,
            "replicas": deployment.spec.replicas,
            "readyReplicas": deployment.status.ready_replicas,
            "podStatuses": pod_statuses
        })

    return jsonify(all_statuses)

'''
    this function is a self-service deployer for postgres database
    method: POST
    essential parameters:
        appName
        resources = {cpu , memory}
        external(true,false)
'''
@app.route('/deployment/self-service/postgres', methods=['POST'])
def self_service_postgres():

    data = request.get_json()
    app_name = data.get('appName')
    resources = data.get('resources', {})
    external = data.get('external', False)

    container = client.V1Container(
        name=app_name,
        image=postgres_image,
        ports=[client.V1ContainerPort(container_port=postgres_port)],
        resources=client.V1ResourceRequirements(
            requests=resources.get('requests', {}),
            limits=resources.get('limits', {})
        ),
        env=[
            client.V1EnvVar(name="POSTGRES_DB", value="postgres_db"),
            client.V1EnvVar(name="POSTGRES_USER", value="kaas_user"),
            client.V1EnvVar(name="POSTGRES_PASSWORD", value="12345")
        ]
    )

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": app_name}),
        spec=client.V1PodSpec(containers=[container])
    )

    spec = client.V1DeploymentSpec(
        replicas=postgres_replicas,
        template=template,
        selector={'matchLabels': {"app": app_name}}
    )

    deployment = client.V1Deployment(
        api_version=apps_version,
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=app_name),
        spec=spec
    )

    try:
        apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
    except client.ApiException as error:
        return jsonify({"kaas postgres-self-service internal error": str(error)}), 500

    if external:
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=app_name),
            spec=client.V1ServiceSpec(
                selector={"app": app_name},
                ports=[client.V1ServicePort(port=80, target_port=postgres_port)],
                type="NodePort"
            )
        )
        try:
            v1.create_namespaced_service(namespace="default", body=service)
        except client.ApiException as error:
            return jsonify({"kaas postgres-self-service internal error": str(error)}), 500

    return jsonify({"kaas/postgres-self-service: your postgres app is ready": app_name}), 200
        
# Monitoring CronJob
@app.route('/monitor/cronjob', methods=['POST'])
def create_monitor_cronjob():
    data = request.get_json()
    cron_schedule = data.get('schedule')
    namespace = data.get('namespace', 'default')

    cronjob = V1CronJob(
        api_version='batch/v1',
        kind='CronJob',
        metadata=V1ObjectMeta(name='monitor-cronjob'),
        spec=V1CronJobSpec(
            schedule=cron_schedule,
            job_template=V1JobTemplateSpec(
                spec=client.V1JobSpec(
                    template=V1PodTemplateSpec(
                        spec=V1PodSpec(
                            containers=[
                                V1Container(
                                    name='monitor-container',
                                    image='your-monitor-image',
                                    env=[
                                        V1EnvVar(name='ENV_VAR_NAME', value='env_var_value')
                                    ],
                                    volume_mounts=[
                                        V1VolumeMount(name='secret-volume', mount_path='/etc/secret')
                                    ]
                                )
                            ],
                            restart_policy='OnFailure',
                            volumes=[
                                V1Volume(
                                    name='secret-volume',
                                    secret=V1SecretVolumeSource(secret_name='your-secret-name')
                                )
                            ]
                        )
                    )
                )
            )
        )
    )

    try:
        batch_v1 = client.BatchV1Api()
        batch_v1.create_namespaced_cron_job(namespace=namespace, body=cronjob)
    except client.ApiException as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "CronJob created successfully"})

@app.route('/health/<string:app_name>', methods=['GET'])
def get_app_health(app_name):
    try:
        deployment = apps_v1.read_namespaced_deployment(name=app_name, namespace="default")
        pods = v1.list_namespaced_pod(namespace="default", label_selector=f"app={app_name}")
        
        pod_statuses = []
        for pod in pods.items:
            pod_statuses.append({
                "name": pod.metadata.name,
                "phase": pod.status.phase,
                "hostIP": pod.status.host_ip,
                "podIP": pod.status.pod_ip,
                "startTime": pod.status.start_time
            })

        health_data = {
            "deploymentName": deployment.metadata.name,
            "replicas": deployment.spec.replicas,
            "readyReplicas": deployment.status.ready_replicas,
            "podStatuses": pod_statuses,
            "last_check": datetime.datetime.now().isoformat()
        }

        return jsonify(health_data), 200
    except client.exceptions.ApiException as e:
        return jsonify({"get health internal error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
