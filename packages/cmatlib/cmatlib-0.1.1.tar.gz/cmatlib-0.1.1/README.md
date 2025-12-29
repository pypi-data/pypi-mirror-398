# chatinpylib

Простая библиотека для работы с ChatGPT.

## Установка 
```bash
pip install cmatlib==0.1.0
```
## Пример использования
```bash
from chatinpylib import Chat
chat = Chat(token="YourToken")
condition = True
while condition:
    user_request = input('Введите свой запрос:')
    print(chat.ask(user_request))
    choice = input('Вы хотите продолжить? y/n:')
    if choice == 'y':
        condition = True
    elif choice == 'n':
        condition = False



