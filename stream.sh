#!/bin/sh

ICECAST_SERVER=""
ICECAST_PORT=""
ICECAST_PASSWORD=""
ICECAST_MOUNT=""
STREAM_TITLE=""
STREAM_DESC=""
STREAM_URL=""

./stream.py /dev/video* | ~/oggfwd/oggfwd $ICECAST_SERVER \
                                          $ICECAST_PORT \
                                          $ICECAST_PASSWORD \
                                          $ICECAST_MOUNT \
                                          -n $STREAM_TITLE \
                                          -d $STREAM_TITLE \
                                          -u $STREAM_URL \
                                          -g $STREAM_DESC
