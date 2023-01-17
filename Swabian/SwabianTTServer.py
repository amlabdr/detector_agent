# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 14:22:09 2022

@author: qlab
"""

# this server will provide either time tag data as requested or histograms as requested

import numpy as np
import matplotlib.pyplot as plt
import time, sys
import datetime
import yaml
import Pyro5, io, base64
import zmq

def send_array(socket, A, flags=0, copy=True, track=False):
    """send a numpy array with metadata"""
    md = dict(
        dtype = str(A.dtype),
        shape = A.shape,
    )
    socket.send_json(md, flags|zmq.SNDMORE)
    return socket.send(A, flags, copy=copy, track=track)

try:
    import Pyro5.api
except ModuleNotFoundError:
    import sys
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
        
        self.tt = self.TimeTagger.createTimeTagger(dicty[party]["serial"])
        self.tt.reset() # Reset all settings to default values
        print('Time Tagger serial:', self.tt.getSerial())
        
        
        self.activeChannels = dicty[party]["active_ch"]
        
        for n in range(len(dicty[party]["active_ch"])):
            self.tt.setInputDelay((dicty[party]["active_ch"])[n], (dicty[party]["input_delay"])[n])
            self.tt.setDeadtime((dicty[party]["active_ch"])[n], (dicty[party]["deadtime"])[n])
            self.tt.setTriggerLevel((dicty[party]["active_ch"])[n], (dicty[party]["threshold"])[n])

        # timetags
        self.ttagData = np.array([], dtype=np.uint64)
        
        if bool((dicty[party]["condFilter"]["status"])):
            self.tt.setConditionalFilter((dicty[party]["condFilter"]["trigger"]), (dicty[party]["condFilter"]["filtered"]))
    
    def getActiveChannels(self):
        return self.activeChannels
    
    def initCounts(self, channels = [1, 2]):
        self.rate = self.TimeTagger.Countrate(self.tt, channels)
        time.sleep(1)   
    
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
        

if (__name__ == '__main__'):
    
    
    TT = TimeTag("TTServerConfig.yaml", "Alice")
        
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    
    
    TT.initCounts(TT.activeChannels)
    time.sleep(2)
    print("counts:" + str(TT.getCounts()))
    
    
    TT.initTimeTagStream(max_buf_size = 10**7, channels = TT.activeChannels)
    TT.clearTimeTagStream()
    
    print("ready to distribute time tags")    
    while True:
        #  Wait for next request from client
        message = socket.recv()
        print("Received request: %s" % message)
        
        #  Do some 'work'
        #time.sleep(1)

        #  Send reply back to client
        TT.startTimeTagStream()
        time.sleep(0.1)
        TT.stopTimeTagStream()       
        send_array(socket, TT.getTimeTagStream())
       
    TT.close()
    
    

'''

    Alice = TimeTag(IP,"Alice.yaml")
    Bob = TimeTag(IP,"Bob.yaml")
    fig1 = plt
    
    
    Alice.initCounts(Alice.getActiveChannels())
    Bob.initCounts(Bob.getActiveChannels())
    
    print('Alice counts:')
    print(Alice.getCounts())
    print('Bob counts:')
    print(Bob.getCounts())
    
    
    Alice.openTTFile('AliceTTagADVRsourceWith10MHzSync0_5pps')
    Bob.openTTFile('BobTTagADVRsourceWith10MHzSync0_5pps')
    
    Alice.initTimeTagStream(max_buf_size=10**7, channels = [1, 7, 8])
    Bob.initTimeTagStream(max_buf_size=10**7, channels = [1, 3, 4])
    
    Alice.clearTimeTagStream()
    Bob.clearTimeTagStream()
    Alice.startTimeTagStream()
    Bob.startTimeTagStream()
    
    for n in range(1):
        test = Alice.getTimeTagStream()
        test = Bob.getTimeTagStream()
        time.sleep(0.5)
        Alice.writeTTFile()
        Bob.writeTTFile()
    Alice.closeTTFile()
    Bob.closeTTFile()
    
    
  
    ttag.initHistogram()
    for n in range(10):
        a = ttag.getHistogram()
        print(max(a[1]))
        fig1.plot(a[0], a[1])
        fig1.show()

    Alice.close()
    Bob.close()
'''