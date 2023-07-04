from machine import Pin
import machine
import utime as time
import ubinascii
from dht11file import DHT11Sensor
from umqttsimple import MQTTClient

# Config for Sensor
sensor_pin = Pin(28, Pin.OUT, Pin.PULL_DOWN)
dht_sensor = DHT11Sensor(sensor_pin)

# Config for MQTT
CLIENT = ubinascii.hexlify(machine.unique_id())
MQTT_HOST = "io.adafruit.com"
PORT_NUM = 1883
ADA_USERNAME = ""
ADA_PASSWORD = ""
PUB_TEMPERATURE = b"{ADA_USERNAME}/f/temperature"
PUB_HUMIDITY = b"{ADA_USERNAME}/f/humidity"

last_pub = time.time()  # timestamp of the last published message
publish_gap = 60  # interval between messages

def reboot():
    print("Resetting...")
    time.sleep(5)
    machine.reset()

def read_temperature_sensor():
    time.sleep(2)
    try:
        temp = dht_sensor.temperature
        time.sleep(2)
    except Exception as e:
        print("Exception occurred:", str(e))
        return None
    return temp

def read_humidity_sensor():
    time.sleep(2)
    try:
        hum = dht_sensor.humidity
        time.sleep(2)
    except Exception as e:
        print("Exception occurred:", str(e))
        return None
    return hum

def run():
    print(f"Starting connection with MQTT Broker :: {MQTT_HOST}")
    client = MQTTClient(CLIENT, MQTT_HOST, PORT_NUM, ADA_USERNAME, ADA_PASSWORD, keepalive=60)
    client.connect()
    print(f"Connected to MQTT Broker :: {MQTT_HOST}, and waiting for callback function to trigger!")

    while True:
        client.check_msg()
        global last_pub
        if (time.time() - last_pub) >= publish_gap:
            temperature_value = read_temperature_sensor()
            humidity_value = read_humidity_sensor()
            if temperature_value is not None:
                client.publish(PUB_TEMPERATURE, str(temperature_value).encode())
                last_pub = time.time()
                print("Temperature data sent:", temperature_value)
            if humidity_value is not None:
                client.publish(PUB_HUMIDITY, str(humidity_value).encode())
                last_pub = time.time()
                print("Humidity data sent:", humidity_value)
        time.sleep(1)

if __name__ == "__main__":
    while True:
        try:
            run()
        except OSError as e:
            print("Error: " + str(e))
            reboot()
