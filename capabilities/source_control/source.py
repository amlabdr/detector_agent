import pyvisa
import time, datetime
import logging 

#PYVISA package is required for interfacing measurement devices
class CLD1015():
    
    def __init__(self, serialNumber=''):
        rm=pyvisa.ResourceManager()
        deviceList=rm.list_resources()
        self.FoundDevice = False
        self.connected = False
        #looking through the device list
        for i in deviceList:
            logging.info(i)
            if serialNumber in i:
                device=i
                logging.info("laser driver found, device ID:", device)
                self.FoundDevice=True
            else:
                logging.info("Cannot find laser driver:", i)
                break
                
            if self.FoundDevice:
                try:
                    self.CLD1015=rm.open_resource(device)
                    self.connected = True
                    logging.info("CLD1015 connected.")
                except OSError:
                    self.connected = False
                    logging.info('Cannot open device')
                 
    #switching on laser
    def laser_on(self):
        self.CLD1015.write("OUTP 1")
        time.sleep(0.5)
        logging.info('laser on.')
    
    #switching off laser    
    def laser_off(self):
        self.CLD1015.write("OUTP 0")
        time.sleep(0.5)
        logging.info('laser off.')
    
    #switching on tec PID loop
    def tec_on(self):
        self.CLD1015.write("OUTP2 1")
        time.sleep(0.5)
        logging.info('tec on.')
            
    #switching off tec PID loop
    def tec_off(self):
        self.CLD1015.write("OUTP2 0")
        time.sleep(0.5)
        logging.info('tec off.')
    
    #setting laser current, input current in units of Amps; max current allowed is 0.12A
    def set_laser_current(self, current=0):
        if current > 0.12:
            logging.info("exceeding the laser current limit!")
            self.CLD1015.write("SOUR:CURR:LEV:AMPL 0)")
        else:
            self.CLD1015.write("SOUR:CURR:LEV:AMPL "+str(current))
            time.sleep(0.5)
            logging.info("laser current set to "+str(current))
    
    #request a status update in ascii
    def show_status(self):
        print("-------------------------------------------------------------------------")
        result=[]
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-2]
        result.append(timestamp)
        print(self.CLD1015.query("*IDN?"))
        logging.info("{0: >30}".format("Laser on? 1(yes)/0(no):"), self.CLD1015.query("OUTP?"),end='')
        result.append("{}".format(self.CLD1015.query("OUTP?")))
        logging.info("{0: >30}".format("TEC on? 1(yes)/0(no):"), self.CLD1015.query("OUTP2?"),end='')
        result.append("{}".format(self.CLD1015.query("OUTP2?")))
        self.CLD1015.write("CONF:TEMP")
        temp=self.CLD1015.query("READ?")
        self.CLD1015.write("CONF:CURR")
        curr=self.CLD1015.query("READ?")
        self.CLD1015.write("CONF:VOLT")
        volt=self.CLD1015.query("READ?")
        logging.info("{0: >30}".format('Laser temperature:'),"{0}".format(temp),end='')
        result.append("{}".format(temp))
        logging.info("{0: >30}".format('Laser current:'),"{0}".format(curr),end='')
        result.append("{}".format(curr))
        logging.info("{0: >30}".format("Forward voltage:"),"{0}".format(volt),end='')
        result.append("{}".format(volt))
        return result
    
    #disconnect the laser driver
    def disconnect(self):
        self.CLD1015.close()
        logging.info('CLD1015 disconnected.')