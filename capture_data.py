import json
import datetime
import numpy as np

class CaptureData:

    def __init__(self) -> None:
        # These are public values. Set them as you go!
             
        self.capture_time = datetime.datetime.now()
        self.pir_fired = None
        self.node_name = None
        self.camera_num = None
        self.object_detected = None
        self.rectangles = []    # You need to append to these lists
        self.scores = []        # You need to append to these lists
        self.classes = []       # You need to append to these lists

    # TODO: Figure out how to get this to work. Need to read up on it.
    # 
    # def __setattr__(self, name, value):
    #     if name == "capture_time" and isinstance(value, datetime.datetime):
    #         value = value.strftime("%Y-%m-%d %H:%M:%S")
    #     super().__setattr__(name, value)

    def capture_time_str(self):
        return self.capture_time.strftime("%Y-%m-%d_%H-%M-%S")
    
    def to_json(self):
        def convert(obj):
            retval = None
            if isinstance(obj, np.ndarray):
                retval = str(obj.tolist())
            if isinstance(obj, datetime.datetime):
                retval = obj.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(obj, np.float32):
                retval = obj.item()
            return retval

        str = json.dumps(self.__dict__, default=convert)

        return str

    def to_short_string(self):
        pir_status = "PIR" if self.pir_fired else "No PIR"
        object_status = "Object" if self.object_detected else "No Object"
        classes = str(self.classes) # ", ".join(self.classes)
        return f"{pir_status} - {object_status} - Classes: {classes}"
    
    def to_coco(self):
        """
            Here's an example of a minimal bounding box JSON in COCO format for a single image:

            ```json
            {
            "images": [
                {
                "id": 1,
                "width": 800,
                "height": 600,
                "file_name": "example_image.jpg"
                }
            ],
            "categories": [
                {
                "id": 1,
                "name": "object"
                }
            ],
            "annotations": [
                {
                "id": 1,
                "image_id": 1,
                "category_id": 1,
                "bbox": [100, 150, 200, 250],
                "area": 50000,
                "iscrowd": 0
                }
            ]
            }
            ```

            Let's break down the key components of this minimal COCO JSON format:

            1. **Images**: Contains information about the image[1][2].
            - `id`: A unique identifier for the image
            - `width` and `height`: Dimensions of the image in pixels
            - `file_name`: The name of the image file

            2. **Categories**: Defines the object classes in the dataset[2].
            - `id`: A unique identifier for the category
            - `name`: The name of the object class

            3. **Annotations**: Contains the bounding box information[1][2][3].
            - `id`: A unique identifier for the annotation
            - `image_id`: References the image this annotation belongs to
            - `category_id`: References the category of the object
            - `bbox`: The bounding box coordinates in the format [x_min, y_min, width, height]
            - `area`: The area of the bounding box in square pixels
            - `iscrowd`: A flag (0 or 1) indicating whether the annotation represents a crowd of objects

            In the `bbox` array[1]:
            - `x_min` and `y_min` are the coordinates of the top-left corner of the bounding box
            - `width` and `height` represent the dimensions of the bounding box

            This minimal example includes just one image, one category, and one annotation. In a real-world scenario, you would typically have multiple images, categories, and annotations in your COCO JSON file[2][3].

            Citations:
            [1] https://albumentations.ai/docs/getting_started/bounding_boxes_augmentation/
            [2] https://roboflow.com/formats/coco-json
            [3] https://github.com/matterport/Mask_RCNN/issues/1433
            [4] https://towardsdatascience.com/how-to-work-with-object-detection-datasets-in-coco-format-9bf4fb5848a4?gi=13ccc27bf284
            
        """        
        pass
