import turtle
import math
import colorsys

def Fill(n):
    code = n
    screen = turtle.Screen()
    screen.bgcolor("black")

    stick1 = turtle.Turtle()
    stick1.hideturtle()
    stick1.color("blue")

    stick2 = turtle.Turtle()
    stick2.hideturtle()
    stick2.color("green")
    stick2.pensize(3)

    pen = turtle.Turtle()
    pen.hideturtle()
    pen.penup()
    pen.pensize(2)

    r1, r2 = 175, 175
    angle = 0
    col = 0
    turtle.tracer(0, 0)

    try:
        while True:
            radians1 = math.radians(angle)
            radians2 = math.radians(angle * code)
            
            col += 1/180
            recol = colorsys.hsv_to_rgb(col % 1, 1, 1)
            pen.color(recol)

            x1 = r1 * math.cos(radians1)
            y1 = r1 * math.sin(radians1)
            x2 = x1 + r2 * math.cos(radians2)
            y2 = y1 + r2 * math.sin(radians2)

            stick1.clear()
            stick2.clear()

            stick1.penup(); stick1.goto(0, 0); stick1.pendown(); stick1.goto(x1, y1)
            stick2.penup(); stick2.goto(x1, y1); stick2.pendown(); stick2.goto(x2, y2)

            pen.goto(x2, y2)
            pen.pendown()
            pen.dot(3)
            
            turtle.update()
            angle += 1
    except turtle.Terminator:
        pass
    turtle.done()