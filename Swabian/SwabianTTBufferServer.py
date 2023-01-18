# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 14:22:09 2022

@author: qlab
"""

# this server will provide either time tag data as requested or histograms as requested

import numpy as np
import time, sys
import datetime
import yaml
import Pyro5, io, base64
import zmq
import threading, collections, itertools
import re


sys.path.append('C:\daq\qlab-scripts')
from WhiteRabbitSwitches import WRS_lib

global runThread



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



try:
    import Pyro5.api
except ModuleNotFoundError:

    print('Please install Pyro5 module. "python -m pip install Pyro5"')
    sys.exit()

def load_numpy_array(classname, data):
    assert classname == 'numpy.ndarray'
    buffer = io.BytesIO(base64.b64decode(data['data'].encode('ASCII')))
    return np.load(buffer, allow_pickle=False)

class TimeTag():
    def __init__(self, yaml_fn, party):
        
        fn = open(yaml_fn,'r')
        dicty = yaml.load(fn, Loader=yaml.SafeLoader)    
        fn.close()
        
        IP = dicty[party]["IP"]
               
        Pyro5.api.register_dict_to_class(classname='numpy.ndarray', converter=load_numpy_array)
        mes = "PYRO:TimeTagger@" + IP + ":23000"
        print(mes)
        self.TimeTagger = Pyro5.api.Proxy(mes)
        
        if dicty[party]["serial"] == 'virtual':
            self.tt = self.TimeTagger.createTimeTaggerVirtual()
        else:
            self.tt = self.TimeTagger.createTimeTagger(dicty[party]["serial"])
        self.tt.reset() # Reset all settings to default values
        print('Time Tagger serial:', self.tt.getSerial())
        
        self.pps_chan = dicty[party]["pps"]
        
        self.activeChannels = dicty[party]["active_ch"]
        
        for n in range(len(dicty[party]["active_ch"])):
            self.tt.setInputDelay((dicty[party]["active_ch"])[n], (dicty[party]["input_delay"])[n])
            self.tt.setDeadtime((dicty[party]["active_ch"])[n], (dicty[party]["deadtime"])[n])
            self.tt.setTriggerLevel((dicty[party]["active_ch"])[n], (dicty[party]["threshold"])[n])

        # timetags
        self.ttagData = np.array([], dtype=np.uint64)
        
        if bool((dicty[party]["condFilter"]["status"])):
            self.tt.setConditionalFilter((dicty[party]["condFilter"]["trigger"]), (dicty[party]["condFilter"]["filtered"]))
            
        if bool(dicty[party]["WRS"]["present"]):
            try:
                self.WRS = WRS_lib.dev('COM'+str(dicty[party]["WRS"]["COM"]))
            except: 
                print('WRS not connected')
    
    def getActiveChannels(self):
        return self.activeChannels
    
    def initCounts(self, channels = [1, 2]):
        self.rate = self.TimeTagger.Countrate(self.tt, channels)
        time.sleep(0.25)   
    
    def getCounts(self):
        return self.rate.getData()
    
        
    def initTimeTagStream(self, max_buf_size = 10**7, channels = [1, 2]):        
        self.stream = self.TimeTagger.TimeTagStream(self.tt, max_buf_size, channels)
        time.sleep(0.1)
                
    def clearTimeTagStream(self):
        self.stream.clear()
        
    def startTimeTagStream(self):        
        self.stream.start()
        
    def stopTimeTagStream(self):        
        self.stream.stop()    
    
    def getCaptureDuration(self):        
        return self.stream.getCaptureDuration()

    def getTimeTagStream(self):        
        self.ttagData = self.stream.getData()
               
        sys.stdout.write("\r" + str(len(self.ttagData)) + " timetags     ")
        sys.stdout.flush()
        
        return self.ttagData
    

        '''
        # ttag data structure: 
            #   8 bit overflow getEventType()
            #   8 bit reserved nothing
            #   16 bit missed events GetMissedEvents()
            #   32 bit channel number getChannels()
            #   64 bit timestamp in ps getTimeStamps()
            # ------------------------
            #   128 bit total
    
        a = np.array(dat.getEventTypes(),dtype=np.uint64)
        b = np.array(dat.getMissedEvents(),dtype=np.uint64)
        c = np.array(dat.getChannels(),dtype=np.uint64)
        d = np.array(dat.getTimestamps(),dtype = np.uint64)
        
        # prepare 2, 64 bit packets and join those
        ttagData = np.vstack((np.left_shift(a,56) + np.left_shift(b,32) + c  ,d)).reshape((-1,),order='F')       
        
                
        # short timestamp
        # 58 bits for time tag, 6 bits for channel number -> this will overfloww once every 80 hours
        # if overflow occurs: 4 bits for overflow type, 48 bits for missed events
        
        if dat.hasOverflows:
            print('overflow')
        else:
            compTTdata = np.array(np.left_shift(np.array(d & (2**58 -1), dtype=np.uint64),6) + c, dtype=np.uint64)
                    
            
        '''
    
    def openTTFile(self,basefn):     
        tim  = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        fn   = basefn + '_' + tim + '.bin'
        print('opening output file: ' + fn)
        self.binwrite = open(fn,'ab')
        
    def writeTTFile(self):        
        self.ttagData.tofile(self.binwrite)          
        print('writing to output file')
        
    def closeTTFile(self):
        self.binwrite.close()
        
    def close(self):
        self.TimeTagger.freeTimeTagger(self.tt)


def runBuffer(max_len, party):
    
    global runThread, circ_buf, meta_data

    circ_buf = collections.deque(maxlen = int(max_len))    
    TT = TimeTag("TTServerConfig.yaml", party)
    
    TT.initCounts(TT.activeChannels)
    time.sleep(2)
    print("counts:" + str(TT.getCounts()))
       
    TT.initTimeTagStream(max_buf_size = 10**7, channels = TT.activeChannels)
    TT.clearTimeTagStream()
    
    TT.startTimeTagStream()
    print("started logging thread.")
    old_pps = 0
    cur_pps = 0
    TAIdate = ''
    cal_fac = 0
    while runThread == 1:
        temp = TT.getTimeTagStream()
        circ_buf.extend(temp)
        pps_idx = np.where(np.array(temp)==TT.pps_chan)
        #print(pps_idx)
        if len(pps_idx[0]) != 0:
            try:
                TAIdate = TT.WRS.getDate()[1]
            except:
                TAIdate = 'no WRS connected'
            cur_pps = temp[pps_idx[0][0] + 1]
            #print(cur_pps, TAIdate)            
            if old_pps != 0:
                cal_fac = 1e12/(cur_pps - old_pps)
                #print(cal_fac-1)
            old_pps = cur_pps
        #else:
            #TAIdate = 'no pps found'            
        #time.sleep(0.001)
        meta_data = ([cur_pps, TAIdate, cal_fac])
        #print(circ_buf)
        
        
        
    TT.stopTimeTagStream()    
    TT.close()
    TT.WRS.close()
    


if (__name__ == '__main__'):
    
    
   
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    #socket.bind("tcp://*:5555")
            
    max_len   = 10**7
    
    if len(sys.argv) < 2:
        party = "Alice"
    else:
        party = str(sys.argv[1]) 
    
    # this is a quick fix for running two servers on the same PC
    if party == 'Alice':
        socket.bind("tcp://*:5555")
        print('Alice')
    if party == 'Bob':
        socket.bind("tcp://*:5556")
        print('Bob')
    
    TTlocal = TimeTag("TTServerConfig.yaml", party) # creating a local instance of the time tagger
    
    runThread = 1
    circBufThread = threading.Thread(target = runBuffer, args = (max_len, party))
    circBufThread.start()
    
    time.sleep(5)
    print('calibrating')
    #time.sleep(10)    
    print("ready to distribute time tags")    
    RunServer = True
    while RunServer:
        print('server running')
        #  Wait for next request from client
        message = socket.recv()
        print("Received request: %s" % message)
        lengthCB = len(circ_buf)
        # get last size timetags
    
        if message.decode().split(',')[0] == 'ttags':   
            #print('test')
            size = int(message.decode().split(',')[1])
            M = dict(cal_fac = meta_data[2], pps = int(meta_data[0]), TAI = meta_data[1])                
            # get the last 'size' elements            
            #print(circ_buf)
            if lengthCB < size:
                buf = (list(itertools.islice(circ_buf, 0, lengthCB)))    
            else:
                buf = (list(itertools.islice(circ_buf, lengthCB-size, lengthCB)))                            
            send_array(socket, np.array(buf, dtype = np.uint64), M)
        # get last m sec timetags    
        elif message.decode().split(',')[0] == 'past_sec':
            # get last m seconds of data
            dt  = int(float(message.decode().split(',')[1])*1e12) # in ps
            M   = dict(cal_fac = meta_data[2], pps = int(meta_data[0]), TAI = meta_data[1])
            CB  = np.array(circ_buf)            
            idx = np.where(CB > int(CB[-1:][0]-dt))[0][0]
            if idx == 0:
                print('not enough time accumulated using full buffer')                
                buf = (list(itertools.islice(CB, 0, lengthCB)))                                
            else:
                buf = (list(itertools.islice(CB, idx-1, lengthCB)))                                
            send_array(socket, np.array(buf, dtype = np.uint64), M)
            
        elif message.decode().split(',')[0] == 'get_cal_data':
            M   = dict(cal_fac = meta_data[2], pps = int(meta_data[0]), TAI = meta_data[1])
            send_array(socket, np.array([0], dtype = np.uint64), M)
            
        elif message.decode().split(',')[0] == 'ttag_range':
            mintt = int(float(message.decode().split(',')[1]))
            maxtt = int(float(message.decode().split(',')[2]))            
            #print(mintt,maxtt)
            M    = dict(cal_fac = meta_data[2], pps = int(meta_data[0]), TAI = meta_data[1])
            CB   = np.array(circ_buf)
            idx1 = np.where(CB > mintt)[0][0]-1
            idx2 = np.where(CB > maxtt)[0][0]-1
            #print(idx1,idx2)
            buf = (list(itertools.islice(CB, idx1, idx2)))   
            send_array(socket, np.array(buf, dtype = np.uint64), M)
        
        # simulated countrates
        elif message.decode().split(',')[0] == 'countrates_virtual':
            mess = message.decode().split(',')
            CR = np.empty([1,0])
            for n in range(len(mess)-1):
                #CR = np.append(CR, int((re.findall(r'\d+', mess[n+1]))[0]))
                CR = np.append(CR, np.random.poisson((n+1)*1000))
            M    = dict(cal_fac = 0, pps = 0, TAI = '')
            send_array(socket, np.array(CR, dtype = np.uint64), M)
        
        elif message.decode().split(',')[0] == 'countrates':
            mess = message.decode().split(',')
            channels = []
            for n in range(len(mess)-1):
                channels.append(int((re.findall(r'\d+', mess[n+1]))[0]))
            
            M    = dict(cal_fac = meta_data[2], pps = int(meta_data[0]), TAI = meta_data[1])
            #M    = dict(cal_fac = 0, pps = 0, TAI = '')
            
            #print(channels)
            TTlocal.initCounts(channels)
            CR = (TTlocal.getCounts())
            print(CR)
            
            send_array(socket, np.array(CR, dtype = np.uint64), M)
        
  #      initCounts(self, channels = [1, 2]):
  #      self.rate = self.TimeTagger.Countrate(self.tt, channels)
  #      time.sleep(1)   
  #  def getCounts(self):
  #      return self.rate.getData()
        
        elif message.decode().split(',')[0] == 'end':
            runThread = 0
            while circBufThread.is_alive():
                print("waiting for logging thread to terminate")
                time.sleep(1)

            print("terminated logging thread. exiting.")
            send_array(socket, np.array([], dtype = np.uint64), [0, 0, 'server ended'])
            RunServer = False
        else:
            send_array(socket, np.array([], dtype = np.uint64), [0, 0, 'bad request'])
   
  
    