#!/usr/bin/python3
import sys
import math
import arcade
import colorsys
import png
import numpy
from decimal import *
from time import time
import subprocess as s

WINDOW_WIDTH = 683
WINDOW_HEIGHT = 384

# The image will be rendered in WINDOW_WIDTH*RENDERING_SCALE x WINDOW_HEIGHT*RENDERING_SCALE,
RENDERING_SCALE = 1
ORIGIN = numpy.array([Decimal(0), Decimal(0), Decimal(1)])

GRAPH_HEIGHT = Decimal(2)
GRAPH_WIDTH = Decimal(WINDOW_WIDTH/WINDOW_HEIGHT) * GRAPH_HEIGHT
MAX_COUNT = 100
RECT_SCALE_FACTOR=0.1
RECT_ROT_FACTOR=1
ANTI_ALIASING = False
HIDE_GUI = False


SHIFT_PRESSED = False
NEW_RENDERING_SCALE = 1
isReady = False
isNew = False
TWOPLACES = Decimal(10) ** -2


def scaleMatrix(s):
    return [
        [s, Decimal(0),  Decimal(0)],
        [Decimal(0), s,  Decimal(0)],
        [Decimal(0), Decimal(0),  Decimal(1)]
    ]
def translationMatrix(x, y):
    return [
        [Decimal(1),    Decimal(0), x           ],
        [Decimal(0),    Decimal(1), y           ],
        [Decimal(0),    Decimal(0), Decimal(1)  ]
    ]

def rotationMatrix(angle):
    return [
        [Decimal(math.cos(angle)),  Decimal(-math.sin(angle)),  Decimal(0)  ],
        [Decimal(math.sin(angle)),  Decimal(math.cos(angle)),   Decimal(0)  ],
        [Decimal(0),                Decimal(0),                 Decimal(1)  ]
    ]


def applyTransformations(v, list):
    for m in list:
        v = numpy.dot(m,v)
    return v

def iteration(z, c):
    return numpy.array([z[0] ** 2 - z[1] ** 2 + c[0],
                        2 * z[0] * z[1] + c[1],
                        Decimal(1)])

def hsl2arcade(h, s, l):
    color=colorsys.hsv_to_rgb(h, s, l)
    return (round(color[0]*255), round(color[1]*255), round(color[2]*255))


def resetTransformationParameters():
    global ANGLE
    global TRANSLATION
    ANGLE = 0
    TRANSLATION = (Decimal(0), Decimal(0))


# For elements in the arcade coordinates
def arcadePointToCenter(p):
    return numpy.array([Decimal(- WINDOW_WIDTH / 2) + p[0],
                        Decimal(- WINDOW_HEIGHT / 2) + p[1],
                        Decimal(1)])


M = scaleMatrix(GRAPH_WIDTH/Decimal(WINDOW_WIDTH))


def loop():
    global isNew
    global isReady
    global RENDERING_SCALE
    global ROTATED
    global ORIGIN
    isReady = False
    RENDERING_SCALE = NEW_RENDERING_SCALE
    m = [[0 for col in range(WINDOW_WIDTH*RENDERING_SCALE*3)] for row in range(WINDOW_HEIGHT*RENDERING_SCALE)]
    valMatrix = [[0 for col in range(WINDOW_WIDTH*RENDERING_SCALE)] for row in range(WINDOW_HEIGHT*RENDERING_SCALE)]
    startTime = time()
    maxVal = 0
    for row in range(0, WINDOW_HEIGHT*RENDERING_SCALE):
        for col in range(0, WINDOW_WIDTH*RENDERING_SCALE):
            #print("Calculating ("+str(col)+", "+str(row)+")")
            screenPoint = numpy.array([Decimal(col/RENDERING_SCALE-WINDOW_WIDTH/2), Decimal(WINDOW_HEIGHT/2-row/RENDERING_SCALE), Decimal(1)])
            graphPoint = numpy.dot(M, screenPoint)
            ANTI_ALIASING = False
            if ANTI_ALIASING:
                list = [(r, i),(r-quarter, i+quarter), (r+quarter, i+quarter), (r+quarter, i-quarter), (r-quarter, i-quarter)]
            else:
                list = [(graphPoint[0],graphPoint[1])]
            val = 0
            for c in list:
                z = iteration(numpy.array([Decimal(0),
                                           Decimal(0),
                                           Decimal(1)]), c)
                count = 1
                while count < MAX_COUNT and math.isfinite(z[0]) and math.isfinite(z[1]):
                    z = iteration(z, c)
                    count += 1
                if math.isinf(z[0]) or math.isinf(z[1]):
                    val += count

            if ANTI_ALIASING:
                val = val/5
            valMatrix[row][col]=val
            if val > maxVal:
                maxVal = val
        done = row*100/(WINDOW_HEIGHT*RENDERING_SCALE)
        barLen = round(done/10)
        now = time()
        if done != 0:
            remaining = round((now-startTime)/done*(100-done))
            seconds = remaining % 60
            minutes = math.floor(remaining / 60) % 60
            hours = round((remaining - seconds - minutes * 60)/120)
            remainingString =  " Time remaining {:02d}:{:02d}:{:02d}       ".format(hours, minutes, seconds)
        else:
            remainingString = "                                      "
        print("\r"+"█"*barLen+"░"*(10-barLen)+" {0:.2f}%{1}".format(done, remainingString), end="")
    for row in range(0, WINDOW_HEIGHT*RENDERING_SCALE):
        for col in range(0, WINDOW_WIDTH*RENDERING_SCALE):
            if valMatrix[row][col] != 0:
                av = hsl2arcade(valMatrix[row][col]/maxVal*0.4, 1, 0.5)
                m[row][col*3]=av[0]
                m[row][col*3+1]=av[1]
                m[row][col*3+2]=av[2]
    print("\r"+"██████████ 100.00% Done                                         ")
    f = open('graph.png', 'wb')
    w = png.Writer(WINDOW_WIDTH*RENDERING_SCALE, WINDOW_HEIGHT*RENDERING_SCALE, greyscale=False)
    w.write(f, m)
    f.close()
    isNew = True
    isReady = True
    s.call(['notify-send','Mandelbrot set','Rendering has been completed.'])

class Rect:
    def __init__(self, centerX, centerY, width, height, rotation, visibility):
        self.centerX = centerX
        self.centerY = centerY
        self.width = width
        self.height = height
        self.visibility = visibility
        self.rotation = rotation

    def scale(self, factor):
        self.width = self.width * factor
        self.height = self.height * factor

    def move(self, x, y):
        self.centerX = x
        self.centerY = y

    def normalizeAngle(self):
        if self.rotation > 360 or self.rotation < 0:
            self.rotation = self.rotation % 360
    def rotateTo(self, angle):
        self.rotation = angle
        self.normalizeAngle()

    def rotateBy(self, angle):
        self.rotation += angle
        self.normalizeAngle()

    def draw(self):
        arcade.draw_rectangle_outline(self.centerX, self.centerY, self.width, self.height, arcade.color.WHITE, tilt_angle = self.rotation)

class Visualizer(arcade.Window):
    def __init__(self):
        self.rect = Rect(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, WINDOW_WIDTH/4, WINDOW_HEIGHT/4, 0, False)
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Mandelbrot set")
        self.firstInit = False

    def on_draw(self):
        global isNew
        global TRANSLATION
        if not self.firstInit:
            self.firstInit=True
            loop()
        else:
            arcade.start_render()
            if isReady:
                if isNew:
                    arcade.cleanup_texture_cache()
                isNew = False
                arcade.draw_scaled_texture_rectangle(round(WINDOW_WIDTH/2), round(WINDOW_HEIGHT/2), arcade.load_texture("graph.png"), 1/RENDERING_SCALE)
                h = str(int(WINDOW_HEIGHT * NEW_RENDERING_SCALE))
                w = str(int(WINDOW_WIDTH * NEW_RENDERING_SCALE))
                resetTransformationParameters()
                if not HIDE_GUI:
                    arcade.draw_text("H: show/hide UI\nMouse sx: position rectangle\nMouse dx: start rendering\nMouse scroll: change rectangle zoom\nShift + Mouse scroll: rotate rectangle\nMouse wheel click: show/hide rectangle\n+/-: Increase/decrease rendering quality\nR: Reset rectangle rotation\nS: Snap rectangle rotation\nA: Antialiasing on/off", 0, WINDOW_HEIGHT-120, arcade.color.WHITE, 9)
                    arcade.draw_text("NEXT RENDERING AT {}x{}, ANTI ALIASING = {}".format(w, h, ANTI_ALIASING), 0, 0, arcade.color.WHITE, 9)
                if self.rect.visibility:
                    self.rect.draw()


    def on_mouse_press(self, x, y, button, modifier):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.rect.visibility = True
            self.rect.move(x, y)
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self.rect.visibility = not self.rect.visibility

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if SHIFT_PRESSED:
            if scroll_y < 0:
                self.rect.rotateBy(-RECT_ROT_FACTOR)
            else:
                self.rect.rotateBy(RECT_ROT_FACTOR)
        else:
            if self.rect.visibility:
                if scroll_y < 0:
                    self.rect.scale(1-RECT_SCALE_FACTOR)
                else:
                    self.rect.scale(1+RECT_SCALE_FACTOR)
    def on_key_press(self, symbol, modifiers):
        global NEW_RENDERING_SCALE
        global GRAPH_WIDTH
        global GRAPH_HEIGHT
        global ANTI_ALIASING
        global HIDE_GUI
        if symbol == arcade.key.PLUS:
            NEW_RENDERING_SCALE += 1
        elif symbol == arcade.key.MINUS:
            if NEW_RENDERING_SCALE != 1:
                NEW_RENDERING_SCALE -= 1
        elif symbol == arcade.key.A:
            ANTI_ALIASING = not ANTI_ALIASING
        elif symbol == arcade.key.H:
            HIDE_GUI = not HIDE_GUI
        elif symbol == arcade.key.R:
            self.rect.rotateTo(0)
        elif symbol == arcade.key.S:
            angle = self.rect.rotation
            if angle <= 45 or angle >= 315:
                self.rect.rotateTo(0)
            elif 45 < angle <= 135:
                self.rect.rotateTo(90)
            elif 135 < angle <= 225:
                self.rect.rotateTo(180)
            else:
                self.rect.rotateTo(270)
        elif symbol == arcade.key.LSHIFT:
            global SHIFT_PRESSED
            SHIFT_PRESSED = True
        elif symbol == arcade.key.ENTER:
            if self.rect.visibility:
                global ORIGIN
                global GRAPH_WIDTH
                global GRAPH_HEIGHT
                global M
                cursorPos = numpy.array([   Decimal(self.rect.centerX),
                                            Decimal(self.rect.centerY),
                                            Decimal(1)])
                rectPos = arcadePointToCenter(cursorPos)
                returnToCenterMatrix=translationMatrix(-ORIGIN[0], -ORIGIN[1])
                ORIGIN = numpy.dot(M, rectPos)
                T = translationMatrix(ORIGIN[0], ORIGIN[1])
                angle = Decimal(math.radians(self.rect.rotation))
                R = rotationMatrix(angle)
                S = scaleMatrix(Decimal(self.rect.width / WINDOW_WIDTH))
                M = numpy.dot(numpy.dot(numpy.dot(numpy.dot(T,R),S),returnToCenterMatrix),M)
                GRAPH_WIDTH = GRAPH_WIDTH * Decimal(self.rect.width / WINDOW_WIDTH)
                GRAPH_HEIGHT = GRAPH_HEIGHT * Decimal(self.rect.height / WINDOW_HEIGHT)
            arcade.start_render()
            arcade.draw_xywh_rectangle_filled(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, arcade.color.BLACK)
            arcade.draw_text("LOADING...", 0, 0, arcade.color.WHITE)
            arcade.finish_render()
            loop()
    def on_key_release(self, symbol, modifiers):
        global SHIFT_PRESSED
        SHIFT_PRESSED = False


def main():
    app = Visualizer()
    arcade.start_render()
    arcade.set_background_color(arcade.color.BLACK)
    arcade.draw_text("RENDERING...", 1, 1, arcade.color.WHITE, 12)
    arcade.finish_render()
    arcade.run()

main()
