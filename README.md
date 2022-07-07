## 准备工作
下载yolo4.h5文件

文件已经分享到百度云盘

    链接：https://pan.baidu.com/s/1r6EjtMv30uVs-JLZ-a50zA 
    提取码：3lvv

把下载完的yolo4.h5文件放进**traffic_counting/model_data**和**object_counting/model_data**即可

***

## 环境
* 显卡 MX350
* CUDA 10.2.89
* CUDnn 8.2.2.26
* Python 3.6.13 
* tensorflow-gpu==1.14 (***tensorflow2版本要改很多,不建议用tensorflow2***)
* numpy==1.16.4 (***numpy版本高，会出现很多问题***)

详情可见文件condaenvironment_jackrma.yml 即为 环境导出包

可用以下命令来直接导入

    conda env create -f condaenvironment_jackrma.yml


***

## 运行
在 **traffic_counting** 文件夹下

先运行

     python app.py

同时要运行

     python video_streamer1.py
和

     python video_streamer2.py

来打开两个摄像头，
* 其中    **cap = cv2.VideoCapture(0)**   中的 0 需要更改成相对应的usb摄像头编号。
* 如何查找相应的usb摄像头编号：


    xawtv /dev/video*



***

## 最后效果
* 由于原代码的数据集只是针对汽车和大巴，对摩托车、自行车和行人识别效果并不佳
* 请注意，由于DETRAC不包含任何摩托车，因此它们是唯一被忽略的车辆。此外，DETRAC数据集仅包含中国的交通图像，因此由于缺乏培训数据，它很难正确检测其他国家的某些车辆。例如，它经常会将掀背车误分类为SUV，或者由于不同的配色方案，无法检测到出租车。

<div align='center'>
<img src="/video/测试效果1.gif" width="1104"/>
</div>

<div align='center'>
<img src="/video/测试效果2.gif" width="1104"/>
</div>

<div align='center'>
<img src="/video/测试效果3.gif" width="1104"/>
</div>

***

## 最后
全部的代码和模型文件放到了百度云盘和天翼网盘中
**百度网盘:**

        链接：https://pan.baidu.com/s/11-H3JM30q1oaqi32NktRYA 
        提取码：apnb
**天翼网盘:**

        https://cloud.189.cn/t/YbArmmyueEne (访问码:ptu1)




