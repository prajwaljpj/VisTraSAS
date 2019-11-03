/* #include <boost/python.hpp> */
#include "inference.hpp"


vector<float> Inference::prepareImage(cv::Mat& img)
{
    using namespace cv;

    /* int c = parser::getIntValue("C"); */
    /* int h = parser::getIntValue("H");   //net h */
    /* int w = parser::getIntValue("W");   //net w */

    float scale = min(float(w)/img.cols,float(h)/img.rows);
    auto scaleSize = cv::Size(img.cols * scale,img.rows * scale);

    cv::Mat rgb ;
    cv::cvtColor(img, rgb, CV_BGR2RGB);
    cv::Mat resized;
    cv::resize(rgb, resized,scaleSize,0,0,INTER_CUBIC);

    cv::Mat cropped(h, w,CV_8UC3, 127);
    Rect rect((w- scaleSize.width)/2, (h-scaleSize.height)/2, scaleSize.width,scaleSize.height); 
    resized.copyTo(cropped(rect));

    cv::Mat img_float;
    if (c == 3)
        cropped.convertTo(img_float, CV_32FC3, 1/255.0);
    else
        cropped.convertTo(img_float, CV_32FC1 ,1/255.0);

    //HWC TO CHW
    vector<Mat> input_channels(c);
    cv::split(img_float, input_channels);

    vector<float> result(h*w*c);
    auto data = result.data();
    int channelLength = h * w;
    for (int i = 0; i < c; ++i) {
        memcpy(data,input_channels[i].data,channelLength*sizeof(float));
        data += channelLength;
    }

    return result;
}

void Inference::DoNms(vector<Detection>& detections,int classes ,float nmsThresh)
{
    auto t_start = chrono::high_resolution_clock::now();

    vector<vector<Detection>> resClass;
    resClass.resize(classes);

    for (const auto& item : detections)
        resClass[item.classId].push_back(item);

    auto iouCompute = [](float * lbox, float* rbox)
    {
        float interBox[] = {
            max(lbox[0] - lbox[2]/2.f , rbox[0] - rbox[2]/2.f), //left
            min(lbox[0] + lbox[2]/2.f , rbox[0] + rbox[2]/2.f), //right
            max(lbox[1] - lbox[3]/2.f , rbox[1] - rbox[3]/2.f), //top
            min(lbox[1] + lbox[3]/2.f , rbox[1] + rbox[3]/2.f), //bottom
        };
        
        if(interBox[2] > interBox[3] || interBox[0] > interBox[1])
            return 0.0f;

        float interBoxS =(interBox[1]-interBox[0])*(interBox[3]-interBox[2]);
        return interBoxS/(lbox[2]*lbox[3] + rbox[2]*rbox[3] -interBoxS);
    };

    vector<Detection> result;
    for (int i = 0;i<classes;++i)
    {
        auto& dets =resClass[i]; 
        if(dets.size() == 0)
            continue;

        sort(dets.begin(),dets.end(),[=](const Detection& left,const Detection& right){
            return left.prob > right.prob;
        });

        for (unsigned int m = 0;m < dets.size() ; ++m)
        {
            auto& item = dets[m];
            result.push_back(item);
            for(unsigned int n = m + 1;n < dets.size() ; ++n)
            {
                if (iouCompute(item.bbox,dets[n].bbox) > nmsThresh)
                {
                    dets.erase(dets.begin()+n);
                    --n;
                }
            }
        }
    }

    //swap(detections,result);
    detections = move(result);

    auto t_end = chrono::high_resolution_clock::now();
    float total = chrono::duration<float, milli>(t_end - t_start).count();
    cout << "Time taken for nms is " << total << " ms." << endl;
}


vector<Bbox> Inference::postProcessImg(cv::Mat& img,vector<Detection>& detections,int classes)
{
    using namespace cv;

    /* int h = parser::getIntValue("H");   //net h */
    /* int w = parser::getIntValue("W");   //net w */

    //scale bbox to img
    int width = img.cols;
    int height = img.rows;
    float scale = min(float(w)/width,float(h)/height);
    float scaleSize[] = {width * scale,height * scale};

    //correct box
    for (auto& item : detections)
    {
        auto& bbox = item.bbox;
        bbox[0] = (bbox[0] * w - (w - scaleSize[0])/2.f) / scaleSize[0];
        bbox[1] = (bbox[1] * h - (h - scaleSize[1])/2.f) / scaleSize[1];
        bbox[2] /= scaleSize[0];
        bbox[3] /= scaleSize[1];
    }
    
    //nms
    /* float nmsThresh = parser::getFloatValue("nms"); */
    if(nmsThresh > 0) 
        DoNms(detections,classes,nmsThresh);

    vector<Bbox> boxes;
    for(const auto& item : detections)
    {
        auto& b = item.bbox;
        Bbox bbox = 
        { 
            item.classId,   //classId
            max(int((b[0]-b[2]/2.)*width),0), //left
            min(int((b[0]+b[2]/2.)*width),width), //right
            max(int((b[1]-b[3]/2.)*height),0), //top
            min(int((b[1]+b[3]/2.)*height),height), //bot
            item.prob       //score
        };
        boxes.push_back(bbox);
    }

    return boxes;
}

vector<string> Inference::split(const string& str, char delim)
{
    stringstream ss(str);
    string token;
    vector<string> container;
    while (getline(ss, token, delim)) {
        container.push_back(token);
    }

    return container;
}

bool Inference::loadTRTModel(string netname)
{

    // cout << "Enter loadTRTModel function \n";

    if (netname.length() > 0){
        net.reset(new trtNet(netname));
        assert(net->getBatchSize() == batchSize);
    }
    else 
      cerr << "no net present";
    return false;
    /* outputCount = net->getOutputSize()/sizeof(float); */
    /* outputData = make_unique<float[]>(outputCount); */
    return true;
}

std::list<vector<Bbox>> Inference::infer(vector<cv::Mat> image)
{
    std::list<vector<Bbox>> outputs;
    int outputCount;
    outputCount = net->getOutputSize()/sizeof(float);
    unique_ptr<float[]> outputData(new float[outputCount]);
    inputData.reserve(h*w*c*batchSize);
    for (auto r = 0; r<image.size(); r++)
    {
        vector<float> curInput = prepareImage(image[r]);
        if (!curInput.data())
            continue;
        inputImgs.emplace_back(image[r]);

        inputData.insert(inputData.end(), curInput.begin(), curInput.end());
        batchCount++;

        if(batchCount < batchSize && r + 1 <  image.size())
            continue;

        net->doInference(inputData.data(), outputData.get(),batchCount);

        //Get Output    
        auto output = outputData.get();
        auto outputSize = net->getOutputSize()/ sizeof(float) / batchCount;
        for(int i = 0;i< batchCount ; ++i)
        {    
        //first detect count
            int detCount = output[0];
        //later detect result
        vector<Detection> result;
            result.resize(detCount);
            memcpy(result.data(), &output[1], detCount*sizeof(Detection));

            auto boxes = postProcessImg(inputImgs[i],result,classNum);
        outputs.emplace_back(boxes);

            output += outputSize;
        }
        inputImgs.clear();
        inputData.clear();

        batchCount = 0;
    }
    return outputs;
}

vector<Bbox> Inference::infer_single_image(cv::Mat image)
{
    vector<Bbox> outputs;
    int outputCount;
    vector<Bbox> fail_case;
    outputCount = net->getOutputSize()/sizeof(float);
    unique_ptr<float[]> outputData(new float[outputCount]);
    inputData.reserve(h*w*c*batchSize);
    vector<float> curInput = prepareImage(image);
    if (!curInput.data())
    {
        cerr << "No input data" << endl;
        return fail_case;
        /* exit(EXIT_FAILURE) */
    }
    inputImgs.emplace_back(image);

    inputData.insert(inputData.end(), curInput.begin(), curInput.end());
    batchCount++;

    if(batchCount < batchSize)
    {
        cerr << "BatchCount > batchSize" << endl;
        return fail_case;
        /* exit(EXIT_FAILURE) */
    }

    net->doInference(inputData.data(), outputData.get(),batchCount);

    //Get Output    
    auto output = outputData.get();
    auto outputSize = net->getOutputSize()/ sizeof(float) / batchCount;
    for(int i = 0;i< batchCount ; ++i)
    {    
    //first detect count
        int detCount = output[0];
    //later detect result
    vector<Detection> result;
        result.resize(detCount);
        memcpy(result.data(), &output[1], detCount*sizeof(Detection));

        auto boxes = postProcessImg(inputImgs[i],result,classNum);
	outputs = boxes;

	output += outputSize;
    }
    inputImgs.clear();
    inputData.clear();

    batchCount = 0;
    return outputs;
}


/* class World */
/* { */
/*     public: */
/*         void print(); */
/*         World(std::string m) { cout << "Hello" << endl;} */
/* }; */
/* void World::print() */
/* { */
/*     cout<< "hello" << endl; */
/* } */

// ******************************************************************************
// boost wrapper for python

/* using namespace boost::python; */

/* BOOST_PYTHON_MODULE(inference) */
/* { */
/*     /1* std::list<vector<Bbox>>(inference::*in1)(vector<cv::Mat>) = &inference::infer; *1/ */
/*     /1* std::list<vector<Bbox>>(inference::*in2)(cv::Mat) = &inference::infer; *1/ */

/*     class_<Inference, Inference*, boost::noncopyable>("Inference", boost::python::no_init) */
/*         .def("doNMS", &Inference::DoNms) */
/*         .def("postprocessimg", &Inference::postProcessImg) */
/*         .def("prepareimg", &Inference::prepareImage) */
/*         .def("split", &Inference::split) */
/*         .def("load_trt", &Inference::loadTRTModel) */
/*         .def("infer", &Inference::infer) */
/*         .def("infer_single_image", &Inference::infer_single_image) */
/*         ; */

/*     /1* class_<World>("World", init<std::string>()) *1/ */
/*     /1*     .def("print", &World::print) *1/ */
/*     /1*     ; *1/ */
/* }; */
