"""Docker skill implementation for agno runtime."""
from agno.tools import Toolkit
import docker
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin


class DockerTools(SchemaFixMixin, Toolkit):
    """
    Docker management tools.

    Provides Docker container, image, volume, and network management.
    """

    def __init__(
        self,
        enable_container_management: bool = True,
        enable_image_management: bool = False,
        enable_volume_management: bool = False,
        enable_network_management: bool = False,
        docker_host: str = "unix:///var/run/docker.sock",
        **kwargs
    ):
        """
        Initialize Docker tools.

        Args:
            enable_container_management: Enable container operations
            enable_image_management: Enable image operations
            enable_volume_management: Enable volume operations
            enable_network_management: Enable network operations
            docker_host: Docker daemon socket
            **kwargs: Additional configuration
        """
        super().__init__(name="docker")
        self.client = docker.DockerClient(base_url=docker_host)
        self.enable_containers = enable_container_management
        self.enable_images = enable_image_management
        self.enable_volumes = enable_volume_management
        self.enable_networks = enable_network_management

        # Register functions based on enabled features
        if self.enable_containers:
            self.register(self.list_containers)
            self.register(self.start_container)
            self.register(self.stop_container)

        # Fix: Rebuild function schemas with proper parameters
        self._rebuild_function_schemas()

    def list_containers(self, all: bool = False) -> str:
        """List Docker containers."""
        containers = self.client.containers.list(all=all)
        return "\\n".join([f"{c.id[:12]} {c.name} {c.status}" for c in containers])

    def start_container(self, container_id: str) -> str:
        """Start a Docker container."""
        container = self.client.containers.get(container_id)
        container.start()
        return f"Container {container_id} started"

    def stop_container(self, container_id: str) -> str:
        """Stop a Docker container."""
        container = self.client.containers.get(container_id)
        container.stop()
        return f"Container {container_id} stopped"
