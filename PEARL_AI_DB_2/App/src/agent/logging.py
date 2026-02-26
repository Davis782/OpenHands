import logging

class AgentLogger:
    def __init__(self):
        self.log = logging.getLogger("agent-pearl")
        if not self.log.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s"
            )
            handler.setFormatter(formatter)
            self.log.addHandler(handler)
            self.log.setLevel(logging.INFO)

    def info(self, msg: str):
        self.log.info(msg)

    def error(self, msg: str):
        self.log.error(msg)