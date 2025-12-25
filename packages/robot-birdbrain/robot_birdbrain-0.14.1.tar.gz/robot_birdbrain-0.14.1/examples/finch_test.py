from robot.finch import Finch
from time import sleep

finch = Finch('A')

for i in range(0, 10):
    finch.beak(100, 100, 100)
    sleep(0.1)

    finch.beak(0, 0, 0)
    sleep(0.1)

finch.stop_all()
