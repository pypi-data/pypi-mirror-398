import docker
from docker.errors import DockerException
from rich.console import Console

console = Console()

def get_client():
    try:
        client = docker.from_env()
        client.ping()
        return client
    except docker.errors.DockerException as e:
        msg = str(e)
        if "Permission denied" in msg:
            console.print(
                "[red]Permission denied accessing Docker socket. "
                "Are you in the 'docker' group or running as root?[/red]"
            )
        elif "Cannot connect to the Docker daemon" in msg or "Is the docker daemon running?" in msg:
            console.print("[red]Docker daemon not running. Please start Docker.[/red]")
        else:
            console.print(f"[red]Docker client error:[/red] {msg}")
        raise SystemExit(1)

def get_api_client():
    return docker.APIClient(base_url="unix:///var/run/docker.sock")