import socket

server_name = "localhost"
server_port = 12000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.sendto("hi".encode(), (server_name, server_port))
received_msg, server_address = client_socket.recvfrom(2048)
print(received_msg.decode())
client_socket.close()
