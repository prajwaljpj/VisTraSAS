#include <iostream>
#include <boost/filesystem.hpp>
#include <boost/range.hpp>

namespace fs = boost::filesystem;

std::string latestFile(std::string dirPath);