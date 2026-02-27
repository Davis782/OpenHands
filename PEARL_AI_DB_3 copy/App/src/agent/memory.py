from .semantic import PearlClient

class PearlMemory:
    def __init__(self, client: PearlClient, crdt_table: str, log_table: str):
        self.client = client
        self.crdt_table = crdt_table
        self.log_table = log_table

    def append_thought(self, thought: str):
        sql = f"""
        UPDATE {self.crdt_table}
        SET log = CRDT_APPEND(
          log,
          json_object('thought', {self._q(thought)})
        )
        WHERE id = 'agent-pearl';
        """
        return self.client.query(sql)

    def retrieve_relevant(self, seed: str, limit: int = 20):
        sql = f"""
        SELECT *
        FROM {self.log_table}
        WHERE pearl_id ≈ PEARL_ID({self._q(seed)})
        ORDER BY timestamp DESC
        LIMIT {limit};
        """
        return self.client.query(sql)

    @staticmethod
    def _q(s: str) -> str:
        return "'" + s.replace("'", "''") + "'"