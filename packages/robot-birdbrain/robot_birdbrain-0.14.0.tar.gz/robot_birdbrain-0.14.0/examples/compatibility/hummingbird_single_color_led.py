from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

# Exercise 1 - changing the 100 to smaller numbers makes the LED less bright
bird.setLED(1, 100)  # Turn on LED 1
sleep(1)  # Wait 1 second

bird.stopAll()  # Turn everything off

# Exercise 2
bird.setLED(1, 100)  # Turn on LED 1
sleep(5)  # Wait 5 seconds

# Exercise 3
bird.setLED(1, 100)  # Turn on LED 1
sleep(1)  # Wait 1 second
bird.setLED(1, 0)  # Turn off LED 1
bird.setLED(2, 100)  # Turn on LED 2
sleep(1)  # Wait 1 second

# Exercise 3 - modified
bird.setLED(1, 100)  # Turn on LED 1
sleep(1)  # Wait 1 second
bird.setLED(1, 0)  # Turn off LED 1
bird.setLED(2, 100)  # Turn on LED 2
sleep(1)  # Wait 1 second
bird.setLED(3, 100)  # Turn on LED 3
sleep(1)  # Wait 1 second

# Exercise 4
bird.setLED(1, 100)  # Turn on LED 1
bird.setLED(2, 100)  # Turn on LED 2
bird.setLED(3, 100)  # Turn on LED 3
sleep(2)
bird.setLED(1, 75)  # Turn on LED 1 at 75%
bird.setLED(2, 75)  # Turn on LED 2 at 75%
bird.setLED(3, 75)  # Turn on LED 3 at 75%
sleep(2)
bird.setLED(1, 50)  # Turn on LED 1 at 50%
bird.setLED(2, 50)  # Turn on LED 2 at 50%
bird.setLED(3, 50)  # Turn on LED 3 at 50%
sleep(2)
bird.setLED(1, 25)  # Turn on LED 1 at 25%
bird.setLED(2, 25)  # Turn on LED 2 at 25%
bird.setLED(3, 25)  # Turn on LED 3 at 25%
sleep(2)

bird.stopAll()  # Turn everything off
