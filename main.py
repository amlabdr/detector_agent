'''
Created on Oct 17 11:25:54 2022
agent  for quantum capabilities
@author: amlabdr
'''
#standards imports
from asyncio.log import logger
import json, time, yaml, argparse, importlib, sys

import logging
import traceback
from threading import Thread

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#imports to use AMQP 1.0 communication protocol
from utils.send import Send
from utils.receive import RecvSpecification
from proton.reactor import Container


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("capability", help="Name of the capability to use for example : coincidences_analyzing|photon_detection|source_control ")
    return parser.parse_args()

def send_capability(url,topic,period,capabilityData):
    while True:
        # Publish Capability in "/capabilities"
        try:
            Container(Send(url,topic, capabilityData)).run()
            logging.info('capability sent')
        except Exception:
            logging.error("Agent can't send capability to the controller. Traceback:")
            traceback.print_exc()
        time.sleep(period)

if __name__ == "__main__":
    #read configuration file
    yf    = open('config/config.yaml','r')
    config = yaml.load(yf, Loader=yaml.SafeLoader)
    yf.close()
    PERIOD = config["controller"]["capability_period"]
    url = config["controller"]["IP"] +':'+ config["controller"]["port"]
    topic = 'topic://'+'/capabilities'

    CAPABILITY = config["agent"]["capability"]
    module = "capabilities." + CAPABILITY + ".capability_agent"
    agent_path = "capabilities/" + CAPABILITY + "/"
    agent_module = importlib.import_module(module)
    agent = agent_module.capability_agent()

    for capability in agent.capabilities:
        capabilityFile = open(agent_path + capability, 'r')
        capabilityData = json.load(capabilityFile)
        capabilityFile.close()
        thread_send_capability = Thread(target=send_capability, args=(url,topic,PERIOD,capabilityData))
        thread_send_capability.start()

    #start lesstning for a specification from the controller 
    #capabilityData['endpoint'] should be the same for all capabilities
    topic='topic://'+capabilityData['endpoint']+'/specifications'
    logging.info("Agent will start lesstning for a specification from the controller")
    Container(RecvSpecification(url,topic, agent=agent)).run()

