# Note: For simplicity, we focused only on if-else statements. Some challenges
# could be completed with if statements that don't have an else.

from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

# Exercise 1
print(bird.getLight(1))  # Print sensor value

# Exercise 2
if bird.getLight(1) < 10:  # if it is dark
    bird.setLED(1, 100)  # turn on the light
    bird.setDisplay([0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0])  # Display <
else:  # otherwise
    bird.setLED(1, 0)  # turn off the light
    bird.setDisplay([0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0])  # Display >
sleep(1)

# Exercise 3 - when the threshold is 0, the light will never come on (because
# the light sensor can't have a value less than 0). When the threshold is 101, the
# light will always come on (because the light sensor value is always less than 101).

threshold = 10  # declaring a variable
if bird.getLight(1) < threshold:  # if it is dark
    bird.setLED(1, 100)  # turn on the light
else:  # otherwise
    bird.setLED(1, 0)  # turn off the light
sleep(5)

# Exercise 4
# Note that we don't need to declare the variable again
if bird.getLight(1) > threshold:  # if it is bright
    bird.setRotationServo(1, 100)  # turn on the motor
else:  # otherwise
    bird.setRotationServo(1, 0)  # turn off the motor
sleep(5)
bird.setRotationServo(1, 0)  # turn it off if it's on

# Exercise 5
if bird.getLight(1) < threshold:  # if it is dark
    bird.playNote(40, 1)  # low note
else:  # otherwise
    bird.playNote(80, 1)  # high note
sleep(1)

# Extra Challenge
for i in range(25):
    if bird.getLight(1) < threshold:  # if it is dark
        bird.playNote(40, 1)  # low note
    else:  # otherwise
        bird.playNote(80, 1)  # high note
    sleep(1)

bird.stopAll()

# micro:bit V2 Extra Challenge
if bird.getTemperature() > 20:  # if it is hot
    bird.setTriLED(1, 100, 0, 0)  # red
else:  # otherwise
    bird.setTriLED(1, 0, 0, 100)  # blue
sleep(1)
