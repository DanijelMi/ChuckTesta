import network   # For WiFI connection
from robust import MQTTClient
from ubinascii import hexlify
from machine import unique_id

# Change the file names from where to read configuration parameters
AP_FILENAME = "ap.txt"
WIFI_FILENAME = "wifi.txt"
MQTT_FILENAME = "mqtt.txt"
info = None

ID = hexlify(unique_id())
AP = network.WLAN(network.AP_IF)
wlan = network.WLAN(network.STA_IF)

mqttActive = False


def readFile(filename):
    f = open(filename, 'r')
    text = f.read().split('\r\n')
    f.close()
    info = {}
    for i in text:
        if len(i) > 0 and i[0] != '#':
            info[i.split('=')[0]] = i.split('=')[1]
    return info


# Reads configuration parameteres from a text file and sets the access point accordingly.
# Bool arg, to turn off or on.
def setAP(state):
    AP.active(False)
    if state:
        try:
            AP.active(True)
            info = readFile(AP_FILENAME)
            AP.config(essid=info['ssid'], channel=int(info['channel']), hidden=int(
                info['hidden']), authmode=int(info['authmode']), password=info['password'])
        except OSError:
            print("AP config file does not exist")


def setWifi(state):
    wlan.disconnect()
    wlan.active(False)
    if state:
        try:
            info = readFile(WIFI_FILENAME)
            wlan.active(True)
            if info['StaticIP'] == "DHCP":
                wlan.ifconfig((wlan.ifconfig()[0], wlan.ifconfig()[1],
                               wlan.ifconfig()[2], wlan.ifconfig()[3]))
            else:
                wlan.ifconfig((info['StaticIP'], wlan.ifconfig()[1],
                               wlan.ifconfig()[2], wlan.ifconfig()[3]))
            wlan.connect(info['SSID'], info['NetworkKey'])
        except OSError:
            print("Wifi config file does not exist")


# Reads configuration parameteres from a text file and sets the MQTT connection accordingly
# Set to false to turn mqtt off, or for ex. put in "mqtt.txt" to turn it on
def setMQTT(callback):
    global info
    try:
        info = readFile(MQTT_FILENAME)
        client = MQTTClient(client_id=ID, server=info['host'],
                            user=info['username'], password=info['password'], port=int(info['port']))
        client.set_last_will(topic=info['topic'], msg=info['lastWillMsg'])
        # Print diagnostic messages when retries/reconnects happens
        client.DEBUG = (info['consoleVerbose'] == "True")
        client.set_callback(callback)
        return client
    except OSError:
        print("MQTT config file does not exist")


def connMQTT(obj, state):
    global mqttActive
    if not state:
        if mqttActive:
            obj.disconnect()
        mqttActive = False
        return False
    elif state:
        try:
            # info = readFile(MQTT_FILENAME)
            obj.connect()
            obj.subscribe(info['topic'])
            mqttActive = True
            return True
        except OSError:
            mqttActive = False
            return False
