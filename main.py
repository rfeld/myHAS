#!/usr/bin/python

import string
import librato
import socket
import datetime
import signal
import sys
import time
import os
import httplib, urllib

secretfilename = os.path.dirname(os.path.realpath(__file__)) + "/secrets.txt"
secretfile = open(secretfilename, 'r')
secrets = secretfile.readline().rstrip().split(';');

# Include your credentials here
api = librato.connect(secrets[0], secrets[1])

pushoverAppToken = secrets[2]
pushoverUserKey = secrets[3]

print "Secrets: ", secrets

print "Api: ", api

sys.stdout.flush()

def sendPushoverAlert( message ):
	conn = httplib.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
  		urllib.urlencode({
    		"token": pushoverAppToken,
    		"user": pushoverUserKey,
    		"message": message,
		"priority": 1
  	}), { "Content-type": "application/x-www-form-urlencoded" })
	conn.getresponse()


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

def submitVoltageToPlotly(sensorId, voltage):
		retstring = "Sucessfully transmitted voltage of " + sensorId

		try:
			api.submit(sensorId + "_v", voltage)

		except:
			print "Sensor " + sensorId + " Error in Voltage " + str(voltage) 
			retstring = "Error transmitting Voltage of " + sensorId
		
		return retstring

def handleHumTemp(items):
	sensor_id   = items[2]
	humidity    = float(items[3]) / 10
	temperature = float(items[4]) / 100

	print "Sensor ID  = ", sensor_id
	print "Rel LF     = ", humidity
	print "Temperatur = ", temperature

	return submitHumTempToPlotly(sensor_id,humidity, temperature)

def handleVoltage(items):
	sensor_id  = items[2]
	voltage    = float(items[3])
	print "Received Voltage: " + str(voltage) + " from " + sensor_id
	return submitVoltageToPlotly(sensor_id, voltage)

# Handles incoming Log Messages
# Expected format: 
# *MyHomeProto;LogMessage;<Sender/Source>;<Priority:HIGH|MEDIUM|LOW>;<Message>;END#
def handleLogMessage(items):
	logmessage = "(" + items[3] + ") "+ items[2]+": " + items[4] 
	if items[3] == "HIGH":
		sendPushoverAlert(logmessage) 
	
	return logmessage

def handleDingDong(items):
	t=datetime.datetime.now()
	message = "{0} - {1}".format(t, items[2])
	sendPushoverAlert(message)
	return message


# Takes Message and verifies it is a known type. 
# If everything is ok a sub handler is called and its output
# (=the content of the packet as string) returned. 
# In Case of en error it returns an Error message is returned
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
	elif items[1] == "DingDong":
		return handleDingDong(items)
	elif items[1] == "Voltage":
		return handleVoltage(items)
	else:
		return "Error: Unknown Message Type"

# Create datetime object to obtain current timestamp
t=datetime.datetime.now()

# Open Socket to listen for incoming Messages
#create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Make sure the connection is closed properly when interrupted with Ctrl-C
def signal_handler(signal, frame):
	print("Abbruch durch Ctrl-c!")
	serversocket.shutdown(2)
	serversocket.close()
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Bind to Port 12000
while True:
	try:
		serversocket.bind((socket.gethostname(), 12000))
		break
	except:
		print("Socket not available, yet. Retry in 2s...")
		time.sleep(2)

serversocket.listen(5)

# Give indication of program start
print "Waiting for incoming connections in port 12000"
sendPushoverAlert("myHAS wurde gestartet!")

while 1:
	# Make sure all Output from last iteration is on screen
	sys.stdout.flush()
	
	#accept connections from outside
	(clientsocket, address) = serversocket.accept()
	
	print str(t.now()), " Incoming Connection"
	
	# Set timeout to avoid blocking in case of error
	clientsocket.settimeout(1)

	try:	
		line = clientsocket.recv(1024)
	except:
		print(">>> Reading from socket triggered exception!")
		print "Unexpected error:", sys.exc_info()[0]

	clientsocket.close()

	print "Text received: " + line 
	
	# High Level Message Handler
	print handleMessage(line)

	#values = line.split(";")
	#print values


