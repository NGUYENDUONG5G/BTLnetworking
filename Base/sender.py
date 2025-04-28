import argparse
import socket
import sys
import threading

from utils import PacketHeader, compute_checksum

# Cấu hình cơ bản
MAX_SIZE_PKT = 1024  # số bytes tối đa trong 1 packet, bạn tùy chỉnh thêm

def sender(receiver_ip, receiver_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.05)

    start_header=PacketHeader(type=0,seq_num=0)
    start_header.computer_checksum(packet_header/b"")
    pkt=start_header/b""
    s.sendto(pkt.encode(), (receiver_ip, receiver_port))
     
    seq_num=0

    try:
        data, address=s.recvfrom(2048)
        ackHeader=data[:16]
        if(ackHeader.type!=3 or ackHeader.seq_num!=1) :
            print("Couldn't connect")
            return
        seq_num+=1
    except socket.timeout:
        print("time limit")
        return

    message = sys.stdin.buffer.read()
    packets=[]
    for i in range(0, len(message), MAX_SIZE):
        chunk = message[i:i + MAX_SIZE_PKT]
        pkt_header = PacketHeader(type=2, seq_num=seq_num, length=len(chunk))
        pkt_header.checksum = compute_checksum(pkt_header / chunk)
        pkt = pkt_header / chunk
        packets.append(bytes(pkt))
        seq_num += 1

    timer = None

    def start_timer():
        nonlocal timer
        if timer:
            timer.cancel()
        timer = Timer(0.5, timeout_handler)
        timer.start()

    



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    sender(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
