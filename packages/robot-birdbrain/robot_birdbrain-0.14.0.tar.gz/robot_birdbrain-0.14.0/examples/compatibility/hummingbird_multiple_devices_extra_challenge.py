from robot.hummingbird import Hummingbird, Microbit
from time import sleep

bird1 = Hummingbird('A')  # Declare Hummingbird object
bird2 = Hummingbird('B')  # Declare Microbit object

while not (bird1.getButton('A')):

    # Light sensor of the first Hummingbird controls a light on the second
    if bird1.getLight(1) < 10:
        bird2.setTriLED(1, 0, 100, 0)
    else:
        bird2.setTriLED(1, 0, 0, 0)

    # Distance sensor on the second Hummingbird controls a motor on the first
    if bird2.getDistance(1) < 20:
        bird1.setPositionServo(1, 90)
    else:
        bird1.setPositionServo(1, 0)

bird1.stopAll()
bird2.stopAll()
