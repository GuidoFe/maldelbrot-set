#!/usr/bin/python3
import sys
import math
import arcade
import colorsys
import png
from decimal import *

IM_WIDTH = 1366
IM_HEIGTH = 768
ORIGIN = (Decimal(-2.278645833),Decimal(-1))
GRAPH_WIDTH = Decimal(3.557291667)
GRAPH_HEIGHT = Decimal(2)
MAX_COUNT = 100
SCALE_FACTOR=0.2

isReady = False
isNew = False
def iteration(z, c):
    return (z[0]*z[0]-z[1]*z[1]+c[0], 2*z[0]*z[1]+c[1])

def hsl2arcade(h, s, l):
    color=colorsys.hsv_to_rgb(h, s, l)
    return (round(color[0]*255), round(color[1]*255), round(color[2]*255))

def loop():
    global isNew
    global isReady
    isReady = False
    m = []
    wunit = Decimal(GRAPH_WIDTH / IM_WIDTH)
    hunit = Decimal(GRAPH_HEIGHT / IM_HEIGTH)
    for row in range(IM_HEIGTH):
        m.append([])
        i = ORIGIN[1] + hunit * row
        for col in range(IM_WIDTH):
            #print("Calculating ("+str(col)+", "+str(row)+")")
            r = ORIGIN[0] + wunit * col
            wquarter = wunit/4
            hquarter = hunit/4
            av = [0,0,0]
            for c in (r, i),(r-wquarter, i+hquarter), (r+wquarter, i+hquarter), (r+wquarter, i-hquarter), (r-wquarter, i-hquarter):
                c = (Decimal(r),Decimal(i))
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
            m[row].append(int(av[0]/5))
            m[row].append(int(av[1]/5))
            m[row].append(int(av[2]/5))
    f = open('graph.png', 'wb')
    w = png.Writer(IM_WIDTH, IM_HEIGTH, greyscale=False)
    w.write(f, m)
    f.close()
    isNew = True
    isReady = True

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


class Visualizer(arcade.Window):
    def __init__(self):
        self.rect = Rect(IM_WIDTH/2, IM_HEIGTH/2, IM_WIDTH/4, IM_HEIGTH/4, False)
        super().__init__(IM_WIDTH, IM_HEIGTH, "Mandelbrot set")
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
                arcade.draw_lrwh_rectangle_textured(0, 0, IM_WIDTH, IM_HEIGTH, arcade.load_texture("graph.png"))
                arcade.draw_text("x=["+str(ORIGIN[0])+", "+str(ORIGIN[0]+GRAPH_WIDTH)+"], y=["+str(ORIGIN[1])+", "+str(ORIGIN[1]+GRAPH_HEIGHT)+"]", 0, 0, arcade.color.WHITE)
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
                wunit = GRAPH_WIDTH/IM_WIDTH
                hunit = GRAPH_HEIGHT/IM_HEIGTH
                scale = Decimal(self.rect.width / IM_WIDTH)
                ORIGIN = (ORIGIN[0]+Decimal(self.rect.centerX-self.rect.width/2)*wunit, ORIGIN[1]+Decimal(self.rect.centerY-self.rect.height/2)*hunit)
                GRAPH_WIDTH = GRAPH_WIDTH * scale
                GRAPH_HEIGHT = GRAPH_HEIGHT * scale
                arcade.start_render()
                arcade.draw_lrwh_rectangle_textured(0, 0, IM_WIDTH, IM_HEIGTH, arcade.load_texture("graph.png"))
                arcade.draw_text("LOADING...", 0, 0, arcade.color.WHITE)
                arcade.finish_render()
                loop()
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y < 0:
            self.rect.scale(1-SCALE_FACTOR)
        else:
            self.rect.scale(1+SCALE_FACTOR)

def main():
    app = Visualizer()
    arcade.start_render()
    arcade.set_background_color(arcade.color.BLACK)
    arcade.draw_text("RENDERING...", 1, 1, arcade.color.WHITE, 12)
    arcade.finish_render()
    arcade.run()

main()
