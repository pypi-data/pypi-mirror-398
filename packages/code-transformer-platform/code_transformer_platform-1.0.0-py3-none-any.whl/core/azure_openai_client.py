from openai import AzureOpenAI


class AzureOpenAIClient:
    def __init__(self, config: dict):
        self.client = AzureOpenAI(
            api_key=config["api_key"],
            azure_endpoint=config["endpoint"],
            api_version=config["api_version"]
        )
        self.deployment = config["deployment"]
        self.params = config

    def generate(self, messages):
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=self.params["temperature"],
            max_tokens=self.params["max_tokens"],
            top_p=self.params["top_p"]
        )
        return response.choices[0].message.content
