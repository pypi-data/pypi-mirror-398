# Example: ghcr.io/perspictech/bo-status-mq-consumer
def parse_component_name(component: str) -> str:
    if component.startswith("ghcr"):
        parts = component.split('/')
        if len(parts) == 3:
            return parts[2]
    return component
