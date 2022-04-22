import socket

server_port = 12000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', server_port))
print("Waiting for request")
message, client_address = server_socket.recvfrom(2048)
print("Request received from ", client_address)
server_socket.sendto("Received".encode(), client_address)
server_socket.close()
