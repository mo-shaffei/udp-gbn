import socket
import sys
import random


class Receiver:
    """
    Class to implement a sender

    """

    def __init__(self, max_seg_size: int, receiver_port: int = 12001, sim_loss_rate: float = 0.15):
        """

        :param max_seg_size: maximum segment size in bytes
        :param receiver_port: port to use for the receiver
        :param sim_loss_rate: simulated packet loss rate in the range (0-1)
        """
        self._max_seg_size = max_seg_size  # store maximum segment size
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create UDP socket
        self._socket.bind(('', receiver_port))  # bind socket to the receiver port
        self._expectedseqnum = 0
        self.sim_loss_rate = sim_loss_rate

    def receive_file(self, filename: str) -> None:
        """
        Receive file from sender
        :param filename: name of received file
        :return: None
        """
        received_data = bytearray()  # init received_data to empty bytearray
        while 1:  # loop until all packets have been received
            # receive a packet, set buffer size to max_seg_size + header size
            packet, sender_address = self._socket.recvfrom(self._max_seg_size + 6)
            if random.random() <= self.sim_loss_rate:
                continue
            packet_id = int.from_bytes(packet[:2], sys.byteorder)  # extract packet_id from first 16 bits
            file_id = packet[2:4]  # extract file_id from second 16 bits
            if packet_id == self._expectedseqnum:  # if packet id matched expectedseqnum, then accept it
                print("Received packet ", packet_id)
                self._send_ack(sender_address, file_id)  # send ACK to sender
                received_data.extend(packet[4:-2])  # extract payload and append it to received_data
                trailer_bits = packet[-2:]  # extract trailer bits from last 16 bits
                if trailer_bits.hex() == 'ffff':  # if trailer_bits is 'ffff' then all data is received
                    break
                self._expectedseqnum += 1  # increment expectedseqnum
            else:  # received unexpected packet, discard it
                print(f"Expected packet {self._expectedseqnum} but received {packet_id} and discarding it")
                self._send_ack(sender_address, file_id)

        print("Received all packets")
        with open(filename, 'wb') as file:  # write received data to file
            file.write(received_data)
        print("File written at ", filename)

    def _send_ack(self, sender_address, file_id):
        """
        send acknowledgement to sender
        :param sender_address: tuple containing (sender_ip: str, sender_port: int)
        :param file_id: id of current file being transmitted
        :return:
        """
        packet = self._expectedseqnum.to_bytes(2, sys.byteorder)  # create ack packet and add expectedseqnum to it
        packet += file_id  # add file id to packet
        self._socket.sendto(packet, sender_address)  # send packet

    def close_socket(self) -> None:
        self._socket.close()


def main():
    assert len(sys.argv) == 3
    receiver = Receiver(max_seg_size=2048, sim_loss_rate=float(sys.argv[2]))
    receiver.receive_file(sys.argv[1])
    receiver.close_socket()


if __name__ == "__main__":
    main()
