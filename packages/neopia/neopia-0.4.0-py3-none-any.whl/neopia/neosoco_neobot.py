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

import time
import threading

from neopia.runner import Runner
from neopia.model import DeviceType
from neopia.model import DataType
from neopia.model import Neobot
from neopia.connector import Result
from neopia.neosoco import Neosoco
from neopia.serial_connector import SerialConnector
from neopia.linker import Linker

START_BYTES = 'CDAB'


class NeosocoConnectionChecker(object):
    def __init__(self, neobot):
        self._neobot = neobot

    def check(self, info):
        if info[1] == "Hamster" and info[2] == "04":
            self._neobot._set_model_code(0x04)
            return True
        elif info[2] == "0E":
            self._neobot._set_model_code(0x0E)
            return True
        else:
            return False


class NeosocoNeobot(Neobot):
    _COLOR_TO_RGB = {
        0: (0, 0, 0),
        1: (0, 0, 255),
        2: (0, 255, 0),
        3: (0, 255, 255),
        4: (255, 0, 0),
        5: (255, 0, 255),
        6: (255, 255, 0),
        7: (255, 255, 255)
    }
    _SPEED_TO_GAIN = {
        1: 6,
        2: 6,
        3: 5,
        4: 5,
        5: 4,
        6: 4,
        7: 3,
        8: 3,
        9: 2,
        10: 2
    }

    def __init__(self, index):
        super(NeosocoNeobot, self).__init__(Neosoco.ID, "Neosoco", 0x00400000)
        self._index = index
        self._connector = None
        self._ready = False
        self._thread = None
        self._thread_lock = threading.Lock()

        self._output_1 = 0
        self._output_2 = 0
        self._output_3 = 0
        self._left_motor = 0
        self._right_motor = 0
        self._note = 0
        
        self._create_model()

    def _set_model_code(self, code):
        self._model_code = code

    def _create_model(self):
        from neopia.neosoco import Neosoco
        dict = self._device_dict = {}
        dict[Neosoco.OUTPUT_1] = self._output_1_device = self._add_device(Neosoco.OUTPUT_1, "Output1", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Neosoco.OUTPUT_2] = self._output_2_device = self._add_device(Neosoco.OUTPUT_2, "Output2", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Neosoco.OUTPUT_3] = self._output_3_device = self._add_device(Neosoco.OUTPUT_3, "Output3", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Neosoco.INPUT_1] = self._input_1_device = self._add_device(Neosoco.INPUT_1, "Input1", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Neosoco.INPUT_2] = self._input_2_device = self._add_device(Neosoco.INPUT_2, "Input2", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Neosoco.INPUT_3] = self._input_3_device = self._add_device(Neosoco.INPUT_3, "Input3", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Neosoco.REMOCTL] = self._remoctl_device = self._add_device(Neosoco.REMOCTL, "RemoteCtl", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Neosoco.BATTERY] = self._battery_device = self._add_device(Neosoco.BATTERY, "Battery", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Neosoco.LEFT_MOTOR] = self._left_motor_device = self._add_device(Neosoco.LEFT_MOTOR, "LeftMotor", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 47, 0)
        dict[Neosoco.RIGHT_MOTOR] = self._right_motor_device = self._add_device(Neosoco.RIGHT_MOTOR, "RightMotor", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 47, 0)
        dict[Neosoco.NOTE] = self._note_device = self._add_device(Neosoco.NOTE, "Note", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 72, 0)

    def find_device_by_id(self, device_id):
        return self._device_dict.get(device_id)

    def _run(self):
        try:
            while self._running or self._releasing:
                if self._receive(self._connector):
                    self._send(self._connector)
                    self._releasing = False
                time.sleep(0.005)
        except:
            pass

    def _init(self, port_name=None, reg_neobots=None):
        Runner.register_required()
        self._running = True
        thread = threading.Thread(target=self._run)
        self._thread = thread
        thread.daemon = True
        thread.start()

        tag = "Neosoco[{}]".format(self._index)
        self._connector = SerialConnector(tag, NeosocoConnectionChecker(self))
        result = self._connector.open(port_name, reg_neobots)
        if result == Result.FOUND:
            while self._ready == False and self._is_disposed() == False:
                time.sleep(0.01)
        elif result == Result.NOT_AVAILABLE:
            Runner.register_checked()

    def _release(self):
        self._releasing = True
        self._running = False
        thread = self._thread
        self._thread = None
        if thread:
            thread.join()

        connector = self._connector
        self._connector = None
        if connector:
            # Lastly send init packet to stop all action in the controller
            self._encode_init_packet()
            self._send(connector)
            connector.close()

    def _dispose(self):
        if self._is_disposed() == False:
            super(NeosocoNeobot, self)._dispose()
            self._release()

    def _reset(self):
        super(NeosocoNeobot, self)._reset()

        self._output_1 = 0
        self._output_2 = 0
        self._output_3 = 0
        self._left_motor = 0
        self._right_motor = 0
        self._note = 0

    def _request_motoring_data(self):
        with self._thread_lock:
            self._output_1 = self._output_1_device.read()
            self._output_2 = self._output_2_device.read()
            self._output_3 = self._output_3_device.read()
            self._left_motor = self._left_motor_device.read()
            self._right_motor = self._right_motor_device.read()
            self._note = self._note_device.read()
        self._clear_written()

    def _color_to_rgb(self, color):
        if isinstance(color, (int, float)):
            color = int(color)
            if color > 7: color = 7
            elif color < 0: color = 0
            return NeosocoNeobot._COLOR_TO_RGB[color]
        return NeosocoNeobot._COLOR_TO_RGB[0]

    def _speed_to_gain(self, speed):
        if isinstance(speed, (int, float)):
            speed = int(speed)
            if speed > 10: speed = 10
            elif speed < 1: speed = 1
            return NeosocoNeobot._SPEED_TO_GAIN[speed]
        return 2
    
    def _encode_init_packet(self):
        result = ""
        with self._thread_lock:
            result += START_BYTES
            result += self._to_hex(0) # OUT1
            result += self._to_hex(0) # OUT2
            result += self._to_hex(0) # OUT3
            result += self._to_hex(0) # MLA
            result += self._to_hex(0) # MRA
            result += self._to_hex(0) # BUZZER
            result += self._to_hex(0) # FND
            result += self._to_hex(0) # Not Used
            result += self._to_hex(self._make_checksum(result)) # Checksum
        return result

    def _encode_motoring_packet(self):
        result = ""
        with self._thread_lock:
            result += START_BYTES
            result += self._to_hex(self._output_1) # OUT1
            result += self._to_hex(self._output_2) # OUT2
            result += self._to_hex(self._output_3) # OUT3
            result += self._to_hex(self._left_motor)  # MLA
            result += self._to_hex(self._right_motor) # MRA
            result += self._to_hex(self._note) # BUZZER
            result += self._to_hex(0) # FND
            result += self._to_hex(0) # Not Used
            result += self._to_hex(self._make_checksum(result)) # Checksum
        return result

    def _decode_sensory_packet(self, packet):
        # packet[0]~[1] is StartBytes
        self._input_1_device._put(packet[2])
        self._input_2_device._put(packet[3])
        self._input_3_device._put(packet[4])
        self._remoctl_device._put(packet[5])
        self._battery_device._put(packet[6])
        return True

    def _receive(self, connector):
        if connector:
            packet = connector.read()
            if packet:
                if self._decode_sensory_packet(packet):
                    if self._ready == False:
                        self._ready = True
                        Runner.register_checked()
                    self._notify_sensory_device_data_changed()
                return True
        return False

    def _send(self, connector):
        if connector:
            packet = self._encode_motoring_packet()
            connector.write(packet)


class NeosocoLinkNeobot(NeosocoNeobot):
    def __init__(self, index):
        super(NeosocoLinkNeobot, self).__init__(index)
        self._is_hamster_s = False
        self._motoring = {
            'module': 'hamster',
            'index': index
        }
        self._clear_id_and_motoring()

    def _init(self, port_name=None):
        self._tag = "Neosoco[{}]".format(self._index)
        Linker.register_neobot('hamster', 'hamster', self._index, self._tag, self)
        while self._ready == False and self._is_disposed() == False:
            time.sleep(0.01)
        if self._is_hamster_s:
            self._config_band_width = 0
            self._motoring['configBandWidth'] = 0

    def _release(self):
        super(NeosocoLinkNeobot, self)._release()
        Linker.print_message(self._tag, 'Disposed')

    def _clear_id_and_motoring(self):
        self._topology_id = 0
        self._left_led_id = 0
        self._right_led_id = 0
        self._pulse_id = 0
        self._note_id = 0
        self._sound_id = 0
        self._line_tracer_mode_id = 0
        self._line_tracer_gain_id = 0
        self._line_tracer_speed_id = 0
        self._io_mode_a_id = 0
        self._io_mode_b_id = 0
        self._motion_id = 0
        self._motor_mode_id = 0
        self._config_proximity_id = 0
        self._config_gravity_id = 0
        self._config_band_width_id = 0
        self._line_tracer_state_id = -1
        self._tilt_id = -1
        self._battery_state_id = -1
        motoring = self._motoring
        motoring['leftWheel'] = self._left_wheel
        motoring['rightWheel'] = self._right_wheel
        motoring['buzzer'] = self._buzzer
        motoring['outputA'] = self._output_a
        motoring['outputB'] = self._output_b
        motoring['topologyId'] = 0
        motoring['topology'] = self._topology
        motoring['leftLedId'] = 0
        motoring['leftLed'] = self._left_led
        motoring['leftRed'] = 0
        motoring['leftGreen'] = 0
        motoring['leftBlue'] = 0
        motoring['rightLedId'] = 0
        motoring['rightLed'] = self._right_led
        motoring['rightRed'] = 0
        motoring['rightGreen'] = 0
        motoring['rightBlue'] = 0
        motoring['pulseId'] = 0
        motoring['pulse'] = 0
        motoring['noteId'] = 0
        motoring['note'] = self._note
        motoring['soundId'] = 0
        motoring['sound'] = 0
        motoring['lineTracerModeId'] = 0
        motoring['lineTracerMode'] = self._line_tracer_mode
        motoring['lineTracerGainId'] = 0
        motoring['lineTracerGain'] = 4
        motoring['lineTracerSpeedId'] = 0
        motoring['lineTracerSpeed'] = self._line_tracer_speed
        motoring['ioModeAId'] = 0
        motoring['ioModeA'] = self._io_mode_a
        motoring['ioModeBId'] = 0
        motoring['ioModeB'] = self._io_mode_b
        motoring['motorModeId'] = 0
        motoring['motorMode'] = 0
        motoring['configProximityId'] = 0
        motoring['configProximity'] = self._config_proximity
        motoring['configGravityId'] = 0
        motoring['configGravity'] = self._config_gravity
        motoring['configBandWidthId'] = 0
        motoring['configBandWidth'] = self._config_band_width

    def _reset(self):
        super(NeosocoLinkNeobot, self)._reset()
        self._clear_id_and_motoring()

    def get_motoring(self):
        return self._motoring

    def encode_motoring(self):
        with self._thread_lock:
            motoring = self._motoring
            motoring['leftWheel'] = self._left_wheel
            motoring['rightWheel'] = self._right_wheel
            motoring['buzzer'] = self._buzzer
            motoring['outputA'] = self._output_a
            motoring['outputB'] = self._output_b
            if self._note_written:
                self._note_written = False
                motoring['note'] = self._note
                self._note_id = (self._note_id % 255) + 1
                motoring['noteId'] = self._note_id
            if self._line_tracer_mode_written:
                self._line_tracer_mode_written = False
                motoring['lineTracerMode'] = self._line_tracer_mode
                self._line_tracer_mode_id = (self._line_tracer_mode_id % 255) + 1
                motoring['lineTracerModeId'] = self._line_tracer_mode_id
            if self._io_mode_a_written:
                self._io_mode_a_written = False
                motoring['ioModeA'] = self._io_mode_a
                self._io_mode_a_id = (self._io_mode_a_id % 255) + 1
                motoring['ioModeAId'] = self._io_mode_a_id
            if self._io_mode_b_written:
                self._io_mode_b_written = False
                motoring['ioModeB'] = self._io_mode_b
                self._io_mode_b_id = (self._io_mode_b_id % 255) + 1
                motoring['ioModeBId'] = self._io_mode_b_id
            if self._config_proximity_written:
                self._config_proximity_written = False
                motoring['configProximity'] = self._config_proximity
                self._config_proximity_id = (self._config_proximity_id % 255) + 1
                motoring['configProximityId'] = self._config_proximity_id
            if self._config_gravity_written:
                self._config_gravity_written = False
                motoring['configGravity'] = self._config_gravity
                self._config_gravity_id = (self._config_gravity_id % 255) + 1
                motoring['configGravityId'] = self._config_gravity_id
            if self._config_band_width_written:
                self._config_band_width_written = False
                motoring['configBandWidth'] = self._config_band_width
                self._config_band_width_id = (self._config_band_width_id % 255) + 1
                motoring['configBandWidthId'] = self._config_band_width_id
            if self._is_hamster_s:
                motoring['module'] = 'hamsterS'
                if self._left_led_written:
                    self._left_led_written = False
                    rgb = self._color_to_rgb(self._left_led)
                    motoring['leftRed'] = rgb[0]
                    motoring['leftGreen'] = rgb[1]
                    motoring['leftBlue'] = rgb[2]
                if self._right_led_written:
                    self._right_led_written = False
                    rgb = self._color_to_rgb(self._right_led)
                    motoring['rightRed'] = rgb[0]
                    motoring['rightGreen'] = rgb[1]
                    motoring['rightBlue'] = rgb[2]
                if self._line_tracer_speed_written:
                    self._line_tracer_speed_written = False
                    motoring['lineTracerSpeed'] = self._line_tracer_speed
                    self._line_tracer_speed_id = (self._line_tracer_speed_id % 255) + 1
                    motoring['lineTracerSpeedId'] = self._line_tracer_speed_id
                    motoring['lineTracerGain'] = self._speed_to_gain(self._line_tracer_speed)
                    self._line_tracer_gain_id = (self._line_tracer_gain_id % 255) + 1
                    motoring['lineTracerGainId'] = self._line_tracer_gain_id
                motoring['pulse'] = 0
                self._pulse_id = (self._pulse_id % 255) + 1
                motoring['pulseId'] = self._pulse_id
                motoring['sound'] = 0
                self._sound_id = (self._sound_id % 255) + 1
                motoring['soundId'] = self._sound_id
                motoring['motorMode'] = 0
                self._motor_mode_id = (self._motor_mode_id % 255) + 1
                motoring['motorModeId'] = self._motor_mode_id
            else:
                motoring['module'] = 'hamster'
                if self._topology_written:
                    self._topology_written = False
                    motoring['topology'] = self._topology
                    self._topology_id = (self._topology_id % 255) + 1
                    motoring['topologyId'] = self._topology_id
                if self._left_led_written:
                    self._left_led_written = False
                    motoring['leftLed'] = self._left_led
                    self._left_led_id = (self._left_led_id % 255) + 1
                    motoring['leftLedId'] = self._left_led_id
                if self._right_led_written:
                    self._right_led_written = False
                    motoring['rightLed'] = self._right_led
                    self._right_led_id = (self._right_led_id % 255) + 1
                    motoring['rightLedId'] = self._right_led_id
                if self._line_tracer_speed_written:
                    self._line_tracer_speed_written = False
                    motoring['lineTracerSpeed'] = self._line_tracer_speed
                    self._line_tracer_speed_id = (self._line_tracer_speed_id % 255) + 1
                    motoring['lineTracerSpeedId'] = self._line_tracer_speed_id

    def decode_sensory(self, received):
        self._is_hamster_s = received['module'] == 'hamsterS'
        self._ready = True
        self._signal_strength_device._put(received['signalStrength'])
        self._left_proximity_device._put(received['leftProximity'])
        self._right_proximity_device._put(received['rightProximity'])
        self._left_floor_device._put(received['leftFloor'])
        self._right_floor_device._put(received['rightFloor'])
        self._acceleration_device._put_at(0, received['accelerationX'])
        self._acceleration_device._put_at(1, received['accelerationY'])
        self._acceleration_device._put_at(2, received['accelerationZ'])
        self._light_device._put(received['light'])
        self._temperature_device._put(received['temperature'])
        self._input_a_device._put(received['inputA'])
        self._input_b_device._put(received['inputB'])
        t = received['lineTracerStateId']
        if t != self._line_tracer_state_id:
            if self._line_tracer_state_id != -1: self._line_tracer_state_device._put(received['lineTracerState'])
            self._line_tracer_state_id = t
        t = received['tiltId']
        if t != self._tilt_id:
            if self._tilt_id != -1: self._tilt_device._put(received['tilt'])
            self._tilt_id = t
        t = received['batteryStateId']
        if t != self._battery_state_id:
            if self._battery_state_id != -1: self._battery_state_device._put(received['batteryState'])
            self._battery_state_id = t