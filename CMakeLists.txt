cmake_minimum_required(VERSION 2.8)
project(demo)

set(CMAKE_BUILD_TYPE Release)
# set(CMAKE_BUILD_TYPE Debug)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -Wall -Ofast -Wfatal-errors")

#add python
FIND_PACKAGE(PythonInterp 3)
FIND_PACKAGE(PythonLibs 3)

#add wrapper
set(TRT_WRAPPER_DIR ${CMAKE_CURRENT_SOURCE_DIR}/tensorRTWrapper/code)
add_subdirectory(${TRT_WRAPPER_DIR})
include_directories(${TRT_WRAPPER_DIR}/include)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)
set(SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src)

#add opencv
FIND_PACKAGE(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})
link_directories(${OpenCV_LIBRARIES_DIRS})

# find and set Boost packages
set(Boost_USE_STATIC_LIBS ON) 
set(Boost_USE_MULTITHREADED ON)  
set(Boost_USE_STATIC_RUNTIME OFF) 
find_package(Boost REQUIRED COMPONENTS system filesystem) 

# Build our library
#add_library( yolotrt SHARED inference.cpp eval.cpp dataReader.cpp)

# Define the wrapper library that wraps our library
#add_library( yolotrt_ext SHARED inference_ext.cpp )

#target_link_libraries( yolotrt_ext ${Boost_LIBRARIES} yolotrt )
# don't prepend wrapper library name with lib
#set_target_properties( yolotrt_ext PROPERTIES PREFIX "" )


#build runYolov3
add_executable(runYolov3 ${SOURCE_DIR}/main_infer.cpp ${SOURCE_DIR}/inference.cpp ${SOURCE_DIR}/eval.cpp ${SOURCE_DIR}/dataReader.cpp ${SOURCE_DIR}/get_latest.cpp)
target_link_libraries(runYolov3 TrtNet ${OpenCV_LIBS})
# link boost libraries 
if(Boost_FOUND)
    include_directories(${Boost_INCLUDE_DIRS}) 
    target_link_libraries(runYolov3 ${Boost_FILESYSTEM_LIBRARY} ${Boost_SYSTEM_LIBRARY})
endif()

install(TARGETS runYolov3 DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install/)

#build createEngine
add_executable(createEngine ${SOURCE_DIR}/main.cpp ${SOURCE_DIR}/inference.cpp ${SOURCE_DIR}/eval.cpp ${SOURCE_DIR}/dataReader.cpp)
target_link_libraries(createEngine TrtNet ${OpenCV_LIBS})

install(TARGETS createEngine DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install/)
