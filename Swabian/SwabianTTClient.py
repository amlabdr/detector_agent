# -*- coding: utf-8 -*-
"""
Created on Wed Jul 27 11:24:06 2022

@author: qlab
"""

import zmq
import numpy as np
import time




def send_array(socket, A, meta_data, flags=0, copy=True, track=False):
    """send a numpy array with metadata"""
    md = dict(
        dtype = str(A.dtype),
        shape = A.shape,
    )
    socket.send_json(meta_data, flags|zmq.SNDMORE)
    socket.send_json(md, flags|zmq.SNDMORE)
    return socket.send(A, flags, copy=copy, track=track)

def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    meta_data = socket.recv_json(flags=flags)
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = msg
    A = np.frombuffer(buf, dtype=md['dtype'])
    return A.reshape(md['shape']), meta_data



context = zmq.Context()

#  Socket to talk to server
print("Connecting to TimeTag server…")
socketA = context.socket(zmq.REQ)
socketA.connect("tcp://129.6.168.224:5555") #Alice

socketB = context.socket(zmq.REQ)
socketB.connect("tcp://129.6.168.224:5556") #Alice

socketA.send(b"past_sec, 5")
#time.sleep(1)
socketB.send(b"past_sec, 5")
A = recv_array(socketA)
B = recv_array(socketB)
print(A)
print(B)