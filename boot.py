from machine import Pin
import utime
import network

NETWORK_NAME = ""
NETWORK_PASSWORD = ""

def connect_to_network():
    interface = network.WLAN(network.STA_IF)
    interface.active(False)  # Disconnect if connected
    print('Initiating connection to network...')
    interface.active(True)
    interface.connect(NETWORK_NAME, NETWORK_PASSWORD)
    while not interface.isconnected():
        print("Connecting...")
        utime.sleep(1)
    print('Connection established! Network details:', interface.ifconfig())
   
print("Starting connection process...")
connect_to_network()
