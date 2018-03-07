import connectionManager as cm
import webrepl
from boot import SESSION_FILENAME
from boot import readSession


def oneFirstBit():
    text = readSession()
    f = open(SESSION_FILENAME, 'w')
    f.write("1" + text[1:])
    f.close()


# Set a flag so the device goes to workMode the next time it reboots
def main():
    # Sets a flag in a file to force the device into work mode on ntext reboot
    oneFirstBit()
    cm.setAP(True)          # Activate Access Point
    webrepl.start()         # Activate webREPL
