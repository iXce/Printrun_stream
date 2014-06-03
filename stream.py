#!/usr/bin/env python
# coding: utf-8

import os, sys

import xmlrpclib
import threading
import datetime

rpc = xmlrpclib.ServerProxy('http://localhost:7978')

import cStringIO
import matplotlib as mpl
mpl.use('Agg')
import pylab

import pygst
pygst.require("0.10")
import gst
import gobject, glib
glib.threads_init()

pipeline_string= """v4l2src device=%s ! tee name=videoout ! queue leaky=1 ! \
videorate ! video/x-raw-yuv,width=800,height=600,fps=24,framerate=(fraction)24/1 ! queue leaky=1 ! \
ffmpegcolorspace ! \
rsvgoverlay name=graphoverlay width-relative=0.2 height-relative=0.3 x-relative=0.02 y-relative=0.02 ! \
textoverlay name=overlay text="---" shaded-background=true font-desc="Ubuntu Mono 11" deltay=15 ! \
ffmpegcolorspace ! \
theoraenc bitrate=8000 ! queue leaky=1 ! oggmux ! fdsink""" % sys.argv[1]#muxout. pulsesrc ! audio/x-raw-int,rate=22000,channels=1,width=16 ! queue ! audioconvert ! vorbisenc ! queue ! muxout. oggmux name=muxout ! fdsink""" % sys.argv[1]

def on_message(bus, message):
    t = message.type
    if t == gst.MESSAGE_ERROR:
        err, debug = message.parse_error()
        print >> sys.stderr,"Error: %s" % err, debug
    elif t == gst.MESSAGE_WARNING:
        err, debug = message.parse_warning()
        print >> sys.stderr,"Warning: %s" % err, debug
    elif t == gst.MESSAGE_INFO:
        err, debug = message.parse_info()
        print >> sys.stderr,"Info: %s" % err, debug

pipeline = gst.parse_launch(pipeline_string)
overlay = pipeline.get_by_name("overlay")
graphoverlay = pipeline.get_by_name("graphoverlay")
pipeline.set_state(gst.STATE_PLAYING)
bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", on_message)

def format_duration(delta):
    return str(datetime.timedelta(seconds = int(delta)))

TEMP_LOG_SIZE = 60
LINEWIDTH = 10

def make_temp_graph(temp_log):
    first_log = temp_log[0]
    tempnames = first_log.keys()
    tempnames.sort()
    temps = {}
    for name in tempnames:
        temps[name] = zip(*[entry[name] for entry in temp_log])

    pylab.rcParams['ytick.major.pad'] = '20'
    fig = pylab.figure(figsize = (10, 10))

    try:
        fig.patch.set_facecolor('gray')
        fig.patch.set_alpha(0.4)

        ax = fig.add_subplot(1, 1, 1)
        for child in ax.get_children():
            if isinstance(child, mpl.spines.Spine):
                child.set_color('#dddddd')
        ax.tick_params(axis='y', colors='white')

        ax.patch.set_facecolor('gray')
        ax.patch.set_alpha(0.2)

        pylab.xlim([0, TEMP_LOG_SIZE])
        pylab.ylim([0, 300])
        for name in tempnames:
            thistemps = temps[name]
            extra = (TEMP_LOG_SIZE - len(thistemps[0]))
            idxs = range(extra, extra + len(thistemps[0]))
            pylab.plot(idxs, thistemps[0], '-', linewidth = LINEWIDTH)
            pylab.plot(idxs, thistemps[1], '--', linewidth = LINEWIDTH)

        ax.get_xaxis().set_ticks([])
        for item in ax.get_xticklabels() + ax.get_yticklabels():
            item.set_fontsize(30)

        svg = cStringIO.StringIO()
        fig.savefig(svg, format = 'svg', bbox_inches = 'tight', pad_inches = 0.1, facecolor = fig.get_facecolor())
    finally:
        pylab.close(fig)
    return svg.getvalue()

class StatusHandler(object):

    def __init__(self):
        self.temp_log = []
        self.update_status()

    def update_status(self):
        try:
            status = rpc.status()
            status_text = ""
            if status["filename"] is not None:
                status_text += "Printing %s\n" % os.path.basename(status["filename"])
            if status["eta"] is not None:
                secondsremain, secondsestimate, progress = status["eta"]
                status_text += "Est: %s of %s remaining\n" % (format_duration(secondsremain),
                                                            format_duration(secondsestimate))
            if status["temps"] is not None:
                temps = status["temps"]
                self.temp_log.append(temps)
                if len(self.temp_log) > TEMP_LOG_SIZE:
                    self.temp_log.pop(0)
                graphsvg = make_temp_graph(self.temp_log)
                graphoverlay.set_property("data", graphsvg)
                #print >> sys.stderr, len(self.temp_log), graphsvg
                status_text += "Temps: H: %s/%s, B: %s/%s\n" % (temps["T"][0], temps["T"][1], temps["B"][0], temps["B"][1])
            if status["z"] is not None:
                status_text += "Z = %s\n" % status["z"]
            if not status_text:
                status_text = "Printer online"
        except:
            status_text = "Printer offline"
        overlay.set_property("text", status_text.strip())
        self.timer = threading.Timer(3.0, self.update_status)
        self.timer.start()

    def stop(self):
        self.timer.cancel()

statushandler = StatusHandler()

loop = gobject.MainLoop()
try:
    loop.run()
except KeyboardInterrupt:
    pass

pipeline.set_state(gst.STATE_NULL)
statushandler.stop()
