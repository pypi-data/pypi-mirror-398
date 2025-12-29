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

import sys
import threading
import time
from timeit import default_timer as timer
import websocket
import json
from neopia.runner import Runner
from neopia.connector import State


class Link(object):
    def __init__(self, tag, neobot):
        self._neobot = None
        self._tag = tag
        self._neobot = neobot
        self._connection_state = -1

    def get_motoring(self):
        return self._neobot.get_motoring()

    def handle_sensory(self, received):
        connection_state = received['connectionState']
        if connection_state != self._connection_state:
            self._connection_state = connection_state
            if connection_state == State.CONNECTING:
                Linker.print_message(self._tag, 'Connecting')
            elif connection_state == State.CONNECTED:
                Linker.print_message(self._tag, 'Connected')
            elif connection_state == State.CONNECTION_LOST:
                Linker.print_error(self._tag, 'Connection lost')
            elif connection_state == State.DISCONNECTED:
                Linker.print_error(self._tag, 'Disconnected')
        if self._neobot is not None:
            self._neobot.decode_sensory(received)

    def handle_motoring(self):
        self._neobot.encode_motoring()


class Linker(object):
    _links = {}
    _links_by_group = {}
    _packet = {}
    _url = ''
    _wsapp = None
    _start_flag = False
    _keep_running = False
    _keep_send = False
    _recv_thread = None
    _send_thread = None
    _server_state = False
    _opened = False

    @staticmethod
    def _get_link(module, index):
        key = module + str(index)
        if key in Linker._links:
            return Linker._links[key]
        else:
            return None

    @staticmethod
    def _get_or_create_link(group, module, index, tag, neobot):
        index = str(index)
        key = module + index
        if key in Linker._links:
            link = Linker._links[key]
        else:
            link = Link(tag, neobot)
            Linker._links[key] = link
            Linker._packet[key] = link.get_motoring()
        Linker._links_by_group[group + index] = link
        return link

    @staticmethod
    def register_neobot(group, module, index, tag, neobot):
        Linker._get_or_create_link(group, module, index, tag, neobot)

    @staticmethod
    def _on_open(wsapp):
        Linker._opened = True
        Linker._server_state = True

    @staticmethod
    def _on_close(wsapp, close_status_code, close_msg):
        Linker._opened = False
        Linker._server_state = False
        if Linker._keep_running:
            Runner.wait(500)
            if Linker._opened == False:
                Linker._open()

    @staticmethod
    def _on_message(wsapp, message):
        try:
            received = json.loads(message)
            index = received['index']
            if index >= 0:
                link = Linker._get_link(received['module'], index)
                if link is None:
                    link = Linker._get_link(received['group'], index)
                if link is not None:
                    link.handle_sensory(received)
        except:
            pass

    @staticmethod
    def _on_error(wsapp, ex):
        pass

    @staticmethod
    def _open():
        try:
            Linker._wsapp = websocket.WebSocketApp(Linker._url, on_open=Linker._on_open, on_close=Linker._on_close, on_message=Linker._on_message, on_error=Linker._on_error)
            Linker._wsapp.run_forever()
        except:
            pass

    @staticmethod
    def _send_forever():
        target_time = timer()
        while Linker._keep_running and Linker._keep_send:
            if Linker._opened:
                if timer() > target_time:
                    try:
                        if Linker._wsapp is not None:
                            links = Linker._links
                            for key in links:
                                link = links[key]
                                if link is not None:
                                    link.handle_motoring()
                            str = json.dumps(Linker._packet)
                            if Linker._wsapp is not None:
                                Linker._wsapp.send(str)
                    except:
                        pass
                    target_time += 0.02
                    time.sleep(0.01)
                time.sleep(0.001)
            else:
                time.sleep(0.01)

    @staticmethod
    def start(url):
        if Linker._start_flag == False:
            Linker._start_flag = True
            Linker._url = url
            Linker._keep_running = True
            thread = threading.Thread(target=Linker._open)
            Linker._recv_thread = thread
            thread.daemon = True
            thread.start()
            Linker._keep_send = True
            thread = threading.Thread(target=Linker._send_forever)
            Linker._send_thread = thread
            thread.daemon = True
            thread.start()

    @staticmethod
    def stop():
        if Linker._start_flag:
            Linker._start_flag = False
            Linker._keep_send = False
            Linker._keep_running = False
            thread = Linker._send_thread
            Linker._send_thread = None
            if thread:
                thread.join()
            thread = Linker._recv_thread
            Linker._recv_thread = None
            if thread:
                thread.join()
            if Linker._wsapp:
                Linker._wsapp.teardown()

    @staticmethod
    def print_message(tag, message):
        sys.stdout.write("{} {}\n".format(tag, message))

    @staticmethod
    def print_error(tag, message):
        sys.stderr.write("{} {}\n".format(tag, message))