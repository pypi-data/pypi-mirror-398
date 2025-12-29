from __future__ import annotations
from kubernetes.utils.create_from_yaml import FailToCreateError
import threading
from pathlib import Path
import yaml
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
from kubernetes.dynamic import DynamicClient
from kubernetes.dynamic.exceptions import NotFoundError
from service_forge.sft.util.logger import log_error, log_info, log_success, log_warning

class KubernetesServiceDetails:
    def __init__(self, name: str, type: str | None = None, port: int | None = None, target_port: int | None = None):
        self.name = name
        self.type = type
        self.port = port
        self.target_port = target_port

class KubernetesManager:
    _instance_lock = threading.Lock()

    def __init__(self):
        try:
            config.load_incluster_config()
            # 使用InCluster配置创建DynamicClient
            self.dynamic_client = DynamicClient(client.ApiClient())
        except config.ConfigException:
            config.load_kube_config()
            # 如果InCluster配置失败，使用kubeconfig文件创建DynamicClient
            self.dynamic_client = DynamicClient(config.new_client_from_config())

        self.k8s_client = client.CoreV1Api()
        self.k8s_apps_client = client.AppsV1Api()
        self.k8s_batch_client = client.BatchV1Api()
        self.k8s_rbac_client = client.RbacAuthorizationV1Api()
        self.k8s_networking_client = client.NetworkingV1Api()
        self.k8s_apiextensions_client = client.ApiextensionsV1Api()

        self.api_mapping = {
            "v1": self.k8s_client,
            "apps/v1": self.k8s_apps_client,
            "batch/v1": self.k8s_batch_client,
            "rbac.authorization.k8s.io/v1": self.k8s_rbac_client,
            "networking.k8s.io/v1": self.k8s_networking_client,
            "apiextensions.k8s.io/v1": self.k8s_apiextensions_client,
        }

    def __new__(cls) -> KubernetesManager:
        if not hasattr(cls, '_instance'):
            with KubernetesManager._instance_lock:
                if not hasattr(cls, '_instance'):
                    KubernetesManager._instance = super().__new__(cls)
        return KubernetesManager._instance

    def get_services_in_namespace(self, namespace: str) -> list[str]:
        try:
            services = self.k8s_client.list_namespaced_service(namespace=namespace)
            return [svc.metadata.name for svc in services.items if svc.metadata.name.startswith("sf-")]
        except ApiException as e:
            log_error(f"Failed to get services: {e.reason}")
            return []
        except Exception as e:
            log_error(f"Failed to get services: {e}")
            return []

    def get_service_details(self, namespace: str, service_name: str) -> KubernetesServiceDetails:
        try:
            service = self.k8s_client.read_namespaced_service(name=service_name, namespace=namespace)
            return KubernetesServiceDetails(
                name=service.metadata.name,
                type=service.spec.type,
                port=service.spec.ports[0].port,
                target_port=service.spec.ports[0].target_port
            )
        except ApiException as e:
            log_error(f"Failed to get service details: {e.reason}")
            return KubernetesServiceDetails(name=service_name)
        except Exception as e:
            log_error(f"Failed to get service details: {e}")
            return KubernetesServiceDetails(name=service_name)

    def get_pods_for_service(self, namespace: str, service_name: str) -> list[str]:
        try:
            service = self.k8s_client.read_namespaced_service(name=service_name, namespace=namespace)
            selector = service.spec.selector
            if not selector:
                log_error(f"Service '{service_name}' has no selector")
                return []
            label_selector = ",".join([f"{k}={v}" for k, v in selector.items()])
            pods = self.k8s_client.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
            return [pod.metadata.name for pod in pods.items]
        except ApiException as e:
            log_error(f"Failed to get pods for service: {e.reason}")
            return []
        except Exception as e:
            log_error(f"Failed to get pods for service: {e}")
            return []

    def get_pod_containers(self, namespace: str, pod_name: str) -> list[str]:
        try:
            pod = self.k8s_client.read_namespaced_pod(name=pod_name, namespace=namespace)
            containers = []
            if pod.spec.containers:
                containers.extend([c.name for c in pod.spec.containers])
            if pod.spec.init_containers:
                containers.extend([c.name for c in pod.spec.init_containers])
            return containers
        except ApiException as e:
            log_error(f"Failed to get pod containers: {e.reason}")
            return []
        except Exception as e:
            log_error(f"Failed to get pod containers: {e}")
            return []

    def get_pod_logs(self, namespace: str, pod_name: str, container_name: str, tail: int, follow: bool, previous: bool) -> str:
        try:
            logs = self.k8s_client.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container_name,
                tail_lines=tail if not follow else None,
                previous=previous,
                follow=follow,
                _preload_content=not follow
            )
            return logs
        except ApiException as e:
            log_error(f"Failed to get pod logs: {e.reason}")
            return ""
        except Exception as e:
            log_error(f"Failed to get pod logs: {e}")

    def apply_dynamic_yaml(self, obj: dict, namespace: str) -> None:
        api_version = obj["apiVersion"]
        kind = obj["kind"]
        metadata = obj["metadata"]
        name = metadata["name"]

        resource = self.dynamic_client.resources.get(api_version=api_version, kind=kind)

        try:
            resource.get(name=name, namespace=namespace)
            print(f"{kind}/{name} exists → patching...")
            resource.patch(name=name, namespace=namespace, body=obj, content_type="application/merge-patch+json")

        except NotFoundError:
            print(f"{kind}/{name} not found → creating...")
            resource.create(body=obj, namespace=namespace)


    def apply_deployment_yaml(self, deployment_yaml: Path, namespace: str) -> None:
        with open(deployment_yaml, 'r') as f:
            objs = yaml.safe_load_all(f)
            for obj in objs:
                api_version = obj["apiVersion"]
                kind = obj["kind"]
                metadata = obj["metadata"]

                name = metadata["name"]

                api_client = self.api_mapping.get(api_version)
                if not api_client:
                    self.apply_dynamic_yaml(obj, namespace)
                    continue

                read_fn = getattr(api_client, f"read_namespaced_{kind.lower()}", None)
                create_fn = getattr(api_client, f"create_namespaced_{kind.lower()}", None)
                patch_fn = getattr(api_client, f"patch_namespaced_{kind.lower()}", None)

                if not read_fn:
                    raise Exception(f"Unsupported resource type: {kind}")

                try:
                    read_fn(name=name, namespace=namespace)
                    print(f"{kind}/{name} exists → patching...")
                    patch_fn(name=name, namespace=namespace, body=obj)

                except ApiException as e:
                    if e.status == 404:
                        print(f"{kind}/{name} not found → creating...")
                        create_fn(namespace=namespace, body=obj)
                    else:
                        raise

    def delete_service(self, namespace: str, service_name: str, force: bool = False) -> None:
        delete_options = client.V1DeleteOptions()
        if force:
            delete_options.grace_period_seconds = 0
            delete_options.propagation_policy = "Background"
        
        # Delete deployment
        try:
            log_info(f"Attempting to delete deployment '{service_name}'...")
            self.k8s_apps_client.delete_namespaced_deployment(
                name=service_name,
                namespace=namespace,
                body=delete_options
            )
            log_success(f"Deployment '{service_name}' deleted successfully")
        except ApiException as e:
            if e.status == 404:
                log_warning(f"Deployment '{service_name}' not found, skipping...")
            else:
                log_warning(f"Failed to delete deployment '{service_name}': {e.reason}")
                log_warning("Continuing with service deletion...")
        except Exception as e:
            log_warning(f"Failed to delete deployment '{service_name}': {e}")
            log_warning("Continuing with service deletion...")
        
        # Delete service
        try:
            log_info(f"Attempting to delete service '{service_name}'...")
            self.k8s_client.delete_namespaced_service(
                name=service_name,
                namespace=namespace,
                body=delete_options
            )
            log_success(f"Service '{service_name}' deleted successfully")
        except ApiException as e:
            if e.status == 404:
                log_warning(f"Service '{service_name}' not found, skipping...")
            else:
                log_error(f"Failed to delete service '{service_name}': {e.reason}")
                if e.body:
                    log_error(f"Error details: {e.body}")
        except Exception as e:
            log_error(f"Failed to delete service '{service_name}': {e}")
        
        # Delete IngressRoute (Traefik CRD)
        try:
            log_info(f"Attempting to delete IngressRoute '{service_name}'...")
            ingressroute_resource = self.dynamic_client.resources.get(
                api_version="traefik.io/v1alpha1",
                kind="IngressRoute"
            )
            ingressroute_resource.delete(name=service_name, namespace=namespace)
            log_success(f"IngressRoute '{service_name}' deleted successfully")
        except NotFoundError:
            log_warning(f"IngressRoute '{service_name}' not found, skipping...")
        except Exception as e:
            log_warning(f"Failed to delete IngressRoute '{service_name}': {e}")
        
        # Delete Middleware (Traefik CRD)
        middleware_name = f"strip-prefix-{service_name}"
        try:
            log_info(f"Attempting to delete Middleware '{middleware_name}'...")
            middleware_resource = self.dynamic_client.resources.get(
                api_version="traefik.io/v1alpha1",
                kind="Middleware"
            )
            middleware_resource.delete(name=middleware_name, namespace=namespace)
            log_success(f"Middleware '{middleware_name}' deleted successfully")
        except NotFoundError:
            log_warning(f"Middleware '{middleware_name}' not found, skipping...")
        except Exception as e:
            log_warning(f"Failed to delete Middleware '{middleware_name}': {e}")
        
