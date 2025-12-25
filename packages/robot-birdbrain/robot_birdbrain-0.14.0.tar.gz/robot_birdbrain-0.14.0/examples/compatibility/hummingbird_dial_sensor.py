from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

# Exercise 1
soundThreshold = 50
while bird.getSound(2) < soundThreshold:  # While it is quiet
    bird.setLED(1, 100)  # Turn on the light
bird.setLED(1, 0)  # Turn off the light
sleep(1)

# Exercise 1 - modified (the sleep() times inside the loop need to be short.
# Otherwise, you may need to clap a long time.)
while bird.getSound(2) < soundThreshold:  # While it is quiet
    bird.setLED(1, 100)  # Blink
    sleep(0.1)
    bird.setLED(1, 0)
    sleep(0.1)

sleep(1)

# Exercise 2
while bird.getSound(2) < soundThreshold:  # While it is quiet
    bird.setLED(1, bird.getDial(1))  # Set brightness with dial

sleep(1)

# Exercise 2 - modified
while bird.getSound(2) < soundThreshold:  # While it is quiet
    bird.setRotationServo(1, bird.getDial(1))  # Set speed with dial

sleep(1)

# Exercise 3
while bird.getSound(2) < soundThreshold:  # While it is quiet
    bird.setPositionServo(1, 1.8 * bird.getDial(1))  # Set angle with dial

sleep(1)

# Exercise 4
while bird.getSound(2) < soundThreshold:  # While it is quiet
    bird.setTriLED(1, bird.getDial(1), 0, 100 - bird.getDial(1))  # Set color with dial

sleep(1)

# Exercise 5
while bird.getSound(2) < soundThreshold:  # While it is quiet
    bird.setRotationServo(1, 2 * bird.getDial(1) - 100)  # Set speed with dial

sleep(1)

# Extra Challenge
dialThreshold = 50
while bird.getDial(1) < dialThreshold:  # While the dial value is low
    bird.setTriLED(1, bird.getSound(2), 0, 100 - bird.getSound(2))  # Set color with sound sensor
bird.stopAll()
