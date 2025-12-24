from progressvertical import vertical
import time

name_list = ["Mel", "Bianca", "Melissa", "Piqueno", "Netuno", "Merenga"]
numbers_list = [10, 20, 30, 40, 50]
color_list = ["vermelho", "verde", "azul", "amarelo"]

print("starting")


for items in vertical(
    name_list, numbers_list, color_list,
    labels=["Names", "Numbers", "Colors"],
    colors=["cyan", "green", "magenta"],
    height=5,
    spacing=5
):
    time.sleep(0.5)

print("finished")
