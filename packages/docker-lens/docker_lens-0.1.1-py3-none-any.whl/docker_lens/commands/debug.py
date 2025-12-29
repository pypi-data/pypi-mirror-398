from rich.console import Console
import dockerpty
import docker

from docker_lens.core.docker import get_client, get_api_client
from docker_lens.utils.pull import ensure_image
from docker_lens.utils.name import generate_debug_container_name
from docker_lens.core.config import load_config

console = Console()


def debug_container(target: str, image: str | None, shell: str):

    client = get_client()
    api = get_api_client()

    ensure_image(client, image)

    target_container = client.containers.get(target)
    console.print(f"[bold]Debugging container:[/bold] {target_container.name} ({target_container.id[:12]})")

    host_config = api.create_host_config(
        network_mode=f"container:{target_container.id}",
        pid_mode=f"container:{target_container.id}",
        volumes_from=[target_container.id],
        privileged=True,
        auto_remove=True,
    )

    debug_name = generate_debug_container_name(target_container.name)
    container = api.create_container(
        name=debug_name,
        image=image,
        command=shell,
        tty=True,
        stdin_open=True,
        host_config=host_config,
    )

    api.start(container["Id"])
    dockerpty.start(api, container["Id"])
    console.print(f"[green]Debug container {debug_name} removed[/green]")
    
