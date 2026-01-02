# -*- coding: utf-8 -*-

# Copyright (C) 2019-2022  Marcus Rickert
#
# See https://github.com/marcus67/some_flask_helpers
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import logging
import time
from typing import Optional

import werkzeug
from werkzeug.serving import BaseWSGIServer

orig_make_server = werkzeug.serving.make_server

the_server: Optional[BaseWSGIServer] = None

def my_make_server(*argc, **argv):
    global the_server
    the_server = orig_make_server(*argc, **argv)
    return the_server

werkzeug.serving.make_server = my_make_server


class FlaskStopper(object):

    def __init__(self, p_app, p_logger=None):

        self._app = p_app
        self._logger = p_logger

        if self._logger is None:
            self._logger = logging.getLogger('flaskstopper')

    def set_secret(self, p_secret):
        self._secret = p_secret

    def stop(self, host=None, port=None):

        try:
            if the_server is None:
                self._logger.info("Waiting for a second for the web server to be available for shutdown.")
                time.sleep(1)

            self._logger.info("Shutting down the web server.")
            the_server.shutdown()

        except Exception as e:
            msg = "Exception '{exception}' while shutting down the web server"
            self._logger.error(msg.format(exception=str(e)))

    def destroy(self):
        pass
