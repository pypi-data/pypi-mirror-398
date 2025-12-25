from heaserver.service.runner import init_cmd_line

def main() -> None:
    config = init_cmd_line(description='a service for managing organization information for research laboratories and other research groups',
                           default_port=8087)
    # Delay importing service until after command line is parsed and logging is configured.
    from heaserver.organization import service
    service.start_with(config)
