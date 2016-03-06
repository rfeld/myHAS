#!/usr/bin/python

import serial
import string
import librato
import socket

secretfile = open("secrets.txt",'r')
secrets = secretfile.readline().rstrip().split(';');

# Include your credentials here
api = librato.connect(secrets[0], secrets[1])

print secrets

def handleHumTemp(items):
	sensor_id   = items[2]
	humidity    = float(items[3]) / 10
	temperature = float(items[4]) / 100

	print "Sensor ID  = ", sensor_id
	print "Rel LF     = ", humidity
	print "Temperatur = ", temperature


# Takes Message and verifies it is a known type. 
# If everything is ok a sub handler is called and "OK" returned. 
# In Case of en error it returns "Error"
def handleMessage(message):
	items = message.split(";")
	
	if len(items) < 4:
		return 	"Error: Message too short!"
	
	#Check if complete Message has been received
        if items[0] != '*MyHomeProto' or items[len(items)-1] != 'END#':
              	return "Error: Start or End Symbols incorrect/missing!"

	if items[1] == "HumTemp":
		handleHumTemp(items)
	else:
		return "Error: Unknown Message Type"


# Open Socket to listen for incoming Messages
#create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind to Port 12000
serversocket.bind((socket.gethostname(), 12000))
serversocket.listen(5)

while 1:
	#accept connections from outside
	(clientsocket, address) = serversocket.accept()
	
	print "Incoming Connection"
	
	line = clientsocket.recv(1024)
	clientsocket.close()

	print "Text received: " + line 
	
	# High Level Message Handler
	print handleMessage(line)

	#line=ser.readline().rstrip()
	
	values = line.split(";")
	print values

	# Rough check if useful values were read
	if line[0] != 'M' and len(values) == 3 :
		try:
			humidity = float(values[1])
			print "Humidity = " 
			print humidity
			api.submit("relativeLuftfeuchtigkeit", humidity)
		except:
			print "Error in " + line
		
		try:
			temperature = float(values[2])
			print "Temperature = "
			print temperature
			api.submit("Temperatur", temperature)
		except:
			print "Error in " + line

#ser.close()

