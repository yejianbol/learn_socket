#!/usr/bin/env python2
# coding:utf-8
# Proof of Concept: UDP Hole Punching
# Two client connect to a server and get redirected to each other.
#
# This is the rendezvous server.
#
# Koen Bollen <meneer koenbollen nl>
# 2010 GPL
#

import socket
import struct
import sys
from collections import namedtuple

FullCone = "Full Cone"  # 0
RestrictNAT = "Restrict NAT"  # 1
RestrictPortNAT = "Restrict Port NAT"  # 2
SymmetricNAT = "Symmetric NAT"  # 3
NATTYPE = (FullCone, RestrictNAT, RestrictPortNAT, SymmetricNAT)


def addr2bytes(addr, nat_type_id):
    """Convert an address pair to a hash."""
    host, port = addr
    try:
        host = socket.gethostbyname(host)
    except (socket.gaierror, socket.error):
        raise ValueError("invalid host")
    try:
        port = int(port)
    except ValueError:
        raise ValueError("invalid port")
    try:
        nat_type_id = int(nat_type_id)
    except ValueError:
        raise ValueError("invalid NAT type")
    bytes = socket.inet_aton(host)
    bytes += struct.pack("H", port)
    bytes += struct.pack("H", nat_type_id)
    return bytes


def main():
    port = 29325
    try:
        port = int(sys.argv[1])
    except (IndexError, ValueError):
        pass

    sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockfd.bind(("", port))
    print "listening on *:%d (udp)" % port

    poolqueue = {}
    ClientInfo = namedtuple("ClientInfo", "addr, nat_type_id")
    while True:
        data, addr = sockfd.recvfrom(32)
        print "connection from %s:%d" % addr

        pool, nat_type_id = data.strip().split()
        sockfd.sendto("ok {0}".format(pool), addr)
        print("pool={0}, nat_type={1}, ok sent to client".format(pool, NATTYPE[int(nat_type_id)]))
        data, addr = sockfd.recvfrom(2)
        if data != "ok":
            continue

        print "request received for pool:", pool

        try:
            a, b = poolqueue[pool].addr, addr
            nat_type_id_a, nat_type_id_b = poolqueue[pool].nat_type_id, nat_type_id
            sockfd.sendto(addr2bytes(a, nat_type_id_a), b)
            sockfd.sendto(addr2bytes(b, nat_type_id_b), a)
            print "linked", pool
            del poolqueue[pool]
        except KeyError:
            poolqueue[pool] = ClientInfo(addr, nat_type_id)


if __name__ == "__main__":
    main()
