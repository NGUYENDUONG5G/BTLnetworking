import argparse
import socket
import sys

from utils import PacketHeader, compute_checksum



def receiver(receiver_ip, receiver_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((receiver_ip,receiver_port))

    while True :
        pkt,senderAddress= s.recvfrom(2048)
        header=PacketHeader(pkt[:16])
        body=pkt[16:]
        oldCheckSum=header.checksum
        header.checksum=0

        pkt_checkSum=compute_checksum(header/body)
        if(oldCheckSum!=pkt_checkSum) :
            print("Error packet")
        else : print(body.decode())
   



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