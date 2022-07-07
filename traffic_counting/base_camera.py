import time
import threading
import imagezmq

try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent:
    """
    一个类事件类，当有新帧可用时向所有活动客户端发出信号。
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """
        从每个客户端的线程调用以等待下一帧"""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # 在 self.events 字典中为其添加一个条目
            # 每个条目有两个元素，一个 threading.Event() 和一个时间戳
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """
        当有新帧可用时由相机线程调用"""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # 如果未设置此客户端的事件，则设置它还将最后设置的时间戳更新为现在
                event[0].set()
                event[1] = now
            else:
                """
                如果客户端的事件已经设置，这意味着客户端没有处理前一帧如果事件保持设置
                超过 5 秒，则假设客户端已消失并将其删除
                """
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """
        处理完一帧后从每个客户端的线程调用"""
        self.events[get_ident()][0].clear()


class BaseCamera:
    threads = {}  # 从相机读取帧的后台线程
    frame = {}  # 当前帧由后台线程存储在这里
    last_access = {}  # 上次客户端访问相机的时间
    event = {}

    def __init__(self, feed_type, device, port_list):
        """
        如果后台摄像头线程尚未运行，则启动它"""
        self.unique_name = (feed_type, device)
        BaseCamera.event[self.unique_name] = CameraEvent()

        if self.unique_name not in BaseCamera.threads:
            BaseCamera.threads[self.unique_name] = None
        if BaseCamera.threads[self.unique_name] is None:
            BaseCamera.last_access[self.unique_name] = time.time()

            # 启动背景框架线程
            BaseCamera.threads[self.unique_name] = threading.Thread(target=self._thread,
                                                                    args=(self.unique_name, port_list))
            BaseCamera.threads[self.unique_name].start()

            # 等到帧可用
            while self.get_frame(self.unique_name) is None:
                time.sleep(0)

    @classmethod
    def get_frame(cls, unique_name):
        """返回当前相机帧"""
        BaseCamera.last_access[unique_name] = time.time()

        # 等待来自相机线程的信号
        BaseCamera.event[unique_name].wait()
        BaseCamera.event[unique_name].clear()

        return BaseCamera.frame[unique_name]

    @staticmethod
    def frames():
        """"
        从相机返回帧的生成器。"""
        raise RuntimeError('Must be implemented by subclasses')

    @staticmethod
    def yolo_frames(image_hub, unique_name):
        """"从相机返回帧的生成器."""
        raise RuntimeError('Must be implemented by subclasses')

    @staticmethod
    def server_frames(image_hub):
        """"从相机返回帧的生成器"""
        raise RuntimeError('Must be implemented by subclasses')

    @classmethod
    def yolo_thread(cls, unique_name, port):
        device = unique_name[1]

        image_hub = imagezmq.ImageHub(open_port='tcp://*:{}'.format(port))

        frames_iterator = cls.yolo_frames(image_hub, unique_name)
        try:
            for frame in frames_iterator:
                BaseCamera.frame[unique_name] = frame
                BaseCamera.event[unique_name].set()  # 向客户端发送信号
                time.sleep(0)
                if time.time() - BaseCamera.last_access[unique_name] > 60:
                    frames_iterator.close()
                    print('Stopping YOLO thread for device {} due to inactivity.'.format(device))
                    pass
        except Exception as e:
            BaseCamera.event[unique_name].set()  # 向客户端发送信号
            frames_iterator.close()
            print('Stopping YOLO thread for device {} due to error.'.format(device))
            print(e)

    @classmethod
    def server_thread(cls, unique_name, port):
        device = unique_name[1]

        image_hub = imagezmq.ImageHub(open_port='tcp://*:{}'.format(port))

        frames_iterator = cls.server_frames(image_hub)
        try:
            for cam_id, frame in frames_iterator:
                BaseCamera.frame[unique_name] = cam_id, frame
                BaseCamera.event[unique_name].set()  # send signal to clients
                time.sleep(0)
                if time.time() - BaseCamera.last_access[unique_name] > 5:
                    frames_iterator.close()
                    image_hub.zmq_socket.close()
                    print('Closing server socket at port {}.'.format(port))
                    print('Stopping server thread for device {} due to inactivity.'.format(device))
                    pass
        except Exception as e:
            frames_iterator.close()
            image_hub.zmq_socket.close()
            print('Closing server socket at port {}.'.format(port))
            print('Stopping server thread for device {} due to error.'.format(device))
            print(e)

    @classmethod
    def _thread(cls, unique_name, port_list):
        feed_type, device = unique_name
        if feed_type == 'camera':
            port = port_list[int(device)]
            print('Starting server thread for device {} at port {}.'.format(device, port))
            cls.server_thread(unique_name, port)

        elif feed_type == 'yolo':
            port = port_list[int(device)]
            print('Starting YOLO thread for device {}.'.format(device))
            cls.yolo_thread(unique_name, port)

        BaseCamera.threads[unique_name] = None
