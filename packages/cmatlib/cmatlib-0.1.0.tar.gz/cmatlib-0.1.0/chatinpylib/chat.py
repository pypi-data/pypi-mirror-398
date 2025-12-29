from .client import OpenAIClient

class Chat:
    def __init__(self, token: str):
        self._client = OpenAIClient(token)
        self._history = []  # сюда будем сохранять историю сообщений

    def ask(self, prompt: str) -> str:
        # добавляем сообщение пользователя
        self._history.append({"role": "user", "content": prompt})

        # отправляем всю историю на API
        response = self._client.send(self._history)  # <-- передаём список, а не строку

        # добавляем ответ ассистента в историю
        self._history.append({"role": "assistant", "content": response})

        return response
