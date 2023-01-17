#standards imports
import json, traceback, logging

#imports to use AMQP 1.0 communication protocol
from proton.handlers import MessagingHandler
from proton.reactor import Container
from utils.send import Send


class RecvSpecification(MessagingHandler):
    def __init__(self, server,topic, agent):
        super(RecvSpecification, self).__init__()
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
            logging.info("specification received for {}".format(specification))
            logging.info("Agent will send receipt to the controller for {}".format(specification))
           
            #agent will publish a receipt for spec
            specification_receiptData=jsonData.copy()
            
            specification_receiptData['receipt'] = jsonData['specification']
            del specification_receiptData['specification']
            topic = event.message.reply_to
            Container(Send(self.server,topic, specification_receiptData)).run()
            logging.info("agent will do the {}".format(specification))

            #agent will do the spec
            resultValues = self.agent.run(specification,parameters)
            #Agent will send the results to the controller
            result_msg = jsonData.copy()
            result_msg['result'] = result_msg['specification']
            del result_msg['specification']
            result_msg['resultValues'] = resultValues
            logging.info("Agent will send result {} to the controller".format(result_msg['resultValues']))
            result_topic = 'topic://'+endpoint+'/results'
            Container(Send(self.server,result_topic, result_msg)).run()
        except Exception:
            traceback.print_exc()
            