class MyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def greet(self, name: str) -> str:
        return f"Hello, {name}! Your API key is {self.api_key}"