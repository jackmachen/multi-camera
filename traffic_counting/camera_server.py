from base_camera import BaseCamera
import time
import cv2


class Camera(BaseCamera):

    def __init__(self, feed_type, device, port_list):
        super(Camera, self).__init__(feed_type, device, port_list)

    @staticmethod
    def server_frames(image_hub):
        num_frames = 0
        total_time = 0
        while True:  # main loop
            time_start = time.time()

            cam_id, frame = image_hub.recv_image()
            image_hub.send_reply(b'OK')  # this is needed for the stream to work with REQ/REP pattern
            # 这是流使用REQ/REP模式所必需的

            num_frames += 1

            time_now = time.time()
            total_time += time_now - time_start
            fps = num_frames / total_time

            # uncomment below to see FPS of camera stream
            # 取消下面的注释以查看相机流的FPS
            # cv2.putText(frame, "FPS: %.2f" % fps, (int(20), int(40 * 5e-3 * frame.shape[0])), 0, 2e-3 * frame.shape[0],(255, 255, 255), 2)

            yield cam_id, frame
