#standards imports
import json, logging

#imports to use AMQP 1.0 communication protocol
from proton import Message
from proton.handlers import MessagingHandler

class Send(MessagingHandler):
    def __init__(self, server, topic, messages):
        super(Send, self).__init__()
        self.server = server
        self.topic = topic
        self.confirmed = 0
        self.data = messages
        self.total = 1

    def on_connection_error(self, event):
        logging.error("connection error while sending msg to server: {} for topic: {}".format(self.server, self.topic))
        return super().on_connection_error(event)
    
    def on_transport_error(self, event) -> None:
        logging.error("transport error while sending msg to server: {} for topic: {}".format(self.server, self.topic))
        return super().on_transport_error(event)
        
    def on_start(self, event):
        conn = event.container.connect(self.server)
        event.container.create_sender(conn, self.topic)
   
    def on_sendable(self, event):
        logging.info("Agent sending msg to topic{}".format(self.topic))
        msg = Message(body=json.dumps(self.data))
        event.sender.send(msg)
        event.sender.close()
        
    def on_rejected(self, event):
        logging.error("msg regected while sending msg to server: {} for topic: {}".format(self.server, self.topic))
        return super().on_rejected(event)
        
    def on_accepted(self, event):
        logging.info("msg accepted in topic {}".format(self.topic))
        self.confirmed += 1
        if self.confirmed == self.total:
            event.connection.close()
    

    def on_disconnected(self, event):
        logging.error("disconnected error while sending msg to server: {} for topic: {}".format(self.server, self.topic))
        self.sent = self.confirmed