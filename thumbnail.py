# Copyright (c) 2023 TheJMaster28
# Copyright (c) 2023 Molodos
# Copyright (c) 2023 sigathi
# Copyright (c) 2020 DhanOS
# The ElegooNeptuneThumbnailPrusa plugin is released under the terms of the AGPLv3 or higher.


import argparse
import base64
import logging
import platform
import re
import os
import sys
from array import array
from ctypes import *
from datetime import datetime
from io import BytesIO
from os import path
from shutil import copy

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter


script_dir = path.dirname(sys.argv[0])
log_file = path.join(script_dir, "app.log")
logging.basicConfig(filename=log_file, filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("my_logger")


app = QGuiApplication(sys.argv)


class Neptune_Thumbnail:
    thumbnail = ""
    time_to_print = ""
    filament_used = ""

    def __init__(self, slicer_output, old_printer=False, img_size="200x200", short_time_format=False, debug=False):
        self.slicer_output = slicer_output
        self.run_old_printer = old_printer
        self.short_time_format = short_time_format
        self.img_size = img_size
        self.debug = debug
        _ = img_size.split("x")
        self.img_x = int(_[0])
        self.img_y = int(_[1])
        logger.info(f"gcode input file from slicer: {args.input_file}")
        if self.run_old_printer:
            logger.info("Using Older printer settings")
        if self.img_size != "200x200":
            logger.info(f"Not using default img size. Will find a thumbnail with size of {img_size}")

    def parse_through_gcode_file(self):
        """
        Finds thumbnail encoding generated from PrusaSlicer in the gcode file
        """
        thumbnail_str = ""
        found_thumbnail = False
        with open(self.slicer_output, "r") as file:
            for index, line in enumerate(file):
                if re.search(f"; thumbnail[_A-Z]* begin {self.img_size}", line):
                    logger.debug(f"found thumbnail begin at file line: {index}")
                    found_thumbnail = True
                elif re.search("; thumbnail[_A-Z]* end", line) and found_thumbnail:
                    if found_thumbnail:
                        logger.debug(f"found thumbnail end at file line: {index}")
                        self.thumbnail = thumbnail_str
                        found_thumbnail = False
                elif found_thumbnail:
                    clean_line = line.replace("; ", "")
                    thumbnail_str += clean_line.strip()

                elif "; estimated printing time (normal mode) =" in line:
                    time = line.split("=")
                    self.time_to_print = time[1].strip()
                    # 00d 00h 00m 00s
                    days = 0
                    hours = 0
                    minutes = 0
                    seconds = 0
                    days_match = re.search("([0-9]+)d", self.time_to_print)
                    if days_match:
                        days = int(days_match.group(1))
                    hours_match = re.search("([0-9]+)h", self.time_to_print)
                    if hours_match:
                        hours = int(hours_match.group(1))
                    minutes_match = re.search("([0-9]+)m", self.time_to_print)
                    if minutes_match:
                        minutes = int(minutes_match.group(1))
                    seconds_match = re.search("([0-9]+)m", self.time_to_print)
                    if seconds_match:
                        seconds = int(seconds_match.group(1))

                    if self.short_time_format:
                        hours += days * 24
                        self.time_to_print = "{}h{:02d}m".format(hours, minutes)
                    elif days != 0:
                        self.time_to_print = "{}d {}h {}m".format(days, hours, minutes)

                elif "; total filament used [g] =" in line:
                    used = line.split("=")
                    self.filament_used = used[1].strip() + "g"

            if not self.thumbnail:
                raise Exception(f"End of file reached. Could not find thumbnail {self.img_size} encoding in provided gcode file: {self.slicer_output}")
            if not self.time_to_print:
                raise Exception(f"End of file reached. Could not find estimated printing time in provided gcode file: {self.slicer_output}")
            if not self.filament_used:
                raise Exception(f"End of file reached. Could not find estimated total filament used in provided gcode file: {self.slicer_output}")

    def decode(self, text) -> QImage:
        """
        Decodes thumbnail string into a QImage object
        """
        if not text:
            raise Exception("thumbnail text is empty")
        logger.debug("Decoding thumbnail from base64")
        text_bytes = text.encode("ascii")
        decode_data = base64.b64decode(text_bytes)
        image_stream = BytesIO(decode_data)
        qimage: QImage = QImage.fromData(image_stream.getvalue())
        return qimage

    def write_text_image(self, qimage: QImage):
        # Write to image
        logger.debug("Writing text to image")
        painter = QPainter()
        painter.begin(qimage)
        size = qimage.height()
        font = QFont("Arial", int(size * 0.075))
        painter.setFont(font)
        painter.setPen(QColor(Qt.GlobalColor.white))
        x_point = int(size * 0.02)
        y_point = int(size * 0.12)
        y_point_1 = size - int(size * 0.05)
        # time
        painter.drawText(x_point, y_point, self.time_to_print)
        # filament
        painter.drawText(x_point, y_point_1, self.filament_used)
        painter.end()

        if self.debug:
            logger.debug(f"Writing test image to {script_dir}\\test.png")
            qimage.save(path.join(script_dir, "test.png"))

    def parse_screenshot(self, img: QImage, width, height, img_type) -> str:
        """
        Parse screenshot to string for old printers
        """
        result = ""
        b_image = img.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        self.write_text_image(b_image)
        img_size = b_image.size()
        result += img_type
        datasize = 0
        for i in range(img_size.height()):
            for j in range(img_size.width()):
                pixel_color = b_image.pixelColor(j, i)
                r = pixel_color.red() >> 3
                g = pixel_color.green() >> 2
                b = pixel_color.blue() >> 3
                rgb = (r << 11) | (g << 5) | b
                str_hex = "%x" % rgb
                if len(str_hex) == 3:
                    str_hex = "0" + str_hex[0:3]
                elif len(str_hex) == 2:
                    str_hex = "00" + str_hex[0:2]
                elif len(str_hex) == 1:
                    str_hex = "000" + str_hex[0:1]
                if str_hex[2:4] != "":
                    result += str_hex[2:4]
                    datasize += 2
                if str_hex[0:2] != "":
                    result += str_hex[0:2]
                    datasize += 2
                if datasize >= 50:
                    datasize = 0
            result += "\rM10086 ;"
            if i == img_size.height() - 1:
                result += "\r"
        return result

    def parse_screenshot_new(self, img: QImage, width, height, img_type) -> str:
        """
        Parse screenshot to string for new printers
        """
        system = platform.system()
        if system == "Darwin":
            dll_path = path.join(path.dirname(__file__), "libColPic.dylib")
            p_dll = CDLL(dll_path)
            logger.debug(f"using {system} dll: {dll_path}")
        elif system == "Linux":
            dll_path = path.join(path.dirname(__file__), "libColPic.so")
            p_dll = CDLL(dll_path)
            logger.debug(f"using {system} dll: {dll_path}")
        else:
            dll_path = path.join(path.dirname(__file__), "ColPic_X64.dll")
            p_dll = CDLL(dll_path)
            logger.debug(f"using {system} dll: {dll_path}")

        result = ""
        b_image = img.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        self.write_text_image(b_image)
        logger.debug("Encoding thumbnail image")
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

        except Exception:
            logger.exception("Failed to prase new thumbnail screenshot")

        return result + "\r"

    def run(self):
        """
        Main runner for executable
        """
        self.parse_through_gcode_file()
        prusa_thumbnail_decoded = self.decode(self.thumbnail)
        new_thumbnail_gcode = ""
        if self.run_old_printer:
            new_thumbnail_gcode += self.parse_screenshot(prusa_thumbnail_decoded, 200, 200, ";gimage:")
            new_thumbnail_gcode += self.parse_screenshot(prusa_thumbnail_decoded, 160, 160, ";simage:")
        else:
            new_thumbnail_gcode += self.parse_screenshot_new(prusa_thumbnail_decoded, 200, 200, ";gimage:")
            new_thumbnail_gcode += self.parse_screenshot_new(prusa_thumbnail_decoded, 160, 160, ";simage:")

        new_thumbnail_gcode += "\r\r"
        new_thumbnail_gcode += "; Thumbnail Generated by ElegooNeptuneThumbnailPrusa\r\r"
        # seeing if this works for N4 printer thanks to Molodos: https://github.com/Molodos/ElegooNeptuneThumbnails-Prusa
        new_thumbnail_gcode += f"; Cura_SteamEngine X.X to trick printer into thinking this is Cura\r\r"

        logger.debug("Parsed new thumbnail screenshot gcode.")

        with open(self.slicer_output, "r") as file:
            file_content = file.read()

        file_content_new = new_thumbnail_gcode + file_content.replace(r"PrusaSlicer", "Prusa-Slicer")

        with open(self.slicer_output, "w") as file:
            file.write(file_content_new)

        logger.info(f"Wrote new thumbnail screenshot in gcode file: {self.slicer_output}")


if __name__ == "__main__":
    try:
        start_time = datetime.now()
        parser = argparse.ArgumentParser(prog=path.basename(__file__))
        parser.add_argument(
            "input_file",
            metavar="gcode-files",
            type=str,
            help="GCode file to be processed.",
        )
        parser.add_argument(
            "--old_printer",
            help="Run for older Neptune Printers",
            default=False,
            action="store_true",
        )
        parser.add_argument(
            "--img_size",
            default="200x200",
            help="Size of image to find in Gcode to encode",
        )
        parser.add_argument(
            "--short_time_format",
            default=False,
            action="store_true",
            help="display a shorter time format on thumbnails",
        )
        parser.add_argument(
            "--debug",
            default=False,
            action="store_true",
        )

        args = parser.parse_args()

        if args.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        obj = Neptune_Thumbnail(args.input_file, old_printer=args.old_printer, img_size=args.img_size, short_time_format=args.short_time_format, debug=args.debug)
        obj.run()
        end_time = datetime.now()
        logger.debug(f"Execution Time: {end_time - start_time}")
    except Exception as ex:
        logger.exception("Error occurred while running application.")
