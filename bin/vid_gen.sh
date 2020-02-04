#!/bin/bash

ffmpeg -hide_banner -loglevel panic -i $1 -framerate 25 -an -vcodec copy -f segment -segment_time 300 -reset_timestamps 0 -strftime 1 ./segments/$2/rtsp_%Y-%m-%d_%H-%M-%S.flv &
