#!/usr/bin/python3
import sys
import math
import arcade
import colorsys
import png
from decimal import *
from time import time
import subprocess as s

WINDOW_WIDTH = 683
WINDOW_HEIGHT = 384

# The image will be rendered in WINDOW_WIDTH*RENDERING_SCALE x WINDOW_HEIGHT*RENDERING_SCALE,
RENDERING_SCALE = 1
ROTATED = False
NEW_ROTATED = False
ORIGIN = (Decimal(-1.778645833),Decimal(-1))
GRAPH_WIDTH = Decimal(3.557291667)
GRAPH_HEIGHT = Decimal(2)
MAX_COUNT = 100
RECT_SCALE_FACTOR=0.2
ANTI_ALIASING = False
HIDE_GUI = False

NEW_RENDERING_SCALE = 1
isReady = False
isNew = False
TWOPLACES = Decimal(10) ** -2
def iteration(z, c):
    return (z[0]*z[0]-z[1]*z[1]+c[0], 2*z[0]*z[1]+c[1])

def hsl2arcade(h, s, l):
    color=colorsys.hsv_to_rgb(h, s, l)
    return (round(color[0]*255), round(color[1]*255), round(color[2]*255))

def loop():
    global isNew
    global isReady
    global RENDERING_SCALE
    global ROTATED
    global ORIGIN
    isReady = False
    m = []
    imageWidth = int(WINDOW_WIDTH * NEW_RENDERING_SCALE)
    imageHeight = int(WINDOW_HEIGHT * NEW_RENDERING_SCALE)
    unit = Decimal(GRAPH_WIDTH / imageWidth)
    print(Decimal(GRAPH_WIDTH / imageWidth), Decimal(GRAPH_HEIGHT / imageHeight))
    startTime = time()
    if NEW_ROTATED and not ROTATED or ROTATED and not NEW_ROTATED:
        ROTATED = True
    else:
        ROTATED = False
    for row in range(imageHeight):
        m.append([])
        if ROTATED:
            r = ORIGIN[0] + (imageHeight - row) * unit
        else:
            i = ORIGIN[1] + (imageHeight - row) * unit
        for col in range(imageWidth):
            #print("Calculating ("+str(col)+", "+str(row)+")")
            if ROTATED:
                i = ORIGIN[1] - col * unit
            else:
                r = ORIGIN[0] + col * unit
            quarter = unit/4
            av = [0,0,0]
            if ANTI_ALIASING:
                list = (r, i),(r-quarter, i+quarter), (r+quarter, i+quarter), (r+quarter, i-quarter), (r-quarter, i-quarter)
            else:
                list = ((r,i),)
            for c in list:
                z = iteration((Decimal(0), Decimal(0)), c)
                count = 1
                while count < MAX_COUNT and math.isfinite(z[0]) and math.isfinite(z[1]):
                    z = iteration(z, c)
                    count += 1
                if math.isinf(z[0]) or math.isinf(z[1]):
                    color = hsl2arcade(count/MAX_COUNT*0.4, 1, 0.5)
                else:
                    color = [0, 0, 0]
                av[0]+=color[0]
                av[1]+=color[1]
                av[2]+=color[2]
            if ANTI_ALIASING:
                av[0] = av[0] / 5
                av[1] = av[1] / 5
                av[2] = av[2] /5
            m[row].append(int(av[0]))
            m[row].append(int(av[1]))
            m[row].append(int(av[2]))
        done = row*100/imageHeight
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
    w = png.Writer(imageWidth, imageHeight, greyscale=False)
    w.write(f, m)
    f.close()
    RENDERING_SCALE = NEW_RENDERING_SCALE
    isNew = True
    isReady = True
    s.call(['notify-send','Mandelbrot set','Rendering has been completed.'])

class Rect:
    def __init__(self, centerX, centerY, width, height, visibility):
        self.centerX = centerX
        self.centerY = centerY
        self.width = width
        self.height = height
        self.visibility = visibility

    def scale(self, factor):
        self.width = self.width * factor
        self.height = self.height * factor

    def move(self, x, y):
        self.centerX = x
        self.centerY = y
    def rotate(self):
        w = self.width
        self.width = self.height
        self.height = w


class Visualizer(arcade.Window):
    def __init__(self):
        self.rect = Rect(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, WINDOW_WIDTH/4, WINDOW_HEIGHT/4, False)
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Mandelbrot set")
        self.firstInit = False

    def on_draw(self):
        global isNew
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
                if not HIDE_GUI:
                    endx = ORIGIN[0] + GRAPH_WIDTH
                    endy = ORIGIN[1] + GRAPH_HEIGHT
                    arcade.draw_text("H: show/hide UI\nMouse sx: position rectangle\nMouse dx: start rendering\nMouse scroll: change rectangle zoom\nMouse wheel click: show/hide rectangle\n+/-: Increase/decrease rendering quality\nR: Rotate rectangle\nA: Antialiasing on/off", 0, WINDOW_HEIGHT-120, arcade.color.WHITE, 9)
                    arcade.draw_text("x=[{}, {}], y=[{}, {}]".format(str(ORIGIN[0].quantize(TWOPLACES)), str(endx.quantize(TWOPLACES)), str(ORIGIN[1].quantize(TWOPLACES)), str(endy.quantize(TWOPLACES))), 0, 11, arcade.color.WHITE, 9)
                    arcade.draw_text("NEXT RENDERING AT {}x{}, ANTI ALIASING = {}".format(w, h, ANTI_ALIASING), 0, 0, arcade.color.WHITE, 9)
                if self.rect.visibility:
                    arcade.draw_rectangle_outline(self.rect.centerX, self.rect.centerY, self.rect.width, self.rect.height, arcade.color.WHITE)


    def on_mouse_press(self, x, y, button, modifier):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.rect.visibility = True
            self.rect.move(x, y)
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self.rect.visibility = not self.rect.visibility
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            if self.rect.visibility:
                global ORIGIN
                global GRAPH_WIDTH
                global GRAPH_HEIGHT
                scale = Decimal(max(self.rect.width, self.rect.height) / WINDOW_WIDTH)
                print(GRAPH_WIDTH / WINDOW_WIDTH, GRAPH_HEIGHT / WINDOW_HEIGHT)
                unit = GRAPH_WIDTH / WINDOW_WIDTH
                print("ROTATED: " + str(ROTATED) +", NEW_ROTATED: " + str(NEW_ROTATED))
                if ROTATED:
                    x = ORIGIN[0] + Decimal(self.rect.centerY - self.rect.height / 2) * unit
                    y = ORIGIN[1] - Decimal(self.rect.centerX + self.rect.width / 2) * unit
                else:
                    x = ORIGIN[0] + Decimal(self.rect.centerX - self.rect.width / 2) * unit
                    if NEW_ROTATED:
                        y = ORIGIN[1] + Decimal(self.rect.centerY + self.rect.height / 2) * unit
                    else:
                        y = ORIGIN[1] + Decimal(self.rect.centerY - self.rect.height / 2) * unit
                ORIGIN = (x, y)
                GRAPH_WIDTH = GRAPH_WIDTH * scale
                GRAPH_HEIGHT = GRAPH_HEIGHT * scale
            arcade.start_render()
            arcade.draw_xywh_rectangle_filled(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, arcade.color.BLACK)
            arcade.draw_text("LOADING...", 0, 0, arcade.color.WHITE)
            arcade.finish_render()
            loop()
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
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
        global NEW_ROTATED
        if symbol == arcade.key.PLUS:
            NEW_RENDERING_SCALE += 1
        elif symbol == arcade.key.MINUS:
            if NEW_RENDERING_SCALE != 1:
                NEW_RENDERING_SCALE -= 1
        elif symbol == arcade.key.R:
            NEW_ROTATED = not NEW_ROTATED
            self.rect.rotate()
        elif symbol == arcade.key.A:
            ANTI_ALIASING = not ANTI_ALIASING
        elif symbol == arcade.key.H:
            HIDE_GUI = not HIDE_GUI


def main():
    app = Visualizer()
    arcade.start_render()
    arcade.set_background_color(arcade.color.BLACK)
    arcade.draw_text("RENDERING...", 1, 1, arcade.color.WHITE, 12)
    arcade.finish_render()
    arcade.run()

main()
