import socket
import sys


class Receiver:
    """
    Class to implement a sender

    """

    def __init__(self, max_seg_size: int, receiver_port: int = 12001):
        self.max_seg_size = max_seg_size  # store maximum segment size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create UDP socket
        self.socket.bind(('', receiver_port))  # bind socket to the receiver port

    def receive(self, filename: str) -> None:
        """
        Receive file from sender
        :param filename: name of received file
        :return: None
        """
        received_data = bytearray()  # init received_data to empty bytearray
        while 1:
            # receive a packet, set buffer size to max_seg_size + header size
            packet, server_address = self.socket.recvfrom(self.max_seg_size + 6)
            packet_id = packet[:2]  # extract packet_id from first 16 bits
            print("Received packet ", int.from_bytes(packet_id, sys.byteorder))
            file_id = packet_id[2:4]  # extract file_id from second 16 bits
            received_data.extend(packet[4:-2])  # extract payload and append it to received_data
            trailer_bits = packet[-2:]  # extract trailer bits from last 16 bits
            if trailer_bits.hex() == 'ffff':  # if trailer_bits is 'ffff' then all data is received
                break

        print("Received all packets")
        with open(filename, 'wb') as file:  # write received data to file
            file.write(received_data)
        print("File written at ", filename)

    def close_socket(self) -> None:
        self.socket.close()


def main():
    receiver = Receiver(max_seg_size=2048)
    receiver.receive("Received Files/SmallFile.png")
    receiver.close_socket()


if __name__ == "__main__":
    main()
