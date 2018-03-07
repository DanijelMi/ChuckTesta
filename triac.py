from machine import Pin
import time
from machine import Timer

inPin = Pin(12, Pin.IN, Pin.PULL_UP)
outPin = Pin(5, Pin.OUT)
tim = Timer(-1)

actDelay = 1


# Sends a single impulse to the triac gate
def pulse(X=0):
    outPin.value(1)
    time.sleep_us(1)
    outPin.value(0)


# When called, sets off a timer with a small delay that ultimately sends a pulse to the triac
# this delay is the heart of phase-shifted light dimming. Using timers instead of sleep to not
# halt the program during the waiting. Half wave duration : 50Hz => (1/50)/2 = 0.01s or 10ms.
# Therefore, delay should be between 0-9 (int only)
def actTriac(x):
    tim.init(period=actDelay, mode=Timer.ONE_SHOT, callback=pulse)


# Turns on the interrupt condition, making it fire every time a zero crossing occurs
def activate(state):
    global inPin
    if(state):
        inPin = Pin(12, Pin.IN, Pin.PULL_UP)
        inPin.irq(trigger=Pin.IRQ_RISING, handler=timeUS)
    # Disables the internal pull-up, therefore preventing any further RISING_EDGE case.
    else:
        inPin = Pin(12, Pin.IN)


atime = 0


def timeUS(x):
    global atime
    # print(time.ticks_us() - atime)
    if((time.ticks_us() - atime) > 8000):
        actTriac(1)
        atime = time.ticks_us()
