import math
import socket
import sys
import signal


class Sender:
    """
    Class to implement a sender using Go-Back-N algorithm on top of UDP to achieve reliable transfer
    """

    def __init__(self, rec_ip: str, rec_port: int, max_seg_size: int, sender_port: int = 12000, win_size: int = 4,
                 timeout: float = 0.1):
        """

        :param rec_ip: ip of the receiver
        :param rec_port: port of the receiver
        :param max_seg_size: maximum segment size
        :param sender_port: port to use for the sender
        :param win_size: Go-Back-N window size
        :param timeout: ACK timeout interval before retransmission
        """
        self.rec_ip = rec_ip  # store receiver ip
        self.rec_port = rec_port  # store receiver port
        self.max_seg_size = max_seg_size  # store maximum segment size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create UDP socket
        self.socket.bind(('', sender_port))  # bind socket to the sender port
        self.win_size = win_size  # store Go-Back-N window size
        self.timeout = timeout  # store ACK timeout interval
        signal.signal(signal.SIGALRM, self._timeout_handler)  # register timeout function handler
        self.base = self.nextseqnum = -1  # init base and nextseqnum to -1

    def send_file(self, filename):
        """
        Send file given by filename from sender to receiver using UDP and GBN
        :param filename: path and name of file to read and send
        :return: None
        """
        self._read_file(filename)  # read file and store it in self.file
        self.base = self.nextseqnum = 0  # init base and nextseqnum to 0
        last_packet_id = math.ceil(len(self.file) / self.max_seg_size) - 1  # calculate and store id of last packet
        while self.base != last_packet_id:  # loop until all packets are transmitted and acknowledged
            if self.nextseqnum < self.base + self.win_size:  # if new packets can be transmitted in window
                self._send_packet(self.nextseqnum)  # transmit the packet with id nextseqnum
                if self.base == self.nextseqnum:  # if first packet in window then start timer
                    signal.setitimer(signal.ITIMER_REAL, self.timeout)
                self.nextseqnum += 1  # increment nextseqnum
            else:  # no packets can be transmitted in window
                self._recv_ack()  # wait for acknowledgement from receiver

    def _read_file(self, filename):
        """
        read file given by filename into self.file
        :param filename: path and name of file to read and send
        :return: None
        """
        with open(filename, 'rb') as file:  # read bytes from file
            self.file = file.read()

        if len(self.file) // self.max_seg_size > (2 ** 16) - 1:  # ensure packet_id won't overflow
            raise Exception('file size and mss overflows 16 bits packet id')

    def _send_packet(self, packet_id: int):
        """
        Send next packet from file given by packet_id
        :param packet_id: id of packet to send
        :return: None
        """
        print("Sending packet ", packet_id)
        file_id = 0  # set file_id to 0
        current_byte = packet_id * self.max_seg_size  # get first byte to be sent
        trailer = "0000" if current_byte + self.max_seg_size < len(
            self.file) else "FFFF"  # if last segment make trailer "ffff"
        packet = packet_id.to_bytes(2, sys.byteorder)  # create packet and add 16 bits packet_id
        packet += file_id.to_bytes(2, sys.byteorder)  # add 16 bits file_id to the packet
        packet += self.file[current_byte: current_byte + self.max_seg_size]  # add payload to the packet
        packet += bytearray.fromhex(trailer)  # add trailer bits to the packet
        self.socket.sendto(packet, (self.rec_ip, self.rec_port))  # send packet to receiver

    def _recv_ack(self):
        """
        Wait to receive acknowledgement from receiver
        :return: None
        """
        ack_packet, _ = self.socket.recvfrom(4)  # wait for acknowledgement with buffer 4 bytes(2 packet_id, 2 file_id)
        print("Received ACK ", int.from_bytes(ack_packet[:2], sys.byteorder))
        self.base = int.from_bytes(ack_packet[:2], sys.byteorder)  # update base to last acknowledged packet id
        if self.base == self.nextseqnum:  # if last packet in window then stop timer
            signal.setitimer(signal.ITIMER_REAL, 0)
        else:  # restart timer
            signal.setitimer(signal.ITIMER_REAL, self.timeout)

    def _timeout_handler(self, signum, frame):
        """
        SIG_ALARM handler automatically called upon timeout
        :return: None
        """
        print("Timeout! Retransmitting...")
        signal.setitimer(signal.ITIMER_REAL, self.timeout)  # start a new time
        for packet_id in range(self.base, self.nextseqnum):  # retransmit all packets in window
            self._send_packet(packet_id)

    def close_socket(self) -> None:
        self.socket.close()


def main():
    sender = Sender(rec_ip='localhost', rec_port=12001, max_seg_size=2048, win_size=4, timeout=1)
    sender.send_file('Test Files/SmallFile.png')
    sender.close_socket()


if __name__ == '__main__':
    main()
