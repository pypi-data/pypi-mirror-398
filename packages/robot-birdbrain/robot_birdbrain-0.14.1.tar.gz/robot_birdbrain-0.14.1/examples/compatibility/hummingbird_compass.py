from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

# Exercise 1
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getCompass() > 75 and bird.getCompass() < 105:  # If both Booleans are true
        bird.print('E')  # Print E
    else:
        bird.print('')  # Print nothing

sleep(1)

# Exercise 1 - Modified
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getCompass() > 75 and bird.getCompass() < 105:  # Direction between 75 and 105
        bird.print('E')
    elif bird.getCompass() > 165 and bird.getCompass() < 195:  # Direction between 165 and 195
        bird.print('S')
    else:
        bird.print('')  # Clear screen


# Exercise 2
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getCompass() > 75 and bird.getCompass() < 105:  # Direction between 75 and 105
        bird.print('E')
    elif bird.getCompass() > 165 and bird.getCompass() < 195:  # Direction between 165 and 195
        bird.print('S')
    elif bird.getCompass() > 255 and bird.getCompass() < 285:  # Direction between 255 and 285
        bird.print('W')
    else:
        bird.print('')  # Clear screen

# Exercise 3
while not (bird.getButton('A')):
    print(bird.getCompass())
    # While button A isn't pressed
    if bird.getCompass() > 75 and bird.getCompass() < 105:  # Direction between 75 and 105
        bird.print('E')
    elif bird.getCompass() > 165 and bird.getCompass() < 195:  # Direction between 165 and 195
        bird.print('S')
    elif bird.getCompass() > 255 and bird.getCompass() < 285:  # Direction between 255 and 285
        bird.print('W')
    elif bird.getCompass() > 345 or bird.getCompass() < 15:  # Direction between 255 and 285
        bird.print('N')
    else:
        bird.print('')  # Clear screen

# Exercise 4
while not (bird.getButton('A')):  # While button A isn't pressed
    if bird.getCompass() > 75 and bird.getCompass() < 105:  # Direction between 75 and 105
        bird.print('E')
        bird.setTriLED(1, 100, 0, 0)
        bird.setRotationServo(1, 100)
    elif bird.getCompass() > 165 and bird.getCompass() < 195:  # Direction between 165 and 195
        bird.print('S')
        bird.setTriLED(1, 0, 100, 0)
        bird.setRotationServo(1, -100)
    elif bird.getCompass() > 255 and bird.getCompass() < 285:  # Direction between 255 and 285
        bird.print('W')
        bird.setTriLED(1, 0, 0, 100)
        bird.setRotationServo(1, 50)
    elif bird.getCompass() > 345 or bird.getCompass() < 15:  # Direction between 255 and 285
        bird.print('N')
        bird.setTriLED(1, 100, 0, 100)
        bird.setRotationServo(1, -50)
    else:
        bird.print('')  # Clear screen
        bird.setTriLED(1, 0, 0, 0)
        bird.setRotationServo(1, 0)


# Going Further - if you tape the Hummingbird Bit on top of the rotation servo, this code
# rotates the Bit until the compass is pointing south
while not (bird.getButton('A')):
    if bird.getCompass() > 190:
        bird.setRotationServo(1, 20)
    elif bird.getCompass() < 170:
        bird.setRotationServo(1, -30)
    else:
        bird.setRotationServo(1, 0)

bird.stopAll()
