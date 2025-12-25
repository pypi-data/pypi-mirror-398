from robot.hummingbird import Hummingbird
from time import sleep

bird = Hummingbird('A')  # Declare Hummingbird object

# Exercise 1
bird.playNote(60, 1)  # C
sleep(1)
bird.playNote(62, 0.5)  # D
sleep(0.5)
bird.playNote(64, 2)  # E
sleep(2)

# Exercise 2
# Example 1
bird.playNote(72, 1)
sleep(1)
bird.setLED(1, 100)
sleep(1)
bird.setLED(1, 0)
sleep(1)

# Example 2
bird.playNote(72, 1)
bird.setLED(1, 100)
sleep(1)
bird.setLED(1, 0)
sleep(1)

# Exercise 3
for i in [60, 65, 69, 72, 60]:  # For each note in the list
    bird.playNote(i, 0.5)  # Play the note
    sleep(0.5)

# Exercise 4 - Answers will vary

# Extra Challenge
beats = [1, 0.5, 1, 2, 0.5]
notes = [60, 65, 69, 72, 60]
for i in range(5):  # For each of the five entries in the lists
    bird.playNote(notes[i], beats[i])  # Play the note with right number of beats
    sleep(beats[i])

bird.stopAll()
