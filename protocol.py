import socket
import logging
import time
py_logger = logging.getLogger(__name__)
py_logger.setLevel(logging.INFO)
class UDPBasedProtocol:
    def __init__(self, *, local_addr, remote_addr):
        self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_socket.settimeout(0.0001)
        self.remote_addr = remote_addr
        self.udp_socket.bind(local_addr)

    def sendto(self, data):
        return self.udp_socket.sendto(data, self.remote_addr)

    def recvfrom(self, n):
        msg, addr = self.udp_socket.recvfrom(n)
        return msg
def sleep():
    time.sleep(0.001)

mx_cnt = 5
cnt_start = 0
hlp_bt = 2
cnt_int = 4
class MyTCPProtocol(UDPBasedProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_connect = False
        self.buf_size = 10006
        self.sz_block = self.buf_size - 6
        self.packets = []
        self.ack = 0

    def connect(self):
        while True:
            self.sendto(int.to_bytes(cnt_start, 1, 'big'))
            try:
                fl = self.recvfrom(self.buf_size)
                fl = int.from_bytes(fl, 'big')
                if fl == cnt_start:
                    break
            except Exception as e:
                sleep()
                pass
        self.is_connect = True

    def split_to_packet(self, data: bytes):
        ln = len(data) // self.sz_block
        if len(data) % self.sz_block != 0:
            ln += 1
        for i in range(0, len(data), self.sz_block):
            wrd = data[i : i + self.sz_block]
            self.packets.append([len(wrd), wrd])

    def create_packet(self, id):
        data = int.to_bytes(len(self.packets), 2, 'big') + \
               int.to_bytes(self.ack, 4, 'big') + \
               self.packets[id][1]
        return data

    def parse_packet(self, data):
        fl = int.from_bytes(data[:2], 'big')
        if fl == cnt_start:
            return 0
        ack = int.from_bytes(data[2:6], 'big')
        return ack

    def send(self, data: bytes):
        if (not self.is_connect):
            self.connect()
        self.packets = []
        self.split_to_packet(data)
        for id in range(len(self.packets)):
            bl = self.create_packet(id)
            for cnt_pks in range(1, mx_cnt):
                for k in range(cnt_pks):
                    self.sendto(bl)
                fl = 0
                while True:
                    try:
                        ack = self.parse_packet(self.recvfrom(self.buf_size))
                        if (ack > self.ack):
                            self.ack = ack
                            fl = 1
                            break
                    except Exception as e:
                        sleep()
                        break
                if fl:
                    break
        return len(data)
    
    def recv_coonection(self):
        while True:
            try:
                data = self.recvfrom(self.buf_size)
                data = int.from_bytes(data, 'big')
                if data == cnt_start:
                    self.sendto(int.to_bytes(cnt_start, 2, 'big'))
                    break
            except Exception as e:
                sleep()
                pass
        self.is_connect = True

    def parse_send_packet(self, data: bytes):
        answ = {}
        fl = int.from_bytes(data[:2], 'big')
        if fl == cnt_start:
            return {}
        answ['cnt'] = fl
        answ['ack'] = int.from_bytes(data[2:6], 'big')
        answ['data'] = data[6:]

        return answ

    def recv(self, n: int):
        if (not self.is_connect):
            self.recv_coonection()
        answer = bytes()
        fl = 0
        cnt_pckt = 0
        while not fl:
            cnt_rp = 0
            while True and cnt_rp < mx_cnt:
                try:
                    data = self.recvfrom(self.buf_size)
                    if len(data) == 6:
                        continue
                    ans = self.parse_send_packet(data)
                    if ans == {}:
                        continue
                    ack = ans['ack']
                    if self.ack > ack:
                        continue
                    if ack == self.ack:
                        answer = answer + ans['data']
                        self.ack += len(ans['data'])
                        cnt_pckt += 1
                        # py_logger.info(f'{cnt_pckt} wtf {ans["data"]}')
                        if cnt_pckt == ans['cnt']:
                            fl = 1
                        break
                except Exception as e:
                    cnt_rp += 1
                    sleep()
                    break
            self.sendto(int.to_bytes(cnt_pckt, 2, 'big') + int.to_bytes(self.ack, 4, 'big'))
        # py_logger.info(f'finish data: {n} {answer[:n]}')
        return answer[:n]