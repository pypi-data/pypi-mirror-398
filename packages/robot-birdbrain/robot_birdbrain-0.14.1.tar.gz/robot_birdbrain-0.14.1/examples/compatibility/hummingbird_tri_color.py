from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

# Exercise 1
bird.setTriLED(1, 100, 0, 0)  # Turn LED Red
sleep(1)
bird.setTriLED(1, 0, 100, 0)  # Turn LED Green
sleep(1)
bird.setTriLED(1, 0, 0, 100)  # Turn LED Blue
sleep(1)

# Exercise 2
bird.setTriLED(1, 100, 0, 100)  # Turn LED Purple
sleep(1)
bird.setTriLED(1, 0, 100, 100)  # Turn LED Aqua
sleep(1)
bird.setTriLED(1, 100, 100, 0)  # Turn LED Yellow
sleep(1)

# Exercise 3
for i in range(5):
    bird.setTriLED(1, 0, 100, 0)  # LED Green
    sleep(0.5)
    bird.setTriLED(1, 0, 0, 0)  # LED Off
    sleep(0.5)

bird.setTriLED(1, 100, 0, 0)  # LED Red
sleep(1)

# Exercise 4
for i in range(6):
    bird.setTriLED(1, 100, 0, 0)  # LED Red
    sleep(0.5)
    bird.setTriLED(1, 0, 0, 0)  # LED Off
    sleep(0.5)

for i in range(3):
    bird.setTriLED(1, 0, 0, 100)  # LED Blue
    sleep(0.5)
    bird.setTriLED(1, 0, 0, 0)  # LED Off
    sleep(0.5)

for i in range(5):
    bird.setTriLED(1, 0, 100, 0)  # LED Green
    sleep(0.5)
    bird.setTriLED(1, 0, 0, 0)  # LED Off
    sleep(0.5)

# Exercise 5
for i in range(5):
    bird.setTriLED(1, 100, 0, 100)  # LED Purple
    sleep(1)
    bird.setTriLED(1, 0, 100, 0)  # LED Green
    sleep(1)
for i in range(5):
    bird.setTriLED(1, 0, 100, 100)  # LED Aqua
    sleep(0.25)
    bird.setTriLED(1, 100, 0, 0)  # LED Red
    sleep(0.25)

# Extra Challenge
for i in range(100):
    bird.setTriLED(1, i, 0, 100 - i)
    sleep(0.1)

bird.stopAll()  # Turn everything off
