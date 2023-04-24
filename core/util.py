import simdjson


class Json:
    @staticmethod
    def dump(data, path: str):
        with open(path, mode='wt', encoding='utf-8') as f:
            return simdjson.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(path: str):
        with open(path, mode='rt', encoding='utf-8') as f:
            return simdjson.load(f)


json = Json
