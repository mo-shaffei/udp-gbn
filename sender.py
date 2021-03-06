import math
import socket
import sys
import signal
from datetime import datetime


class Sender:
    """
    Class to implement a sender using Go-Back-N algorithm on top of UDP to achieve reliable transfer
    """

    def __init__(self, rec_ip: str, rec_port: int, max_seg_size: int, sender_port: int = 12000, win_size: int = 4,
                 timeout: float = 0.1):
        """

        :param rec_ip: ip of the receiver
        :param rec_port: port of the receiver
        :param max_seg_size: maximum segment size in bytes
        :param sender_port: port to use for the sender
        :param win_size: Go-Back-N window size
        :param timeout: ACK timeout interval before retransmission in seconds
        """
        self._rec_ip = rec_ip  # store receiver ip
        self._rec_port = rec_port  # store receiver port
        self._max_seg_size = max_seg_size  # store maximum segment size
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create UDP socket
        self._socket.bind(('', sender_port))  # bind socket to the sender port
        self._win_size = win_size  # store Go-Back-N window size
        self._timeout = timeout  # store ACK timeout interval
        signal.signal(signal.SIGALRM, self._timeout_handler)  # register timeout function handler
        self._base = self._nextseqnum = -1  # init base and nextseqnum to -1
        self._total_packets = 0
        self._total_bytes = 0
        self._total_retrans = 0
        self._trans_begin = 0
        self._trans_end = 0
        self.history = list()
        self._step = 0

    def send_file(self, filename):
        """
        Send file given by filename from sender to receiver using UDP and GBN
        :param filename: path and name of file to read and send
        :return: None
        """
        self._read_file(filename)  # read file and store it in self.file
        self._base = self._nextseqnum = 0  # init base and nextseqnum to 0
        last_packet_id = math.ceil(len(self.file) / self._max_seg_size) - 1  # calculate and store id of last packet
        self._trans_begin = datetime.today()
        while self._base != last_packet_id:  # loop until all packets are transmitted and acknowledged
            if self._nextseqnum < self._base + self._win_size:  # if new packets can be transmitted in window
                self._send_packet(self._nextseqnum)  # transmit the packet with id nextseqnum
                if self._base == self._nextseqnum:  # if first packet in window then start timer
                    signal.setitimer(signal.ITIMER_REAL, self._timeout)
                self._nextseqnum += 1  # increment nextseqnum
            else:  # no packets can be transmitted in window
                self._step += 1
                self._recv_ack()  # wait for acknowledgement from receiver
        print("Transmitted all packets!")
        self._trans_end = datetime.today()

    def _read_file(self, filename):
        """
        read file given by filename into self.file
        :param filename: path and name of file to read and send
        :return: None
        """
        with open(filename, 'rb') as file:  # read bytes from file
            self.file = file.read()

        if len(self.file) // self._max_seg_size > (2 ** 16) - 1:  # ensure packet_id won't overflow
            raise Exception('file size and mss overflows 16 bits packet id')

    def _send_packet(self, packet_id: int):
        """
        Send next packet from file given by packet_id
        :param packet_id: id of packet to send
        :return: None
        """
        self.history.append((packet_id, self._step))
        file_id = 0  # set file_id to 0
        current_byte = packet_id * self._max_seg_size  # get first byte to be sent
        trailer = "0000" if current_byte + self._max_seg_size < len(
            self.file) else "FFFF"  # if last segment make trailer "ffff"
        packet = packet_id.to_bytes(2, sys.byteorder)  # create packet and add 16 bits packet_id
        packet += file_id.to_bytes(2, sys.byteorder)  # add 16 bits file_id to the packet
        packet += self.file[current_byte: current_byte + self._max_seg_size]  # add payload to the packet
        packet += bytearray.fromhex(trailer)  # add trailer bits to the packet
        self._socket.sendto(packet, (self._rec_ip, self._rec_port))  # send packet to receiver
        self._total_packets += 1
        self._total_bytes += len(packet)
        print(f"Sending packet {packet_id}, total packets {self._total_packets}, total bytes {self._total_bytes}")

    def _recv_ack(self):
        """
        Wait to receive acknowledgement from receiver
        :return: None
        """
        ack_packet, _ = self._socket.recvfrom(4)  # wait for acknowledgement with buffer 4 bytes(2 packet_id, 2 file_id)
        self._base = int.from_bytes(ack_packet[:2], sys.byteorder) + 1  # update base to last acknowledged packet id
        if self._base == self._nextseqnum:  # if last packet in window then stop timer
            signal.setitimer(signal.ITIMER_REAL, 0)
        else:  # restart timer
            signal.setitimer(signal.ITIMER_REAL, self._timeout)

    def _timeout_handler(self, signum, frame):
        """
        SIG_ALARM handler automatically called upon timeout
        :return: None
        """
        print("Timeout! Retransmitting...")
        signal.setitimer(signal.ITIMER_REAL, self._timeout)  # start a new time
        self._step += 1
        for packet_id in range(self._base, self._nextseqnum):  # retransmit all packets in window
            self._send_packet(packet_id)
            self._total_retrans += 1

    def get_stats(self):
        """
        Get statistics about the file transfer
        :return:
        """
        stats = dict()
        stats['start'] = self._trans_begin.strftime('%H:%M:%S')
        stats['end'] = self._trans_end.strftime('%H:%M:%S')
        stats['elapsed'] = (self._trans_end - self._trans_begin).seconds
        stats['packets'] = self._total_packets
        stats['bytes'] = self._total_bytes
        stats['retrans'] = self._total_retrans
        stats['avg_packets'] = self._total_packets / stats['elapsed']
        stats['avg_bytes'] = self._total_bytes / stats['elapsed']
        return stats

    def close_socket(self) -> None:
        self._socket.close()


def main():
    assert len(sys.argv) == 4
    sender = Sender(rec_ip=sys.argv[2], rec_port=int(sys.argv[3]), max_seg_size=2048, win_size=4, timeout=1)
    sender.send_file(sys.argv[1])
    sender.close_socket()
    print(30 * '*' + ' Statistics ' + 30 * '*')
    print(sender.get_stats())
    print(72 * '*')


if __name__ == '__main__':
    main()
