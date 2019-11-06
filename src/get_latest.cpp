#include "get_latest.hpp"

std::string latestFile(std::string dirPath){

  fs::path latest;
  std::time_t latest_tm {};

  for (auto&& entry : boost::make_iterator_range(fs::directory_iterator(dirPath), {})) {
    fs::path p = entry.path();
    if (is_regular_file(p) && p.extension() == ".flv") 
      {
	std::time_t timestamp = fs::last_write_time(p);
	if (timestamp > latest_tm) {
	  latest = p;
	  latest_tm = timestamp;
	}
      }
  }
  if (latest.empty()){
    std::cout << "Nothing found\n";
    return "NOFILE";
  }
  else{
    std::cout << "Last modified: " << latest << "\n";
    return latest.string();
  }
}
