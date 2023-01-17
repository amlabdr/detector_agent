'''
Created on Oct 17 11:25:54 2022
agent  for quantum capabilities
@author: amlabdr
'''
#standards imports
from asyncio.log import logger
import json, time, yaml, importlib
from datetime import datetime
import Agent

import logging
import traceback
from threading import Thread

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#import communication protocol

from protocol.send import Sender
from protocol.receive import Receiver


def send_capability(url,topic,period,capabilityData):
    while True:
        # Publish Capability in "/capabilities"
        try:
            sender.send(url,topic, capabilityData)
            logging.info('capability sent')
        except Exception:
            logging.error("Agent can't send capability to the controller. Traceback:")
            traceback.print_exc()
        time.sleep(period)

if __name__ == "__main__":
    Agent = Agent.Agent()
    #read configuration file
    yf    = open('config/config.yaml','r')
    config = yaml.load(yf, Loader=yaml.SafeLoader)
    yf.close()
    PERIOD = config["controller"]["capability_period"]
    url = config["controller"]["IP"] +':'+ config["controller"]["port"]
    topic = 'topic://'+'/capabilities'
    sender = Sender()

    for capability in config["agent_capabilities"]:
        capabilityFile = open("capabilities/" + config["agent_capabilities"][capability]+".json", 'r')
        capabilityData = json.load(capabilityFile)
        capabilityFile.close()
        capabilityData["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        thread_send_capability = Thread(target=send_capability, args=(url,topic,PERIOD,capabilityData))
        thread_send_capability.start()

    #start lesstning for a specification from the controller 
    #capabilityData['endpoint'] should be the same for all capabilities
    topic='topic://'+capabilityData['endpoint']+'/specifications'
    logging.info("Agent will start lesstning for a specification from the controller")
    receiver = Receiver()
    receiver.receive_specification(url,topic, agent=Agent)

