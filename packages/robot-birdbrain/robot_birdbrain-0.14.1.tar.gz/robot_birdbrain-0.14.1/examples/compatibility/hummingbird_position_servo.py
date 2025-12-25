from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

bird.setPositionServo(1, 90)

for i in range(5):
    bird.setPositionServo(1, 0)
    sleep(1)
    bird.setPositionServo(1, 180)
    sleep(1)

for i in range(180):
    bird.setPositionServo(1, i)
    sleep(0.1)
for i in range(180):
    bird.setPositionServo(1, 180 - i)
    sleep(0.1)

for i in range(100):
    bird.setPositionServo(1, 1.8 * i)
    bird.setLED(1, i)
    sleep(0.1)
for i in range(100):
    bird.setPositionServo(1, 180 - 1.8 * i)
    bird.setLED(1, 100 - i)
    sleep(0.1)


angle = input("What angle do you want? ")
bird.setPositionServo(1, int(angle))

bird.stopAll()
