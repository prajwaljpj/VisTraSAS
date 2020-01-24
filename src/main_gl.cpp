#include "get_latest.hpp"

#include <sys/stat.h>
#include <sys/types.h>
#include <thread>
#include <chrono>

using namespace std;

int main(int argc, char** argv){

    string dir_path = argv[1];
    if (dir_path.empty())
        {
        cerr << "Directory does not exist" << endl;
        exit(EXIT_FAILURE);
        }
    while(1){
    fs::path second_latest_file = secondLatestFile(dir_path);
    if (second_latest_file.empty())
      {
        cout << "Waiting for initial files" << endl;
        this_thread::sleep_for (chrono::seconds(10));
        continue;
      }
    string lat_file_path = second_latest_file.string();
    string lat_file_name = second_latest_file.filename().string();
    cout << "The second latest file is :::::: " << lat_file_name << endl;
    this_thread::sleep_for (chrono::seconds(10));
    }
}
