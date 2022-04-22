import socket

server_name = "localhost"
server_port = 12000
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
    client_socket.sendto("hi".encode(), (server_name, server_port))
    received_msg, server_address = client_socket.recvfrom(2048)
    print(received_msg.decode())
