#!/usr/bin/env python
# coding: utf-8

import os, sys

import xmlrpclib
import threading
import datetime

rpc = xmlrpclib.ServerProxy('http://localhost:7978')

import pygst
pygst.require("0.10")
import gst
import gobject, glib
glib.threads_init()

pipeline_string= """v4l2src device=%s ! tee name=videoout ! queue leaky=1 ! \
videorate ! video/x-raw-yuv,width=800,height=600,fps=24,framerate=(fraction)24/1 ! queue leaky=1 ! \
textoverlay name=overlay text="---" shaded-background=true font-desc="Ubuntu Mono 11" deltay=15 ! \
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
pipeline.set_state(gst.STATE_PLAYING)
bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", on_message)

def format_duration(delta):
    return str(datetime.timedelta(seconds = int(delta)))

class StatusHandler(object):

  def __init__(self):
      self.update_status()

  def update_status(self):
      try:
          status = rpc.status()
          status_text = ""
          if status["filename"] is not None:
              status_text += "Printing %s\n" % os.path.basename(status["filename"])
          if status["eta"] is not None:
              secondsremain, secondsestimate, progress = status["eta"]
              status_text += "Est: %s of %s remaining" % (format_duration(secondsremain),
                                                          format_duration(secondsestimate))
          if status["temps"] is not None:
              temps = status["temps"]
              status_text += "Temps: H: %s/%s, B: %s/%s\n" % (temps["T"][0], temps["T"][1], temps["B"][0], temps["B"][1])
          if not status_text:
            status_text = "Printer online"
      except:
        status_text = "Printer offline"
      overlay.set_property("text", status_text.strip())
      self.timer = threading.Timer(1.0, self.update_status)
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
