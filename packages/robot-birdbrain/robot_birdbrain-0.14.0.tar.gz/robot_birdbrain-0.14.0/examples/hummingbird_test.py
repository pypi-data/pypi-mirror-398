from robot.hummingbird import Hummingbird
from time import sleep

hummingbird = Hummingbird('A')

for i in range(0, 10):
    hummingbird.led(1, 100)
    sleep(0.1)

    hummingbird.led(1, 0)
    sleep(0.1)

hummingbird.stop_all()
