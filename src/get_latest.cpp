#include "get_latest.hpp"
fs::path latestFile(std::string dirPath){

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
    //std::cout << "Nothing found\n";
    return latest;
  }
  else{
    //std::cout << "Last modified: " << latest << "\n";
    return latest;
  }
}

fs::path secondLatestFile(std::string dirPath){

  fs::path latest;
  std::time_t latest_tm {};
  std::vector<fs::path> fVector;

  for (auto&& entry : boost::make_iterator_range(fs::directory_iterator(dirPath), {})) {
    fs::path p = entry.path();
    if (is_regular_file(p) && p.extension() == ".flv")
      {
        std::time_t timestamp = fs::last_write_time(p);
        if (timestamp > latest_tm) {
          latest = p;
          latest_tm = timestamp;
          fVector.push_back(p);
        }
      }
  }
  for (std::vector<fs::path>::iterator it = fVector.begin(); it!=fVector.end(); ++it) {
    std::cout << *it << std::endl;
  }
        if (latest.empty()){
          std::cout << "Nothing found\n";
          return latest;
        }
        else if (fVector.size()==1){
          std::cout << "Vector size 1\n";
          fs::path empty_path;
          return empty_path;
        }
        else{
          //std::cout << "Last modified: " << latest << "\n";
          std::cout << "returning 2nd last element\n";
          return fVector.end()[-2];
        }
}


void check_and_delete(std::string dirPath)
{
  typedef std::multimap<std::time_t, fs::path, std::greater <std::time_t>> result_set_t;
  result_set_t result_set;
  fs::directory_iterator end_iter;

  for(fs::directory_iterator dir_iter(dirPath); dir_iter != end_iter; ++dir_iter)
    {
      if (fs::is_regular_file(dir_iter->status()) )
	{
	  result_set.insert(result_set_t::value_type(fs::last_write_time(dir_iter->path()), *dir_iter));
	}
    }

  if (result_set.size() > 10)
    {
      int counter = 1;
      for (std::multimap<std::time_t, fs::path>::iterator it=result_set.begin(); it!=result_set.end(); ++it)
	{
	  if (counter < 4)
	    counter++;
	  else
	    fs::remove_all((*it).second);
	}	
    }
  return;
}
