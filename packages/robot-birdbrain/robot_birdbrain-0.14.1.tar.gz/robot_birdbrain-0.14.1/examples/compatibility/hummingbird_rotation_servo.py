from robot.hummingbird import Hummingbird
from time import sleep
import random  # import random number generator

bird = Hummingbird('A')  # Declare Hummingbird object

# Exercise 1
bird.setRotationServo(2, 100)  # Turn on at full speed
sleep(1)

# Exercise 2
bird.setRotationServo(2, -100)  # Clockwise quickly
sleep(2)
bird.setRotationServo(2, 25)  # Counterclockwise slowly
sleep(3)

# Exercise 3
for i in range(10):
    bird.setRotationServo(2, 100)
    sleep(0.5)
    bird.setRotationServo(2, 0)
    sleep(0.5)

# Exercise 4
for i in range(5):
    bird.setRotationServo(2, random.randint(0, 100))
    sleep(1)

# Exercise 5
for i in range(5):
    bird.setRotationServo(2, random.randint(-100, 100))
    sleep(1)

# Exercise 6
for i in range(5):
    bird.setTriLED(2, random.randint(0, 101), random.randint(0, 101), random.randint(0, 101))
    sleep(1)

# Extra Challenge
for i in range(5):
    bird.setTriLED(2, random.randint(0, 101), random.randint(0, 101), random.randint(0, 101))
    # sleep(random.random())     # Random number from 0-1
    sleep(5 * random.random())  # Random number from 0-5

bird.stopAll()
