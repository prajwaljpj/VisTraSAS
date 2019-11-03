```bash
ffmpeg -i "rtsp://<link-to-rtsp>" -framerate 25 -an -vcodec copy -f segment -segment_time 5 -reset_timestamps 0 -strftime 1 ./segments/<camera-name>/%Y-%m-%d-_%H.%M.%S.flv
```

files will be stored in this format

the latest file will be generated with this command
```sh
clang++ -std=c++11 -Os -Wall -pedantic -lboost_system -lboost_filesystem get_latest.cpp -o getlatest
```

(requires boost)
