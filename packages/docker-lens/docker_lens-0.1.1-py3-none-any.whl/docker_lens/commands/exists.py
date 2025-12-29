from docker_lens.core.docker import get_client
import docker

def container_exists(container_ref: str) -> bool:
    client = get_client()
    try:
        client.containers.get(container_ref)
        return True
    except docker.errors.NotFound:
        return False
