from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

while bird.getButton('A'):  # while button A is pressed
    bird.setTriLED(1, 100, 0, 100)
bird.setTriLED(1, 0, 0, 0)

sleep(1)

# Exercise 1
while not (bird.getButton('A')):  # while button A isn't pressed
    bird.setTriLED(1, 100, 0, 100)  # purple
bird.setTriLED(1, 0, 0, 0)  # off

# Exercise 2
while not (bird.getButton('B')):  # while button B isn't pressed
    if bird.getButton('A'):
        bird.setTriLED(1, 0, 100, 0)
    else:
        bird.setTriLED(1, 0, 0, 0)

# micro:bit V2 challenge
while not (bird.getButton('B')):  # while button B isn't pressed
    if bird.getButton("Logo"):
        bird.setPositionServo(1, 180)
    else:
        bird.setPositionServo(1, 0)

# Exercise 3
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getOrientation() == "Tilt left":  # If micro:bit tilted left
        bird.setPositionServo(1, 0)  # Set angle to 0°
    else:  # Otherwise
        bird.setPositionServo(1, 90)  # Set angle to 90°

# Exercise 3 - modified
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getOrientation() == "Tilt right":  # If micro:bit tilted right
        bird.setPositionServo(1, 180)  # Set angle to 180°
    else:  # Otherwise
        bird.setPositionServo(1, 90)  # Set angle to 90°

# Exercise 4
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getOrientation() == "Tilt left":  # If micro:bit tilted left
        bird.setPositionServo(1, 0)  # Set angle to 0°
    elif bird.getOrientation() == "Tilt right":  # If micro:bit tilted right
        bird.setPositionServo(1, 180)  # Set angle to 180
    else:  # Otherwise
        bird.setPositionServo(1, 90)  # Set angle to 0°

# Exercise 4 - modified
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getOrientation() == "Tilt left":  # If micro:bit tilted left
        bird.setPositionServo(1, 0)  # Set angle to 0°
    elif bird.getOrientation() == "Tilt right":  # If micro:bit tilted right
        bird.setPositionServo(1, 180)  # Set angle to 180
    elif bird.getOrientation() == "Logo down":  # If tilted logo down
        bird.setPositionServo(1, 30)  # Set angle to 30°
    else:  # Otherwise
        bird.setPositionServo(1, 90)  # Set angle to 0°

# Exercise 5 - I chose not to use an else so that I didn't play a note for "In between"
# but students may choose to include an else
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getOrientation() == "Tilt left":
        bird.playNote(60, 1)
    elif bird.getOrientation() == "Tilt right":
        bird.playNote(62, 1)
    elif bird.getOrientation() == "Logo down":
        bird.playNote(64, 1)
    elif bird.getOrientation() == "Logo up":
        bird.playNote(65, 1)
    elif bird.getOrientation() == "Screen up":
        bird.playNote(67, 1)
    elif bird.getOrientation() == "Screen down":
        bird.playNote(69, 1)
    sleep(1)

# Exercise 6
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getOrientation() == "Tilt left":
        bird.playNote(60, 1)
        bird.setPositionServo(1, 0)
        bird.setTriLED(1, 100, 0, 0)
    elif bird.getOrientation() == "Tilt right":
        bird.playNote(62, 1)
        bird.setPositionServo(1, 60)
        bird.setTriLED(1, 0, 100, 0)
    elif bird.getOrientation() == "Logo down":
        bird.playNote(64, 1)
        bird.setPositionServo(1, 120)
        bird.setTriLED(1, 0, 0, 100)
    elif bird.getOrientation() == "Logo up":
        bird.playNote(65, 1)
        bird.setPositionServo(1, 180)
        bird.setTriLED(1, 100, 0, 100)
    elif bird.getOrientation() == "Screen up":
        bird.playNote(67, 1)
        bird.setPositionServo(1, 90)
        bird.setTriLED(1, 100, 100, 0)
    elif bird.getOrientation() == "Screen down":
        bird.playNote(69, 1)
        bird.setPositionServo(1, 30)
        bird.setTriLED(1, 0, 100, 100)
    sleep(1)

# Extra Challenge
while not (bird.getButton('B')):  # while button B isn't pressed
    accelList = bird.getAcceleration()  # Store x, y, and z values of acceleration
    bird.setTriLED(
        1, 10 * abs(accelList[0]), 10 * abs(accelList[1]), 10 * abs(accelList[2])
    )  # Each acceleration value determines one RGB intensity

bird.stopAll()

# micro:bit V2 challenge
if bird.getTemperature() < 18:
    bird.playNote(48, 1)
    print("Brrr, I'm cold.")
elif bird.getTemperature() > 25:
    bird.playNote(72, 1)
    print("I'm burning up!")
else:
    bird.playNote(60, 1)
    print("I'm just right.")
sleep(1)
bird.stopAll()
