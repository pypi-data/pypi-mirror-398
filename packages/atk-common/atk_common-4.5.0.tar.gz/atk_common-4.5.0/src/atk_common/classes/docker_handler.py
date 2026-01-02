import docker
import socket
from atk_common.interfaces import IDockerHandler
from atk_common.interfaces import ILogger

class DockerHandler(IDockerHandler):
    def __init__(self, logger: ILogger, image_name, image_version):
        self.logger = logger
        self.image_name = image_name
        self.image_version = image_version
        self.container_data = self.set_container_metadata()

    def get_image_name_and_version(self, tags):
        if tags:
            # Use the first tag (usually only one)
            full_tag = tags[0]  # e.g., 'bo-crypto-wrapper-api:latest'

            if ":" in full_tag:
                image_name, image_version = full_tag.split(":", 1)
            else:
                image_name = full_tag
                image_version = "<none>"
            return image_name, image_version
        else:
            return None, None
        
    def create_port_item(self, port, binding):
        data = {}
        data['port'] = port
        data['binding'] = binding
        return data

    def create_container_log(self, container_data):
        image_name = container_data.get('imageName') or 'Unknown'
        image_version = container_data.get('imageVersion') or 'Unknown'
        
        log_str = f'Image name: {image_name}, image version: {image_version}'
        self.logger.info(log_str)

    def get_current_container_info(self):
        try:
            data = {}
            client = docker.from_env()

            # Get current container's hostname (usually the container ID)
            container_id = socket.gethostname()

            # Fetch container object using partial ID
            container = client.containers.get(container_id)

            tags_info = self.get_image_name_and_version(container.image.tags)
            data['imageName'] = tags_info[0]
            data['imageVersion'] = tags_info[1]
            data['containerName'] = container.name
            ports = container.attrs['NetworkSettings']['Ports']
            data['ports'] = []
            if ports:
                for container_port, host_bindings in ports.items():
                    if host_bindings:
                        for binding in host_bindings:
                            data['ports'].append(self.create_port_item(container_port, f"{binding['HostIp']}:{binding['HostPort']}"))
                    else:
                        data['ports'].append(self.create_port_item(container_port, None))
            self.create_container_log(data)
            return data
        except Exception as e:
            self.logger.error("Error getting container data:" + str(e))
            return None

    def set_container_metadata(self):
        data = {}
        data['imageName'] = self.image_name
        data['imageVersion'] = self.image_version
        data['containerName'] = self.image_name
        self.create_container_log(data)
        return data

    def get_container_metadata(self):
        return self.container_data
