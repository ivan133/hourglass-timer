#!/usr/bin/env python
# Eggtimer

# based on:

# # clock_ex4.py
# 
# # a pygtk widget that implements a clock face
# # porting of Davyd Madeley's
# # http://www.gnome.org/~davyd/gnome-journal-cairo-article/clock-ex4.c
# 
# # author: Lawrence Oluyede <l.oluyede@gmail.com>
# # date: 16 February 2005

import gtk
from gtk import gdk
import gobject

import math
from datetime import datetime, timedelta

import sys

import cairo

import random

TIMEOUT=35

def clamp(val, minimum, maximum):
    return min(maximum,max(minimum,val))

class EggClockFace(gtk.DrawingArea):
    # EggClockFace signals
    __gsignals__ = dict(time_changed=(gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE,
                                      (gobject.TYPE_INT, gobject.TYPE_INT)))

    def __init__(self, seconds, config={}):
        super(EggClockFace, self).__init__()

        self.config = config

        # gtk.Widget signals
        self.connect("expose_event", self.expose)

        self.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.connect('key_press_event', self.on_key_press)
        self.set_flags(gtk.CAN_FOCUS)
        self.grab_focus()

        self.update()

        self.dir = True
        if seconds < 0:
            self.dir = False
            seconds = -seconds

        self.delta_time = timedelta(seconds=seconds)
        self.target_time = self.time + self.delta_time
        
        # update the clock once a second
        gobject.timeout_add(TIMEOUT, self.update)
        
    def on_key_press(self, widget, event):
        key = event.keyval
        if key == gtk.keysyms.Escape and not self.config.get("sausage_fingers"):
            gtk.main_quit()
        elif key == gtk.keysyms.w and event.state & gtk.gdk.CONTROL_MASK:
            gtk.main_quit()
            
    def expose(self, widget, event):
        context = widget.window.cairo_create()

        # set a clip region for the expose event
        context.rectangle(event.area.x, event.area.y,
                          event.area.width, event.area.height)
        context.clip()

        self.draw(context)

        return False

    def is_running(self):
        return self.target_time > self.time

    def draw(self, context):
        rect = self.get_allocation()

        x = rect.x + rect.width / 2.0
        y = rect.y + rect.height / 2.0
        radius = min(rect.width / 2.0, rect.height / 2.0) - 5

        # time is running
        if self.is_running():

            # clock back
            context.set_line_width(radius*0.02)
            context.arc(x, y, radius, 0, 2.0 * math.pi)
            context.set_source_rgb(1, 1, 1)
            context.fill_preserve()
            context.set_source_rgb(0, 0, 0)
            context.stroke()



            ratio = self.progress()
            
            angle = -0.5*math.pi

            context.save()
            context.set_line_width(radius*0.35)
            context.arc(x, y, radius*0.75, angle, angle-ratio*2.0*math.pi)
            context.stroke()
            context.restore()
            
        # time is out
        else:

            context.arc(x, y, radius, 0, 2.0 * math.pi)
            context.set_source_rgb(0.3, 0.3, 0.3)
            context.fill_preserve()

            context.set_source_rgb(1.0, 1.0, 1.0)
            self.draw_time(context, x, y)

    def draw_time(self, context, x, y):
        # draw time
        
        text = self.target_time.strftime("%H:%M:%S")
        #text = str(self.time - self.target_time)
        
        context.select_font_face("DejaVu", cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(min(x,y)*0.3)
        
        xbearing, ybearing, width, height, xadvance, yadvance = context.text_extents(text)
        context.move_to(x-width*0.5, y+height*0.4)

        context.show_text(text)
    
    def redraw_canvas(self):
        if self.window:
            alloc = self.get_allocation()
            #rect = gdk.Rectangle(alloc.x, alloc.y, alloc.width, alloc.height)
            #self.window.invalidate_rect(rect, True)
            self.queue_draw_area(alloc.x, alloc.y, alloc.width, alloc.height)
            self.window.process_updates(True)

    def update(self):
        # update the time
        self.time = datetime.now()

        return True # keep running this event

    def progress(self):
        # "progress bar"

        if not self.is_running():
            if self.dir:
                return 0.0
            else:
                return 1.0
        
        delta = self.target_time - self.time
        delta = delta.microseconds + delta.seconds*1000000.0
        timer = self.delta_time.seconds*1000000.0

        if self.dir:
            return delta/timer
        else:
            return 1.0-delta/timer


    # public access to the time member
    def _get_time(self):
        return self._time
    def _set_time(self, datetime):
        self._time = datetime
        self.redraw_canvas()
    time = property(_get_time, _set_time)

def draw_equilateral_triangle(context, bottom_center_x, bottom_center_y,
                              height, hwidth):
    context.move_to(bottom_center_x-hwidth,
                    bottom_center_y)
    context.line_to(bottom_center_x,
                    bottom_center_y+height)
    context.line_to(bottom_center_x+hwidth,
                    bottom_center_y)
    context.line_to(bottom_center_x-hwidth,
                    bottom_center_y)

def lerp(val, a, b):
     return val*a + (1.0-val)*b

def draw_particle(context, x, y, size):
    context.arc(x, y, size, 0, 2*math.pi)
    context.fill()

PART_QUANTITY = 50

particles = [ (random.random(),random.random()) for n in xrange(PART_QUANTITY) ]


class SandClockFace(EggClockFace):

    def draw(self, context):
        rect = self.get_allocation()

        x = rect.x + rect.width / 2.0
        y = rect.y + rect.height / 2.0
        radius = min(rect.width / 2.0, rect.height / 2.0) - 5

        context.save()

        context.translate(rect.width/2.0, rect.height/2.0)

        ORIGINAL_SVG_SIZE = 600.0
        scale = min(rect.width, rect.height)/ORIGINAL_SVG_SIZE
        context.scale(scale,scale)

        # center lines (approx.)

        center_x = 0.0
        center_y = 0.0

        context.move_to(73.0,103.0)
        context.rel_curve_to(-2.31763,-67.16386,
                             -67.21099,-60,
                             -67.95729,-103.57143)
        context.rel_curve_to(0.79877,-43.57143,
                             65.69214,-36.40757,
                             68.00977,-103.57143)
        context.rel_curve_to(0.68979,-19.98983,
                             -10.81557,-73.57143,
                             -72.67126,-73.57143)
        context.rel_curve_to(-61.85568,0,
                             -73.36104,53.5816,
                             -72.67125,73.57143)
        context.rel_curve_to(2.31763,67.16386,
                             67.211,60,
                             67.95729,103.57143)
        context.rel_curve_to(-0.79876,43.57143,
                             -65.69213,36.40757,
                             -68.00976,103.57143)
        context.rel_curve_to(-0.68979,19.98983,
                             10.81557,73.57143,
                             72.67125,73.57143)
        context.rel_curve_to(61.85568,0,
                             73.36104,-53.5816,
                             72.67125,-73.57143)
        # fill
        context.set_source_rgb(1, 1, 1)
        context.fill_preserve()
        context.set_source_rgb(0, 0, 0)

        context.stroke_preserve()
        context.clip()

        # context.stroke()


        # half(!) sizes
        size_x = 72
        size_y = 177


        # upper part

        upper_speed = 1.0 # 1.8
        full_upper_height = size_y*0.9
        upper_height = full_upper_height*(1.0-(1.0-self.progress())**upper_speed)

        context.rectangle(center_x-size_x,center_y,
                          size_x*2,-upper_height)

        context.fill()

        # lower part

        lower_speed = 1.0 # 1.5
        full_lower_height = size_y*0.9
        # lower_height = full_lower_height*(1.0-self.progress())
        height = size_x*2
        start_pos = center_y+size_y+height
        end_pos = center_y+size_y
        base_pos = lerp(self.progress()**lower_speed,start_pos,end_pos)

        draw_equilateral_triangle(context,
                                  center_x, base_pos,
                                  -height,
                                  size_x*2)
        context.fill()


        if self.is_running():
            t = self.time.second+self.time.microsecond*0.000001

            flow_width = size_x*0.04
            overlap = size_y*0.01
            self.draw_particles(context, t,
                                center_x-flow_width, center_y-overlap,
                                flow_width*2, size_y+overlap)
        else:
            context.restore()
            context.set_source_rgb(0, 0, 0)
            self.draw_time(context, x, y)

    def draw_particles(self, context, time, x, y, w, h):
        size = w*0.15
        period = 5.0
        timescale = 3.0
        time = time*timescale
        
        for rx,phase in particles:
            px = rx*w
            t = ((time+phase*h)%period)/period
            if self.dir:
                py = h*t*t
            else:
                py = h-h*t*t
            draw_particle(context, x+px, y+py, size)

DEFAULT_FACE = SandClockFace

clock_faces = {"circle":EggClockFace,
               "sand":SandClockFace}

def main(time, config):
    window = gtk.Window()
    # clock = EggClockFace(time)
    # clock = SandClockFace(time)

    face = config["mode"]
                
    if face in clock_faces:
        clock = clock_faces[face]
    else:
        print("Unknown face: '%s'" % face)
        print("Availible faces:")
        for k,v in clock_faces.iteritems():
            print("\t"+k)
        clock = DEFAULT_FACE
        #exit(1)

    window.add(clock(time, config))
    window.connect("destroy", gtk.main_quit)
    window.show_all()

    try:
        gtk.main()
    except KeyboardInterrupt:
        exit(0)

config = {}

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-m", "--mode", action="store",
                      dest="mode", default="sand",
                      help="select \"skin\"")
    parser.add_option("--sausage-fingers", action="store_true",
                      dest="sausage_fingers", default=False,
                      help="do not exit on ESC press")
    (options, args) = parser.parse_args()

    config = vars(options)
    
    if len(args) < 1:
        print("usage:\n     ./%s [-m %s] [+/-]<seconds>" %
              (sys.argv[0], "/".join(clock_faces.keys())))
        exit(1)
    try:
        main(int(args[0]), config)
    except ValueError,e:
        print e
        exit(1)
