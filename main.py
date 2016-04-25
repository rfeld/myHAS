#!/usr/bin/python

import serial
import string
import librato
import socket
import datetime
import signal
import sys
import time


secretfile = open("secrets.txt",'r')
secrets = secretfile.readline().rstrip().split(';');

# Include your credentials here
api = librato.connect(secrets[0], secrets[1])

print "Secrets: ", secrets

def submitHumTempToPlotly(sensorId, hum, temp):
		retstring = "Sucessfully transmitted Hum and Temp of " + sensorId

		try:
			api.submit(sensorId + "_relf", hum)

			#api.submit("relativeLuftfeuchtigkeit", humidity)
		except:
			print "Sensor " + sensorId + " Error in Hum " + str(hum) 
			retstring = "Error transmitting Humidity of " + sensorId
		
		try:
			api.submit(sensorId + "_temp", temp)
			#api.submit("Mondfeuchtigkeit", temp)
		except:
			print "Sensor " + sensorId + "Error in temp " + str(temp)
			retstring = "Error transmitting Temperature of " + sensorId

		return retstring

def handleHumTemp(items):
	sensor_id   = items[2]
	humidity    = float(items[3]) / 10
	temperature = float(items[4]) / 100

	print "Sensor ID  = ", sensor_id
	print "Rel LF     = ", humidity
	print "Temperatur = ", temperature

	return submitHumTempToPlotly(sensor_id,humidity, temperature)

# Handles incoming Log Messages
# Expected format: 
# *MyHomeProto;LogMessage;<Sender/Source>;<Priority:HIGH|MEDIUM|LOW>;<Message>;END#
def handleLogMessage(items):
	return "(" + items[3] + ") "+ items[2]+": " + items[4] 


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
		return handleHumTemp(items)
	elif items[1] == "LogMessage":
		return handleLogMessage(items)
	else:
		return "Error: Unknown Message Type"

# Create datetime object to obtain current timestamp
t=datetime.datetime.now()

# Open Socket to listen for incoming Messages
#create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind to Port 12000
while True:
	try:
		serversocket.bind((socket.gethostname(), 12000))
		break
	except:
		print("Socket not available, yet. Retry in 2s...")
		time.sleep(2)

serversocket.listen(5)

# Make sure the connection is closed properly when interrupted with Ctrl-C
def signal_handler(signal, frame):
	print("Abbruch durch Ctrl-c!")
	serversocket.shutdown(2)
	serversocket.close()
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

while 1:
	#accept connections from outside
	(clientsocket, address) = serversocket.accept()
	
	print str(t.now()), " Incoming Connection"
	
	line = clientsocket.recv(1024)
	clientsocket.close()

	print "Text received: " + line 
	
	# High Level Message Handler
	print handleMessage(line)

	values = line.split(";")
	print values


