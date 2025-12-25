import IlyasMessageProtocol
import socket


def execute_query(query: str, host: str, port: int):
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_client.connect((host, port))
    IlyasMessageProtocol.send(socket_client, query.encode(), 'TXT', 'a')
    response = IlyasMessageProtocol.receive(socket_client)
    socket_client.close()
    return response[1]
