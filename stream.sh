#!/bin/sh

ICECAST_SERVER=""
ICECAST_PORT=""
ICECAST_PASSWORD=""
ICECAST_MOUNT=""
STREAM_TITLE=""
STREAM_DESC=""
STREAM_URL=""
STREAM_GENRE=""

[ -f ./stream_params ] && . ./stream_params

python2 stream.py /dev/video* | oggfwd $ICECAST_SERVER \
                                       $ICECAST_PORT \
                                       $ICECAST_PASSWORD \
                                       $ICECAST_MOUNT \
                                       -n "$STREAM_TITLE" \
                                       -d "$STREAM_DESC" \
                                       -u "$STREAM_URL" \
                                       -g "$STREAM_GENRE"
