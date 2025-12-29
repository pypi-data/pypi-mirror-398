from docker_lens.core.docker import get_client


def docker_ps(all_containers: bool = False):
    client = get_client()
    containers = client.containers.list(all=all_containers)

    print(f"{'CONTAINER ID':<20}  {'IMAGE':<20}  {'NAMES':<15}  {'STATUS'}  ")

    for c in containers:
        container_id = c.id[:12]
        image = c.image.tags[0] if c.image.tags else "<none>"
        status = c.status
        name = c.name

        print(f"{container_id:<20}  {image:<20}  {name:<15}  {status}  ")

