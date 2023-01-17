import yaml, logging
from capabilities.source_control.source import CLD1015
class capability_agent():
    def __init__(self):
        super(capability_agent, self).__init__()
        self.capabilities = {"capabilities/command_capability.json","capabilities/measurement_capability.json"}
        #read configuration file
        yf    = open('capabilities/source_control/config/config.yaml','r')
        config = yaml.load(yf, Loader=yaml.SafeLoader)
        yf.close()
        self.serialNumber = config["source"]["serial"]
    def run(self,specification,parameters):
        return ["ok"]
        self.source = CLD1015(self.serialNumber)
        if self.source.connected:
            status = ""
            if specification == "measure":
                status=self.source.show_status()
                
            elif specification == "command":
                if "Laser" in parameters:
                    if parameters["Laser"] == "ON":
                        status += self.source.laser_on()
                    elif parameters["Laser"] == "OFF":
                        status += self.source.laser_off()
                    else:
                        pass
                elif "Tec" in parameters:
                    if parameters["Tec"] == "ON":
                        status += self.source.laser_on()
                    elif parameters["Tec"] == "OFF":
                        status += self.source.laser_off()
                    else:
                        pass
                elif "Laser_current" in parameters:
                    status += self.source.set_laser_current(int(parameters["Laser_current"]))
                else:
                    pass
            return [status]

    