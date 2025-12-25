from heaserver.service.runner import init_cmd_line

def main() -> None:
    config = init_cmd_line(description='a service for managing laboratory/user credentials',
                           default_port=8080)
    # Delay importing service until after command line is parsed and logging is configured.
    from heaserver.keychain import service
    service.start_with(config)