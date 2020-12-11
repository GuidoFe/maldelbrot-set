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
ORIGIN = numpy.array([  [Decimal(0)],
                        [Decimal(0)],
                        [Decimal(1)]])
GRAPH_WIDTH = Decimal(3.557291667)
GRAPH_HEIGHT = Decimal(2)
MAX_COUNT = 25
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
    return numpy.matrix([
        [s, 0,  0],
        [0, s,  0],
        [0, 0,  1]
    ])
def translationMatrix(x, y):
    return numpy.matrix([
        [Decimal(1),    Decimal(0), x           ],
        [Decimal(0),    Decimal(1), y           ],
        [Decimal(0),    Decimal(0), Decimal(1)  ]
    ])

def rotationMatrix(angle):
    return numpy.matrix([
        [Decimal(math.cos(angle)),  Decimal(-math.sin(angle)),  Decimal(0)  ],
        [Decimal(math.sin(angle)),  Decimal(math.cos(angle)),   Decimal(0)  ],
        [Decimal(0),                Decimal(0),                 Decimal(1)  ]
    ])


def applyTransformations(v, list):
    for m in list:
        v = m.dot(v)
    return v


def iteration(z, c):
    return  numpy.array([   [z[0][0]*z[0][0]-z[1][0]*z[1][0]+c[0][0]],
                            [2*z[0][0]*z[1][0]+c[1][0]]
                            [Decimal(1)]])

def hsl2arcade(h, s, l):
    color=colorsys.hsv_to_rgb(h, s, l)
    return (round(color[0]*255), round(color[1]*255), round(color[2]*255))


def resetTransformationParameters():
    global ANGLE
    global TRANSLATION
    ANGLE = 0
    TRANSLATION = (Decimal(0), Decimal(0))


# For elements in the arcade coordinates
def screenPointToCenter(p, w, h):
    return numpy.array([[Decimal(- w / 2 + p[0][0])],
                        [Decimal(- h / 2 + p[1][0])],
                        [Decimal(1)]])

# For elements in the image coordinages
def imagePointToCenter(p, w, h):
    return numpy.array([[Decimal(- w / 2 + p[0][0])],
                        [Decimal(h / 2 - p[1][0])],
                        [Decimal(1)]])
SS = numpy.matrix([
    [Decimal(GRAPH_WIDTH/WINDOW_WIDTH), Decimal(0), Decimal(0)],
    [Decimal(0), Decimal(GRAPH_HEIGHT/WINDOW_HEIGHT), Decimal(0)],
    [Decimal(0), Decimal(0), Decimal(1)]])

ST = numpy.matrix([
    [Decimal(1),    Decimal(0), ORIGIN[0][0]],
    [Decimal(0),    Decimal(1), ORIGIN[1][0]],
    [Decimal(0),    Decimal(0), Decimal(1)]
])

SR = numpy.matrix([
    [Decimal(1),    Decimal(0), Decimal(0)],
    [Decimal(0),    Decimal(1), Decimal(0)],
    [Decimal(0),    Decimal(0), Decimal(1)]
])

M = ST.dot(SR).dot(SS)


def loop():
    global isNew
    global isReady
    global RENDERING_SCALE
    global ROTATED
    global ORIGIN
    isReady = False
    m = []
    startTime = time()
    #transformations = [reference, translationMatrix(-LEFT_X, -TOP_Y)]
    #transformations = [reference, rotationMatrix(angle), rotationMatrix(angle).dot([[LEFT_X],[TOP_Y]])]
    for row in range(WINDOW_HEIGHT*RENDERING_SCALE):
        m.append([])
        for col in range(WINDOW_WIDTH*RENDERING_SCALE):
            #print("Calculating ("+str(col)+", "+str(row)+")")
            screenPoint = imagePointToCenter(numpy.array([ [col/RENDERING_SCALE],
                                                            [row/RENDERING_SCALE],
                                                            [1]]), WINDOW_WIDTH, WINDOW_HEIGHT)
            graphPoint = M.dot(screenPoint)
            ANTI_ALIASING = False
            av=[0,0,0]
            if ANTI_ALIASING:
                list = (r, i),(r-quarter, i+quarter), (r+quarter, i+quarter), (r+quarter, i-quarter), (r-quarter, i-quarter)
            else:
                list = (graphPoint,)
            for c in list:
                z = iteration(numpy.array([[Decimal(0)],
                                           [Decimal(0)]]), c)
                count = 1
                while count < MAX_COUNT and math.isfinite(z[0][0]) and math.isfinite(z[1][0]):
                    z = iteration(z, c)
                    count += 1
                if math.isinf(z[0][0]) or math.isinf(z[1][0]):
                    color = hsl2arcade(count/MAX_COUNT*0.4, 1, 0.5)
                else:
                    color = [0, 0, 0]
                av[0]+=color[0]
                av[1]+=color[1]
                av[2]+=color[2]
            if ANTI_ALIASING:
                av[0] = av[0] / 5
                av[1] = av[1] / 5
                av[2] = av[2] / 5
            m[row].append(int(av[0]))
            m[row].append(int(av[1]))
            m[row].append(int(av[2]))
            # if -0.001<graphPoint[0][0]<0.001:
            #     m[row].append(0)
            #     m[row].append(0)
            #     m[row].append(255)
            # elif -0.001<graphPoint[1][0]<0.001:
            #     m[row].append(255)
            #     m[row].append(0)
            #     m[row].append(0)
            # elif graphPoint[0][0]<-0.001 and graphPoint[1][0]>0.001:
            #     m[row].append(0)
            #     m[row].append(0)
            #     m[row].append(60)
            # elif graphPoint[1][0]<-0.001 and graphPoint[0][0]>0.001:
            #     m[row].append(60)
            #     m[row].append(0)
            #     m[row].append(0)
            # elif graphPoint[0][0]>0.001 and graphPoint[1][0]>0.001:
            #     m[row].append(0)
            #     m[row].append(60)
            #     m[row].append(0)
            # else:
            #     m[row].append(0)
            #     m[row].append(0)
            #     m[row].append(0)
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
    print("\r"+"██████████ 100.00% Done                                         ")
    f = open('graph.png', 'wb')
    w = png.Writer(WINDOW_WIDTH*RENDERING_SCALE, WINDOW_HEIGHT*RENDERING_SCALE, greyscale=False)
    w.write(f, m)
    f.close()
    RENDERING_SCALE = NEW_RENDERING_SCALE
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
                cursorPos = numpy.array([ [self.rect.centerX],
                                            [self.rect.centerY],
                                            [1]])
                rectPos = screenPointToCenter(cursorPos, WINDOW_WIDTH, WINDOW_HEIGHT)
                newOrigin = M.dot(rectPos)
                translation = newOrigin - ORIGIN
                angle = Decimal(math.radians(self.rect.rotation))
                T = translationMatrix(translation[0][0], translation[1][0])
                R = rotationMatrix(angle)
                S = scaleMatrix(Decimal(self.rect.width / WINDOW_WIDTH))
                M = R.dot(S).dot(T).dot(M)
                ORIGIN = newOrigin
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
