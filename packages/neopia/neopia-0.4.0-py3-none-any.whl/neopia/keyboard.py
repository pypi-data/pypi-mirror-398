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

from pynput.keyboard import Key, KeyCode, Listener


class Keyboard(object):
    BACKSPACE = Key.backspace
    TAB = Key.tab
    ESC = Key.esc

    ENTER = Key.enter
    F1 = Key.f1
    F2 = Key.f2
    F3 = Key.f3
    F4 = Key.f4
    F5 = Key.f5
    F6 = Key.f6
    F7 = Key.f7
    F8 = Key.f8
    F9 = Key.f9
    F10 = Key.f10
    F11 = Key.f11
    F12 = Key.f12

    HOME = Key.home
    UP = Key.up
    PAGE_UP = Key.page_up
    LEFT = Key.left
    RIGHT = Key.right
    END = Key.end
    DOWN = Key.down
    PAGE_DOWN = Key.page_down
    SPACE = Key.space
    DELETE = Key.delete

    @staticmethod
    def key_to_str(key: KeyCode):
        return key.char
    
    @staticmethod
    def read(handler):
        with Listener(on_press = handler) as listener:
            listener.join()
