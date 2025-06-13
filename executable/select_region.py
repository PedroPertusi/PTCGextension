# select_region.py

import tkinter as tk

selected_region = {}

def select_screen_region():
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.configure(background='black')
    root.attributes("-topmost", True)
    canvas = tk.Canvas(root, cursor="cross", bg="black")
    canvas.pack(fill=tk.BOTH, expand=True)

    region = {}

    def on_mouse_down(event):
        region['x1'] = event.x
        region['y1'] = event.y
        region['rect'] = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

    def on_mouse_drag(event):
        canvas.coords(region['rect'], region['x1'], region['y1'], event.x, event.y)

    def on_mouse_up(event):
        region['x2'] = event.x
        region['y2'] = event.y
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    root.mainloop()

    x1, y1 = min(region['x1'], region['x2']), min(region['y1'], region['y2'])
    x2, y2 = max(region['x1'], region['x2']), max(region['y1'], region['y2'])

    return {
        "top": y1,
        "left": x1,
        "width": x2 - x1,
        "height": y2 - y1
    }
