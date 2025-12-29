import docker
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()
client = docker.from_env()

def ensure_image(client: docker.DockerClient, image_name: str):
    try:
        client.images.get(image_name)
        console.print(f"[green]Image already exists locally:[/green] {image_name}")
        return
    except docker.errors.ImageNotFound:
        console.print(f"[yellow]Image not found locally. \n   Pulling:[/yellow] {image_name}")

    try:
        pull_stream = client.api.pull(image_name, stream=True, decode=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Pulling {image_name}", total=100)

            for line in pull_stream:
                status = line.get("status", "")
                progress_detail = line.get("progressDetail", {})
                current = progress_detail.get("current", 0)
                total = progress_detail.get("total", 0)

                if total > 0:
                    progress_percent = int(current / total * 100)
                    progress.update(task, completed=progress_percent, description=f"{status}")
                else:
                    progress.update(task, description=f"{status}")

        console.print(f"[green]Image pulled successfully:[/green] {image_name}")

    except docker.errors.APIError as e:
        console.print(f"[red]Failed to pull image {image_name}: {e}[/red]")
        raise
