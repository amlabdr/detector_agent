#standards imports
import json, traceback, logging, re, time
from datetime import datetime
from threading import Thread

#imports to use AMQP 1.0 communication protocol
from proton.handlers import MessagingHandler
from proton.reactor import Container
from protocol.send import Sender

sender = Sender()

def when2time(when):
    match = re.search(r'(now|\d+)\s*\.\.\.\s*(\d+)\s*/\s*(\d+)', when)
    if match:
        start_time = match.group(1)
        if start_time == "now":
            start_time = datetime.now().timestamp()
        else:
            start_time = int(start_time)
        stop_time = int(match.group(2))
        period = int(match.group(3))
    else:
        raise ValueError("Invalid time string format")

    return start_time, stop_time, period



class Receiver():
    def __init__(self):
        super(Receiver, self).__init__()
        
    def receive_specification(self, server, topic, agent):
        print("will start the rcv")
        Container(Specification_Receiver_handller(server,topic, agent)).run()


class Specification_Receiver_handller(MessagingHandler):
    def __init__(self, server,topic, agent):
        super(Specification_Receiver_handller, self).__init__()
        self.server = server
        self.topic = topic
        self.agent = agent
        logging.info("Agent will start listning for spec in the topic: {}".format(self.topic))
        self.interrupt = False

    def on_start(self, event):
        conn = event.container.connect(self.server)
        event.container.create_receiver(conn, self.topic)

    def process_specification(self, event, jsonData):
        logging.info("spec  received")
        specification = jsonData['specification']
        parameters = jsonData['parameters']
        endpoint = jsonData['endpoint']
        when = jsonData['when']
        start_time , stop_time, period = when2time(when)
        
        logging.info("specification received for {}".format(specification))
        logging.info("Agent will send receipt to the controller for {}".format(specification))
    
        #agent will publish a receipt for spec
        specification_receiptData=jsonData.copy()
        specification_receiptData['receipt'] = jsonData['specification']
        specification_receiptData["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        del specification_receiptData['specification']
        topic = event.message.reply_to
        sender.send(self.server,topic, specification_receiptData)
        logging.info("agent will do the {}".format(specification))
        result_msg = jsonData.copy()
        result_msg['result'] = result_msg['specification']
        del result_msg['specification']
        #agent will do the spec
        current_time = time.time()
        cumulated_seconds = 0
        while current_time < stop_time and not(self.interrupt):
            if current_time >= start_time:
                resultValues = []
                resultValues.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4])
                resultValues.append(int(cumulated_seconds*1000))
                resultValues.extend(self.agent.run(specification,parameters))
                print([type(x) for x in resultValues])
                #Agent will send the results to the controller
                result_msg["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
                result_msg['resultValues'] = [resultValues]
                logging.info("Agent will send result {} to the controller".format(result_msg['resultValues']))
                result_topic = 'topic://'+endpoint+'/results'
                sender.send(self.server,result_topic, result_msg)
            time.sleep(period/1000)
            cumulated_seconds +=(time.time() - current_time)
            current_time = time.time()
        self.interrupt = False

    def process_interrupt(self, event, jsonData):
        logging.info("interruption received")
        #agent will publish a receipt for interuption
        interruption_receiptData=jsonData.copy()
        interruption_receiptData['receipt'] = jsonData['interrupt']
        interruption_receiptData["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        del interruption_receiptData['interrupt']
        topic = event.message.reply_to
        sender.send(self.server,topic, interruption_receiptData)
        self.interrupt = True
    def on_message(self, event):
        try:
            jsonData = json.loads(event.message.body)
            logging.info("msg received {}".format(jsonData))
            if'specification' in jsonData:
                thread_process_specification = Thread(target=self.process_specification, args=(event, jsonData))
                thread_process_specification.start()
                return
            elif 'interrupt' in jsonData:
                thread_process_interruption = Thread(target=self.process_interrupt, args=(event, jsonData))
                thread_process_interruption.start()
                return
            else:
                pass
            
        except Exception:
            traceback.print_exc()
            