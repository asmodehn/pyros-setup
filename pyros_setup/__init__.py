# -*- coding: utf-8 -*-
from __future__ import absolute_import

from ._version import __version__

import logging
import os
import pkgutil
import types

import sys

from .utils import deprecated
from pyros_config import ConfigImport, ConfigHandler

# Configuring logging default handler
import logging
_logger = logging.getLogger(__package__)
_logger.addHandler(logging.NullHandler())

#: Smart Default distro detection (as early as possible)
if os.path.exists('/opt/ros/kinetic'):
    DETECTED_DISTRO = 'kinetic'
elif os.path.exists('/opt/ros/jade'):
    DETECTED_DISTRO = 'jade'
elif os.path.exists('/opt/ros/indigo'):
    DETECTED_DISTRO = 'indigo'
else:
    DETECTED_DISTRO = 'unknown'


# class to allow delayed conditional import, with behavior based on configuration.
# This way it can work with or without preset environment
class _PyrosSetup(ConfigImport):

    _default_config = {
        'DISTRO': DETECTED_DISTRO,
        'WORKSPACES': [],
    }

    def __init__(self, instance_path=None, instance_relative_config=True, root_path=None):

        relay_import_dict = {
            'rospy': 'rospy',  # early except to detect errors and prevent unintentional useless workarounds
        }
        fix_imports = self._attempt_import_fix

        self.deprecated = deprecated

        # Needed for the module to have a "__file__" and a "__version__" attribute
        self.__file__ = __file__
        self.__version__ = __version__

        super(_PyrosSetup, self).__init__('pyros_setup',
                                          'Small setup package to dynamically interface with ROS',
                                          relay_import_dict=relay_import_dict,
                                          fix_imports=fix_imports,
                                          instance_path=instance_path,
                                          instance_relative_config=instance_relative_config,
                                          root_path=root_path,
                                          default_config=self._default_config)

    def _attempt_import_fix(self):
        _logger.warning("Error detected while importing ROS python modules. Attempting fix via ROS setup emulation...")
        from .ros_setup import ROS_emulate_setup
        # we want this to except in case of bad config, because default_config has to have these fields.
        ROS_emulate_setup(self.config['DISTRO'], *self.config['WORKSPACES'])

    def configure(self, config=None, ):
        """
        load configuration
        :param config:
        :return:
        """
        super(_PyrosSetup, self).configure(
            config,
            create_if_missing="""
# default configuration generated by pyros-setup
# Usage from python :
# import pyros_setup
# pyros_setup.configurable_import().configure().activate()
#
# Fill in your workspaces here, if you want to dynamically import ROS packages from it.
WORKSPACES=[]

# ROS distribution. Change this value to the ROS distribution you want to use with this environment.
""" + "DISTRO='{0}'".format(DETECTED_DISTRO) + """
""")

        return self

    def activate(self):
        """
        Activate import relay (via setting sys.modules[])
        :return: self
        """
        super(_PyrosSetup, self).activate()

        return self

    # encapsulating local imports to delay them until ROS setup is done
    @classmethod
    @deprecated
    def delayed_import(cls, distro=None, *workspaces):

        # building a one time config for bwcompat purpose
        cfg = cls._default_config
        cfg['DISTRO'] = distro or cls._default_config['DISTRO']
        cfg['WORKSPACES'] = workspaces
        module_redirect = cls()
        module_redirect.configure(cfg)
        module_redirect.activate()

        return module_redirect

    @classmethod
    @deprecated
    def delayed_import_auto(cls, distro=None, base_path=None):
        import os

        distro = distro or cls._default_config['DISTRO']
        # default basepath working if pyros-setup is directly cloned in your workspace
        # This file think it is in devel/lib/python2.7/dist-packages/pyros_setup for some reason...
        # NOTE : maybe the default here is a bad idea, making it simpler than it should be for the user...
        base_path = base_path or os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')

        # using this for bwcompat purpose only. now seems like a bad idea after all.
        from .ros_setup import ROS_find_workspaces
        workspaces = ROS_find_workspaces(distro, base_path)

        return cls.delayed_import()

    #
    # Factory method
    #

    @classmethod
    def configurable_import(cls, instance_path=None, instance_relative_config=True, root_path=None):
        """
        Configure an import relay, using a configuration file (found in the instance or root path).
        This is designed after Flask instance configuration mechanism http://flask.pocoo.org/docs/0.10/config/#instance-folders
        :param instance_path: path to the instance folder. defaults to a sensible 'instance' location (refer to Flask doc)
        :param instance_relative_config: whether the configuration file is in the instance folder (or the root_path)
        :param root_path: path to the application's folder
        :return:
        """
        # we return a relay of imported names, accessible the same way a direct import would be.
        module_redirect = cls(
            instance_path=instance_path,
            instance_relative_config=instance_relative_config,
            root_path=root_path
        )
        return module_redirect

delayed_import = _PyrosSetup.delayed_import
delayed_import_auto = _PyrosSetup.delayed_import_auto
configurable_import = _PyrosSetup.configurable_import


__all__ = [
    '__version__',
    'deprecated',
    'delayed_import',
    'delayed_import_auto',
    'configurable_import',
]
