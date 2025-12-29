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

import math

from neopia.runner import Runner
from neopia.util import Util
from neopia.model import Robot
from neopia.mode import Mode


class Neosoco(Robot):
    ID = "kr.neobot.physical.neosoco"

    OUTPUT_1    = 0x00400000
    OUTPUT_2    = 0x00400001
    OUTPUT_3    = 0x00400002
    INPUT_1     = 0x00400003
    INPUT_2     = 0x00400004
    INPUT_3     = 0x00400005
    REMOCTL     = 0x00400006
    BATTERY     = 0x00400007
    LEFT_MOTOR  = 0x00400008
    RIGHT_MOTOR = 0x00400009
    NOTE        = 0x0040000a

    COLOR_NAME_WHITE = "white"
    COLOR_NAME_RED = "red"
    COLOR_NAME_YELLOW = "yellow"
    COLOR_NAME_GREEN = "green"
    COLOR_NAME_BLUE = "blue"

    _COLORS = {
        "white": COLOR_NAME_WHITE,
        "red": COLOR_NAME_RED,
        "yellow": COLOR_NAME_YELLOW,
        "green": COLOR_NAME_GREEN,
        "blue": COLOR_NAME_BLUE
    }

    _NOTE_OFF = 0
    _NOTE_C_1 = 1
    _NOTE_C_SHARP_1 = 2
    _NOTE_D_FLAT_1 = 2
    _NOTE_D_1 = 3
    _NOTE_D_SHARP_1 = 4
    _NOTE_E_FLAT_1 = 4
    _NOTE_E_1 = 5
    _NOTE_F_1 = 6
    _NOTE_F_SHARP_1 = 7
    _NOTE_G_FLAT_1 = 7
    _NOTE_G_1 = 8
    _NOTE_G_SHARP_1 = 9
    _NOTE_A_FLAT_1 = 9
    _NOTE_A_1 = 10
    _NOTE_A_SHARP_1 = 11
    _NOTE_B_FLAT_1 = 11
    _NOTE_B_1 = 12
    _NOTE_C_2 = 13
    _NOTE_C_SHARP_2 = 14
    _NOTE_D_FLAT_2 = 14
    _NOTE_D_2 = 15
    _NOTE_D_SHARP_2 = 16
    _NOTE_E_FLAT_2 = 16
    _NOTE_E_2 = 17
    _NOTE_F_2 = 18
    _NOTE_F_SHARP_2 = 19
    _NOTE_G_FLAT_2 = 19
    _NOTE_G_2 = 20
    _NOTE_G_SHARP_2 = 21
    _NOTE_A_FLAT_2 = 21
    _NOTE_A_2 = 22
    _NOTE_A_SHARP_2 = 23
    _NOTE_B_FLAT_2 = 23
    _NOTE_B_2 = 24
    _NOTE_C_3 = 25
    _NOTE_C_SHARP_3 = 26
    _NOTE_D_FLAT_3 = 26
    _NOTE_D_3 = 27
    _NOTE_D_SHARP_3 = 28
    _NOTE_E_FLAT_3 = 28
    _NOTE_E_3 = 29
    _NOTE_F_3 = 30
    _NOTE_F_SHARP_3 = 31
    _NOTE_G_FLAT_3 = 31
    _NOTE_G_3 = 32
    _NOTE_G_SHARP_3 = 33
    _NOTE_A_FLAT_3 = 33
    _NOTE_A_3 = 34
    _NOTE_A_SHARP_3 = 35
    _NOTE_B_FLAT_3 = 35
    _NOTE_B_3 = 36
    _NOTE_C_4 = 37
    _NOTE_C_SHARP_4 = 38
    _NOTE_D_FLAT_4 = 38
    _NOTE_D_4 = 39
    _NOTE_D_SHARP_4 = 40
    _NOTE_E_FLAT_4 = 40
    _NOTE_E_4 = 41
    _NOTE_F_4 = 42
    _NOTE_F_SHARP_4 = 43
    _NOTE_G_FLAT_4 = 43
    _NOTE_G_4 = 44
    _NOTE_G_SHARP_4 = 45
    _NOTE_A_FLAT_4 = 45
    _NOTE_A_4 = 46
    _NOTE_A_SHARP_4 = 47
    _NOTE_B_FLAT_4 = 47
    _NOTE_B_4 = 48
    _NOTE_C_5 = 49
    _NOTE_C_SHARP_5 = 50
    _NOTE_D_FLAT_5 = 50
    _NOTE_D_5 = 51
    _NOTE_D_SHARP_5 = 52
    _NOTE_E_FLAT_5 = 52
    _NOTE_E_5 = 53
    _NOTE_F_5 = 54
    _NOTE_F_SHARP_5 = 55
    _NOTE_G_FLAT_5 = 55
    _NOTE_G_5 = 56
    _NOTE_G_SHARP_5 = 57
    _NOTE_A_FLAT_5 = 57
    _NOTE_A_5 = 58
    _NOTE_A_SHARP_5 = 59
    _NOTE_B_FLAT_5 = 59
    _NOTE_B_5 = 60
    _NOTE_C_6 = 61
    _NOTE_C_SHARP_6 = 62
    _NOTE_D_FLAT_6 = 62
    _NOTE_D_6 = 63
    _NOTE_D_SHARP_6 = 64
    _NOTE_E_FLAT_6 = 64
    _NOTE_E_6 = 65
    _NOTE_F_6 = 66
    _NOTE_F_SHARP_6 = 67
    _NOTE_G_FLAT_6 = 67
    _NOTE_G_6 = 68
    _NOTE_G_SHARP_6 = 69
    _NOTE_A_FLAT_6 = 69
    _NOTE_A_6 = 70
    _NOTE_A_SHARP_6 = 71
    _NOTE_B_FLAT_6 = 71
    _NOTE_B_6 = 72
    
    NOTE_NAME_C = "C"
    NOTE_NAME_C_SHARP = "C#"
    NOTE_NAME_D_FLAT = "Db"
    NOTE_NAME_D = "D"
    NOTE_NAME_D_SHARP = "D#"
    NOTE_NAME_E_FLAT = "Eb"
    NOTE_NAME_E = "E"
    NOTE_NAME_F = "F"
    NOTE_NAME_F_SHARP = "F#"
    NOTE_NAME_G_FLAT = "Gb"
    NOTE_NAME_G = "G"
    NOTE_NAME_G_SHARP = "G#"
    NOTE_NAME_A_FLAT = "Ab"
    NOTE_NAME_A = "A"
    NOTE_NAME_A_SHARP = "A#"
    NOTE_NAME_B_FLAT = "Bb"
    NOTE_NAME_B = "B"
    
    _NOTES = {
        0: _NOTE_OFF,
        "c": _NOTE_C_1,
        "c#": _NOTE_C_SHARP_1,
        "db": _NOTE_D_FLAT_1,
        "d": _NOTE_D_1,
        "d#": _NOTE_D_SHARP_1,
        "eb": _NOTE_E_FLAT_1,
        "e": _NOTE_E_1,
        "f": _NOTE_F_1,
        "f#": _NOTE_F_SHARP_1,
        "gb": _NOTE_G_FLAT_1,
        "g": _NOTE_G_1,
        "g#": _NOTE_G_SHARP_1,
        "ab": _NOTE_A_FLAT_1,
        "a": _NOTE_A_1,
        "a#": _NOTE_A_SHARP_1,
        "bb": _NOTE_B_FLAT_1,
        "b": _NOTE_B_1
    }

    _MOTOR_PERCENT_CVT = { 
        '100': 15,
        '90': 14,
        '80': 13,
        '70': 12,
        '60': 10,
        '50': 9,
        '40': 7,
        '30': 5,
        '20': 3,
        '10': 2,
        '0': 0
    }

    _SERVO_PERCENT_CVT = { 
        '100': 100,
        '90': 90,
        '80': 80,
        '70': 70,
        '60': 60,
        '50': 50,
        '40': 40,
        '30': 30,
        '20': 20,
        '10': 10,
        '0': 0
    }

    _SERVO_DEGREE_CVT = {
        '180': 180,
        '175': 175,
        '170': 170,
        '165': 165,
        '160': 160,
        '155': 155,
        '150': 150,
        '145': 145,
        '140': 140,
        '135': 135,
        '130': 130,
        '125': 125,
        '120': 120,
        '115': 115,
        '110': 110,
        '105': 105,
        '100': 100,
        '95': 95,
        '90': 90,
        '85': 85,
        '80': 80,
        '75': 75,
        '70': 70,
        '65': 65,
        '60': 60,
        '55': 55,
        '50': 50,
        '45': 45,
        '40': 40,
        '35': 35,
        '30': 30,
        '25': 25,
        '20': 20,
        '15': 15,
        '10': 10,
        '5': 5,
        '0': 0
    }

    _MOTOR_DIR = { 
        'forward': 16,
        'backward': 32
    }

    _SERVO_DIR = { 
        'forward': 192,
        'backward': 208
    }

    _SERVO_DIR_FOR_DEG = { 
        'forward': 188,
        'backward': 189
    }

    _SERVO_STOP = 254
    _SERVO_RESET_DEG = 186

    _REMOTE_BTN_CVT = {
        'up': 1,
        'down': 2,
        'left': 3,
        'right': 4,
        '1': 10,
        '2': 11,
        '3': 12,
        '4': 13,
    }
    
    _robots = {}

    def __init__(self, index=0, port_name=None):
        if isinstance(index, str):
            index = 0
            port_name = index
        if index in Neosoco._robots:
            robot = Neosoco._robots[index]
            if robot: robot.dispose()
        Neosoco._robots[index] = self
        super(Neosoco, self).__init__(Neosoco.ID, "Neosoco", index)
        self._bpm = 60
        self._init(port_name)

    def dispose(self):
        # Lastly send init packet to stop all action in the controller
        self.write(Neosoco.OUTPUT_1, 0) 
        self.write(Neosoco.OUTPUT_2, 0) 
        self.write(Neosoco.OUTPUT_3, 0)
        self.write(Neosoco.LEFT_MOTOR, 0) 
        self.write(Neosoco.RIGHT_MOTOR, 0) 
        self.write(Neosoco.NOTE, 0)
        Neosoco._robots[self.get_index()] = None
        self._neobot._dispose()
        Runner.unregister_robot(self)

    def reset(self):
        self._bpm = 60
        self._neobot._reset()

    def _init(self, port_name):
        if Mode.is_link_mode():
            from neopia.neosoco_neobot import NeosocoLinkNeobot
            self._neobot = NeosocoLinkNeobot(self.get_index())
        else:
            from neopia.neosoco_neobot import NeosocoNeobot
            self._neobot = NeosocoNeobot(self.get_index())
        self._add_neobot(self._neobot)
        Runner.register_robot(self)
        Runner.start()
        self._neobot._init(port_name, Runner.get_robots())

    def find_device_by_id(self, device_id):
        return self._neobot.find_device_by_id(device_id)

    def _request_motoring_data(self):
        self._neobot._request_motoring_data()

    def _update_sensory_device_state(self):
        self._neobot._update_sensory_device_state()

    def _update_motoring_device_state(self):
        self._neobot._update_motoring_device_state()

    def _notify_sensory_device_data_changed(self):
        self._neobot._notify_sensory_device_data_changed()

    def _notify_motoring_device_data_changed(self):
        self._neobot._notify_motoring_device_data_changed()

    def set_value(self, port='out1', value=255):
        if isinstance(port, str) and isinstance(value, int):
            if value < 0 or value > 255:
                raise ValueError('Wrong value of input value')
                
            if port.lower() =='out1':
                self.write(Neosoco.OUTPUT_1, Util.round(value)) 
            elif port.lower() =='out2':
                self.write(Neosoco.OUTPUT_2, Util.round(value)) 
            elif port.lower() =='out3':
                self.write(Neosoco.OUTPUT_3, Util.round(value)) 
            elif port.lower() =='all':
                self.write(Neosoco.OUTPUT_1, Util.round(value)) 
                self.write(Neosoco.OUTPUT_2, Util.round(value)) 
                self.write(Neosoco.OUTPUT_3, Util.round(value))
            else:
                raise ValueError('Wrong value of port')
        else:
            raise TypeError

    def get_value(self, port='in1'):
        if isinstance(port, str):
            if port.lower() =='in1':
                return self.read(Neosoco.INPUT_1)
            elif port.lower() =='in2':
                return self.read(Neosoco.INPUT_2)
            elif port.lower() =='in3':
                return self.read(Neosoco.INPUT_3)
            elif port.lower() =='remo':
                return self.read(Neosoco.REMOCTL)
            elif port.lower() =='bat':
                return self.read(Neosoco.BATTERY)
            else:
                raise ValueError('Wrong value of port')
        else:
            raise TypeError

    def get_angle(self, port='in1'):
        if isinstance(port, str):
            if port.lower() =='in1':
                return self.read(Neosoco.INPUT_1)
            elif port.lower() =='in2':
                return self.read(Neosoco.INPUT_2)
            elif port.lower() =='in3':
                return self.read(Neosoco.INPUT_3)
            else:
                raise ValueError('Wrong value of port')
        else:
            raise TypeError

    def convert_scale(self, port='in1', omin=0, omax=255, tmin=0, tmax=100):
        if isinstance(port, str):
            if port.lower() =='in1':
                value = self.read(Neosoco.INPUT_1)
            elif port.lower() =='in2':
                value = self.read(Neosoco.INPUT_2)
            elif port.lower() =='in3':
                value = self.read(Neosoco.INPUT_3)
            else:
                raise ValueError('Wrong value of port')
            if isinstance(omin, (int, float)) and isinstance(omax, (int, float)) and \
                isinstance(tmin, (int, float)) and isinstance(tmax, (int, float)):
                if omin > omax:
                    temp = omin
                    omin = omax
                    omax = temp
                if tmin > tmax:
                    temp = tmin
                    tmin = tmax
                    tmax = temp
                value -= omin
                value = value * ((tmax - tmin) / (omax - omin))
                value += tmin
                value = min(tmax, value)
                value = max(tmin, value)
                return Util.round(value)
            else:
                raise TypeError
        else:
            raise TypeError

    def check_color(self, port='in1', color='white'):
        if isinstance(port and color, str):
            if port.lower() =='in1':
                c_value = self.read(Neosoco.INPUT_1)
            elif port.lower() =='in2':
                c_value = self.read(Neosoco.INPUT_2)
            elif port.lower() =='in3':
                c_value = self.read(Neosoco.INPUT_3)
            else:
                raise ValueError("Wrong value of port")

            if not color.lower() in Neosoco._COLORS.keys():
                raise ValueError('Wrong value of color')
            if (c_value >= 10 and c_value <= 50):
                if (color.lower() == self.COLOR_NAME_WHITE): 
                    return True
                else: 
                    return False
            elif (c_value >= 51 and c_value <= 90):
                if (color.lower() == self.COLOR_NAME_RED): 
                    return True
                else: 
                    return False
            elif (c_value >= 91 and c_value <= 130):
                if (color.lower() == self.COLOR_NAME_YELLOW): 
                    return True
                else: 
                    return False
            elif (c_value >= 131 and c_value <= 170):
                if (color.lower() == self.COLOR_NAME_GREEN): 
                    return True
                else: 
                    return False
            elif (c_value >= 171 and c_value <= 210):
                if (color.lower() == self.COLOR_NAME_BLUE): 
                    return True
                else: 
                    return False
            else:
                return False 
        else:
            raise TypeError

    def _write_to_output_port(self, port, out_val):
        if port.lower() == 'out1':
            self.write(Neosoco.OUTPUT_1, out_val)
        elif port.lower() == 'out2':
            self.write(Neosoco.OUTPUT_2, out_val)
        elif port.lower() == 'out3':
            self.write(Neosoco.OUTPUT_3, out_val)
        elif port.lower() == 'all':
            self.write(Neosoco.OUTPUT_1, out_val)
            self.write(Neosoco.OUTPUT_2, out_val)
            self.write(Neosoco.OUTPUT_3, out_val)
        else:
            raise ValueError('Wrong value of out port')

    def color_led_on(self, port='out1', red=255, blue=0, green=0):
        if isinstance(port, str):
            if isinstance(red and blue and green, (int, float)):
                red = max(red, 1)
                red = min(red, 251)
                green = max(green, 1)
                green = min(green, 251)
                blue = max(blue, 1)
                blue = min(blue, 251)

                # Red
                self._write_to_output_port(port, 252)
                Runner.wait(100)
                self._write_to_output_port(port, red)
                Runner.wait(100)
                # Green
                self._write_to_output_port(port, 253)
                Runner.wait(100)
                self._write_to_output_port(port, green)
                Runner.wait(100)
                # Blue
                self._write_to_output_port(port, 254)
                Runner.wait(100)
                self._write_to_output_port(port, blue)
                Runner.wait(100)
                # Accept
                self._write_to_output_port(port, 255)
                Runner.wait(100)
            else:
                raise TypeError
        else:
            raise TypeError

    def led_on(self, port='out1', brightness='100'):
        percent_cvt = {
            '100': 255,
            '90': 230,
            '80': 204,
            '70': 179,
            '60': 153,
            '50': 128,
            '40': 102,
            '30': 77,
            '20': 51,
            '10': 26
        }
        if brightness in percent_cvt.keys():
            cvt_val = percent_cvt[brightness]
        else:
            raise ValueError('Wrong value of percentage')

        if isinstance(port, str):
            self._write_to_output_port(port, cvt_val)
        else:
            raise TypeError

    def led_by_port(self, in_port='in1', out_port='out1'):
        if isinstance(in_port and out_port, str):
            in_value = self._convert_scale_from_input_port(in_port, 255)
            self._write_to_output_port(out_port, in_value)
        else:
            raise TypeError 

    def led_off(self, port='out1'):
        if isinstance(port, str):
            self._write_to_output_port(port, 0)
        else:
            raise TypeError

    def motor_move(self, direction='forward'):
        if isinstance(direction, str):
            speed = self._MOTOR_PERCENT_CVT['60']
            if direction.lower() =='forward':
                self.write(Neosoco.LEFT_MOTOR, self._MOTOR_DIR['forward']+speed)
                self.write(Neosoco.RIGHT_MOTOR, self._MOTOR_DIR['forward']+speed)
            elif direction.lower() =='backward':
                self.write(Neosoco.LEFT_MOTOR, self._MOTOR_DIR['backward']+speed)
                self.write(Neosoco.RIGHT_MOTOR, self._MOTOR_DIR['backward']+speed)
            elif direction.lower() =='left':
                self.write(Neosoco.LEFT_MOTOR, self._MOTOR_DIR['backward']+speed)
                self.write(Neosoco.RIGHT_MOTOR, self._MOTOR_DIR['forward']+speed)
            elif direction.lower() =='right':
                self.write(Neosoco.LEFT_MOTOR, self._MOTOR_DIR['forward']+speed)
                self.write(Neosoco.RIGHT_MOTOR, self._MOTOR_DIR['backward']+speed)
            elif direction.lower() =='stop':
                self.write(Neosoco.LEFT_MOTOR, 0)
                self.write(Neosoco.RIGHT_MOTOR, 0)
            else:
                raise ValueError('Wrong value of direction')
        else:
            raise TypeError
        
    def motor_stop(self, which_motor='both'):
        if isinstance(which_motor, str):
            if which_motor.lower() =='right':
                self.write(Neosoco.RIGHT_MOTOR, 0)
            elif which_motor.lower() =='left':
                self.write(Neosoco.LEFT_MOTOR, 0)
            elif which_motor.lower() =='both':
                self.write(Neosoco.LEFT_MOTOR, 0)
                self.write(Neosoco.RIGHT_MOTOR, 0)
            else:
                raise ValueError('Wrong value of motor')
        else:
            raise TypeError

    def _convert_sacle_within_100(self, value, cvt_max_val):
        # Map to 0~limited_val from 0~100(max), it's same as Entry
        value = max(value, 0)
        value = min(value, 100)
        value = math.ceil(value / 100 * cvt_max_val)
        return value

    def _convert_scale_from_input_port(self, port, cvt_max_val):
        if port.lower() =='in1':
            value = self.read(Neosoco.INPUT_1)
        elif port.lower() =='in2':
            value = self.read(Neosoco.INPUT_2)
        elif port.lower() =='in3':
            value = self.read(Neosoco.INPUT_3)
        else:
            raise ValueError('Wrong value of port')

        if value:
            value = self._convert_sacle_within_100(value, cvt_max_val)
        return value

    def motor_rotate(self, motor='both', direction='forward', speed='100'):
        if isinstance(motor, str) and isinstance(direction, str) and isinstance(speed, str):
            if speed == 'in1' or speed == 'in2' or speed == 'in3' :
                speed = self._convert_scale_from_input_port(speed, 15)
            elif speed in self._MOTOR_PERCENT_CVT.keys():
                speed = self._MOTOR_PERCENT_CVT[speed]
            else:
                raise ValueError('Wrong value of speed')

            if direction.lower() =='forward':
                l_direction = self._MOTOR_DIR['forward']
                r_direction = self._MOTOR_DIR['forward']
            elif direction.lower() =='backward':
                l_direction = self._MOTOR_DIR['backward']
                r_direction = self._MOTOR_DIR['backward']
            elif direction.lower() =='left':
                l_direction = self._MOTOR_DIR['backward']
                r_direction = self._MOTOR_DIR['forward']
            elif direction.lower() =='right':
                l_direction = self._MOTOR_DIR['forward']
                r_direction = self._MOTOR_DIR['backward']
            else:
                raise ValueError('Wrong value of direction')

            if motor.lower() == 'both':
                self.write(Neosoco.LEFT_MOTOR, l_direction + speed)
                self.write(Neosoco.RIGHT_MOTOR, r_direction + speed)
            elif motor.lower() == 'left':
                self.write(Neosoco.LEFT_MOTOR, l_direction + speed)
            elif motor.lower() == 'right':
                self.write(Neosoco.RIGHT_MOTOR, r_direction + speed)
            else:
                raise ValueError('Wrong value of motor')
        else:
            raise TypeError

    def servo_rotate(self, port='out1', direction='forward', speed='100'):
        if isinstance(port, str) and isinstance(direction, str) and isinstance(speed, str):
            if speed == 'in1' or speed == 'in2' or speed == 'in3' :
                speed = self._convert_scale_from_input_port(speed, 10)
            elif speed in self._SERVO_PERCENT_CVT.keys():
                speed = self._SERVO_PERCENT_CVT[speed]
                speed = self._convert_sacle_within_100(speed, 10)
            else:
                raise ValueError('Wrong value of speed')

            if direction.lower() =='forward':
                direction = self._SERVO_DIR['forward']
            elif direction.lower() =='backward':
                direction = self._SERVO_DIR['backward']
            else:
                raise ValueError('Wrong value of direction')

            out_val = direction + speed
            if out_val == direction: # Speed is 0
                out_val = self._SERVO_STOP
            else:
                out_val = out_val - 1
            
            self._write_to_output_port(port, out_val)
        else:
            raise TypeError

    def servo_reset_degree(self, port='out1'):
        if isinstance(port, str):
            self._write_to_output_port(port, self._SERVO_RESET_DEG)
            Runner.wait(100)
            self._write_to_output_port(port, 1) # Set where the motor is to 1 degree
            Runner.wait(100)
        else:
            raise TypeError

    def servo_rotate_by_degree(self, port='out1', direction='forward', speed='100', degree='90'):
        if isinstance(port, str) and isinstance(direction, str) and \
            isinstance(speed, str) and isinstance(degree, str):
            if direction.lower() =='forward':
                direction = self._SERVO_DIR_FOR_DEG['forward']
            elif direction.lower() =='backward':
                direction = self._SERVO_DIR_FOR_DEG['backward']
            else:
                raise ValueError('Wrong value of direction')

            if speed.lower() =='in1':
                speed = self.read(Neosoco.INPUT_1)
            elif speed.lower() =='in2':
                speed = self.read(Neosoco.INPUT_2)
            elif port.lower() =='in3':
                speed = self.read(Neosoco.INPUT_3)
            elif speed in self._SERVO_PERCENT_CVT.keys():
                speed = self._SERVO_PERCENT_CVT[speed]
            else:
                raise ValueError('Wrong value of speed')
            speed = max(speed, 0)
            speed = min(speed, 100)
            speed = math.ceil(speed / 10) + 240 # range of speed is 240 ~ 250
            
            if degree.lower() =='in1':
                degree = self.read(Neosoco.INPUT_1)
            elif port.lower() =='in2':
                degree = self.read(Neosoco.INPUT_2)
            elif port.lower() =='in3':
                degree = self.read(Neosoco.INPUT_3)
            elif degree in self._SERVO_DEGREE_CVT.keys():
                degree = self._SERVO_DEGREE_CVT[degree]
            else:
                raise ValueError('Wrong value of degree')
            degree = max(degree, 0)
            degree = min(degree, 180) # max of degree is 180
            degree = degree + 1

            self._write_to_output_port(port, direction)
            Runner.wait(100)
            self._write_to_output_port(port, speed)
            Runner.wait(100)
            self._write_to_output_port(port, degree)
            Runner.wait(100)
        else:
            raise TypeError

    def servo_stop(self, port = 'out1'):
        if isinstance(port, str):
            self._write_to_output_port(port, self._SERVO_STOP)
        else:
            raise TypeError

    def buzzer(self, pitch='3', note='c', beats='4'):
        self.write(Neosoco.NOTE, 0) # init
        if not isinstance(pitch, str) or not (int(pitch) >= 1 and int(pitch) <= 6):
            raise ValueError('Wrong value of pitch')
        if note != 0 and not note.lower() in Neosoco._NOTES.keys():
            raise ValueError('Wrong value of note')
        else:
            pitch = Neosoco._NOTES[note.lower()] + (int(pitch) - 1) * 12
        if isinstance(pitch, (int, float)):
            bpm_cvt = {
                '2': 1,
                '4': 0.5,
                '8': 0.25,
                '16': 0.125
            }
            if beats in bpm_cvt.keys():
                bpm = self._bpm # default 60
                if note == 0:
                    self.write(Neosoco.NOTE, Neosoco._NOTE_OFF)
                    Runner.wait(bpm_cvt[beats] * 60 * 1000.0 / bpm)
                else:
                    timeout = bpm_cvt[beats] * 60 * 1000.0 / bpm
                    tail = 0
                    if timeout > 100:
                        tail = 100
                    self.write(Neosoco.NOTE, pitch)
                    Runner.wait(timeout - tail)
                    self.write(Neosoco.NOTE, Neosoco._NOTE_OFF)
                    if tail > 0:
                        Runner.wait(tail)
            else:
                raise ValueError('Wrong value of beats')

    def buzzer_by_port(self, port='in1'):
        if isinstance(port, str):
            # Map to 0~65 from 0~100(max), it's same as Entry
            value = self._convert_scale_from_input_port(port, 65)
            self.write(Neosoco.NOTE, value)
        else:
            raise TypeError

    def buzzer_stop(self):
        self.write(Neosoco.NOTE, 0)

    def remote_button(self, button='1'):
        if isinstance(button, str):
            if button in self._REMOTE_BTN_CVT.keys():
                if self._REMOTE_BTN_CVT[button] == self.read(Neosoco.REMOCTL):
                    return True
                else:
                    return False
            else:
                raise ValueError('Wrong value of button')
        else:
            raise TypeError
