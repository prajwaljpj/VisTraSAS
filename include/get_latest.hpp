#include <iostream>
#include <string>
#include <map>
#include <boost/filesystem.hpp>
#include <boost/range.hpp>

namespace fs = boost::filesystem;

std::string latestFile(std::string dirPath);
void check_and_delete(std::string dirPath);