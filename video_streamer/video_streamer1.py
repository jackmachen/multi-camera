import cv2
import errno
import imagezmq
import os
import socket


# """
#     读本地视频
# """
#
# def create_streamer_local(file, connect_to='tcp://127.0.0.1:5555', loop=True):
#     """
#     You can use this function to emulate an IP camera for the counting apps.
#     您可以使用此功能模拟计数应用程序的IP摄像头。
#     Parameters 参数
#     ----------
#     file : str
#         Path to the video file you want to stream. 要流式处理的视频文件的路径。
#     connect_to : str, optional
#         Where the video shall be streamed to. 视频应传输到的位置。
#         The default is 'tcp://127.0.0.1:5555'.
#     loop : bool, optional  循环：布尔，可选
#         Whether the video shall be looped. The default is True. 视频是否应循环播放。默认值为True。
#
#     Returns
#     -------
#     None.
#
#     """
#
#     # 读本地视频
#     ## check if file exists and open capture 检查文件是否存在并打开捕获
#     if os.path.isfile(file):
#         cap = cv2.VideoCapture(file)
#     else:
#         raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file)
#
#     # 直接读摄像头   ##################
#     # cap = cv2.VideoCapture(0)  # 0 指本地摄像头
#
#     # prepare streaming  准备流媒体
#     sender = imagezmq.ImageSender(connect_to=connect_to)
#     host_name = socket.gethostname()
#
#     while True:
#         ret, frame = cap.read()
#
#         if ret:
#             # if a frame was returned, send it  如果返回了帧，请发送它
#             sender.send_image(host_name, frame)
#         else:
#             # if no frame was returned, either restart or stop the stream
#             # 如果未返回任何帧，请重新启动或停止流
#             if loop:
#                 # cap = cv2.VideoCapture(0)
#                 cap = cv2.VideoCapture(file)
#             else:
#                 break
#
#
# if __name__ == '__main__':
#     streamer = create_streamer_local('/home/jackrma/Code/Multi-Camera-Live-Object-Tracking-master/video/1.mp4')


"""
    直接读摄像头
"""

def create_streamer(connect_to='tcp://127.0.0.1:5555', loop=False):

    """
    可以使用此功能模拟计数应用程序的IP摄像头。
    Parameters 参数
    ----------
    file : str
        要流式处理的视频文件的路径。
    connect_to : str, optional
        视频应传输到的位置。
        The default is 'tcp://127.0.0.1:5555'.
    loop : bool, optional  循环：布尔，可选
        视频是否应循环播放。默认值为True。

    Returns
    -------
    None.

    """
    
    # 读本地视频
    # 检查文件是否存在并打开捕获
    # if os.path.isfile(file):
    #     cap = cv2.VideoCapture(file)
    # else:
    #     raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file)

    # 直接读摄像头   ##################
    cap = cv2.VideoCapture(0)  # 0 指本地摄像头
    
    # 准备流媒体
    sender = imagezmq.ImageSender(connect_to=connect_to)
    host_name = socket.gethostname()
    
    while True:
        ret, frame = cap.read()
        
        if ret:
            # 如果返回了帧，请发送它
            sender.send_image(host_name, frame)
        else:
            # 如果未返回任何帧，请重新启动或停止流
            if loop:
                cap = cv2.VideoCapture(0)
            else:
                break



if __name__ == '__main__':
    streamer = create_streamer()

