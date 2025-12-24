from progressvertical import vertical
import time

name_list = ["Mel", "Bianca", "Melissa", "Piqueno", "Netuno", "Merenga"]

print("starting")

progress_vertical = vertical(name_list, label="Names")

index = 0
while index < len(name_list):
    next(progress_vertical)  
    time.sleep(0.5)
    index += 1

print("finished")
