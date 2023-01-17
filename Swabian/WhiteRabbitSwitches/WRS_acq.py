# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 13:45:39 2022

@author: qlab
"""

import serial
import datetime
import numpy as np
import pandas as pd

wr = serial.Serial()

wr.baudrate = 115200
wr.port = 'COM6'
wr.open()
wr.flushInput()

results = pd.DataFrame()
outputs = np.arange(1000)

isEol = False
start = False

timestamp = datetime.datetime.utcnow();

year =str(datetime.datetime.utcnow().year)
month = str(datetime.datetime.utcnow().month)
day = str(datetime.datetime.utcnow().day)

hour = str(datetime.datetime.utcnow().hour)
minute = str(datetime.datetime.utcnow().minute)
second = str(datetime.datetime.utcnow().second)

f = 'wrOutput'+year+month+day+hour+minute+second+'.csv'

#wr.write(b'wr_mon\r\n')
data = ''
ser_bytes = wr.readline()

decoded_bytes = ser_bytes.decode("utf-8")

data = decoded_bytes.replace('[01;34m', '')
data = data.replace('[01;39m', '')
data = data.replace('[01;36m', '')
data = data.replace('[01;31m', '')
data = data.replace('[01;32m', '')
data = data.replace('[2J[1;1H[1;1f', '')



count = 0

for output in outputs:

  ser_bytes = wr.readline()
  decoded_bytes = ser_bytes.decode("utf-8")

  data = decoded_bytes.replace('[01;34m', '')
  data = data.replace('[01;39m', '')
  data = data.replace('[01;36m', '')
  data = data.replace('[01;31m', '')
  data = data.replace('[01;32m', '')
  data = data.replace('[2J[1;1H[1;1f', '')
  data = data.replace('\r\n','')
  data = data.replace(',','')

  temp={}
  while data.startswith('WR Switch Sync Monitor') is False or start is False:
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

 #   if data.startswith('Leap seconds:') is True:
#     words = data.split(': ')
    if data.startswith('TimingMode') is True:
        words = data.split(': ')
        temp['Clock State'] = words[1]
        temp['PLL State'] = words[2]

    if data.startswith('Servo state:') is True:
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
       

    ser_bytes = wr.readline()
    decoded_bytes = ser_bytes.decode("utf-8")

    data = decoded_bytes.replace('[01;34m', '')
    data = data.replace('[01;39m', '')
    data = data.replace('[01;36m', '')
    data = data.replace('[01;31m', '')
    data = data.replace('[01;32m', '')
    data = data.replace('[2J[1;1H[1;1f', '')

    if temp != {} and isEol == True:
      results = results.append(temp, ignore_index=True)
      isEol = False
      
  ret = ([ float(temp['leader-follower delay (ns)']), float(temp['UpdateCounter']), float(temp['FPGA']), float(temp['PLL']), float(temp['PSR']), float(temp['PSL']), float(temp['delay asymetry (ns)']), float(temp['meanDelay (ns)']), float(temp['round-trip delay (ns)']), float(temp['delayCoefficient']), float(temp['ingressLatency (ns)']), float(temp['egressLatency (ns)']), float(temp['semistaticLatency (ns)']), float(temp['offsetFromMaster (ns)']), float(temp['phase setpoint (ns)']), float(temp['skew (ns)']), float(temp['leader_TX']), float(temp['leader_RX']), float(temp['follower_TX']), float(temp['follower_RX'])])
  print(ret)  
    

