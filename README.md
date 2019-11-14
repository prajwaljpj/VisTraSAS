# Visual Traffic Surveillance and Analytics System

## Introduction
A complete system for the analysis of Indian Traffic Patterns

Provides a novel approach to acquiring traffic counts and link speeds
---
## Prerequisite Installation
0) The code was tested on Ubuntu 18.04
1) First it is suggested to have your nvidia-drivers to be installed properly
This can be checked by:
	```bash
	nvidia-smi
	```
2) Install cuda-10.0 and cudnn (latest for cuda-10.0)
	```bash
	nvcc -V
	```
3) Create a virtualenvironment using virtualenv and virtualenvwrapper
	```bash
	pip install virtualenv virtualenvwrapper
	mkvirtualenv all
	workon all
	```
4) Install opencv-3.4.4 (pyimagesearch website tutorial)
	```python3
	# In python3
	import cv2
	cv2.__version__
	```
5) Install tensorflow-gpu==1.15.0
	```python3
	import tensorflow as tf
	tf.__version__
	```
6) Install pytorch (pip installation, cuda-10.0,10.1)
	```python3
	import torch
	import torchvision
	```
7) Install nvidia tensorrt 5.1.5. To check tensorrt installation
	```bash
	dpkg -l | grep nvinfer
	```
8) Install boost and all its dependencies
	```bash
	sudo apt-get install libboost-all-dev
	```

### Installation
1) Create a build folder
	```sh
	mkdir build && cd build
	```
2) Compile and install
	```sh
	cmake ..
	make -j8
	make install
	cd ..
	```

### Creating model
Run the following command after setting up:
	```sh
	./install/createEngine --caffemodel=./models/yolov3_traffic_final.caffemodel --prototxt=./models/yolov3_traffic_final.prototxt --input=./test/test.jpg --W=416 --H=416 --class=9
	```
	
if you want batching, then run
	```sh
	./install/createEngine --caffemodel=./models/yolov3_traffic_final.caffemodel --prototxt=./models/yolov3_traffic_final.prototxt --input=./test/test.jpg --W=416 --H=416 --class=9 --batchsize=2
	```

This will create an engine file namely **yolov3_fp32.engine**.

Move this engine file into the models folder

### Adjust Config
__NOT IMPLEMENTED YET__

### Run 
Just run main.sh
	```sh
	./main.sh --engine=./models/yolov3_fp32.engine --pipe-path=/tmp/fifopipe1 --segment-path=./segments/test_cam/ --line-coord=./configs/line_coord/test_cam.json --intrinsics=./configs/cam_intrinsic/test_cam.json
	```

## Results
Soon to be out
---
## Authors/Maintainers
* Prajwal Rao - [prajwaljpj@gmail.com](mailto:prajwaljpj@gmail.com), [prajwalrao@iisc.ac.in](mailto:prajwalrao@iisc.ac.in)
* Sadgun Srinivas - [sadgun.srinivas@gmail.com](mailto:sadgun.srinivas@gmail.com), [sadguns@iisc.ac.in](mailto:sadguns@iisc.ac.in)
