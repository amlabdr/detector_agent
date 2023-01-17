# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 09:06:47 2022

@author: qlab
"""

import time
import numpy as np
import serial


class dev(object):
  def __init__(self,serialport=''):
    self.wrs = serial.Serial(serialport,115200,timeout=0.25,bytesize=8, stopbits=1)
    print('connecting to WRS')



  def write(self, msg):
      self.wrs.write(msg.encode())
      
  def read(self):      # needs better termination instance - currently timeout after 250 ms
      #print('waiting for response')
      msg = self.wrs.read(20000)      
      try:
          ret = msg.decode()              
      except:
          ret = '-1'
      return ret
      

  def getAll(self):
      
      print('getting all WRS parameters')
      count = 0
      isEol = False
      start = False
      data = ''
      ser_bytes = self.wrs.readline()
        
      decoded_bytes = ser_bytes.decode("utf-8")
        
      data = decoded_bytes.replace('[01;34m', '')
      data = data.replace('[01;39m', '')
      data = data.replace('[01;36m', '')
      data = data.replace('[01;31m', '')
      data = data.replace('[01;32m', '')
      data = data.replace('[2J[1;1H[1;1f', '')

      temp={}      
      while data.startswith('WR Switch Sync Monitor') is False or start is False:
          
        #print(data)
        count = count + 1
        
        start = True
    
        if data.startswith('WR time (TAI):') is True:
           words = data.split(': ')
           temp['wr_time'] = words[1]
           temp['leap seconds'] = words[3]
    
        if data.startswith('Switch time (UTC):') is True:
           words = data.split(': ')
           temp['sw_time'] = words[1]
           temp['UTCOffset'] = words[2]
    

        if data.startswith('TimingMode') is True:
            words = data.split(': ')
            temp['Clock State'] = words[1]
            temp['PLL State'] = words[2]
    
        if data.startswith('Servo state*:') is True:
           words = data.split(':')
           #if words[1].endswith('wri1') is True:
           #    temp['servo_state'] = words[2] #Report status
           #else:
           #    temp['servo_state'] = words[1] #no status
           temp['servo_state'] = words[3]
     
        if data.startswith(' | meanDelay') is True:
           data = data.replace('nsec', '')
           data = data.replace(' ', '')
           words = data.split(':')
           temp['meanDelay (ns)'] = words[1]
    
        if data.startswith(' | delayMS') is True:
           data = data.replace('nsec', '')
           data = data.replace(' ', '')
           words = data.split(':')
           temp['leader-follower delay (ns)'] = words[1]
    
        if data.startswith(' | delayMM') is True:
            data = data.replace('nsec', '')
            data = data.replace(' ', '')
            words = data.split(':')
            temp['round-trip delay (ns)'] = words[1]
    
        if data.startswith(' | delayAsymmetry') is True:
            data = data.replace('nsec', '')
            data = data.replace(' ', '')
            words = data.split(':')
            temp['delay asymetry (ns)'] = words[1]
    
        if data.startswith('Total link') is True:
           data = data.replace('nsec', '')
           words = data.split(',')
           asym = words[0].split(': ')
           alpha = words[1].split(':')
           temp['total-link asymmetry (ns)'] = asym[1]
           temp['alpha'] = alpha[1]
    
        if data.startswith('Clock') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')
           temp['clock offset (ns)'] = words[1]
    
        if data.startswith(' | Phase') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')
           temp['phase setpoint (ns)'] = words[1].strip(' ')
    
    
        if data.startswith(' | delayCoefficient') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')       
           temp['delayCoefficient'] = words[1][:-4]
    
        if data.startswith(' | ingressLatency') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')       
           temp['ingressLatency (ns)'] = words[1].strip(' ')
    
        if data.startswith(' | egressLatency') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')       
           temp['egressLatency (ns)'] = words[1].strip(' ')
    
        if data.startswith(' | semistaticLatency') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')       
           temp['semistaticLatency (ns)'] = words[1].strip(' ')
    
        if data.startswith(' | offsetFromMaster') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')       
           temp['offsetFromMaster (ns)'] = words[1].strip(' ')
    
        if data.startswith(' | Update counter') is True:
           data = data.replace('times', '')
           words = data.split(': ')       
           temp['UpdateCounter'] = words[1].strip(' ')
    
        if data.startswith(' | Skew') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')
           temp['skew (ns)'] = words[1].strip(' ')
    
        if data.startswith('Servo update') is True:
           data = data.replace('times', '')
           words = data.split(': ')
           temp['servo_update'] = words[1]
    
        if data.startswith(' | Master PHY') is True:
           data = data.replace('nsec', '')
           words = data.split(': ')
           tx = words[1][:-2]
           rx = words[2][:-2]
           temp['leader_TX'] = tx.strip(' ')
           temp['leader_RX'] = rx.strip(' ')
    
        if data.startswith(' | Slave  PHY') is True:        
           data = data.replace('nsec', '')
           words = data.split(': ')
           tx = words[1][:-2]
           rx = words[2][:-2]
           temp['follower_TX'] = tx.strip(' ')
           temp['follower_RX'] = rx.strip(' ')
       
    
        if data.startswith('FPGA') is True:
           isEol = True
           words = data.split(' ')
           temp['FPGA'] = words[1]
           temp['PLL'] = words[3]
           temp['PSR'] = words[5]
           temp['PSL'] = words[7]
           
    
        ser_bytes = self.wrs.readline()
        decoded_bytes = ser_bytes.decode("utf-8")
    
        data = decoded_bytes.replace('[01;34m', '')
        data = data.replace('[01;39m', '')
        data = data.replace('[01;36m', '')
        data = data.replace('[01;31m', '')
        data = data.replace('[01;32m', '')
        data = data.replace('[2J[1;1H[1;1f', '')
    

          
      ret = ([ float(temp['leader-follower delay (ns)']), float(temp['UpdateCounter']), float(temp['FPGA']), float(temp['PLL']), float(temp['PSR']), float(temp['PSL']), float(temp['delay asymetry (ns)']), float(temp['meanDelay (ns)']), float(temp['round-trip delay (ns)']), float(temp['delayCoefficient']), float(temp['ingressLatency (ns)']), float(temp['egressLatency (ns)']), float(temp['semistaticLatency (ns)']), float(temp['offsetFromMaster (ns)']), float(temp['phase setpoint (ns)']), float(temp['skew (ns)']), float(temp['leader_TX']), float(temp['leader_RX']), float(temp['follower_TX']), float(temp['follower_RX'])])
        
      
      return ret, temp
    
    


      

  def getDate(self):
      #print("getting WRS time")
      self.write('wr_date get\r\n')
      ret = self.read()      
      
      TAItimestamp = ret.split('\r')[1][1:-4]
      TAIdate      = ret.split('\r')[2][1:-4]
      UTCdate      = ret.split('\r')[3][1:-4]      
      return [TAItimestamp, TAIdate, UTCdate]
  
    
  def startGetAll(self):
      self.write('wr_mon\r\n')
      ret = ''
      while ret == '':
          ret = self.read()   
          time.sleep(0.2)          
      return ret
  
  def getDelay(self):
      # takes return from getAll and returns MS delay
      idx = -1
      print('getting MS delay')
      while idx == -1:
        ret = ''
        while ret == '':
          ret = self.read()   
          time.sleep(0.2)       
        idx = ret.find('MS')
        if idx !=-1:
            temp  = ret[idx:idx+100]
            idx2  = temp.find('01;39m')
            idx3  = temp.find('ns')
            delay = int((float(temp[idx2+6:idx3])*1000))
        
        
      print('MS delay: %d ps'%delay)
      return delay


  def getCounter(self):
      # takes return from getAll and returns MS delay
      idx = -1
      print('getting WRS counter')
      while idx == -1:
        ret = ''
        while ret == '':
          ret = self.read()   
          time.sleep(0.2)    
        idx = ret.find('counter')
        if idx !=-1:
            temp  = ret[idx:idx+100]            
            idx2  = temp.find('01;39m')
            idx3  = temp.find('times')
            delay = int((float(temp[idx2+6:idx3])))
            
        
        
      print('update counter: %d'%delay)
      return delay
  
    
  def getTemps(self):
      idx = -1
      print('getting WRS temps')
      while idx == -1:
        ret = ''
        while ret == '':
          ret = self.read()   
          time.sleep(0.2)    
        idx = ret.find('FPGA')
        if idx !=-1:
            temp     = ret[idx:idx+110]            
            idx2     = temp.find('01;39m')            
            FPGAtemp = float(temp[idx2+6:idx2+12])
           
            idx = temp.find('PLL')
            if idx !=-1:
                temp2   = temp[idx:idx+20]            
                idx2    = temp2.find('01;39m')            
                PLLtemp = float(temp2[idx2+6:idx2+12])
                
            idx = temp.find('PSL')
            if idx !=-1:
                temp2   = temp[idx:idx+20]            
                idx2    = temp2.find('01;39m')            
                PSLtemp = float(temp2[idx2+6:idx2+12])
                
            idx = temp.find('PSR')
            if idx !=-1:
                temp2   = temp[idx:idx+20]            
                idx2    = temp2.find('01;39m')            
                PSRtemp = float(temp2[idx2+6:idx2+12])
        
      return [FPGAtemp, PLLtemp, PSLtemp, PSRtemp]
       
       
  def getAsymmetry(self):
      idx = -1
      print('getting WRS asymmetry')
      while idx == -1:
        ret = ''
        while ret == '':
          ret = self.read()   
          time.sleep(0.2)    
        idx = ret.find('delayAsymmetry')
        if idx !=-1:
            temp     = ret[idx:idx+50]            
            idx2     = temp.find('01;39m')            
            delas    = float(temp[idx2+6:idx2+23])           
        
      return delas
    
  def close(self):
      self.wrs.close()
      
      
    
if (__name__ == '__main__'):
  
    
  WRS = dev('COM22')  
  #ret = WRS.getDate()  
  #print(ret[1])  
  #test = WRS.startGetAll()
  #while 1:
  #data = WRS.read()
  #test = WRS.getCounter()
  #test = WRS.getDelay()
  #test = WRS.getTemps()
  #for n in range(10000):
  #    test,temp = WRS.getAll()
  #    print(test)
  #    time.sleep(1)
  WRS.close()