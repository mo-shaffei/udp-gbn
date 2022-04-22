import socket
import sys


class Sender:
    """
    Class to implement a sender
    """

    def __init__(self, rec_ip: str, rec_port: int, max_seg_size: int, sender_port: int = 12000):
        self.rec_ip = rec_ip  # store receiver ip
        self.rec_port = rec_port  # store receiver port
        self.max_seg_size = max_seg_size  # store maximum segment size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create UDP socket
        self.socket.bind(('', sender_port))  # bind socket to the sender port

    def send(self, filename: str) -> None:
        """
        Send file to the receiver by dividing it into ceil(file_len/max_seg_size) segments
        and append headers to each segment
        :param filename: path and name of file to send
        :return: None
        """
        with open(filename, 'rb') as file:  # read bytes from file
            image = file.read()

        if len(image) // self.max_seg_size > (2 ** 16) - 1:  # ensure packet_id won't overflow
            raise Exception('image size and mss overflows 16 bits packet id')

        packet_id = 0  # init packet_id
        file_id = 0  # init file_id
        for i in range(0, len(image), self.max_seg_size):  # get max_seg_size bytes from file at a time
            packet = packet_id.to_bytes(2, sys.byteorder)  # create packet and add 16 bits packet_id
            packet += file_id.to_bytes(2, sys.byteorder)  # add 16 bits file_id to the packet
            packet += image[i: i + self.max_seg_size]  # add payload to the packet
            trailer = "0000" if i + self.max_seg_size < len(image) else "FFFF"  # if last segment make trailer "ffff"
            packet += bytearray.fromhex(trailer)  # add trailer bits to the packet
            self.socket.sendto(packet, (self.rec_ip, self.rec_port))  # send packet to receiver
            print("Sent packet ", packet_id)
            packet_id += 1  # increment packet_id

        print("Sent all packets")

    def close_socket(self) -> None:
        self.socket.close()


def main():
    sender = Sender(rec_ip='localhost', rec_port=12001, max_seg_size=2048)
    sender.send('Test Files/SmallFile.png')
    sender.close_socket()


if __name__ == '__main__':
    main()
