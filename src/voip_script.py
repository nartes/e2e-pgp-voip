import pyaudio
import ssl
import socket
import pprint
import multiprocessing
import os

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class Audio:
    def __init__(self):
        self.p = None
        self.in_stream = None
        self.out_stream = None

    def start_audio(self):
        self.p = pyaudio.PyAudio()

        self.in_stream = self.p.open(format = FORMAT,
                                     channels = CHANNELS,
                                     rate = RATE,
                                     input = True,
                                     frames_per_buffer = CHUNK)

        self.out_stream = self.p.open(format = FORMAT,
                                      channels = CHANNELS,
                                      rate = RATE,
                                      output = True)

    def close_audio(self):
        self.out_stream.stop_stream()
        self.out_stream.close()
        self.in_stream.stop_stream()
        self.in_stream.close()
        self.p.terminate()

    def record_audio(self):
        data = self.in_stream.read(CHUNK)

        return data

    def play_audio(self, data):
        self.out_stream.write(data)

    def loop_chunk(self):
        self.play_audio(self.record_audio())

def prepare_client():
    c_ctx = ssl.SSLContext(protocol = ssl.PROTOCOL_TLSv1_2)
    c_ctx.verify_mode = ssl.CERT_REQUIRED
    c_ctx.check_hostname = False
    c_ctx.load_cert_chain(certfile = 'build/client_ec.crt',
                          keyfile = 'build/client_ec')
    c_ctx.load_verify_locations(cafile = 'build/server_ec.crt')

    return c_ctx

def prepare_server():
    s_ctx = ssl.SSLContext(protocol = ssl.PROTOCOL_TLSv1_2)
    s_ctx.verify_mode = ssl.CERT_REQUIRED
    s_ctx.check_hostname = False
    s_ctx.load_cert_chain(certfile = 'build/server_ec.crt',
                          keyfile = 'build/server_ec')
    s_ctx.load_verify_locations(cafile = 'build/client_ec.crt')

    return s_ctx

def create_client(c_ctx):
    a = Audio()

    c_conn = c_ctx.wrap_socket(socket.socket(socket.AF_INET),
                               server_hostname = os.environ['CLIENT_HOST'])
    c_conn.connect(("localhost", int(os.environ['CLIENT_PORT'])))

    try:
        c_cert = c_conn.getpeercert()
        pprint.pprint(c_cert)

        a.start_audio()
        while True:
            c_conn.send(a.record_audio())
    finally:
        a.close_audio()
        c_conn.shutdown(socket.SHUT_RDWR)
        c_conn.close()

def create_server(s_ctx):
    a = Audio()

    s_conn = socket.socket()
    s_conn.bind((os.environ['SERVER_HOST'],
                 int(os.environ['SERVER_PORT'])))
    s_conn.listen(5)

    while True:
        s_newsocket, s_fromaddr = s_conn.accept()
        s_connstream = s_ctx.wrap_socket(s_newsocket, server_side = True)
        try:
            a.start_audio()
            data = s_connstream.recv(CHUNK)
            while data:
                a.play_audio(data)
                data = s_connstream.recv(CHUNK)
        finally:
            a.close_audio()
            s_connstream.shutdown(socket.SHUT_RDWR)
            s_connstream.close()

def test1():
    a = Audio()
    a.start_audio()
    for k in range(1000):
        a.loop_chunk()
    a.close_audio()

def test2():
    try:
        s = multiprocessing.Process(target = create_server,
                                    args = (prepare_server(),))

        c = multiprocessing.Process(target = create_client,
                                    args = (prepare_client(),))

        s.start()
        c.start()
    finally:
        s.join()
        c.join()

def test3():
    try:
        s = multiprocessing.Process(target = create_server,
                                    args = (prepare_server(),))

        s.start()
    finally:
        s.join()

def test4():
    try:
        c = multiprocessing.Process(target = create_client,
                                    args = (prepare_client(),))

        c.start()
    finally:
        c.join()
