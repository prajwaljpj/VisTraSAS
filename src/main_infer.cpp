#include "inference.hpp"
#include "get_latest.hpp"

#include <iostream>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <string.h>
#include <thread>
#include <chrono>
#include "opencv2/opencv.hpp"

using namespace std;

int main(int argc, char** argv)
{ 
  if (argc < 4)
    return -1;
  string enginename = argv[1];
  Inference iff;
  iff.loadTRTModel(enginename);
  int fd;
  string named_pipe = argv[2];
  const char* myfifo = named_pipe.c_str();
  mkfifo(myfifo, 0666);
  fd = open(myfifo, O_WRONLY);

  while (1) {
    string dir_path = argv[3];
    fs::path latest_file = latestFile(dir_path);
    string lat_file_path = latest_file.string();
    // TODO get parent file path
    string lat_file_name = latest_file.filename().string();
    cout << "latest_file_path " << lat_file_path << endl;
    cout << "latest_file_name " << lat_file_name << endl;
    // TODO Send character length of file with folder
    // TODO send second video file path
    // TODO get two video capture objs
    cv::VideoCapture cap(lat_file_path);
    cout << "videocap success" << endl;
    // TODO double frame number and frame number handling
    int frame_num = 0;
    if(!cap.isOpened()){
      cout << "C++ side ::::::::: Error opening video stream or file" << endl;
      continue;
      
    }
    cout << "before strcpy" << endl;
    char* lat_fil_cstr = new char[lat_file_name.length()+1];
    strcpy(lat_fil_cstr, lat_file_name.c_str());
    cout << "latest file strcpy :: " << lat_fil_cstr << endl;
    cout << "latest file len :: " << strlen(lat_fil_cstr) << endl;
    // TODO sending latest files with its folder paths
    write(fd, lat_fil_cstr, strlen(lat_fil_cstr)+1);
    // TODO separate delete process running for both folders (IMPORTANT)
    delete [] lat_fil_cstr;
    while(1){
      auto start = chrono::high_resolution_clock::now();
      // TODO read both frames
      cv::Mat frame;
      cap >> frame;
  
      if (frame.empty())
	// TODO process single file with dual frame input
	break; 

      frame_num++;
      
      // TODO add inference of batch 2 and its corresponding files
      vector<Bbox> op1 = iff.infer_single_image(frame);
      frame.release();

      if (op1.empty())
	{
	  char delim_char = (unsigned char) 0;
	  cout << "delim :: number :: " << op1.size() << endl;
	  cout << "delim :: sizeof :: " << sizeof(delim_char) << endl;
	  write(fd, &delim_char, sizeof(delim_char));
	  continue;
	}

      char delim_char = (unsigned char) op1.size();
      write(fd, &delim_char, sizeof(delim_char));
	
      for(const auto& item : op1)  
	{

	  unsigned char* box = const_cast<unsigned char*>(reinterpret_cast<const unsigned char*>(&item));
	  write(fd, box, sizeof(item));
	  
	}
      auto stop = chrono::high_resolution_clock::now();
      auto duration = chrono::duration_cast<chrono::milliseconds>(stop - start);
      cout << "Duration for complete C++ side yolo inference : " << duration.count() << "ms" << endl;
    }
    check_and_delete(dir_path);

    }
  close(fd);
  unlink(myfifo);
  return 0;

}
