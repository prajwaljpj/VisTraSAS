#include "get_latest.hpp"

struct vidFile {
  fs::path vidPath;
  std::time_t vidCreationTime;
};


// bool timeDiff(vidFile a, vidFile b){
//   double timedif = std::difftime(a.vidCreationTime, b.vidCreationTime);

//   if (timediff < 0) return false;
//   else return true;
// }

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
  // std::time_t latest_tm {};
  std::vector<vidFile> fVector;

  for (auto&& entry : boost::make_iterator_range(fs::directory_iterator(dirPath), {})) {
    vidFile dirFile;
    fs::path p = entry.path();
    dirFile.vidPath = p;
    dirFile.vidCreationTime = fs::last_write_time(p);
    fVector.push_back(dirFile);
  }

  if (fVector.empty()){
    // std::cout << "Nothing found\n";
    fs::path empty_path;
    return empty_path;
  }

  if (fVector.size()==1){
    // std::cout << "Vector size 1\n";
    fs::path empty_path;
    return empty_path;
  }

  std::sort(fVector.begin(), fVector.end(), [](vidFile a, vidFile b){return a.vidCreationTime < b.vidCreationTime;});
  // std::sort(fVector.begin(), fVector.end(), timeDiff());

  // for (std::vector<fs::path>::iterator it = fVector.begin(); it!=fVector.end(); ++it) {
  //   if (is_regular_file(it) && p.extension() == ".flv")
  //     {
  //       std::time_t timestamp = fs::last_write_time(p);
  //       if (timestamp > latest_tm) {
  //         latest = p;
  //         latest_tm = timestamp;
  //       }
  //     }
  // }
  // for (std::vector<vidFile>::iterator it = fVector.begin(); it!=fVector.end(); ++it) {
  //   std::cout << (*it).vidPath << std::endl;
  //   std::cout << (*it).vidCreationTime << std::endl;
  // }
  // for (int it = 0; it<fVector.size(); it++) {
  //   std::cout << it.vidPath.string() << std::endl;
  // }
  //std::cout << "Last modified: " << latest << "\n";
  // std::cout << "returning 2nd last element\n";
  // return fVector.end()[-2];
  return fVector[fVector.size()-2].vidPath;

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
