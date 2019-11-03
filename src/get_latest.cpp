#include <iostream>
#include <vector>
#include <algorithm>
#include <iterator>
#include <boost/filesystem.hpp>
#include <boost/iterator/filter_iterator.hpp>
namespace fs = boost::filesystem;

int main()
{
  fs::path p("toydata/");
  fs::directory_iterator dir_first(p), dir_last;
  std::vector<fs::path> files;

  auto pred = [](const fs::directory_entry& p)
	      {
		return fs::is_regular_file(p);
	      };

  std::copy(boost::make_filter_iterator(pred, dir_first, dir_last),
	    boost::make_filter_iterator(pred, dir_last, dir_last),
	    std::back_inserter(files)
	    );

  std::sort(files.begin(), files.end(),
	    [](const fs::path& p1, const fs::path& p2)
	    {
	      return fs::last_write_time(p1) < fs::last_write_time(p2);
	    });
  std::cout << files[0] << std::endl;

}
