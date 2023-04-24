import yaml


class Server:
    def __init__(self, data: dict):
        data = data or {}
        self.host: str = data.get('host', '127.0.0.1')
        self.port: int = data.get('port', 48910)

    @property
    def params(self):
        return {
            'host': self.host,
            'port': self.port
        }


class Config:
    def __init__(self, data: dict):
        data = data or {}
        self.server: Server = Server(data.get('server'))


try:
    with open('config.yaml', mode='rt', encoding='utf-8') as f:
        config = Config(yaml.safe_load(f))
except FileNotFoundError:
    config = Config({})
