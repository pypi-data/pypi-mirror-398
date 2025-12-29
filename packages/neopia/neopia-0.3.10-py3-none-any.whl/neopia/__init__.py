# Part of the RoboticsWare project - https://roboticsware.uz
# Copyright (C) 2022 RoboticsWare (neopia.uz@gmail.com)
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General
# Public License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA  02111-1307  USA

import signal
import atexit
import sys

from neopia.scanner import Scanner
from neopia.mode import Mode
from neopia.keyboard import Keyboard
from neopia.runner import Runner
from neopia.model import DeviceType
from neopia.model import DataType
from neopia.neosoco import Neosoco
from neopia.opencv_camera import Camera
from neopia.ai_detection import FaceDetection
from neopia.ai_detection import FaceMeshDetection
from neopia.ai_detection import PoseDetection
from neopia.ai_detection import QRDetection
from neopia.ai_detection import ObjectDetection
from neopia.ai_detection import GestureDetection
from neopia.ai_detection import Voice


__version__ = "0.1.0"

__all__ = [
    "DeviceType", 
    "DataType", 
    "Neosoco", 
    "Keyboard", 
    "scan", 
    "is_link_mode", 
    "link_mode", 
    "dispose", 
    "set_executable", 
    "wait", 
    "wait_until_ready", 
    "wait_until", 
    "when_do", 
    "while_do", 
    "parallel",
    "Camera",
    "FaceDetection",
    "FaceMeshDetection",
    "PoseDetection",
    "QRDetection",
    "ObjectDetection",
    "GestureDetection",
    "Voice",
]

def scan():
    Scanner.scan()

def is_link_mode():
    return Mode.is_link_mode()

def link_mode(url='ws://127.0.0.1:59418'):
    Mode.set_link_mode(url)

def dispose():
    Runner.dispose_all()

def set_executable(execute):
    Runner.set_executable(execute)

def wait(milliseconds):
    Runner.wait(milliseconds)

def wait_until_ready():
    Runner.wait_until_ready()

def wait_until(condition, args=None):
    Runner.wait_until(condition, args)

def when_do(condition, do, args=None):
    Runner.when_do(condition, do, args)

def while_do(condition, do, args=None):
    Runner.while_do(condition, do, args)

def parallel(*functions):
    Runner.parallel(functions)

# It's called when an abnormal exit as CTRL+C
def _handle_signal(signal, frame):
    Runner.shutdown()
    raise SystemExit
signal.signal(signal.SIGINT, _handle_signal) # CTRL+C
if sys.platform != "win32":
    signal.signal(signal.SIGHUP, _handle_signal) # When kill process in VS code

# It's called for a safe exit by sending initial packet to HW, even a normal exit
def exit_handler():
    Runner.shutdown()
atexit.register(exit_handler)