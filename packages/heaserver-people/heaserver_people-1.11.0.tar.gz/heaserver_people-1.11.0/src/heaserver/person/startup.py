from heaserver.service.runner import init_cmd_line

def main() -> None:
    config = init_cmd_line(description='Wrapper around Keycloak for accessing and updating user information.',
                           default_port=8080)
    from heaserver.person import service
    service.start_with(config)
