print("importing libs")
import turtle as t
import tkinter as tk
import time as clk
print("now importing mini libs")
from tkinter import messagebox
print("libs imported")
print("")
print("")
print("welcome to turtle helper lib.")
print("you can find the documentation at tinyurl.com/turtlehldoc")
print("")
print("")
print("")

def wait(amount):
    clk.sleep(amount)
    return None

def newline(amount=8):
    true_amount = int(amount / 2)
    for _ in range(true_amount):
        print("       }")
        print("       {")
    return None

def infobox(title="title", message="message"):
    messagebox.showinfo(title, message)
    return None

def warnbox(title="title", message="message"):
    messagebox.showwarning(title, message)
    return None

def errorbox(title="title", message="message"):
    messagebox.showerror(title, message)
    return None

def yn(title="title", message="message"):
    result = messagebox.askyesno(title, message)
    return result

def okcan(title="title", message="message"):
    result = messagebox.askokcancel(title, message)
    return result

def recan(title="title", message="message"):
    result = messagebox.askretrycancel(title, message)
    return result

def yncan(title="title", message="message"):
    result = messagebox.askyesnocancel(title, message)
    return result


def setup(name="turtlehl"):
    global sc
    global tur
    sc = t.Screen()
    sc.title(name)
    tur = t.Turtle()
    return None

def square(size=5):
    for _ in range(4):
        tur.forward(size)
        tur.left(90)
    return None

def triangle(size=5):
    for _ in range(3):
        tur.forward(size)
        tur.left(120)
    return None

def circle(radius=5):
    for _ in range(360):
        tur.forward(radius)
        tur.left(1)
    return None

def rectangle(width=10, height=5):
    for _ in range(2):
        tur.forward(width)
        tur.left(90)
        tur.forward(height)
        tur.left(90)
    return None

def ellipse(width=10, height=5):
    for _ in range(360):
        tur.forward(width)
        tur.left(1)
    return None

def polygon(sides=5, size=5):
    for _ in range(sides):
        tur.forward(size)
        tur.left(360/sides)
    return None

def star(sides=5, size=5):
    for _ in range(sides):
        tur.forward(size)
        tur.left(180-180/sides)
    return None

def test():
    square()
    square(45)
    square(100)
    square(10)
    square(15)
    square(20)
    square(25)
    square(30)
    square(35)
    square(40)
    square(50)
    square(55)
    square(60)
    square(65)
    square(70)
    square(75)
    square(80)
    square(85)
    square(90)
    square(95)
    return None

def make_trippin():
    for _ in range(4):
        test()
        tur.left(90)
    return None

def ultimate_trippin():
    make_trippin()
    tur.forward(100)
    make_trippin()
    tur.right(180)
    tur.forward(200)
    make_trippin()
    tur.right(180)
    tur.forward(100)
    tur.right(90)
    return None
