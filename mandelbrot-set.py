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
APP = None
COMPLETED_ROWS = 0
ROWS = 0
MAX_VALUE = 0
MIN_VALUE = math.inf
VAL_MATRIX = []
STARTING_TIME=0

# TODO: Set if should save the picture in a screenshot folder
# TODO: Parse arguments
# TODO: GUI
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
            while count < maxCount and (z[0]**2+z[1]**2)<=4:
                z = iteration(z, c)
                count += 1
            if (z[0]**2+z[1]**2)>4:
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
    if COMPLETED_ROWS == ROWS:
        APP.renderResults()



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
        self.newRenderingScale = self.renderingScale
        self.M = scaleMatrix(self.graphWidth/Decimal(self.windowWidth))
        self.shiftPressed = False
        self.isLoading = True
        self.newImage = False

    def on_draw(self):
        if not self.firstInit:
            self.firstInit=True
            self.startRendering()
        elif self.isLoading:
            arcade.start_render()
            outerBarWidth = round(self.windowWidth/2)
            totalRows = self.windowHeight * self.renderingScale
            padding = 5
            outerBarHeight = outerBarWidth * 1/9
            innerBarWidth = round((outerBarWidth-padding*2)*COMPLETED_ROWS/totalRows)
            innerBarHeight = outerBarHeight - padding*2
            innerBarX = round(self.windowWidth/2-outerBarWidth/2 + padding)
            innerBarY = round(self.windowHeight/2-outerBarHeight/2+padding)
            arcade.draw_rectangle_outline(self.windowWidth//2, self.windowHeight//2, outerBarWidth, outerBarHeight, arcade.color.WHITE, 2)
            arcade.draw_xywh_rectangle_filled(innerBarX, innerBarY, innerBarWidth, innerBarHeight, arcade.color.WHITE)
            done = COMPLETED_ROWS*100/(ROWS)
            barLen = round(done/10)
            now = time()
            arcade.draw_text("Shift+Esc for cancel loading process", 0, 0, arcade.color.WHITE)
            if done != 0:
                remaining = round((now-STARTING_TIME)/done*(100-done))
                seconds = remaining % 60
                minutes = math.floor(remaining / 60) % 60
                hours = round((remaining - seconds - minutes * 60)/120)
                timeStr = str(seconds)+"s remaining"
                if minutes != 0 or hours != 0:
                    timeStr = str(minutes) + "m "+timeStr
                if hours != 0:
                    timeStr = str(hours)+"h "+timeStr
                arcade.draw_text(timeStr, self.windowWidth//2, self.windowHeight//2-outerBarHeight//2-5, arcade.color.WHITE, 12, anchor_x="center", anchor_y="top")
            arcade.draw_text("LOADING...", self.windowWidth//2, self.windowHeight//2+outerBarHeight//2+5, arcade.color.WHITE, 12, anchor_x="center")
        else:
            arcade.start_render()
            if self.newImage:
                self.newImage = False
                arcade.cleanup_texture_cache()
            arcade.draw_scaled_texture_rectangle(round(self.windowWidth/2), round(self.windowHeight/2), arcade.load_texture("graph.png"), 1/self.renderingScale)
            h = str(int(self.windowHeight * self.newRenderingScale))
            w = str(int(self.windowWidth * self.newRenderingScale))
            if not self.hideGui:
                helpText =   """G: show/hide UI
Mouse sx: position rectangle
Enter when selection visible: render selected area
Enter when selection hidden: rerender current area
Mouse scroll: change rectangle zoom
Shift + Mouse scroll: rotate rectangle
H: show/hide rectangle
+/-: Increase/decrease rendering quality
R: Reset rectangle rotation
S: Snap rectangle rotation
A: Antialiasing on/off
"""
                rotatedUnit = numpy.dot(translationMatrix(-self.origin[0], -self.origin[1]), numpy.dot(self.M, numpy.array([1, 0, 1])))[:2]
                module = numpy.sqrt(numpy.dot(rotatedUnit, rotatedUnit))
                rotatedUnit = rotatedUnit/module
                scale = 1/module
                currentAngle = math.degrees(math.atan2(rotatedUnit[1], rotatedUnit[0]))
                arcade.draw_text(helpText, 0, self.windowHeight, arcade.color.WHITE, 9, anchor_x="left", anchor_y="top")
                arcade.draw_text("Center position: {0:.2e} + ({1:.2e})i, scale: {2}:1, rotated by {3:.2g}°\nNEXT RENDERING AT {4}x{5}, ANTI ALIASING = {6}".format(self.origin[0],
                     self.origin[1], scale.to_integral_value(), currentAngle, w, h, self.antiAliasing), 0, 0, arcade.color.WHITE, 9)
            if self.rect.visibility:
                self.rect.draw()


    def on_mouse_press(self, x, y, button, modifier):
        if not self.isLoading:
            if button == arcade.MOUSE_BUTTON_LEFT:
                self.rect.visibility = True
                self.rect.move(x, y)


    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self.isLoading:
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
        if symbol == arcade.key.LSHIFT:
            self.shiftPressed = True
        if not self.isLoading:
            if symbol == arcade.key.PLUS:
                self.newRenderingScale += 1
            elif symbol == arcade.key.MINUS:
                if self.newRenderingScale != 1:
                    self.newRenderingScale -= 1
            elif symbol == arcade.key.A:
                self.antiAliasing = not self.antiAliasing
            elif symbol == arcade.key.G:
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
            elif symbol == arcade.key.H:
                self.rect.visibility = not self.rect.visibility
            elif symbol == arcade.key.ENTER:
                self.renderingScale = self.newRenderingScale
                if self.rect.visibility:
                    cursorPos = numpy.array([   Decimal(self.rect.centerX),
                                                Decimal(self.rect.centerY),
                                                Decimal(1)])
                    rectPos = self.arcadePointToCenter(cursorPos)
                    returnToCenterMatrix=translationMatrix(-self.origin[0], -self.origin[1])
                    self.oldOrigin = numpy.copy(self.origin)
                    self.oldM = numpy.copy(self.M)
                    self.oldGraphWidth = self.graphWidth
                    self.oldGraphHeight = self.graphHeight
                    self.origin = numpy.dot(self.M, rectPos)
                    T = translationMatrix(self.origin[0], self.origin[1])
                    angle = Decimal(math.radians(self.rect.rotation))
                    R = rotationMatrix(angle)
                    S = scaleMatrix(Decimal(self.rect.width / self.windowWidth))
                    self.M = numpy.dot(numpy.dot(numpy.dot(numpy.dot(T,R),S),returnToCenterMatrix),self.M)
                    self.graphWidth = self.graphWidth * Decimal(self.rect.width / self.windowWidth)
                    self.graphHeight = self.graphHeight * Decimal(self.rect.height / self.windowHeight)
                self.startRendering()
        elif symbol == arcade.key.ESCAPE and self.shiftPressed:
            self.pool.terminate()
            self.origin = numpy.copy(self.oldOrigin)
            self.M = numpy.copy(self.oldM)
            self.graphWidth = self.oldGraphWidth
            self.graphHeight = self.oldGraphHeight
            self.isLoading = False
            # TODO: manage canceling first loading


    def on_key_release(self, symbol, modifiers):
        if symbol==arcade.key.LSHIFT:
            self.shiftPressed = False

    def startRendering(self):
        global VAL_MATRIX
        global MAX_VALUE
        global COMPLETED_ROWS
        global ROWS
        global STARTING_TIME
        COMPLETED_ROWS = 0
        MAX_VALUE = 0
        VAL_MATRIX = [[0 for col in range(self.windowWidth*self.renderingScale)] for row in range(self.windowHeight*self.renderingScale)]
        self.pool = mp.Pool(mp.cpu_count())
        processes = []
        STARTING_TIME = time()
        self.isLoading = True
        ROWS = self.windowHeight * self.renderingScale
        for row in range(self.windowHeight*self.renderingScale):
            process = self.pool.apply_async(loop, args=(row, self.windowWidth, self.windowHeight, self.renderingScale, self.M, self.antiAliasing, self.maxCount), callback=callback_result)
            processes.append(process)
        self.pool.close()

    def renderResults(self):
        pixels = [[0 for col in range(self.windowWidth*self.renderingScale*3)] for row in range(self.windowHeight*self.renderingScale)]
        for row in range(0, self.windowHeight*self.renderingScale):
            for col in range(0, self.windowWidth*self.renderingScale):
                if VAL_MATRIX[row][col] != 0:
                    av = hsl2arcade((VAL_MATRIX[row][col]-MIN_VALUE)/(MAX_VALUE-MIN_VALUE), 1, 0.5)
                    pixels[row][col*3]=av[0]
                    pixels[row][col*3+1]=av[1]
                    pixels[row][col*3+2]=av[2]
        f = open('graph.png', 'wb')
        w = png.Writer(self.windowWidth*self.renderingScale, self.windowHeight*self.renderingScale, greyscale=False)
        w.write(f, pixels)
        f.close()
        self.isLoading = False
        self.newImage = True
        self.rect.visibility = False
        s.call(['notify-send','Mandelbrot set','Rendering has been completed.'])


    def arcadePointToCenter(self, p):
        return numpy.array([Decimal(- self.windowWidth / 2) + p[0],
                            Decimal(- self.windowHeight / 2) + p[1],
                            Decimal(1)])



def main():
    global APP
    APP = Visualizer(683, 384)
    arcade.start_render()
    arcade.set_background_color(arcade.color.BLACK)
    arcade.draw_text("RENDERING...", 1, 1, arcade.color.WHITE, 12)
    arcade.finish_render()
    arcade.run()

main()
