from imutils.video import VideoStream
import imagezmq


path = "rtsp://192.168.1.70:8080//h264_ulaw.sdp"  # 更改IP流地址
cap = VideoStream(path)

sender = imagezmq.ImageSender(connect_to='tcp://localhost:5555')  # 更改服务器线程的IP地址和端口
cam_id = 'Camera 1'  # 该名称将显示在相应的相机流上

stream = cap.start()

while True:

    frame = stream.read()
    sender.send_image(cam_id, frame)
