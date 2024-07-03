# cloud-computing-kubernetes-final-project

## Project Description

KaaS API is a comprehensive solution designed to streamline the deployment, management, and monitoring of applications and databases on Kubernetes. This project provides a set of self-service APIs that enable users to deploy applications and PostgreSQL databases, monitor their health, and visualize performance metrics using Prometheus and Grafana. The aim is to simplify Kubernetes operations and make it more accessible to developers and administrators.

## Features

### 1. **Self-Service Deployment API**
- **Application Deployment**: Deploy any containerized application on Kubernetes with custom configurations including replicas, image details, environment variables, secrets, and external access.
- **PostgreSQL Deployment**: Easily deploy a PostgreSQL database with configurations for master-slave (primary-replica) setups for better availability and load distribution.

### 2. **Monitoring and Health Checks**
- **Health Monitoring**: Monitor the health status of deployed applications using periodic health checks and detailed status reports.
- **CronJob for Health Monitoring**: Schedule periodic jobs to monitor application health and performance.
- **Prometheus Metrics**: Collect and expose metrics such as request count, request latency, and database errors for detailed analysis.

### 3. **Configuration Management for CronJob and Promethues**
- **ConfigMap and Secrets**: Manage application configurations and sensitive data securely using Kubernetes ConfigMaps and Secrets.

### 4. **Visualization with Grafana**
- **Dashboard Integration**: Use Grafana to create interactive dashboards for visualizing metrics collected by Prometheus. This helps in tracking the performance and health of applications over time.

## How It Works

### Deployment API

The deployment API allows users to deploy applications and databases on Kubernetes clusters with a simple POST request. Users can specify the required configurations in a JSON payload.

Example:
```json
{
  "appName": "my-app",
  "replicas": 3,
  "imageAddress": "my-app-image",
  "imageTag": "latest",
  "servicePort": 80,
  "resources": {
    "requests": {"cpu": "100m", "memory": "200Mi"},
    "limits": {"cpu": "200m", "memory": "400Mi"}
  },
  "envs": [{"name": "ENV_VAR_NAME", "value": "env_var_value"}],
  "secrets": [{"name": "secret-name", "mountPath": "/etc/secret"}],
  "externalAccess": true,
  "domainAddress": "example.com"
}
```

### Health Checks and Monitoring

The health endpoint provides real-time status of deployed applications, including pod status, replicas, and readiness.

Example:

```bash
curl -X GET http://localhost:5000/health/my-app
```

### Prometheus and Grafana Integration

Metrics are collected by Prometheus and can be visualized using Grafana dashboards. This integration allows for detailed monitoring and analysis of application performance.

### Prerequisites

- Kubernetes cluster
- Helm
- Docker
- Hpa
- CronJob
- Prometheus and Grafana setup

### Installation
 - **Clone the repository**:
    ```bash
    git clone git@github.com:srvn-nm/cloud-computing-kubernetes-final-project.git
    ```

### Usage

- **Deploy an application**:
    ```bash
    curl -X POST http://localhost:5000/deploy -H "Content-Type: application/json" -d '{"appName": "my-app", ...}'
    ```

- **Check application health**:
    ```bash
    curl -X GET http://localhost:5000/health/my-app
    ```

- **Access Prometheus metrics**:
    ```bash
    curl -X GET http://localhost:5000/metrics/prometheus
    ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
