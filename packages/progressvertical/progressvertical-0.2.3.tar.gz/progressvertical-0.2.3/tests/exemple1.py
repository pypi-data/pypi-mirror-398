from progressvertical import vertical
import time

name_list = ["Mel", "Bianca", "Melissa", "Piqueno", "Netuno", "Merenga"]

print("starting")

for name in vertical(name_list, label="Names"):
    time.sleep(0.5)

print("finished")
