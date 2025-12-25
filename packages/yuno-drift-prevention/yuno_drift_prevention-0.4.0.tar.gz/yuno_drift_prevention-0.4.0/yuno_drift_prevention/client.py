class YunoCoherenceClient:
    def __init__(self, api_key: str, instructions: str):
        self.api_key = api_key
        self.instructions = instructions

    def greet(self, name: str) -> str:
        return f"Hello, {name}! Your API key is {self.api_key}"
    
    def getCoherenceResults(self, input_text: str, output_text: str):
        return {
            "state": "state_name",
            "strategy": "strategy_name",
            "scores": {
                "C_global": 0,
                "theta": 0.65
            },
            "windows": [],
            "decision": {
                "above_threshold": True,
                "hold_required": False,
            },
            "constraints": "",
            "routing": {
                "prompt_snippet_id": "UNKNOWN",
                "safety_mode": "standard"
            },
            "debug": {
                "topic_drift": True,
                "contradiction_flag": False
            }
        }