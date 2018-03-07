import triac     # Used for interfacing with the output
import connectionManager as cm
import machine
import time
import sys
import boot


checkFrequency = 200         # Time in ms between each check operation
# Time in ms between each connection attempt if not connected
reconnAttemptInterval = 5000
# Time in seconds to wait when not connected to a wifi network AND mqtt server before opening it's AP and webREPL.
# The "emergencyMode" function is executed after the timeout
emergencyModeTimeout = 15
lightstate, switchstate = 0, 0
downtimeCounter = 0
mqttActive = False
emergencyMode = False
MainLoop = True
returnCode = 0
compareTime = 0


# Proper shutdown procedure
def resetProcedure(code):
    # We need to disable all possible interrupts because we are writing data to the FS
    # If an interrupt happens during file write, our entire FS will get corrupted.
    global MainLoop
    cm.connMQTT(mqtt, False)
    triac.activate(0)
    MainLoop = False
    boot.saveSession(code, lightstate, switchstate)
    machine.reset()


# this is what gets executed when a message gets received
def sub_cb(topic, msg):
    global lightstate
    sendFeedback = False
    print((topic, msg))
    if not(isinstance(msg, str)):       # Checks if incomming message is a string
        msg = msg.decode("utf-8")       # if not turn it into a string
    if(msg == "ON"):
        sendFeedback = True
        lightstate = 1
        triac.activate(lightstate)
    elif(msg == "OFF"):
        sendFeedback = True
        lightstate = 0
        triac.activate(lightstate)
    elif(msg == "TOGGLE"):
        sendFeedback = True
        lightstate = 1 - lightstate
        triac.activate(lightstate)
    elif(msg == "REPORT"):
        mqtt.publish("light", lightstate, False, 1)
        sendFeedback = True
    elif(msg == "RESTART"):
        resetProcedure(1)
    elif(msg == "EDIT"):
        resetProcedure(0)
    if cm.mqttActive and sendFeedback:  # Sends every change actively to the serv
        mqtt.publish("light", str(lightstate), False, 1)


mqtt = cm.setMQTT(sub_cb)


def attemptConnect():
    global downtimeCounter
    if cm.wlan.isconnected() and not cm.mqttActive:
        print("Attempting to connect MQTT")
        if cm.connMQTT(mqtt, True):
            downtimeCounter = 0
            emergencyReact(False)
    if not cm.wlan.isconnected() or not cm.mqttActive:
        downtimeCounter += 1
    if downtimeCounter >= (emergencyModeTimeout * 1000) / reconnAttemptInterval:
        emergencyReact(True)


def emergencyReact(state):
    global emergencyMode
    if state and not emergencyMode:
        emergencyMode = True
        cm.setAP(True)
        if "webREPL" not in sys.modules:
            import webrepl
        webrepl.start()
    elif not state and emergencyMode:
        emergencyMode = False
        cm.setAP(False)
        webrepl.stop()


#   Checks the physical input pin and toggles the light if the pin state changed from last time when this fn was called.
#   0 - Sends MQTT messaged when the switch changes stage. Uses short pulses for triac activation (via interrupts).
#   1 - Does not send MQTT messages. Uses constant on or off value on the gate pin. (Useful for not corrupting files)
def checkInputChange(mode):
    global switchstate
    global lightstate
    if(switchPin.value() != switchstate):
        switchstate = switchPin.value()
        if mode == 0:
            sub_cb("light", "TOGGLE")
            return 1
        elif mode == 1:
            lightstate = 1 - lightstate
            triac.outPin.value(bool(lightstate))    # Inverts out pin value
    else:
        return 0


def main():
    # Executed on boot
    global switchPin
    global switchstate
    global lightstate
    switchPin = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
    cm.setAP(False)   # We don't want AP in work mode by default
    savedData = boot.readSession()
    lightstate = int(savedData[1])
    switchstate = int(savedData[2])
    triac.activate(lightstate)
    print("Bulb reinitialised")
    attemptConnect()

    # Main program
    while(MainLoop):
        global compareTime
        time.sleep_ms(checkFrequency)
        if time.ticks_diff(time.ticks_ms(), compareTime) > reconnAttemptInterval:
            attemptConnect()
            print("Done MQTT connect")
            compareTime = time.ticks_ms()
        if not emergencyMode:
            checkInputChange(0)
            if cm.mqttActive:
                mqtt.check_msg()
        else:
            checkInputChange(1)
