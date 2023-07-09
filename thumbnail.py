import argparse
import base64
import logging
import platform
import traceback
from array import array
from ctypes import *
from io import BytesIO
from os import path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage

# Get the directory of the Python script
script_dir = path.dirname(path.abspath(__file__))

# Specify the log file path
log_file = path.join(script_dir, "app.log")

logging.basicConfig(
    level=logging.DEBUG, filename=log_file, filemode="w", format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("my_logger")


class Neptune_Thumbnail:
    def __init__(self, slicer_output):
        self.slicer_output = slicer_output

    def find_thumbnail(self):
        size = 600
        thumbnail_str = ""
        with open(self.slicer_output, "r") as file:
            found_thumbnail = False
            while not found_thumbnail:
                file_line = file.readline()
                if "; thumbnail begin" in file_line:
                    found_thumbnail = True
            found_end_thumbnail = False
            while not found_end_thumbnail:
                file_line = file.readline()
                if "; thumbnail end" in file_line:
                    found_end_thumbnail = True
                    break
                clean_line = file_line.replace("; ", "")
                thumbnail_str += clean_line.strip()
        return thumbnail_str

    def decode(self, text) -> QImage:
        text_bytes = text.encode("ascii")
        decode_data = base64.b64decode(text_bytes)
        image_stream = BytesIO(decode_data)
        qimage: QImage = QImage.fromData(image_stream.getvalue())
        return qimage

    def parse_screenshot_new(cls, img, width, height, img_type) -> str:
        """
        Parse screenshot to string for new printers
        """
        system = platform.system()
        if system == "Darwin":
            p_dll = CDLL(path.join(path.dirname(__file__), "libColPic.dylib"))
        elif system == "Linux":
            p_dll = CDLL(path.join(path.dirname(__file__), "libColPic.so"))
        else:
            p_dll = CDLL(path.join(path.dirname(__file__), "ColPic_X64.dll"))

        result = ""
        b_image = img.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        b_image.save("test_1.png")
        img_size = b_image.size()
        color16 = array("H")
        try:
            for i in range(img_size.height()):
                for j in range(img_size.width()):
                    pixel_color = b_image.pixelColor(j, i)
                    r = pixel_color.red() >> 3
                    g = pixel_color.green() >> 2
                    b = pixel_color.blue() >> 3
                    rgb = (r << 11) | (g << 5) | b
                    color16.append(rgb)

            # int ColPic_EncodeStr(U16* fromcolor16, int picw, int pich, U8* outputdata, int outputmaxtsize, int colorsmax);
            fromcolor16 = color16.tobytes()
            outputdata = array("B", [0] * img_size.height() * img_size.width()).tobytes()
            resultInt = p_dll.ColPic_EncodeStr(
                fromcolor16,
                img_size.height(),
                img_size.width(),
                outputdata,
                img_size.height() * img_size.width(),
                1024,
            )

            data0 = str(outputdata).replace("\\x00", "")
            data1 = data0[2 : len(data0) - 2]
            eachMax = 1024 - 8 - 1
            maxline = int(len(data1) / eachMax)
            appendlen = eachMax - 3 - int(len(data1) % eachMax)

            for i in range(len(data1)):
                if i == maxline * eachMax:
                    result += "\r;" + img_type + data1[i]
                elif i == 0:
                    result += img_type + data1[i]
                elif i % eachMax == 0:
                    result += "\r" + img_type + data1[i]
                else:
                    result += data1[i]
            result += "\r;"
            for j in range(appendlen):
                result += "0"

        except Exception as e:
            logger.error(traceback.format_exc())

        return result + "\r"

    def run(self):
        prusa_thumbnail_str = self.find_thumbnail()
        prusa_thumbnail_decoded = self.decode(prusa_thumbnail_str)
        prusa_thumbnail_decoded.save("test.png")
        new_thumbnail_gcode = ""
        new_thumbnail_gcode += self.parse_screenshot_new(prusa_thumbnail_decoded, 200, 200, ";gimage:")
        new_thumbnail_gcode += self.parse_screenshot_new(prusa_thumbnail_decoded, 160, 160, ";simage:")

        with open(self.slicer_output, "r") as file:
            file_content = file.read()

        file_content_new = new_thumbnail_gcode + file_content

        with open(self.slicer_output, "w") as file:
            file.write(file_content_new)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(prog=path.basename(__file__))
        parser.add_argument(
            "input_file",
            metavar="gcode-files",
            type=str,
            help="One or more GCode file(s) to be processed " "- at least one is required.",
        )

        args = parser.parse_args()

        logger.info(f" temp gcode output: {args.input_file}")
        obj = Neptune_Thumbnail(args.input_file)
        obj.run()
    except Exception:
        logger.error(traceback.format_exc())
        exit(1)

# test_file = (
#     r"D:\Documents\3D Printer Models\G code test\xyzCalibration_cube_0.2mm_PLA_NEPTUNE3PRO_45m.gcode"
# )
# obj = Neptune_Thumbnail(test_file)
# obj.run()
