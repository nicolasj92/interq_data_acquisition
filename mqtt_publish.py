import paho.mqtt.client as paho
import mqtt
import time

publisher = mqtt.Publisher()

for i in range(1,2):
	publisher(
		'demo/test', 
		5	
	)
	time.sleep(300)