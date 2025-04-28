import argparse
import socket
import sys
from threading import Timer
import time
from utils import PacketHeader, compute_checksum

# Cấu hình cơ bản
MAX_SIZE_PKT = 1024  # số bytes tối đa trong 1 packet, bạn tùy chỉnh thêm


def sender(receiver_ip, receiver_port, window_size):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.5)

    start_header = PacketHeader(type=0, seq_num=0)
    start_header.checksum = compute_checksum(start_header/b"")
    pkt = start_header/b""
    s.sendto(bytes(pkt), (receiver_ip, receiver_port))

    seq_num = 0
    end_sent = False
    end_timer = None
    timer = None
    root = 0
    next_seq = 0

    try:
        data, addr = s.recvfrom(2048)
        ackHeader = data[:16]
        if ackHeader.type != 3 or ackHeader.seq_num != 1:
            print("Couldn't connect")
            return
        seq_num += 1
    except socket.timeout:
        print("time limit")
        return

    message = sys.stdin.buffer.read()
    packets = []
    for i in range(0, len(message), MAX_SIZE_PKT):
        chunk = message[i:i + MAX_SIZE_PKT]
        pkt_header = PacketHeader(type=2, seq_num=seq_num, length=len(chunk))
        pkt_header.checksum = compute_checksum(pkt_header / chunk)
        pkt = pkt_header / chunk
        packets.append((pkt))
        seq_num += 1

    def start_timer():
        nonlocal timer
        if timer:
            timer.cancel()
        timer = Timer(0.5, timeout_handler)
        timer.start()

    def timeout_handler():
        nonlocal root
        for i in range(root, min(root + window_size, len(packets))):
            s.sendto(bytes(packets[i]), (receiver_ip, receiver_port))
        start_timer()

    def stop_timer():
        nonlocal timer
        if timer:
            timer.cancel()
            timer = None

    def send_end_packet():
        nonlocal end_sent, end_timer
        header = PacketHeader(type=1, seq_num=next_seq)
        checksum = compute_checksum(bytes(header))
        header.checksum = checksum
        s.sendto(bytes(header), (receiver_ip, receiver_port))
        print("Sent END packet")
        end_sent = True

        end_timer = Timer(0.5, end_timeout_handler)
        end_timer.start()

    def end_timeout_handler():
        print("END packet timeout. Exiting.")
        sys.exit(0)

    while root < len(packets):
        while next_seq < root + window_size and next_seq < len(packets):
            s.sendto(bytes(packets[next_seq]), (receiver_ip, receiver_port))
            if root == next_seq:
                start_timer()
            next_seq += 1

        if root == len(packets) and not end_sent:
            send_end_packet()

        try:
            data, address = s.recvfrom(2048)
            ack_header = PacketHeader(data[:16])

            if ack_header.type == 3:
                if ack_header.seq_num >= root:

                    while root < len(packets) and packets[root].seq_num <= ack_header.seq_num:
                        root += 1
                    if root == next_seq:
                        stop_timer()
                    else:
                        start_timer()
            elif ack_header.type == 1:
                print("Received END ACK")
                sys.exit(0)
        except socket.timeout:
            pass

    stop_timer()
    s.close()


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
