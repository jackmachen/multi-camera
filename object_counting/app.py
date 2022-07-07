from importlib import import_module
from flask import Flask, render_template, Response
import cv2
import time

"""
https://www.cnblogs.com/arkenstone/p/7159615.html
利用flask将opencv实时视频流输出到浏览器
flask提供视频流是通过generator函数进行的，
flask通过将一连串独立的jpeg图片输出来实现视频流，这种方法叫做motion JPEG，
好处是延迟很低，但是成像质量一般，因为jpeg压缩图片的质量对motion stream不太够用。
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'


app = Flask(__name__)

@app.route('/')# route装饰器创建路由
def index(): # 访问此路由时执行的视图函数
    """Video streaming home page."""
    # 视频流主页
    return render_template('index.html') # jinja2模板，具体格式保存在index.html文件中


def gen(camera_stream, feed_type, device):
    """Video streaming generator function."""
    # 视频流生成器功能
    unique_name = (feed_type, device)

    num_frames = 0
    total_time = 0
    while True:
        time_start = time.time()

        cam_id, frame = camera_stream.get_frame(unique_name)
        if frame is None:
            break

        num_frames += 1

        # 计算帧数
        time_now = time.time()
        total_time += time_now - time_start
        fps = num_frames / total_time

        # write camera name 写入相机名称
        cv2.putText(frame, cam_id, (int(20), int(20 * 5e-3 * frame.shape[0])), 0, 2e-3 * frame.shape[0], (255, 255, 255), 2)

        if feed_type == 'yolo':
            cv2.putText(frame, "FPS: %.2f" % fps, (int(20), int(40 * 5e-3 * frame.shape[0])), 0, 2e-3 * frame.shape[0],
                        (255, 255, 255), 2)

        frame = cv2.imencode('.jpg', frame)[1].tobytes()  # Remove this line for test camera
        # 删除测试摄像头的这条线
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed/<feed_type>/<device>')# 这个地址返回视频流响应
def video_feed(feed_type, device):
    """Video streaming route. Put this in the src attribute of an img tag."""
    # 视频流路由。将其放入img标记的src属性中
    port_list = (5555, 5566)
    if feed_type == 'camera':
        camera_stream = import_module('camera_server').Camera
        return Response(gen(camera_stream=camera_stream(feed_type, device, port_list), feed_type=feed_type, device=device),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    elif feed_type == 'yolo':
        camera_stream = import_module('camera_yolo').Camera
        return Response(gen(camera_stream=camera_stream(feed_type, device, port_list), feed_type=feed_type, device=device),
                        mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)# 启动web服务
    # 开始运行flask应用程序，可以设置启动的host地址和端口号
    # app.run(debug=True, host='0.0.0.0', threaded=True) # 开始运行flask应用程序，以调试模式运行
    """
    flask源码解析之app.run()的执行流程
    Flask是一个使用 Python 编写的轻量级 Web 应用框架
    """







