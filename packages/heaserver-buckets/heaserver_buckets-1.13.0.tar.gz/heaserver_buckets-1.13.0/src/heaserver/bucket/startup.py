from heaserver.service.runner import init_cmd_line

def main() -> None:
    config = init_cmd_line(description='a service for managing buckets and their data within the cloud',
                           default_port=8080)
    # Delay importing service until after command line is parsed and logging is configured.
    from heaserver.bucket import service
    service.start_service(config)
