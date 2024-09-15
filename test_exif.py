import piexif
import piexif.helper
from PIL import Image
import datetime

# from PIL import Image

image_path = "test.jpg"

# image = cv2.imread(image_path)
image = Image.open(image_path)

# Load existing EXIF data
# exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

user_comment = {}
user_comment["camera_name"] = "Camera Module 3"
user_comment["motion_detected"] = True
user_comment["pir"] = True
user_comment["algorithm_data"] = "algorithm data"

formatted_comment = piexif.helper.UserComment.dump(str(user_comment))

formatted_model = "Model Here".encode()

time_now = datetime.datetime.now()
time_now_str = time_now.strftime("%Y:%m:%d %H:%M:%S")

zeroth_ifd = {piexif.ImageIFD.Make: u"Camera Module 3",
              piexif.ImageIFD.Model: formatted_model,}
exif_ifd = {piexif.ExifIFD.DateTimeOriginal: time_now_str,
            piexif.ExifIFD.UserComment: formatted_comment,}
gps_ifd = {}
first_ifd = {}

exif_dict = {"0th":zeroth_ifd, "Exif":exif_ifd, "GPS":gps_ifd, "1st":first_ifd}
exif_bytes = piexif.dump(exif_dict)

# Set the UserComment
# user_comment = "Your custom comment here"
# exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(user_comment, encoding="unicode")

# # Dump the modified EXIF data back into the image
# exif_bytes = piexif.dump(exif_dict)

# Save the image with the EXIF data
# cv2.imwrite("image_with_exif.jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 100, exif_bytes])
image.save("test_with_exif.jpg", exif=exif_bytes)