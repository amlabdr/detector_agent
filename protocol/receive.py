#standards imports
import json, traceback, logging, re, time
from datetime import datetime

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

    def on_start(self, event):
        conn = event.container.connect(self.server)
        event.container.create_receiver(conn, self.topic)
        
    def on_message(self, event):
        try:
            jsonData = json.loads(event.message.body)
            logging.info("Analyzer will send receipt to the controller")
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
            while current_time < stop_time:
                if current_time >= start_time:
                    resultValues = []
                    resultValues.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4])
                    resultValues.append(cumulated_seconds)
                    resultValues.append(self.agent.run(specification,parameters))
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

        except Exception:
            traceback.print_exc()
            