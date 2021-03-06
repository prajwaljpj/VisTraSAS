#!/bin/bash

while test $# -gt 0; do
    case "$1" in
	-h|--help)
	    echo "VisTraSAS - Visual Traffic surveillance and Analytics System"
	    echo " "
	    echo "main.sh [options] application [arguments]"
	    echo " "
	    echo "options:"
	    echo "-h, --help                               show brief help"
	    echo "-e, --engine=ENGINE                      Specify engine file"
	    echo "-v, --verbose=VERBOSE                    Verbosity(0 or 1)"
	    echo "-c, --caffe-model=CAFFE_MODEL            Specify caffe model (if engine not present)"
	    echo "-p, --caffe-proto=CAFFE_PROTO            Specify caffe prototxt (if engine not present)"
	    echo "-P, --pipe-path=PIPE_PATH                Path where the piping buffer should be created"
	    echo "-s, --segment-path=SEGMENT_PATH          Location of generated segments"
	    echo "-l, --line-coord=LINE_COORD              Line coordinates for camera (specific to camera)"
	    echo "-i, --intrinsics=CAM_PARAM               Camara Intrinsic parameters (specific to camera)"
	    echo "-q, --qlength_conf=Q_CONF                Configuration json for qlength (specific to camera)"
	    exit 0
	    ;;
	-e)
	    shift
	    if test $# -gt 0; then
		export ENGINE=$1
	    else
		echo "no engine file specified specified"
		echo "WARNING::attempting to create engine file"
	    fi
	    shift
	    ;;
	--engine*)
	    export ENGINE=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-v)
	    shift
	    if test $# -gt 0; then
		export VERBOSE=$1
	    else
		echo "no verbosity specified (default to 0)"
	    fi
	    shift
	    ;;
	--verbose*)
	    export VERBOSE=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-c)
	    shift
	    if test $# -gt 0; then
		export CAFFE_MODEL=$1
	    else
		echo "no caffe-model specified specified"
		echo "WARNING::Please provide engine file"
		if [ -z $ENGINE]
		then
		    exit 1
		fi
	    fi
	    shift
	    ;;
	--caffe-model*)
	    export CAFFE_MODEL=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-p)
	    shift
	    if test $# -gt 0; then
		export CAFFE_PROTO=$1
	    else
		echo "no caffe-proto specified specified"
		echo "WARNING::please provide engine file"
		if [ -z $ENGINE]
		then
		    exit 1
		fi
	    fi
	    shift
		    ;;
	--caffe-proto*)
	    export CAFFE_PROTO=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-P)
	    shift
	    if test $# -gt 0; then
		export PIPE_PATH=$1
	    else
		echo "no pipe path specified specified"
		exit 1
	    fi
	    shift
	    ;;
	--pipe-path*)
	    export PIPE_PATH=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-s)
	    shift
	    if test $# -gt 0; then
		export SEGMENT_PATH=$1
	    else
		echo "no Segment source specified"
		exit 1
	    fi
	    shift
	    ;;
	--segment-path*)
	    export SEGMENT_PATH=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-l)
	    shift
	    if test $# -gt 0; then
		export LINE_COORD=$1
	    else
		echo "no line coordinates for counts"
		exit 1
	    fi
	    shift
	    ;;
	--line-coord*)
	    export LINE_COORD=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-i)
	    shift
	    if test $# -gt 0; then
		export CAM_PARAM=$1
	    else
		echo "nocamera intrinsics for speeds"
		exit 1
	    fi
	    shift
	    ;;
	--intrinsics*)
	    export CAM_PARAM=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-q)
	    shift
	    if test $# -gt 0; then
		export Q_CONF=$1
	    else
		echo "nocamera qlen config file"
		exit 1
	    fi
	    shift
	    ;;
	--qlength_conf*)
	    export Q_CONF=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	-r)
	    shift
	    if test $# -gt 0; then
		export RTSP_STRM=$1
	    else
		echo "rtsp stream has to be given for code to work"
		exit 1
	    fi
	    shift
	    ;;
	--rtsp_strm*)
	    export RTSP_STRM=`echo $1 | sed -e 's/^[^=]*=//g'`
	    shift
	    ;;
	*)
	    break
	    ;;
    esac
done

mkdir -p segments/$SEGMENT_PATH
mkdir -p results/$SEGMENT_PATH
# when link is provided uncomment
ffmpeg -hide_banner -loglevel panic -i $RTSP_STRM -framerate 25 -an -vcodec copy -f segment -segment_time 200 -reset_timestamps 0 -strftime 1 ./segments/$SEGMENT_PATH/rtsp_%Y-%m-%d_%H-%M-%S.flv &

# export PYTHONPATH=${PWD}/deep_sort:$PYTHONPATH

# checking if in python env

INVENV=$(python -c 'import sys; print ("1" if hasattr(sys, "real_prefix") else "0")')

if [ $INVENV -eq 1 ]
then echo "inside python environment"
else
    echo "WARNING:: outside python environment" 
    workon all
fi

# checking if engine file is present

if [ ! -f $ENGINE ]; then
    ###### TODO ASSUME ENGINE IS CREATED
    # ./install/createEngine --caffe-model=$CAFFE_MODEL --prototxt=$CAFFE_PROTO
    echo "Engine file not found, Attempting to create one"
fi

echo $ENGINE

./install/runYolov3 $ENGINE ./segments/$SEGMENT_PATH 
# ./runYolov3 $ENGINE $PIPE_PATH ./segments/$SEGMENT_PATH &

#echo $PIPE_PATH $LINE_COORD $CAM_PARAM $Q_CONF

#python3 main.py --segment_path=$SEGMENT_PATH --line_coordinates=$LINE_COORD --camera_intrinsics_file=$CAM_PARAM --q_length_config=$Q_CONF $PIPE_PATH &

# while true;
# do sleep 5;
#    FFMPEG_PROC="$(ps aux | grep  ffmpeg | grep test_cam | awk '{print $2}')"
#    if [ -z "$FFMPEG_PROC" ]
# then
# 	ffmpeg -i $RTSP_STRM -framerate 25 -an -vcodec copy -f segment -segment_time 300 -reset_timestamps 0 -strftime 1 ./segments/$SEGMENT_PATH/rtsp_%Y-%m-%d_%H-%M-%S.flv &
#    else echo "$SEGMENT_PATH stream stopped working at $(date)" >> stream_not_working.log
#    fi
# done
