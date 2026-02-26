import requests

class PearlClient:
    def __init__(self, base_url: str, timeout_ms: int = 5000):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_ms / 1000.0

    def query(self, sql: str):
        resp = requests.post(
            f"{self.base_url}/query",
            json={"query": sql},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def execute_contract(self, name: str, args: dict):
        resp = requests.post(
            f"{self.base_url}/contracts/execute",
            json={"contract": name, "args": args},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def crdt_increment(self, table: str, column: str, key: str, value: int):
        payload = {
            "table": table,
            "column": column,
            "key": key,
            "value": value,
        }
        resp = requests.post(
            f"{self.base_url}/crdt/increment",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()