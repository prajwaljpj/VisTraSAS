#include "inference.hpp"
#include "get_latest.hpp"

#include <iostream>
#include <fstream>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <string.h>
#include <vector>
#include <thread>
#include <chrono>
#include <errno.h>
#include "opencv2/opencv.hpp"

using namespace std;


void tokenize(string &str, const char delim,
              vector<string> &out)
{
  size_t start;
  size_t end = 0;

  while ((start = str.find_first_not_of(delim, end)) != string::npos)
  {
    end = str.find(delim, start);
    out.push_back(str.substr(start, end - start));
  }
}

bool writeStatus(const char* statFifo, const char* writeData, size_t dataSize){
  int statusVal;
  bool success=false;
  statusVal = open(statFifo, O_WRONLY);
  if(statusVal==-1){
    cerr << "Failed to establish Pipe connection" << endl;
    exit(EXIT_FAILURE);
  }
  int initWr = write(statusVal, writeData, dataSize);
  if (initWr==-1){
    cerr << "failed to read Pipe Value" << endl;
    exit(EXIT_FAILURE);
  }
  close(statusVal);
  success=true;
  return success;
}

bool writeStatus(const char* statFifo, unsigned char* writeData, size_t dataSize){
  int statusVal;
  bool success=false;
  statusVal = open(statFifo, O_WRONLY);
  if(statusVal==-1){
    cerr << "Failed to establish Pipe connection" << endl;
    exit(EXIT_FAILURE);
  }
  int initWr = write(statusVal, writeData, dataSize);
  if (initWr==-1){
    cerr << "failed to read Pipe Value" << endl;
    exit(EXIT_FAILURE);
  }
  close(statusVal);
  success=true;
  return success;
}

bool readStatus(const char* statFifo){
  int statusVal;
  bool success=false;
  unsigned char readData;
  statusVal = open(statFifo, O_RDONLY);
  if(statusVal==-1){
    cerr << "Failed to establish Pipe connection" << endl;
    exit(EXIT_FAILURE);
  }
  int initRd = read(statusVal, &readData, 1);
  if (initRd==-1){
    cerr << "failed to read Pipe Value" << endl;
    exit(EXIT_FAILURE);
  }
  close(statusVal);
  if(readData=='1')
    success=true;
  else if (readData=='0')
    success=false;
  else {
    exit(EXIT_FAILURE);
    }
  return success;
}

int main(int argc, char** argv)
{ 
  ofstream logfile;
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
  
  string named_pipe = argv[2];
  vector<string> named_pipe_split;
  tokenize(named_pipe, '/', named_pipe_split);
  logfile.open("logs/clogfile_"+named_pipe_split.end()[-1]+".log");
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
  chrono::time_point<chrono::high_resolution_clock> timenow = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now());
  logfile << "Created FIFO at " << timenow.time_since_epoch().count() << endl;
  mkfifo(myfifo, 0666);
  string dir_path = argv[3];
  if (dir_path.empty())
    {
      cerr << "Directory does not exist" << endl;
      exit(EXIT_FAILURE);
    }

  string previous_file;

  while (1) {
    fs::path latest_file = secondLatestFile(dir_path);
    if (latest_file.empty())
      {
        continue;
      }
    string lat_file_path = latest_file.string();
    string lat_file_name = latest_file.filename().string();

    if (lat_file_name.compare(previous_file)==0)
    {
       continue;
    }
    else{
        logfile << "files are not the same, previous file is diff from lat_file" << endl;
        previous_file = lat_file_name;
    }

    char* lat_fil_cstr = new char[lat_file_name.length()];
    strcpy(lat_fil_cstr, lat_file_name.c_str());
    logfile << "latest file strcpy :: " << lat_fil_cstr << endl;
    logfile << "latest file len :: " << strlen(lat_fil_cstr) << endl;
    auto filename_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now());
    logfile << "Writing File at " << filename_time.time_since_epoch().count() << endl;
    (void)writeStatus(myfifo, lat_fil_cstr, strlen(lat_fil_cstr));
    bool fileReadCorrectStat = readStatus(myfifo);
    logfile << "CPP LOG ## File read status ::::" << fileReadCorrectStat << endl;
    if (!fileReadCorrectStat) {
      exit(EXIT_FAILURE);
    }
    cv::VideoCapture cap(lat_file_path);
    int frame_num = 0;
    if(!cap.isOpened()){
      continue;
    }
    delete [] lat_fil_cstr;
    auto frame_number = 1;
    auto empty_frame_counter = 0;
    while(1){
      logfile << "FRAME NUMBER C++ == " << frame_number << endl;
      frame_number++;
      auto start = chrono::high_resolution_clock::now();
      cv::Mat frame;
      cap >> frame;
      if (frame.empty()){
        logfile << "the loop broke at frame " << frame_number-1 << endl;
        empty_frame_counter++;
        break;
      }
      frame_num++;
      vector<Bbox> op1;
      try
      {
      	op1 = iff.infer_single_image(frame);
      }
      catch (exception &e)
      {
            char delim_char = (unsigned char) 0;
            logfile << "delim :: number :: " << op1.size() << endl;
            logfile << "delim :: sizeof :: " << sizeof(delim_char) << endl;
            auto headni_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now());
            logfile << "Header when no infer written at " << headni_time.time_since_epoch().count() << endl;
            (void)writeStatus(myfifo, &delim_char, sizeof(delim_char));
            bool headniReadCorrectStat = readStatus(myfifo);
            logfile << "CPP LOG ## Header no infer read status ::::" << headniReadCorrectStat << endl;
            if (!headniReadCorrectStat) {
              exit(EXIT_FAILURE);
            }
            continue;
      }
      frame.release();

      if (op1.empty())
      {
        char delim_char = (unsigned char) 0;
        logfile << "delim :: number :: " << op1.size() << endl;
        logfile << "delim :: sizeof :: " << sizeof(delim_char) << endl;
        auto headz_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now());
        logfile << "Header when zero written at " << headz_time.time_since_epoch().count() << endl;
        (void)writeStatus(myfifo, &delim_char, sizeof(delim_char));
        bool headzReadCorrectStat = readStatus(myfifo);
        logfile << "CPP LOG ## Header zero read status ::::" << headzReadCorrectStat << endl;
        if (!headzReadCorrectStat) {
          exit(EXIT_FAILURE);
        }
        continue;
      }
      char delim_char = (unsigned char) op1.size();
      logfile << "delim :: VALUE ::$$$  "<< op1.size() << endl;
      logfile << "delim :: sizeof :: "<< sizeof(delim_char) << endl;
      auto head_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now());
      logfile << "Header written at " << head_time.time_since_epoch().count() << endl;
      (void)writeStatus(myfifo, &delim_char, sizeof(delim_char));
      bool headReadCorrectStat = readStatus(myfifo);
      logfile << "CPP LOG ## Header read status ::::" << headReadCorrectStat << endl;
      if (!headReadCorrectStat) {
        exit(EXIT_FAILURE);
      }
      auto iterm=1;
      for(const auto& item : op1)  
        {
      logfile << "iterm ^^+++^^ :: " << iterm << endl;
      iterm++;
      unsigned char* box = const_cast<unsigned char*>(reinterpret_cast<const unsigned char*>(&item));
      logfile << "box size :: " << sizeof(box) << endl;
      logfile << "item size :: " << sizeof(item) << endl;
      logfile << "class=" << item.classId << " prob=" << item.score*100 << endl;
      logfile << "left=" << item.left << " right=" << item.right << " top=" << item.top << " bot=" << item.bot << endl;
      auto bbox_time = chrono::time_point_cast<chrono::milliseconds>(chrono::high_resolution_clock::now());
      logfile << "BBOX write time at " << bbox_time.time_since_epoch().count() << endl;
      (void)writeStatus(myfifo, box, sizeof(item));
      bool bboxReadCorrectStat = readStatus(myfifo);
      logfile << "CPP LOG ## BBOX read status ::::" << bboxReadCorrectStat << endl;
      if (!bboxReadCorrectStat) {
        exit(EXIT_FAILURE);
      }
        }
      auto stop = chrono::high_resolution_clock::now();
      auto duration = chrono::duration_cast<chrono::milliseconds>(stop - start);
    }
    // check_and_delete(dir_path);
    cap.release();
  }
    unlink(myfifo);
    logfile.close();
    return 0;

}
