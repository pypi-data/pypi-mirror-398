# viztools
Interactive tools to visualize data in python using pygame.

![screenshot](https://github.com/Bluemi/viztools/blob/main/screenshots/screenshot1.png)
*The Image in the screenshot: [Mainichi Shimbun, Public domain, via Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Soba-Noodles-Deliveryman-Tokyo-1935.png)*

## Installation
```shell
pip install viztools
```

See on [pypi](https://pypi.org/project/viztools/).

## Usage
See [examples](https://github.com/Bluemi/viztools/tree/main/examples).

### Minimal example
```python
import pygame as pg
import numpy as np

from viztools.drawable import Points
from viztools.ui.elements import Button
from viztools.viewer import Viewer


class SimpleViewer(Viewer):
    def __init__(self):
        super().__init__()

        self.points = Points(np.random.normal(size=(1000, 2)), size=0.05)
        self.button = Button(pg.Rect(50, 50, 120, 40), "Click me")

    def update(self):
        if self.button.is_clicked:
            print('clicked')


viewer = SimpleViewer()
viewer.run()
```

## Features
- Rendering of different drawable objects (Lines, Points, Images, Texts)
  - Renders 100_000 points fluently, and can also handle 1_000_000 points and above (with some lag) (Rendering Lines is slow)
- UI elements (Buttons, Labels, EditField, TextField)
  - EditField and TextField support many keyboard shortcuts, selection, copy/paste, ...
- Fast scrolling and zooming