def get_metadata_file_name(name: str, version: str) -> str:
    return "sf-meta.yaml"

def get_service_name(name: str, version: str) -> str:
    return f"sf-{name}-{version.replace('.', '-')}v"

def get_service_url_name(name: str, version: str) -> str:
    return f"{name}-{version.replace('.', '-')}"