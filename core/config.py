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


class RateLimit:
    def __init__(self, data: dict):
        data = data or {}
        self.interval: float = data['interval']
        self.query: int = data['query']

    @property
    def param(self) -> dict:
        return {
            'interval': self.interval,
            'query': self.query
        }


class Limit:
    def __init__(self, data: dict):
        data = data or {}
        self.timeout: float = data.get('timeout', 0.1)
        self.rate: dict[str, RateLimit] = {k: RateLimit(v) for k, v in data.get('rate', {}).items()}


class Config:
    def __init__(self, data: dict):
        data = data or {}
        self.key: str = data.get('key')
        self.server: Server = Server(data.get('server'))
        self.limit: Limit = Limit(data.get('limit'))


try:
    with open('config.yaml', mode='rt', encoding='utf-8') as f:
        config = Config(yaml.safe_load(f))
except FileNotFoundError:
    config = Config({})
