from __future__ import division, print_function, absolute_import

import cv2
from base_camera import BaseCamera

import os
import warnings
import numpy as np
from PIL import Image
from yolo import YOLO
from deep_sort import preprocessing
from deep_sort.detection import Detection
from importlib import import_module
from collections import Counter
from collections import deque
import datetime
import math

warnings.filterwarnings('ignore')


class Camera(BaseCamera):
    def __init__(self, feed_type, device, port_list):
        super(Camera, self).__init__(feed_type, device, port_list)

    # 如果线段AB和CD相交，则返回true
    @staticmethod
    def intersect(A, B, C, D):
        return Camera.ccw(A, C, D) != Camera.ccw(B, C, D) and Camera.ccw(A, B, C) != Camera.ccw(A, B, D)

    @staticmethod
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    @staticmethod
    def vector_angle(midpoint, previous_midpoint):
        x = midpoint[0] - previous_midpoint[0]
        y = midpoint[1] - previous_midpoint[1]
        return math.degrees(math.atan2(y, x))

    @staticmethod
    def yolo_frames(image_hub, unique_name):
        device = unique_name[1]

        show_detections = False

        gdet = import_module('tools.generate_detections')
        nn_matching = import_module('deep_sort.nn_matching')
        Tracker = import_module('deep_sort.tracker').Tracker

        # 参数定义
        max_cosine_distance = 0.3
        nn_budget = None

        # deep_sort
        # 深度排序
        model_filename = 'model_data/mars-small128.pb'
        encoder = gdet.create_box_encoder(model_filename, batch_size=1)

        metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
        tracker = Tracker(metric)

        yolo = YOLO()
        nms_max_overlap = 1.0

        num_frames = 0

        current_date = datetime.datetime.now().date()
        count_dict = {}  # 启动dict以存储计数

        total_counter = 0
        up_count = 0
        down_count = 0

        class_counter = Counter()   # 存储每个检测到的类的计数
        already_counted = deque(maxlen=50)   # 用于存储计数ID的临时内存
        intersect_info = []  # 初始化交叉点列表

        memory = {}
        while True:
            cam_id, frame = image_hub.recv_image()
            image_hub.send_reply(b'OK')  # 这是流使用REQ/REP模式所必需的
            # image_height, image_width = frame.shape[:2]

            if frame is None:
                break

            num_frames += 1

            '''
            if num_frames % 2 != 0:  # only process frames at set number of frame intervals
                continue
            '''

            image = Image.fromarray(frame[..., ::-1])  # 将bgr转换为rgb
            boxes, confidence, classes = yolo.detect_image(image)
            features = encoder(frame, boxes)

            detections = [Detection(bbox, confidence, cls, feature) for bbox, confidence, cls, feature in
                          zip(boxes, confidence, classes, features)]

            # Run non-maxima suppression. 运行非最大值抑制。
            boxes = np.array([d.tlwh for d in detections])
            scores = np.array([d.confidence for d in detections])
            classes = np.array([d.cls for d in detections])
            indices = preprocessing.non_max_suppression(boxes, nms_max_overlap, scores)
            detections = [detections[i] for i in indices]

            # Call the tracker
            tracker.predict()
            tracker.update(detections)

            if cam_id == 'Camera 1':
                line = [(0, int(0.5 * frame.shape[0])), (int(frame.shape[1]), int(0.5 * frame.shape[0]))]
            else:
                line = [(0, int(0.33 * frame.shape[0])), (int(frame.shape[1]), int(0.33 * frame.shape[0]))]

            # draw yellow line 绘制黄线
            cv2.line(frame, line[0], line[1], (0, 255, 255), 2)

            for track in tracker.tracks:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue
                bbox = track.to_tlbr()
                track_cls = track.cls  # most common detection class for track 轨道最常见的检测等级

                midpoint = track.tlbr_midpoint(bbox)
                origin_midpoint = (midpoint[0], frame.shape[0] - midpoint[1])  # get midpoint respective to botton-left
                                                                               # 分别取波顿左侧的中点

                if track.track_id not in memory:
                    memory[track.track_id] = deque(maxlen=2)

                memory[track.track_id].append(midpoint)
                previous_midpoint = memory[track.track_id][0]

                origin_previous_midpoint = (previous_midpoint[0], frame.shape[0] - previous_midpoint[1])

                cv2.line(frame, midpoint, previous_midpoint, (0, 255, 0), 2)

                # Add to counter and get intersection details 添加到计数器并获取交叉口详细信息
                if Camera.intersect(midpoint, previous_midpoint, line[0], line[1]) and track.track_id not in already_counted:
                    class_counter[track_cls] += 1
                    total_counter += 1

                    # draw red line 画红线
                    cv2.line(frame, line[0], line[1], (0, 0, 255), 2)

                    already_counted.append(track.track_id)  # Set already counted for ID to true. 将ID的已计数设置为true。

                    intersection_time = datetime.datetime.now() - datetime.timedelta(microseconds=datetime.datetime.now().microsecond)
                    angle = Camera.vector_angle(origin_midpoint, origin_previous_midpoint)
                    intersect_info.append([track_cls, origin_midpoint, angle, intersection_time])

                    if angle > 0:
                        up_count += 1
                    if angle < 0:
                        down_count += 1

                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 255, 255), 2)  # WHITE BOX 白色方框
                cv2.putText(frame, "ID: " + str(track.track_id), (int(bbox[0]), int(bbox[1])), 0,
                            1.5e-3 * frame.shape[0], (0, 255, 0), 2)

                if not show_detections:
                    adc = "%.2f" % (track.adc * 100) + "%"  # Average detection confidence 平均检测置信度
                    cv2.putText(frame, str(track_cls), (int(bbox[0]), int(bbox[3])), 0,
                                1e-3 * frame.shape[0], (0, 255, 0), 2)
                    cv2.putText(frame, 'ADC: ' + adc, (int(bbox[0]), int(bbox[3] + 2e-2 * frame.shape[1])), 0,
                                1e-3 * frame.shape[0], (0, 255, 0), 2)

            # Delete memory of old tracks. 删除旧曲目的内存。
            # This needs to be larger than the number of tracked objects in the frame.
            # 这需要大于帧中跟踪对象的数量。
            if len(memory) > 50:
                del memory[list(memory)[0]]

            # Draw total count. 提取总计数
            cv2.putText(frame, "Total: {} ({} up, {} down)".format(str(total_counter), str(up_count),
                        str(down_count)), (int(0.05 * frame.shape[1]), int(0.1 * frame.shape[0])), 0,
                        1.5e-3 * frame.shape[0], (0, 255, 255), 2)

            if show_detections:
                for det in detections:
                    bbox = det.to_tlbr()
                    score = "%.2f" % (det.confidence * 100) + "%"
                    cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 0, 0), 2)  # BLUE BOX
                    if len(classes) > 0:
                        det_cls = det.cls
                        cv2.putText(frame, str(det_cls) + " " + score, (int(bbox[0]), int(bbox[3])), 0,
                                    1.5e-3 * frame.shape[0], (0, 255, 0), 2)

            # display counts for each class as they appear 显示每个类的计数
            y = 0.2 * frame.shape[0]
            for cls in class_counter:
                class_count = class_counter[cls]
                cv2.putText(frame, str(cls) + " " + str(class_count), (int(0.05 * frame.shape[1]), int(y)), 0,
                            1.5e-3 * frame.shape[0], (0, 255, 255), 2)
                y += 0.05 * frame.shape[0]

            # calculate current minute  计算当前分钟数
            now = datetime.datetime.now()
            rounded_now = now - datetime.timedelta(microseconds=now.microsecond)  # round to nearest second
            # 四舍五入到最接近的秒
            current_minute = now.time().minute

            if current_minute == 0 and len(count_dict) > 1:
                count_dict = {}  # reset counts every hour 每小时重置计数
            else:
                # write counts to file for every set interval of the hour
                # 每设置一小时的写入计数
                write_interval = 5
                if current_minute % write_interval == 0:  # write to file once only every write_interval minutes
                    # 仅每隔write\u间隔分钟写入一次文件
                    if current_minute not in count_dict:
                        count_dict[current_minute] = True
                        total_filename = 'Total counts for {}, {}.txt'.format(current_date, cam_id)
                        counts_folder = './counts/'
                        if not os.access(counts_folder + str(current_date) + '/total', os.W_OK):
                            os.makedirs(counts_folder + str(current_date) + '/total')
                        total_count_file = open(counts_folder + str(current_date) + '/total/' + total_filename, 'a')
                        print('{} writing...'.format(rounded_now))
                        print('Writing current total count ({}) and directional counts to file.'.format(total_counter))
                        total_count_file.write('{}, {}, {}, {}, {}\n'.format(str(rounded_now), device,
                                                                             str(total_counter), up_count, down_count))
                        total_count_file.close()

                        # if class exists in class counter, create file and write counts
                        # 如果类计数器中存在类，则创建文件和写入计数

                        if not os.access(counts_folder + str(current_date) + '/classes', os.W_OK):
                            os.makedirs(counts_folder + str(current_date) + '/classes')
                        for cls in class_counter:
                            class_count = class_counter[cls]
                            print('Writing current {} count ({}) to file.'.format(cls, class_count))
                            class_filename = 'Class counts for {}, {}.txt'.format(current_date, cam_id)
                            class_count_file = open(counts_folder + str(current_date) + '/classes/' + class_filename, 'a')
                            class_count_file.write("{}, {}, {}\n".format(rounded_now, device, str(class_count)))
                            class_count_file.close()

                        # write intersection details
                        # 写入交叉点详细信息
                        if not os.access(counts_folder + str(current_date) + '/intersections', os.W_OK):
                            os.makedirs(counts_folder + str(current_date) + '/intersections')
                        print('Writing intersection details for {}'.format(cam_id))
                        intersection_filename = 'Intersection details for {}, {}.txt'.format(current_date, cam_id)
                        intersection_file = open(counts_folder + str(current_date) + '/intersections/' + intersection_filename, 'a')
                        for i in intersect_info:
                            cls = i[0]

                            midpoint = i[1]
                            x = midpoint[0]
                            y = midpoint[1]

                            angle = i[2]

                            intersect_time = i[3]

                            intersection_file.write("{}, {}, {}, {}, {}, {}\n".format(str(intersect_time), device, cls,
                                                                                      x, y, str(angle)))
                        intersection_file.close()
                        intersect_info = []  # reset list after writing 写入后重置列表

            yield cam_id, frame
