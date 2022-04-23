# udp-gbn
Implementing Go-Back-N algorithm on top of UPD protocol to achieve reliable data transfer between two hosts

Usage:

python sender.py [File to send] [Receiver IP] [Receiver port]

python receiver.py [Name of file to output] [Simulated packet loss probability (0-1)]

Other parameters such as maximum segment size(mss), window size(N), and timeout interval are statically defined in sender.py
