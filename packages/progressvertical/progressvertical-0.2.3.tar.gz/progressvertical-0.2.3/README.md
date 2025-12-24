**ProgressVertical** is a Python library for displaying vertical progress bars for command-line interface (CLI) applications.  
Designed with a focus on usability and customization, allowing the creation of multi-stage progress animations with configurable colors, styles, and durations, inspired by another library [_progressbar_](https://pypi.org/project/progressbar/).



## Installation:

```pip
pip install progressvertical

```

## Example 

```python
from progressvertical import vertical
import time

name_list = ["Mel", "Bianca", "Melissa", "Piqueno", "Netuno", "Merenga"]

print("starting")

for name in vertical(name_list, label="Names"):
    time.sleep(0.5)

print("finished")

```


## Example 2
```python
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

```
## Exemple 3
```python
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

```

[![📊 ProgressVertical](https://img.shields.io/badge/📊%20ProgressVertical-%200.2.3-0073B7?style=for-the-badge)](https://pypi.org/project/progressvertical/)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
