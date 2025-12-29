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

from neopia.linker import Linker


class Mode(object):
    _SERIAL_MODE = 0
    _LINK_MODE = 1
    _mode = 0

    @staticmethod
    def is_serial_mode():
        return Mode._mode == Mode._SERIAL_MODE

    @staticmethod
    def set_serial_mode():
        Mode._mode = Mode._SERIAL_MODE
        Linker.stop()

    @staticmethod
    def is_link_mode():
        return Mode._mode == Mode._LINK_MODE

    @staticmethod
    def set_link_mode(url):
        Mode._mode = Mode._LINK_MODE
        Linker.start(url)