import yaml
from .core_loop import AgentPearl

def dummy_llm(prompt: str) -> str:
    # Placeholder: replace with real LLM call.
    # For now, always answer directly.
    return '{"type":"answer","content":"(dummy) I received your request and PEARLqlite is wired in."}'

def main():
    with open("config/agent.yaml") as f:
        config = yaml.safe_load(f)
    agent = AgentPearl(llm=dummy_llm, config=config)

    print("Agent-PEARL REPL. Ctrl-D to exit.")
    while True:
        try:
            user_input = input("You: ")
        except EOFError:
            break
        answer = agent.handle_request(user_input)
        print("Agent-PEARL:", answer)

if __name__ == "__main__":
    main()