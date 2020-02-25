import time

import xmltodict as xmld
from stomp.listener import ConnectionListener

from ligmos.workers import connSetup
from ligmos.utils import amq, database 

import tempHACKLOIS


class LOISConsumer(ConnectionListener):
    def __init__(self, dbconn=None):
        """
        This will really be stuffed into a
        utils.amq.amqHelper class, so all the connections stuff is
        really over there in that class.  This is just to route the
        specific messages to the right parsers
        """

        # Adding an extra argument to the subclass
        self.dbconn = dbconn

        # Grab all the schemas that are in the ligmos library
        self.schemaDict = amq.schemaDicter()

    def on_message(self, headers, body):
        """
        Basically subclassing stomp.listener.ConnectionListener
        """
        print("NEW MESSAGE:")
        print(headers, body)
        print()
        badMsg = False
        tname = headers['destination'].split('/')[-1].strip()
        # Manually turn the bytestring into a string
        try:
            body = body.decode("utf-8")
            badMsg = False
        except UnicodeDecodeError as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        if badMsg is False:
            try:
                xml = xmld.parse(body)
                # If we want to have the XML as a string:
                # res = {tname: [headers, dumpPacket(xml)]}
                # If we want to have the XML as an object:
                res = {tname: [headers, xml]}
            except xmld.expat.ExpatError:
                # This means that XML wasn't found, so it's just a string
                #   packet with little/no structure. Attach the sub name
                #   as a tag so someone else can deal with the thing
                res = {tname: [headers, body]}
            except Exception as err:
                # This means that there was some kind of transport error
                #   or it couldn't figure out the encoding for some reason.
                #   Scream into the log but keep moving
                print("="*42)
                print(headers)
                print(body)
                print(str(err))
                print("="*42)
                badMsg = True

        # Now send the packet to the right place for processing.
        #   These need special parsing because they're just straight text
        if badMsg is False:
            try:
                if tname.endswith("loisLog"):
                    tempHACKLOIS.parserLOlogs(headers, body, db=self.dbconn)
                else:
                    print("Orphan topic: %s" % (tname))
                    print(headers)
                    print(body)
                    print(res)
            except Exception as err:
                # This is a catch-all to help find parsing errors that need
                #   to be fixed since they're not caught in a parser* func.
                print("="*11)
                print("WTF!!!")
                print(str(err))
                print(headers)
                print(body)
                print("="*11)


if __name__ == "__main__":
    amqhost = 'nasa42.lowell.edu'
    amqport = 61613
    loisLog = 'LOUI.nasa42.loisLog'
    loisCmd = 'LOUI.nasa42.loisCommand'
    cmd = 'gettemp'

    dbhost = 'tweedledee'
    dbport = 8086
    dbname = 'mesa42'

    # Set up our initial broker and database connections
    idbs = database.influxobj(host=dbhost,
                              port=dbport,
                              tablename=dbname,
                              user=None,
                              pw=None,
                              connect=True)

    # This is the listener/parser for LOIS information
    loisListen = LOISConsumer(dbconn=idbs)

    amqs = amq.amqHelper(amqhost, topics=[loisLog], port=amqport, 
                         listener=loisListen, connect=False)
    amqs.connect(listener=loisListen, subscribe=True)

    while True:
        time.sleep(5)
