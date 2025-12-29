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

import os, datetime

class Util(object):
    @staticmethod
    def round(value):
        if isinstance(value, (int, float)):
            if value < 0:
                return -int(0.5 - value)
            else:
                return int(0.5 + value)
        else:
            return 0
        
    @staticmethod
    def make_root_dir(path):
        path = path.replace('\\', '/')
        if path[-1:] != '/':
            path += '/'
        os.makedirs(path, exist_ok=True)
        return path
    
    @staticmethod
    def make_file_path(path, prefix_name):
        path = path.replace('\\', '/')
        extension = '.png'
        name = prefix_name + "_" + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        name += extension
        path += name
        return path
