from client import ChatClient
from console import ConsoleChat

if __name__ == '__main__':
    client = ChatClient(host='localhost', port=50051)
    console_chat = ConsoleChat(client)
    console_chat.start()