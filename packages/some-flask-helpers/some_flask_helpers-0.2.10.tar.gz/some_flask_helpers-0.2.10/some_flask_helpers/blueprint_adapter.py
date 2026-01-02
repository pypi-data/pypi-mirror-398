# -*- coding: utf-8 -*-

# Copyright (C) 2019-2024  Marcus Rickert
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

import inspect
import logging

LOG_NAME = "blueprint_adapter"

# See https://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3
def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls

        meth = meth.__func__  # fallback to __qualname__ parsing

    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])

        if isinstance(cls, type):
            return cls

    return None


class MethodRoute(object):

    def __init__(self, p_rule, p_endpoint, p_view_method, p_options):
        self.rule = p_rule
        self.endpoint = p_endpoint
        self.view_method = p_view_method
        self.options = p_options
        self.instance = None

    # Note : the lambda function cannot be created in the loop of method Blueprint.assign_view_instance
    # since the loop variable (and hence the view method) will be the same for all instances of
    # the loop. See http://math.andrej.com/2009/04/09/pythons-lambda-is-broken/comment-page-1/
    def create_lambda(self, p_instance):
        self.instance = p_instance
        return lambda **p_options: self.view_method(p_instance, **p_options)

    def unassign(self):
        self.instance = None

    @property
    def instance_name(self):
        if self.instance is None:
            return "NOT ASSIGNED TO INSTANCE!"

        return self.instance.__class__.__name__


class BlueprintAdapter(object):
    _logger: logging.Logger = logging.getLogger(LOG_NAME)

    def __init__(self):

        self._unassigned_method_routes: list[MethodRoute] = []
        self._assigned_method_routes: list[MethodRoute] = []

    @classmethod
    def set_logger(cls, p_logger: logging.Logger) -> None:
        cls._logger = p_logger

    def route_method(self, p_rule, **p_options):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """

        def decorator(p_view_method):
            endpoint = p_options.pop("endpoint", p_view_method.__name__)

            self._unassigned_method_routes.append(
                MethodRoute(p_rule=p_rule, p_endpoint=endpoint, p_view_method=p_view_method, p_options=p_options))

            return p_view_method

        return decorator

    def assign_view_handler_instance(self, p_blueprint, p_view_handler_instance):

        for method_route in self._unassigned_method_routes:
            view_method_class = get_class_that_defined_method(method_route.view_method)

            if view_method_class is not None and isinstance(p_view_handler_instance, view_method_class):
                self._assigned_method_routes.append(method_route)

                p_blueprint.add_url_rule(rule=method_route.rule, endpoint=method_route.endpoint,
                                         view_func=method_route.create_lambda(p_instance=p_view_handler_instance),
                                         **method_route.options)
                self._logger.debug(
                    f"Assigning rule '{method_route.rule}' to endpoint '{method_route.endpoint}' "
                    f"at {method_route.instance_name}")

        for method_route in self._assigned_method_routes:
            if method_route in self._unassigned_method_routes:
                self._unassigned_method_routes.remove(method_route)

    def unassign_view_handler_instances(self):

        for method_route in self._assigned_method_routes:
            self._logger.debug(f"Unassigning rule '{method_route.rule}' from endpoint '{method_route.endpoint}' "
                               f"at {method_route.instance_name}")
            method_route.unassign()

        self._unassigned_method_routes = self._assigned_method_routes
        self._assigned_method_routes = []

    def check_view_methods(self):

        logger = logging.getLogger()
        for method in self._unassigned_method_routes:
            msg = "method '{method}' has not been assigned to view handler"
            logger.warning(msg.format(method=method.view_method.__name__))

        assert len(self._unassigned_method_routes) == 0, "Some method routes have not been assigned to a view instance!"
