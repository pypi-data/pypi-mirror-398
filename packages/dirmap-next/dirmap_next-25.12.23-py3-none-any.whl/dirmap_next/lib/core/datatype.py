#!/usr/bin/env python3

'''
@Author: xxlin
@LastEditors: xxlin
@Date: 2019-04-10 13:27:58
@LastEditTime: 2019-04-10 17:48:54
'''

import copy
import types
from typing import Any, TypeVar, cast

from collections.abc import Mapping

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class AttribDict(dict[K, V]):
    """
    This class defines the project object, inheriting from Python data
    type dictionary.

    >>> foo = AttribDict()
    >>> foo.bar = 1
    >>> foo.bar
    1
    """
    
    attribute: Any
    __initialised: bool

    def __init__(self, indict: Mapping[K, V] | None = None, attribute: Any = None):
        if indict is None:
            indict = cast(Mapping[K, V], {})

        # Set any attributes here - before initialisation
        # these remain as normal attributes
        self.attribute = attribute
        dict.__init__(self, indict)
        self.__initialised = True

        # After initialisation, setting attributes
        # is the same as setting an item

    def __getattr__(self, item: str) -> Any:
        """
        Maps values to attributes
        Only called if there *is NOT* an attribute with this name
        """

        try:
            return self.__getitem__(cast(K, item))
        except KeyError:
            raise AttributeError("unable to access item '%s'" % item)

    def __setattr__(self, item: str, value: Any) -> None:
        """
        Maps attributes to values
        Only if we are initialised
        """

        # This test allows attributes to be set in the __init__ method
        if "_AttribDict__initialised" not in self.__dict__:
            return dict.__setattr__(self, item, value)

        # Any normal attributes are handled normally
        elif item in self.__dict__:
            dict.__setattr__(self, item, value)

        else:
            self.__setitem__(cast(K, item), cast(V, value))

    def __getstate__(self) -> dict[str, Any]:
        return self.__dict__

    def __setstate__(self, dict: dict[str, Any]) -> None:
        self.__dict__ = dict

    def __deepcopy__(self, memo: dict[int, Any]) -> 'AttribDict[K, V]':
        retVal = self.__class__()
        memo[id(self)] = retVal

        for attr in dir(self):
            if not attr.startswith('_'):
                value = getattr(self, attr)
                if not isinstance(value, (types.BuiltinFunctionType, types.FunctionType, types.MethodType)):
                    setattr(retVal, attr, copy.deepcopy(value, memo))

        for key, value in self.items():
            retVal.__setitem__(key, copy.deepcopy(value, memo))

        return retVal

