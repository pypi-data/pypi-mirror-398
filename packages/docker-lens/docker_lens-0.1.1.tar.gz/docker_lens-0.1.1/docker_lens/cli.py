import click
from rich.console import Console

from docker_lens.commands.ps import docker_ps
from docker_lens.commands.debug import debug_container
from docker_lens.commands.exists import container_exists
from docker_lens.core.config import load_config, save_config
from docker_lens.core.constants import DEFAULT_IMAGES

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """
    Docker Lens – Docker Debugging Tool

    Default behavior: lists containers (like `docker ps`)
    """
    if ctx.invoked_subcommand is None:
        docker_ps()


@main.command()
@click.argument("container_id", required=True)
@click.option("--image", default=None, help="Debug image to use (optional)")
@click.option("--shell", default=None, help="Shell to use (optional)")
@click.pass_context
def debug(ctx, image, shell, container_id):
    """Attach debug container to a running container"""
    if not image:
        image = load_config()
    if not shell:
        shell = "/bin/bash"
    if container_exists(container_id):
        debug_container(container_id, image=image, shell=shell)
    else:
        console.print(f"[red]Container {container_id} not found.[/red]")


@click.group()
def set():
    """Set docker-lens configuration values"""
    pass


@set.group(invoke_without_command=True)
@click.argument("image_profile", required=False)
@click.pass_context
def image(ctx, image_profile):
    """
    Set default debug image.

    Use one of these profiles:
      minimal
      network
      process
      full

    or set a custom image: \n
      docker-lens set image myorg/debug:latest
    """
    if image_profile is None:
        console.print("[bold]Usage:[/bold]")
        console.print("  docker-lens set image [PROFILE | IMAGE]\n")
        console.print("[bold]Available profiles:[/bold]")
        for name, img in DEFAULT_IMAGES.items():
            console.print(f"  {name:<10} → {img}")
        console.print("\n[bold]Custom image example:[/bold]")
        console.print("  docker-lens set image myorg/debug:latest")
        return
    
    image = DEFAULT_IMAGES.get(image_profile, None)
    if image:
        save_config(image)
        console.print(f"[green]Default debug image set to:[/green] {image}")
    else:
        save_config(image_profile)
        console.print(f"[green]Default debug image set to:[/green] {image_profile}")


main.add_command(set)

if __name__ == "__main__":
    main()
