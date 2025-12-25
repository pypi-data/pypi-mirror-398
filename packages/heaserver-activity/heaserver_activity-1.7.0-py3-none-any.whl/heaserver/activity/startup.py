from heaserver.service.runner import init_cmd_line

def main() -> None:
    config = init_cmd_line(description='A service for tracking activity in hea',
                           default_port=8080)
    # Delay importing service until after command line is parsed and logging is configured.
    from heaserver.activity import service
    service.start_with(config=config)
