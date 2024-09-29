from image_saver import ImageSaver

from  stats_file import accumulate_stats

# Useful reference https://blog.teclado.com/python-abc-abstract-base-classes/

class AbstractObjectDetector:
    def __init__(self, config):
        self._config = config
        self._image_saver = ImageSaver()
        self._image_saver.set_config(config)

    def ReadLabelFile(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        ret = {}
        for line in lines:
            pair = line.strip().split(maxsplit=1)
            ret[int(pair[0])] = pair[1].strip()
        return ret

    def DrawRectangles(request):
        with MappedArray(request, "main") as m:
            for rect in rectangles:
                print(rect)
                rect_start = (int(rect[0] * 2) - 5, int(rect[1] * 2) - 5)
                rect_end = (int(rect[2] * 2) + 5, int(rect[3] * 2) + 5)
                cv2.rectangle(m.array, rect_start, rect_end, (0, 255, 0, 0))
                if len(rect) == 5:
                    text = rect[4]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(m.array, text, (int(rect[0] * 2) + 10, int(rect[1] * 2) + 10),
                            font, 1, (255, 255, 255), 2, cv2.LINE_AA)


    def detect_motion(self, current_array, recording_time, algorithm_data):
        pass

    def print_algorithm_data(self, algorithm_data, motion_detected):
        pass

    def get_object_detection_data(self, algorithm_data):
        pass

    def cleanup(self):
        pass

