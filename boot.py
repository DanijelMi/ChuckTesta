# This file is executed on every boot (including wake-boot from deepsleep)
import esp
import machine
esp.osdebug(None)
SESSION_FILENAME = 'SessionData.txt'
exceptionMessage = None


def reboot():
    machine.reset()


def help1():
    print("This is a WIP help menu")
    print("Some description")


# Reads data about the light state before the restart, used after restart
def readSession():
    try:
        f = open(SESSION_FILENAME, 'r')
        text = f.read()
        f.close()
        return text
    except OSError:
        print("Session File not found")
        return "00000"


# Saves data about the light state before restarting
def saveSession(bootMode, param1, param2):
    f = open(SESSION_FILENAME, 'w')
    f.write(str(bootMode))
    f.write(str(param1))
    f.write(str(param2))
    f.close()


def getCrashReport():
    import sys
    sys.print_exception(exceptionMessage, sys.stderr)


# Decide whether to go into workMode or editMode
def main():
    import gc
    import connectionManager as cm
    cm.setWifi(True)
    gc.collect()
    try:
        text = readSession()
        if int(text[0]) == 0:
            print("Entering Edit Mode gracefully")
            import editMode
            editMode.main()
        else:
            print("Entering Work Mode")
            import workMode
            workMode.main()
            machine.reset()
    except Exception as exc:
        global exceptionMessage
        exceptionMessage = exc
        import triac
        triac.activate(0)
        import editMode
        editMode.main()


if __name__ == "__main__":
    main()
