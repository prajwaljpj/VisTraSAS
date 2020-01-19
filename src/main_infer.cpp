#include "inference.hpp"
#include "get_latest.hpp"

#include <iostream>
#include <fstream>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <string.h>
#include <thread>
#include <chrono>
#include <errno.h>
#include "opencv2/opencv.hpp"

using namespace std;

bool writeStatus(const char* statFifo, const char* writeData, size_t dataSize){
  int statusVal;
  bool success=false;
  statusVal = open(statFifo, O_WRONLY);
  if(statusVal==-1){
    cerr << "Failed to establish Pipe connection" << endl;
    exit(EXIT_FAILURE);
  }
  int initWr = write(statFifo, &writeData, dataSize);
  if (initWr==-1){
    cerr << "failed to read Pipe Value" << endl;
    exit(EXIT_FAILURE);
  }
  success=true;
  return success;
}

bool readStatus(const char* statFifo, int readSize){
  int statusVal;
  bool success=false;
  const char* readData[readSize];
  statusVal = open(statFifo, O_RDONLY);
  if(statusVal==-1){
    cerr << "Failed to establish Pipe connection" << endl;
    exit(EXIT_FAILURE);
  }
  int initRd = read(statFifo, &readData, readSize);
  if (initRd==-1){
    cerr << "failed to read Pipe Value" << endl;
    exit(EXIT_FAILURE);
  }
  if((int)readData==1)
    success=true;
  else if ((int)readData==0)
    success=false;
  else {
    cout << "CRITICAL ERROR:: READ DATA NON BINARY" << endl;
    exit(EXIT_FAILURE);
    }
  return success;
}

int main(int argc, char** argv)
{ 
  ofstream logfile;
  logfile.open("logfile.log");
  if (argc < 4)
    return -1;
  string enginename = argv[1];
  if (enginename.empty())
    {
      cerr << "Invalid Engine Name" << endl;
      exit(EXIT_FAILURE);
    }
  Inference iff;
  if (!iff.loadTRTModel(enginename)) {
    cerr << "Failed to load engine file" << endl;
    exit(EXIT_FAILURE);
  }
  
  int fd;
  string named_pipe = argv[2];
  if (named_pipe.empty())
    {
      cerr << "Invalid PIPE Name" << endl;
      exit(EXIT_FAILURE);
    }
  string sig_pipe = named_pipe + "_rev";
  if (sig_pipe.empty())
    {
      cerr << "Invalid PIPE Name" << endl;
      exit(EXIT_FAILURE);
    }
  const char* myfifo = named_pipe.c_str();
  const char* myfifo_rev = sig_pipe.c_str();
  chrono::time_point<chrono::high_resolution_clock> timenow = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now()); 
  cout << "Created FIFO at " << timenow.time_since_epoch().count() << endl;
  logfile << "Created FIFO at " << timenow.time_since_epoch().count() << endl;
  mkfifo(myfifo, 0666);
  // fd = open(myfifo, O_WRONLY);
  // if (fd==-1) {
  //   cerr << "Failed to establish Pipe connection" << endl;
  //   exit(EXIT_FAILURE);
  // }
  string dir_path = argv[3];
  if (dir_path.empty())
    {
      cerr << "Directory does not exist" << endl;
      exit(EXIT_FAILURE);
    }

  string previous_file;

  while (1) {
    fs::path latest_file = latestFile(dir_path);
    if (latest_file.empty())
      {
        //cerr << "Waiting for initial files" << endl;
        continue;
      }
    string lat_file_path = latest_file.string();
    string lat_file_name = latest_file.filename().string();

    if (lat_file_name.compare(previous_file)==0)
    // if (lat_file_name.compare(previous_file))
    {
       continue;
    }
    else{
        cout << "files are not the same, previous file is diff from lat_file" << endl;
        logfile << "files are not the same, previous file is diff from lat_file" << endl;
        previous_file = lat_file_name;
    }
    cv::VideoCapture cap(lat_file_path);
    //cout << "videocap success" << endl;
    int frame_num = 0;
    if(!cap.isOpened()){
      //cout << "C++ side ::::::::: Error opening video stream or file" << endl;
      continue;
    }
    char* lat_fil_cstr = new char[lat_file_name.length()];
    strcpy(lat_fil_cstr, lat_file_name.c_str());
    cout << "latest file strcpy :: " << lat_fil_cstr << endl;
    logfile << "latest file strcpy :: " << lat_fil_cstr << endl;
    cout << "latest file len :: " << strlen(lat_fil_cstr) << endl;
    logfile << "latest file len :: " << strlen(lat_fil_cstr) << endl;
    // changes made by prajwal
    fd = open(myfifo, O_WRONLY);
    if (fd==-1) {
      cerr << "Failed to establish Pipe connection" << endl;
      exit(EXIT_FAILURE);
    }
    auto filename_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now()); 
    cout << "Writing File at " << filename_time.time_since_epoch().count() << endl;
    logfile << "Writing File at " << filename_time.time_since_epoch().count() << endl;
    int w_success = write(fd, lat_fil_cstr, strlen(lat_fil_cstr));
    if (w_success < 0){
        cout << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE filename FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
        cout << strerror(errno);
        logfile << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE filename FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
        logfile << strerror(errno);
    }
    close(fd);
    delete [] lat_fil_cstr;
    auto frame_number = 1;
    while(1){
      cout << "FRAME NUMBER C++ == " << frame_number << endl;
      logfile << "FRAME NUMBER C++ == " << frame_number << endl;
      frame_number++;
      auto start = chrono::high_resolution_clock::now();
      cv::Mat frame;
      cap >> frame;
      if (frame_number-1 <= 20) {
          std::ostringstream name;
          name << "~/home/rbccps/saved_frames/cpp_frame_" << frame_number-1<<".jpg";
      cv::imwrite(name.str(), frame);
      }
      if (frame.empty()){
        cout << "the loop broke at frame " << frame_number-1 << endl;
        logfile << "the loop broke at frame " << frame_number-1 << endl;
	    break;
      }
      frame_num++;
      //vector<Bbox> op1 = iff.infer_single_image(frame);
      vector<Bbox> op1;
      try
      {
      	op1 = iff.infer_single_image(frame);
      }
      catch (exception &e)
      {
            char delim_char = (unsigned char) 0;
            cout << "delim :: number :: " << op1.size() << endl;
            logfile << "delim :: number :: " << op1.size() << endl;
            cout << "delim :: sizeof :: " << sizeof(delim_char) << endl;
            logfile << "delim :: sizeof :: " << sizeof(delim_char) << endl;
            fd = open(myfifo, O_WRONLY);
            if (fd==-1) {
              cerr << "Failed to establish Pipe connection" << endl;
              exit(EXIT_FAILURE);
            }
            auto headni_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now()); 
            cout << "Header when no infer written at " << headni_time.time_since_epoch().count() << endl;
            logfile << "Header when no infer written at " << headni_time.time_since_epoch().count() << endl;
            int headni_succ = write(fd, &delim_char, sizeof(delim_char));
            if (headni_succ < 0){
                cout << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE head FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
                cout << strerror(errno);
                logfile << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE head FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
                logfile << strerror(errno);
            }
            close(fd);
            //cout << "delim :: sizeof :: " << sizeof(delim_char) << endl;
            continue;
      }
      frame.release();

      if (op1.empty())
	    {
	      char delim_char = (unsigned char) 0;
	      cout << "delim :: number :: " << op1.size() << endl;
	      logfile << "delim :: number :: " << op1.size() << endl;
          // cout << "delim :: VALUE ::$$$  "<< delim_char << endl;
          // logfile << "delim :: VALUE ::$$$  "<< delim_char << endl;
	      cout << "delim :: sizeof :: " << sizeof(delim_char) << endl;
	      logfile << "delim :: sizeof :: " << sizeof(delim_char) << endl;
          fd = open(myfifo, O_WRONLY);
          if (fd==-1) {
            cerr << "Failed to establish Pipe connection" << endl;
            exit(EXIT_FAILURE);
          }
          auto headz_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now()); 
          cout << "Header when zero written at " << headz_time.time_since_epoch().count() << endl;
          logfile << "Header when zero written at " << headz_time.time_since_epoch().count() << endl;
	      int hz_succ = write(fd, &delim_char, sizeof(delim_char));
          if (hz_succ < 0){
              cout << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE head FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
              cout << strerror(errno);
              logfile << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE head FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
              logfile << strerror(errno);
          }
          close(fd);
	      //cout << "delim :: sizeof :: " << sizeof(delim_char) << endl;
	      continue;
	    }
      char delim_char = (unsigned char) op1.size();
      //cout << "LOOP STARTED before write::::::::::::"<< delim_char<<endl;
      cout << "delim :: VALUE ::$$$  "<< op1.size() << endl;
      logfile << "delim :: VALUE ::$$$  "<< op1.size() << endl;
      // cout << "delim :: VALUE ::$$$  "<< delim_char << endl;
      // logfile << "delim :: VALUE ::$$$  "<< delim_char << endl;
      cout << "delim :: sizeof :: "<< sizeof(delim_char) << endl;
      logfile << "delim :: sizeof :: "<< sizeof(delim_char) << endl;
      fd = open(myfifo, O_WRONLY);
      if (fd==-1) {
        cerr << "Failed to establish Pipe connection" << endl;
        exit(EXIT_FAILURE);
      }

      auto head_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now()); 
      cout << "Header written at " << head_time.time_since_epoch().count() << endl;
      logfile << "Header written at " << head_time.time_since_epoch().count() << endl;
      int head_succ = write(fd, &delim_char, sizeof(delim_char));
      if (head_succ < 0){
          cout << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE head FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
          cout << strerror(errno);
          logfile << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE head FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
          logfile << strerror(errno);
      }
      close(fd);
      //cout << "LOOP STARTED FRAME after write::::::::::::"<< endl;
	  auto iterm=1;
      for(const auto& item : op1)  
	{
      this_thread::sleep_for(chrono::milliseconds(100));
      cout << "iterm ^^+++^^ :: " << iterm << endl;
      logfile << "iterm ^^+++^^ :: " << iterm << endl;
      iterm++;
	  unsigned char* box = const_cast<unsigned char*>(reinterpret_cast<const unsigned char*>(&item));
      cout << "box size :: " << sizeof(box) << endl;
      logfile << "box size :: " << sizeof(box) << endl;
      cout << "item size :: " << sizeof(item) << endl;
      logfile << "item size :: " << sizeof(item) << endl;
      cout << "class=" << item.classId << " prob=" << item.score*100 << endl;
      logfile << "class=" << item.classId << " prob=" << item.score*100 << endl;
      cout << "left=" << item.left << " right=" << item.right << " top=" << item.top << " bot=" << item.bot << endl;
      logfile << "left=" << item.left << " right=" << item.right << " top=" << item.top << " bot=" << item.bot << endl;
      fd = open(myfifo, O_WRONLY);
      if (fd==-1) {
        cerr << "Failed to establish Pipe connection" << endl;
        exit(EXIT_FAILURE);
      }
      auto bbox_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now()); 
      cout << "BBOX write time at " << bbox_time.time_since_epoch().count() << endl;
      logfile << "BBOX write time at " << bbox_time.time_since_epoch().count() << endl;
      int box_succ = write(fd, box, sizeof(item));
      if (box_succ < 0){
          cout << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE head FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
          cout << strerror(errno);
          logfile << "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ WRITE head FAILED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" << endl;
          logfile << strerror(errno);
      }
	  //write(fd, box, sizeof(box));
      close(fd);

	}
      auto stop = chrono::high_resolution_clock::now();
      auto duration = chrono::duration_cast<chrono::milliseconds>(stop - start);
      //cout << "Duration for complete C++ side yolo inference : " << duration.count() << "ms" << endl;
    }
    check_and_delete(dir_path);
    cap.release();
  }
  // close(fd);
    unlink(myfifo);
    logfile.close();
    return 0;

}
