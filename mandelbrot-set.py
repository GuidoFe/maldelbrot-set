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
import multiprocessing as mp

TWOPLACES = Decimal(10) ** -2

COMPLETED_ROWS = 0
MAX_VALUE = 0
MIN_VALUE = math.inf
VAL_MATRIX = []
ROWS = 0
STARTING_TIME=0

# TODO: Set if should save the picture in a screenshot folder
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

def iteration(z, c):
    return numpy.array([z[0] ** 2 - z[1] ** 2 + c[0],
                        2 * z[0] * z[1] + c[1],
                        Decimal(1)])

def hsl2arcade(h, s, l):
    color=colorsys.hsv_to_rgb(h, s, l)
    return (round(color[0]*255), round(color[1]*255), round(color[2]*255))

def loop(row, windowWidth, windowHeight, renderingScale, M, antiAliasing, maxCount):
    maxVal = 0
    minVal = math.inf
    array = [0]*(windowWidth*renderingScale)
    for col in range(windowWidth*renderingScale):
        quarter = abs(numpy.dot(M, numpy.array([Decimal(1/renderingScale * 0.25), Decimal(0), Decimal(1)]))[0])
        screenPoint = numpy.array([Decimal(col/renderingScale-windowWidth/2), Decimal(windowHeight/2-row/renderingScale), Decimal(1)])
        graphPoint = numpy.dot(M, screenPoint)
        r=graphPoint[0]
        i=graphPoint[1]
        if antiAliasing:
            list = [(r-quarter, i+quarter), (r+quarter, i+quarter), (r+quarter, i-quarter), (r-quarter, i-quarter)]
        else:
            list = [(r, i),]
        val = 0
        for c in list:
            z = iteration(numpy.array([Decimal(0),
                                       Decimal(0),
                                       Decimal(1)]), c)
            count = 1
            while count < maxCount and math.isfinite(z[0]) and math.isfinite(z[1]):
                z = iteration(z, c)
                count += 1
            if math.isinf(z[0]) or math.isinf(z[1]):
                val += count
        if antiAliasing:
            val = val/4
        array[col]=val
        if val > 0:
            if val > maxVal:
                maxVal = val
            if val < minVal:
                minVal = val
    return (row, minVal, maxVal, array)

def callback_result(result):
    global MAX_VALUE
    global MIN_VALUE
    global VAL_MATRIX
    global COMPLETED_ROWS
    if MAX_VALUE < result[2]:
        MAX_VALUE = result[2]
    if MIN_VALUE > result[1]:
        MIN_VALUE = result[1]
    VAL_MATRIX[result[0]] = result[3]
    COMPLETED_ROWS += 1
    done = COMPLETED_ROWS*100/(ROWS)
    barLen = round(done/10)
    now = time()
    # TODO: Draw progress bar on screen
    if done != 0:
        remaining = round((now-STARTING_TIME)/done*(100-done))
        seconds = remaining % 60
        minutes = math.floor(remaining / 60) % 60
        hours = round((remaining - seconds - minutes * 60)/120)
        remainingString =  " Time remaining {:02d}:{:02d}:{:02d}       ".format(hours, minutes, seconds)
    else:
        remainingString = "                                      "
    print("\r"+"█"*barLen+"░"*(10-barLen)+" {0:.2f}%{1}".format(done, remainingString), end="")

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
    def __init__(self, windowWidth, windowHeight, renderingScale = 1, origin = numpy.array([Decimal(0), Decimal(0), Decimal(1)]), graphHeight = Decimal(2),
    maxCount = 100, rectScaleFactor = 0.01, rectRotFactor = 1, antiAliasing = False, hideGui = False):
        self.windowWidth = windowWidth
        self.windowHeight = windowHeight
        self.rect = Rect(self.windowWidth/2, self.windowHeight/2, self.windowWidth/4, self.windowHeight/4, 0, False)
        super().__init__(self.windowWidth, self.windowHeight, "Mandelbrot set")
        self.firstInit = False
        self.renderingScale = renderingScale
        self.origin = origin
        self.graphHeight = graphHeight
        self.graphWidth = Decimal(self.windowWidth/self.windowHeight) * self.graphHeight
        self.maxCount = maxCount
        self.rectScaleFactor = rectScaleFactor
        self.rectRotFactor = rectRotFactor
        self.antiAliasing = antiAliasing
        self.hideGui = hideGui
        self.isNew = True
        self.newRenderingScale = self.renderingScale
        self.M = scaleMatrix(self.graphWidth/Decimal(self.windowWidth))
        self.shiftPressed = False

    def on_draw(self):
        if not self.firstInit:
            self.firstInit=True
            self.render()
        else:
            arcade.start_render()
            if self.isReady:
                if self.isNew:
                    arcade.cleanup_texture_cache()
                self.isNew = False
                arcade.draw_scaled_texture_rectangle(round(self.windowWidth/2), round(self.windowHeight/2), arcade.load_texture("graph.png"), 1/self.renderingScale)
                h = str(int(self.windowHeight * self.newRenderingScale))
                w = str(int(self.windowWidth * self.newRenderingScale))
                if not self.hideGui:
                    arcade.draw_text("H: show/hide UI\nMouse sx: position rectangle\nMouse dx: start rendering\nMouse scroll: change rectangle zoom\nShift + Mouse scroll: rotate rectangle\nMouse wheel click: show/hide rectangle\n+/-: Increase/decrease rendering quality\nR: Reset rectangle rotation\nS: Snap rectangle rotation\nA: Antialiasing on/off", 0, self.windowHeight-120, arcade.color.WHITE, 9)
                    arcade.draw_text("NEXT RENDERING AT {}x{}, ANTI ALIASING = {}".format(w, h, self.antiAliasing), 0, 0, arcade.color.WHITE, 9)
                if self.rect.visibility:
                    self.rect.draw()


    def on_mouse_press(self, x, y, button, modifier):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.rect.visibility = True
            self.rect.move(x, y)
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self.rect.visibility = not self.rect.visibility

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.shiftPressed:
            if scroll_y < 0:
                self.rect.rotateBy(-self.rectRotFactor)
            else:
                self.rect.rotateBy(self.rectRotFactor)
        else:
            if self.rect.visibility:
                if scroll_y < 0:
                    self.rect.scale(1-self.rectScaleFactor)
                else:
                    self.rect.scale(1+self.rectScaleFactor)
    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.PLUS:
            self.newRenderingScale += 1
        elif symbol == arcade.key.MINUS:
            if self.newRenderingScale != 1:
                self.newRenderingScale -= 1
        elif symbol == arcade.key.A:
            self.antiAliasing = not self.antiAliasing
        elif symbol == arcade.key.H:
            self.hideGui = not self.hideGui
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
            self.shiftPressed = True
        elif symbol == arcade.key.ENTER:
            self.renderingScale = self.newRenderingScale
            if self.rect.visibility:
                cursorPos = numpy.array([   Decimal(self.rect.centerX),
                                            Decimal(self.rect.centerY),
                                            Decimal(1)])
                rectPos = self.arcadePointToCenter(cursorPos)
                returnToCenterMatrix=translationMatrix(-self.origin[0], -self.origin[1])
                self.origin = numpy.dot(self.M, rectPos)
                T = translationMatrix(self.origin[0], self.origin[1])
                angle = Decimal(math.radians(self.rect.rotation))
                R = rotationMatrix(angle)
                S = scaleMatrix(Decimal(self.rect.width / self.windowWidth))
                self.M = numpy.dot(numpy.dot(numpy.dot(numpy.dot(T,R),S),returnToCenterMatrix),self.M)
                self.graphWidth = self.graphWidth * Decimal(self.rect.width / self.windowWidth)
                self.graphHeight = self.graphHeight * Decimal(self.rect.height / self.windowHeight)
            self.render()

    def on_key_release(self, symbol, modifiers):
        self.shiftPressed = False

    def render(self):
        global VAL_MATRIX
        global MAX_VALUE
        global COMPLETED_ROWS
        global ROWS
        global STARTING_TIME
        COMPLETED_ROWS = 0
        MAX_VALUE = 0
        self.isReady = False
        arcade.start_render()
        arcade.draw_xywh_rectangle_filled(0, 0, self.windowWidth, self.windowHeight, arcade.color.BLACK)
        arcade.draw_text("LOADING...", 0, 0, arcade.color.WHITE)
        arcade.finish_render()
        VAL_MATRIX = [[0 for col in range(self.windowWidth*self.renderingScale)] for row in range(self.windowHeight*self.renderingScale)]
        pixels = [[0 for col in range(self.windowWidth*self.renderingScale*3)] for row in range(self.windowHeight*self.renderingScale)]
        pool = mp.Pool(mp.cpu_count())
        processes = []
        STARTING_TIME = time()
        ROWS = self.windowHeight * self.renderingScale
        for row in range(self.windowHeight*self.renderingScale):
            process = pool.apply_async(loop, args=(row, self.windowWidth, self.windowHeight, self.renderingScale, self.M, self.antiAliasing, self.maxCount), callback=callback_result)
            processes.append(process)
        pool.close()
        pool.join()
        for row in range(0, self.windowHeight*self.renderingScale):
            for col in range(0, self.windowWidth*self.renderingScale):
                if VAL_MATRIX[row][col] != 0:
                    av = hsl2arcade(0.038+(VAL_MATRIX[row][col]-MIN_VALUE)/(MAX_VALUE-MIN_VALUE)*0.4, 1, 0.5)
                    pixels[row][col*3]=av[0]
                    pixels[row][col*3+1]=av[1]
                    pixels[row][col*3+2]=av[2]
        f = open('graph.png', 'wb')
        w = png.Writer(self.windowWidth*self.renderingScale, self.windowHeight*self.renderingScale, greyscale=False)
        w.write(f, pixels)
        f.close()
        self.isNew = True
        self.isReady = True
        s.call(['notify-send','Mandelbrot set','Rendering has been completed.'])

    def arcadePointToCenter(self, p):
        return numpy.array([Decimal(- self.windowWidth / 2) + p[0],
                            Decimal(- self.windowHeight / 2) + p[1],
                            Decimal(1)])



def main():
    app = Visualizer(683, 384)
    arcade.start_render()
    arcade.set_background_color(arcade.color.BLACK)
    arcade.draw_text("RENDERING...", 1, 1, arcade.color.WHITE, 12)
    arcade.finish_render()
    arcade.run()

main()
