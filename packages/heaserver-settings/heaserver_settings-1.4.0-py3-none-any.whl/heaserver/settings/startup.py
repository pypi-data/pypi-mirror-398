from heaserver.service.runner import init_cmd_line

def main() -> None:
    config = init_cmd_line(description='Management of user and system settings',
                           default_port=8080)
    from heaserver.settings import service
    service.start_with(config)
