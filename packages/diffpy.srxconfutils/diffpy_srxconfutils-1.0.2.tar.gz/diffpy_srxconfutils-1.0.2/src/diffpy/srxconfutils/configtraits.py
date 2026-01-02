#!/usr/bin/env python
##############################################################################
#
# diffpy.srxconfutils     by Simon J. L. Billinge group
#                   (c) 2013-2025 Trustees of the Columbia University
#                   in the City of New York.  All rights reserved.
#
# File coded by:    Xiaohao Yang
#
# See AUTHORS.rst for a list of people who contributed.
# See LICENSE.rst for license information.
#
##############################################################################
"""Package for organizing program configurations. It can read/write
configurations file, parse arguments from command lines, and also parse
arguments passed from method/function calling inside python.

This one is similar to ConfigBase but use Traits, so every option
(self.*option* is a trait) can be observed and have a GUI interface.
"""

from traits.api import (
    Array,
    Bool,
    CFloat,
    CInt,
    Directory,
    Enum,
    File,
    HasTraits,
    List,
    String,
)

from diffpy.srxconfutils.config import ConfigBase


class ConfigBaseTraits(HasTraits, ConfigBase):
    """_optdatalist_default, _optdatalist are metadata used to
    initialize the options, see below for examples.

    options presents in --help (in cmd), config file, headers have
    same order as in these list, so arrange them in right order here.

    optional args to control if the options presents in args, config file or
    file header

    'args' - default is 'a'
        if 'a', this option will be available in self.args
        if 'n', this option will not be available in self.args
    'config' - default is 'a'
        if 'f', this option will present in self.config and be written to
        config file only in full mode
        if 'a', this option will present in self.config and be written to
        config file both in full and short mode
        if 'n', this option will not present in self.config
    'header' - default is 'a'
        if 'f', this option will be written to header only in full mode
        if 'a', this option will be written to header both in full and short
        mode
        if 'n', this option will not be written to header

    so in short mode, all options with 'a' will be written, in full mode,
    all options with 'a' or 'f' will be written
    """

    # Text to display before the argument help
    _description = """Description of configurations
    """
    # Text to display after the argument help
    _epilog = """
    """

    """
    optdata contains these keys:
    these args will be passed to argparse, see the documents of argparse for
    detail information

    'f': full, (positional)
    's': short
    'h': help
    't': type
    'a': action
    'n': nargs
    'd': default
    'c': choices
    'r': required
    'de': dest
    'co': const

    additional options for traits:
    'tt': traits type
    'l': traits label
    """
    _optdatanamedict = {
        "h": "help",
        "t": "type",
        "a": "action",
        "n": "nargs",
        "d": "default",
        "c": "choices",
        "r": "required",
        "de": "dest",
        "co": "const",
    }
    _traitstypedict = {
        "str": String,
        "int": CInt,
        "float": CFloat,
        "bool": Bool,
        "file": File,
        "directory": Directory,
        "strlist": List,
        "intlist": List,
        "floatlist": List,
        "boollist": List,
        "array": Array,
    }

    # examples, overload it
    _optdatalist_default = [
        [
            "configfile",
            {
                "sec": "Control",
                "config": "f",
                "header": "n",
                "l": "Config File",
                "tt": "file",
                "s": "c",
                "h": "name of input config file",
                "d": "",
            },
        ],
        [
            "createconfig",
            {
                "sec": "Control",
                "config": "n",
                "header": "n",
                "h": (
                    "create a config file according to "
                    "default or current values"
                ),
                "d": "",
            },
        ],
        [
            "createconfigfull",
            {
                "sec": "Control",
                "config": "n",
                "header": "n",
                "h": "create a full configurable config file",
                "d": "",
            },
        ],
    ]
    # examples, overload it
    _optdatalist = [
        [
            "tifdirectory",
            {
                "sec": "Experiment",
                "header": "n",
                "tt": "directory",
                "l": "Tif directory",
                "s": "tifdir",
                "h": "directory of raw tif files",
                "d": "currentdir",
            },
        ],
        [
            "integrationspace",
            {
                "sec": "Experiment",
                "l": "Integration space",
                "h": "integration space, could be twotheta or qspace",
                "d": "twotheta",
                "c": ["twotheta", "qspace"],
            },
        ],
        [
            "wavelength",
            {
                "sec": "Experiment",
                "l": "Wavelength",
                "h": "wavelength of x-ray, in A",
                "d": 0.1000,
            },
        ],
        [
            "rotationd",
            {
                "sec": "Experiment",
                "l": "Tilt Rotation",
                "s": "rot",
                "h": "rotation angle of tilt plane, in degree",
                "d": 0.0,
            },
        ],
        [
            "includepattern",
            {
                "sec": "Beamline",
                "header": "n",
                "config": "f",
                "l": "Include",
                "s": "ipattern",
                "h": "file name pattern for included files",
                "n": "*",
                "d": ["*.tif"],
            },
        ],
        [
            "excludepattern",
            {
                "sec": "Beamline",
                "header": "n",
                "config": "f",
                "l": "Exclude",
                "s": "epattern",
                "h": "file name pattern for excluded files",
                "n": "*",
                "d": ["*.dark.tif", "*.raw.tif"],
            },
        ],
        [
            "fliphorizontal",
            {
                "sec": "Beamline",
                "header": "n",
                "config": "f",
                "l": "Flip horizontally",
                "h": "flip the image horizontally",
                "n": "?",
                "co": True,
                "d": False,
            },
        ],
        [
            "maskedges",
            {
                "sec": "Others",
                "config": "f",
                "tt": "array",
                "l": "Mask edges",
                "h": (
                    "mask the edge pixels, first four means "
                    "the number of pixels masked in each edge "
                    "(left, right, top, bottom), the last one is the "
                    "radius of a region masked around the corner"
                ),
                "n": 5,
                "d": [10, 10, 10, 10, 100],
            },
        ],
    ]

    # default config file path and name
    _defaultdata = {
        "configfile": ["config.cfg"],
        "headertitle": "Configuration information",
    }

    def __init__(self, filename=None, args=None, **kwargs):
        """Init the class and update the values of options if specified
        in filename/args/kwargs.

        it will:
            1. init class using HasTraits
            2. call self._preInit method
            3. find the config file if specified in filename/args/kwargs
                if failed, try to find default config file
            4. update the options value using filename/args/kwargs
                file > args > kwargs
            5. call self._postInitTraits()

        :param filename: str, file name of the config file
        :param args: list of str, args passed from cmd
        :param kwargs: dict, optional kwargs

        :return: None
        """
        HasTraits.__init__(self)
        ConfigBase.__init__(self, filename, args, **kwargs)

        self._postInitTraits()
        return

    def _postInitTraits(self):
        """Additional init process called after traits init."""
        return

    @classmethod
    def _addOptSelfC(cls, optname, optdata):
        """Class method, assign options value to *self.option*, using
        metadata, this one will create traits objects for each option.

        :param optname: string, name of the option
        :param optdata: dict, metadata of the options, get it from
            self._optdatalist
        """
        # value type
        vtype = cls._getTypeStrC(optname)
        ttype = optdata.get("tt", vtype)
        ttype = cls._traitstypedict[ttype]
        kwargs = {
            "label": optdata["l"] if "l" in optdata else optname,
            "desc": optdata["h"],
        }
        args = [optdata["d"]]
        if "c" in optdata:
            ttype = Enum
            args = [optdata["c"]]
            kwargs["value"] = optdata["d"]
        if ttype == Array:
            args = []
            kwargs["value"] = optdata["d"]
        obj = ttype(*args, **kwargs)
        cls.add_class_trait(optname, obj)
        return


# ConfigBaseTraits.initConfigClass()

if __name__ == "__main__":
    test = ConfigBaseTraits(filename="temp.cfg")
    test.updateConfig()
    test.configure_traits()
