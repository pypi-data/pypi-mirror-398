from openai import OpenAI

class OpenAIClient:
    def __init__(self, token: str):
        if not token:
            raise ValueError("API token не может быть пустым")
        self.client = OpenAI(api_key=token)

    def send(self, messages) -> str:
        # messages — список объектов вида {"role": "...", "content": "..."}
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
