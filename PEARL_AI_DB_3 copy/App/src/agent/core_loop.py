from .semantic import PearlClient
from .memory import PearlMemory
from .contracts import ContractExecutor
from .logging import AgentLogger

class AgentPearl:
    def __init__(self, llm, config: dict):
        self.client = PearlClient(**config["pearlqlite"])
        self.memory = PearlMemory(
            self.client,
            crdt_table=config["memory"]["crdt_table"],
            log_table=config["memory"]["log_table"],
        )
        self.contracts = ContractExecutor(
            self.client,
            default_audit=config["contracts"].get("default_audit_contract"),
        )
        self.logger = AgentLogger()
        self.llm = llm
        self.max_steps = config["agent"]["max_steps"]

    def handle_request(self, user_input: str) -> str:
        self.memory.append_thought(f"user_input:{user_input}")
        context = self.memory.retrieve_relevant(f"observation|{user_input[:64]}")

        state = {
            "user_input": user_input,
            "context": context,
            "last_result": None,
            "steps": [],
        }

        for _ in range(self.max_steps):
            plan = self._plan_next_step(state)
            state["steps"].append(plan)

            t = plan.get("type")
            if t == "answer":
                answer = plan["content"]
                self.memory.append_thought(f"answer:{answer}")
                return answer

            if t == "semantic_query":
                result = self.client.query(plan["sql"])
                state["last_result"] = result
                self.memory.append_thought("semantic_query_executed")

            if t == "contract":
                result = self.contracts.execute(plan["name"], plan.get("args", {}))
                state["last_result"] = result
                self.memory.append_thought(f"contract:{plan['name']}")

            if t == "crdt_increment":
                self.client.crdt_increment(
                    plan["table"], plan["column"], plan["key"], plan["value"]
                )
                self.memory.append_thought("crdt_increment")

        return "I reached my reasoning step limit without a stable answer."

    def _plan_next_step(self, state: dict) -> dict:
        prompt = self._build_prompt(state)
        raw = self.llm(prompt)
        return self._parse_plan(raw)

    def _build_prompt(self, state: dict) -> str:
        # High-level: instruct LLM to choose one of:
        # - answer
        # - semantic_query (with S-QL)
        # - contract (with name + args)
        # - crdt_increment
        return f"""
You are Agent-PEARL, an agent whose memory and actions are backed by PEARLqlite.

TOOLS:
- semantic_query(sql)
- contract(name, args)
- crdt_increment(table, column, key, value)
- answer(content)

CONSTRAINTS:
- Prefer semantic_query for retrieval.
- Use contracts for actions.
- Keep behavior deterministic and concise.

STATE:
user_input: {state['user_input']}
context_rows: {state['context']}
last_result: {state['last_result']}

Respond with a JSON object like:
{{"type":"answer","content":"..."}}
or
{{"type":"semantic_query","sql":"SELECT ..."}}
or
{{"type":"contract","name":"...","args":{{...}}}}
or
{{"type":"crdt_increment","table":"...","column":"...","key":"...","value":1}}
""".strip()

    def _parse_plan(self, raw: str) -> dict:
        import json
        try:
            plan = json.loads(raw)
        except Exception:
            return {"type": "answer", "content": "I could not parse my own plan."}
        t = plan.get("type")
        if t not in {"answer", "semantic_query", "contract", "crdt_increment"}:
            return {"type": "answer", "content": "Invalid plan type."}
        return plan