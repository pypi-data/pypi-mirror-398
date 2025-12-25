from robot.hummingbird import Hummingbird, Microbit
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object
bit = Microbit('B')  # Declare Microbit object

# Exercise 1
while not (bit.getOrientation() == "Screen down"):
    if bit.getButton('A'):
        bird.setTriLED(1, 0, 0, 100)
    elif bit.getButton('B'):
        bird.setTriLED(1, 0, 0, 0)

# Exercise 2
while not (bit.getButton('A')):  # While button A isn't pressed
    if bit.getOrientation() == "Tilt left":
        bird.playNote(60, 1)
        bird.setPositionServo(1, 0)
        bird.setTriLED(1, 100, 0, 0)
    elif bit.getOrientation() == "Tilt right":
        bird.playNote(62, 1)
        bird.setPositionServo(1, 60)
        bird.setTriLED(1, 0, 100, 0)
    elif bit.getOrientation() == "Logo down":
        bird.playNote(64, 1)
        bird.setPositionServo(1, 120)
        bird.setTriLED(1, 0, 0, 100)
    elif bit.getOrientation() == "Logo up":
        bird.playNote(65, 1)
        bird.setPositionServo(1, 180)
        bird.setTriLED(1, 100, 0, 100)
    elif bit.getOrientation() == "Screen up":
        bird.playNote(67, 1)
        bird.setPositionServo(1, 90)
        bird.setTriLED(1, 100, 100, 0)
    elif bit.getOrientation() == "Screen down":
        bird.playNote(69, 1)
        bird.setPositionServo(1, 30)
        bird.setTriLED(1, 0, 100, 100)

sleep(1)

# Exercise 3
while not (bit.getButton('A')):  # While button A isn't pressed
    if bit.getCompass() > 75 and bit.getCompass() < 105:  # Direction between 75 and 105
        bit.print('E')
        bird.setTriLED(1, 100, 0, 0)
        bird.setRotationServo(1, 100)
    elif bit.getCompass() > 165 and bit.getCompass() < 195:  # Direction between 165 and 195
        bit.print('S')
        bird.setTriLED(1, 0, 100, 0)
        bird.setRotationServo(1, -100)
    elif bit.getCompass() > 255 and bit.getCompass() < 285:  # Direction between 255 and 285
        bit.print('W')
        bird.setTriLED(1, 0, 0, 100)
        bird.setRotationServo(1, 50)
    elif bit.getCompass() > 345 or bit.getCompass() < 15:  # Direction between 255 and 285
        bit.print('N')
        bird.setTriLED(1, 100, 0, 100)
        bird.setRotationServo(1, -50)
    else:
        bird.setDisplay([0] * 25)  # Clear screen
        bird.setTriLED(1, 0, 0, 0)
        bird.setRotationServo(1, 0)

# Exercise 4
while not (bird.getButton('A')):
    if bird.getDistance(1) < 30:
        bit.print("CLOSE")
        sleep(3)
    else:
        bit.print("FAR")
        sleep(2)

bird.stopAll()
bit.stopAll()
