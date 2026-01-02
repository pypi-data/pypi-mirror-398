class ReplayEngine:
    def __init__(self, agent_handler):
        self.agent_handler = agent_handler

    def replay(self, record):
        """
        Re-run agent deterministically using stored inputs
        """
        return self.agent_handler(
            inputs=record.inputs,
            replay=True
        )
