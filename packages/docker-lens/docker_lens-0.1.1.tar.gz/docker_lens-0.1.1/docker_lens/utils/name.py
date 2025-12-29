import secrets
import string

def generate_debug_container_name(target_name: str, length: int = 6) -> str:
    """
    Generate a debug container name with the convention:
    targetName_debug_<6 random chars>
    """
    alphabet = string.ascii_letters + string.digits
    random_suffix = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{target_name}_debug_{random_suffix}"
