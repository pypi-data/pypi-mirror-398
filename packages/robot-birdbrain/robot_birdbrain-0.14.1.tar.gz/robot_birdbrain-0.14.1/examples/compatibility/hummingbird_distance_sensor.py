from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

print(bird.getDistance(1))  # Print sensor value

# Exercise 1
threshold = 20
if bird.getDistance(1) < threshold:
    bird.setTriLED(1, 100, 0, 0)
else:
    bird.setTriLED(1, 0, 100, 0)
sleep(2)

# Exercise 2
threshold = 30
if bird.getDistance(1) > threshold:
    bird.print("FAR")
else:
    bird.print("NEAR")
sleep(3)

# Exercise 3
threshold = 20
while bird.getDistance(1) < threshold:  # As long as distance less than threshold
    bird.setTriLED(1, 100, 0, 0)  # Set tri-color LED red

bird.setTriLED(1, 0, 100, 0)  # Set tri-color LED green
sleep(1)

# Exercise 7 - This code works the same as Exercise 3, but there are no statements
# in the while loop. It just pauses the program until an object is close to the distance sensor
threshold = 20
bird.setTriLED(1, 100, 0, 0)  # Set tri-color LED red
while bird.getDistance(1) < threshold:  # As long as distance less than threshold
    pass  # Do nothing

bird.setTriLED(1, 0, 100, 0)  # Set tri-color LED green
sleep(1)

# Exercise 4
while bird.getDistance(1) > threshold:  # As long as distance > threshold
    bird.setTriLED(1, 0, 100, 0)  # Set tri-color LED green
bird.setTriLED(1, 100, 0, 0)  # Set tri-color LED red
bird.playNote(60, 1)
sleep(1)

# Exercise 5
while bird.getDistance(1) < threshold:
    bird.setPositionServo(1, 60)
    sleep(0.5)
    bird.setPositionServo(1, 0)
    sleep(0.5)

# Exercise 6 - You may have to hold your hand in front of the distance
# sensor up to 6 seconds to make the LED stop blinking. The Boolean statement
# is only checked at the top of the loop. Once the light turns blue, it will
# be 6 seconds before the Boolean statement is checked again.
while bird.getDistance(1) > threshold:
    bird.setTriLED(1, 0, 0, 100)
    sleep(3)
    bird.setTriLED(1, 100, 0, 100)
    sleep(3)

# Extra Challenge - This code controls a servo and LED with a distance sensor
# until the light sensor is covered.
lightThreshold = 10
distThreshold = 20
while bird.getLight(2) > lightThreshold:
    if bird.getDistance(1) < distThreshold:
        bird.setTriLED(1, 0, 100, 100)
        bird.setPositionServo(1, 90)
    else:
        bird.setTriLED(1, 0, 0, 0)
        bird.setPositionServo(1, 0)

bird.stopAll()
