// #include <boost/python.hpp>
#include <opencv2/opencv.hpp>
#include "TrtNet.h"
/* #include "argsParser.h" */
#include "configs.h"
#include <chrono>
#include "YoloLayer.h"
#include "dataReader.h"
#include "eval.h"
#include <memory>

using namespace std;
/* using namespace argsParser; */
using namespace Tn;
using namespace Yolo;


class Inference
{
    public:

        Inference(){ cout << "Class object created\n";}

        /* list<vector<Bbox>> outputs; */
        float nmsThresh = 0.45;
        int batchSize = 1;
        int classNum = 9;
        int c = 3;
        int h = 416;
        int w = 416;
        int batchCount = 0;
        /* int outputCount; */
        /* unique_ptr<float[]> outputData; */
        std::unique_ptr<trtNet> net;
        vector<float> inputData;
        /* inputData.reserve(h*w*c*batchSize); */
        vector<cv::Mat> inputImgs;
        vector<float> prepareImage(cv::Mat& img);
        void DoNms(vector<Detection>& detections,int classes ,float nmsThresh);
        vector<Bbox> postProcessImg(cv::Mat& img,vector<Detection>& detections,int classes);
        vector<string> split(const string& str, char delim);
        bool loadTRTModel(string netname);
        std::list<vector<Bbox>> infer(vector<cv::Mat> image);
        vector<Bbox> infer_single_image(cv::Mat image);

};


#if 0
using namespace boost::python;

BOOST_PYTHON_MODULE(inference)
{
    /* std::list<vector<Bbox>>(inference::*in1)(vector<cv::Mat>) = &inference::infer; */
    /* std::list<vector<Bbox>>(inference::*in2)(cv::Mat) = &inference::infer; */

    class_<Inference, Inference*, boost::noncopyable>("Inference", boost::python::no_init)
        .def("doNMS", &Inference::DoNms)
        .def("postprocessimg", &Inference::postProcessImg)
        .def("prepareimg", &Inference::prepareImage)
        .def("split", &Inference::split)
        .def("load_trt", &Inference::loadTRTModel)
        .def("infer", &Inference::infer)
        .def("infer_single_image", &Inference::infer_single_image)
        ;

    /* class_<World>("World", init<std::string>()) */
    /*     .def("print", &World::print) */
    /*     ; */
};

/* vector<float> inference::prepareImage(cv::Mat& img); */
/* void inference::DoNms(vector<Detection>& detections,int classes ,float nmsThresh); */
/* vector<Bbox> inference::postProcessImg(cv::Mat& img,vector<Detection>& detections,int classes); */
/* vector<string> inference::split(const string& str, char delim); */
/* bool inference::loadTRTModel(string netname, int batchSize); */
/* list<vector<Bbox>> inference::infer(vector<cv2::Mat> image) */

/*template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}*/
#endif
