from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

bird.print("Hi")  # Print Hi on micro:bit display
sleep(1)

bird.print("Bambi")  # Exercise 1: Name
sleep(3)

bird.setDisplay([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1])  # Display a pattern
sleep(1)

bird.setDisplay([0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0])  # Exercise 2: Display a smiley face
sleep(1)

for i in range(10):  # Exercise 3: Animation
    bird.setDisplay([0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0])
    sleep(0.25)
    bird.setDisplay([0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    sleep(0.25)

# Exercise 4
bird.setDisplay([0] * 25)  # Clear the display

bird.setPoint(1, 1, 1)  # Turn on all the corners
bird.setPoint(1, 5, 1)
bird.setPoint(5, 1, 1)
bird.setPoint(5, 5, 1)
sleep(1)

# Exercise 5
bird.setDisplay([1] * 25)  # Turn on all the LEDS

bird.setPoint(1, 1, 0)  # Turn off all the corners
bird.setPoint(1, 5, 0)
bird.setPoint(5, 1, 0)
bird.setPoint(5, 5, 0)
sleep(1)

# Exercise 6
bird.setDisplay([0] * 25)  # Clear the display
for i in range(5):
    bird.setPoint(i + 1, i + 1, 1)
    sleep(0.5)

# Extra Challenge
bird.setDisplay([0] * 25)  # Clear the display
for i in range(5):
    for j in range(5):
        bird.setPoint(i + 1, j + 1, 1)
        sleep(0.5)
for i in range(5):  # Simple example - students might do much cooler things!
    for j in range(5):
        bird.setPoint(i + 1, j + 1, 0)
        sleep(0.5)

bird.stopAll()  # Turn everything off
