#include <iostream>
#include <string>
#include <map>
#include <boost/filesystem.hpp>
#include <boost/range.hpp>

namespace fs = boost::filesystem;

fs::path latestFile(std::string dirPath);
fs::path secondLatestFile(std::string dirPath);
void check_and_delete(std::string dirPath);
