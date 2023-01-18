import yaml, logging
import numpy as np
import matplotlib.pyplot as plt
import zmq
from datetime import datetime

class TimeTag():    
    def __init__(self,IP = 'localhost' ,port = '5555'):
        
        self.context = zmq.Context()
        print("Connecting to TimeTag server…")
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://" + IP + ":" + port)

    def startGetTagRange(self, mintt = 0, maxtt = 1e12):
        self.socket.send(b"ttag_range, %d, %d"%(mintt, maxtt))        
        
    def getTagRange(self):
        ret = recv_array(self.socket)
        return ret
    
    def getCountRate(self, channels):
        self.socket.send(("countrates, %s"%str(channels)).encode())
        ret = recv_array(self.socket)
        return ret

    def startTagsFor(self, t): # get time tags for t secs
        self.socket.send(b"past_sec, %.3f"%t)
        
    def getTagsFor(self):        
        ret = recv_array(self.socket)
        return ret
    
    def getCalibrations(self): # get time tags for t secs
        self.socket.send(b"get_cal_data")
        ret = recv_array(self.socket)
        return ret
    
    def close(self):
        self.socket.close()
       

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
        

class Agent():
    def __init__(self):
        super(Agent, self).__init__()
        yf    = open('config/config.yaml','r')
        config = yaml.load(yf, Loader=yaml.SafeLoader)
        yf.close()
        self.BufferServerIP = config["BufferServer"]["IP"]
        self.BufferServerPort = config["BufferServer"]["port"]
        self.channel =  config["BufferServer"]["channel"]
        
    def run(self,specification,parameters):
        TT = TimeTag(self.BufferServerIP, self.BufferServerPort)
        result = TT.getCountRate([self.channel])[0][0].tolist()
        logging.info("result is {}".format(result))
        TT.close()
        return result
        

    