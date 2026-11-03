import inspect
from typing import Optional, IO, cast
from types import FrameType
from abc import ABC
from enum import Enum
from ..helpers import memo


# class OnlyPrivateFieldsMeta(type):
#     """will modify a class's __setattr__ so that it's attributes will be
#     private and cannot be changed from outside using "dot notation"

#     An 'AttributeError' will be raised if an attribute will be set not using a class function.
#     """
#     @staticmethod
#     def _get_function_names(cls: type) -> t_set[str]:
#         res = set()
#         for kls in cls.mro():
#             if kls is object:
#                 continue
#             res.update(list(kls.__dict__))
#         return res

#     @staticmethod
#     def _get_prev_frame(frame: Optional[FrameType]) -> Optional[FrameType]:
#         """Get the previous frame (caller's frame) in the call stack.

#         This function retrieves the frame that called the current frame in the Python call stack.

#         Args:
#             frame (Optional[FrameType]): The current frame for which to find the previous frame.

#         Returns:
#             Optional[FrameType]: The previous frame in the call stack, or None if it is not available.

#         Note:
#             If the input frame is None or not of type FrameType, the function returns None.
#         """
#         if frame is None:
#             return None
#         if not isinstance(frame, FrameType):
#             return None
#         frame = cast(FrameType, frame)
#         return frame.f_back

#     @staticmethod
#     def _get_caller_name(steps_back: int = 0) -> Optional[str]:
#         """returns the name caller of the function

#         Returns:
#             str: name of caller

#         USING THIS FUNCTION WHILE DEBUGGING WILL ADD ADDITIONAL FRAMES TO THE TRACEBACK
#         """
#         if not isinstance(steps_back, int):
#             raise TypeError("steps_back must be an int")
#         if steps_back < 0:
#             raise ValueError("steps_back must be a non-negative integer")
#         frame = OnlyPrivateFieldsMeta._get_prev_frame(
#             OnlyPrivateFieldsMeta._get_prev_frame(inspect.currentframe()))
#         if frame is None:
#             return None
#         frame = cast(FrameType, frame)
#         while steps_back > 0:
#             frame = OnlyPrivateFieldsMeta._get_prev_frame(frame)
#             if frame is None:
#                 return None
#             frame = cast(FrameType, frame)
#             steps_back -= 1
#         return frame.f_code.co_name

#     def __new__(mcs, name: str, bases: t_tuple, namespace: dict):
#         def __setattr__(self, name, value):
#             caller = OnlyPrivateFieldsMeta._get_caller_name()
#             if caller in OnlyPrivateFieldsMeta._get_function_names(self.__class__):
#                 return object.__setattr__(self, name, value)
#             raise AttributeError(
#                 f"Attribute '{name}' of '{self.__class__.__name__}' is private and cannot be changed from outside")
#         namespace["__setattr__"] = __setattr__
#         return type(name, bases, namespace)

class OnlyPrivate:
    """will override __setattr__ to make instance's attributes private 
    and so that they can be change only from inside functions
    """
    @classmethod
    @memo
    def __get_function_names(cls, kls: type) -> set:
        res = set()
        mro = kls.mro()
        reversed_last_index = mro[::-1].index(cls)
        last_index = len(mro)-reversed_last_index-1
        for kls_ in mro[:last_index]:
            if kls_ is cls:
                continue
            res.update(list(kls_.__dict__))
        return res

    @staticmethod
    def __get_prev_frame(frame: Optional[FrameType]) -> Optional[FrameType]:
        """Get the previous frame (caller's frame) in the call stack.

        This function retrieves the frame that called the current frame in the Python call stack.

        Args:
            frame (Optional[FrameType]): The current frame for which to find the previous frame.

        Returns:
            Optional[FrameType]: The previous frame in the call stack, or None if it is not available.

        Note:
            If the input frame is None or not of type FrameType, the function returns None.
        """
        if frame is None:
            return None
        if not isinstance(frame, FrameType):
            return None
        frame = cast(FrameType, frame)
        return frame.f_back

    @staticmethod
    def __get_caller_name(steps_back: int = 0) -> Optional[str]:
        """returns the name caller of the function

        Returns:
            str: name of caller

        USING THIS FUNCTION WHILE DEBUGGING WILL ADD ADDITIONAL FRAMES TO THE TRACEBACK
        """
        if not isinstance(steps_back, int):
            raise TypeError("steps_back must be an int")
        if steps_back < 0:
            raise ValueError("steps_back must be a non-negative integer")
        frame = OnlyPrivate.__get_prev_frame(
            OnlyPrivate.__get_prev_frame(inspect.currentframe()))
        if frame is None:
            return None
        frame = cast(FrameType, frame)
        while steps_back > 0:
            frame = OnlyPrivate.__get_prev_frame(frame)
            if frame is None:
                return None
            frame = cast(FrameType, frame)
            steps_back -= 1
        return frame.f_code.co_name

    def __setattr__(self, name, value):
        caller = OnlyPrivate.__get_caller_name()
        if caller in OnlyPrivate.__get_function_names(self.__class__):
            return object.__setattr__(self, name, value)
        raise AttributeError(
            f"Attribute '{name}' of '{self.__class__.__name__}' is private and cannot be changed from outside")


class IdEquality:
    """A parent class implementing hashing and equality of objects based on their 'id' field value
    """

    def __eq__(self, other: object) -> bool:
        if hasattr(self, "id"):
            if type(self) == type(other):  # pylint: disable=unidiomatic-typecheck
                return self.id == other.id  # type:ignore
        return False

    def __hash__(self) -> int:
        if hasattr(self, "id"):
            return hash(self.id)
        return object.__hash__(self)


class IndentedWriter2:
    """every class that will inherit this class will have the following functions available
        write() with the same arguments a builtin print()
        indent()
        undent()

        also, it is expected in the __init__ function to call super().__init__()
        also, the output_stream must be set whether by the first argument io super().__init__(...)
        or by set_stream() explicitly somewhere else.

        this class will not function properly is the output_stream is not set!

    """

    def __init__(self, indent_value: str = "\t"):
        self.indent_level = 0
        self.indent_value = indent_value
        self.buffer: str = ""

    def to_stream(self, stream: IO[str]) -> None:
        """outputs the buffer to a stream

        Args:
            stream (IO[str]): the stream to output to
        """
        stream.write(self.buffer)

    def add_from(self, s: str) -> None:
        """Adds text to inner buffer from supplied string"""
        for i, line in enumerate(s.splitlines()):
            if i == 0:
                self.buffer += line+"\n"
            else:
                self.write(line)

    def write(self, *args, sep=" ", end="\n") -> None:
        """writes the supplied arguments to the output_stream

        Args:
            sep (str, optional): the str to use as a separator between arguments. Defaults to " ".
            end (str, optional): the str to use as the final value. Defaults to "\n".

        Raises:
            ValueError: _description_
        """
        self.buffer += str(self.indent_level *
                           self.indent_value + sep.join(args)+end)

    def indent(self) -> None:
        """indents the preceding output with write() by one quantity more
        """
        self.indent_level += 1

    def undent(self) -> None:
        """un-dents the preceding output with write() by one quantity less
            has a minimum value of 0
        """
        self.indent_level = max(0, self.indent_level-1)


class Printable:
    """A parent class to supply a default implementation of __str__ so 
    that class instances will print nicely"""

    def __str__(self) -> str:
        w = IndentedWriter2(indent_value=" "*4)
        # w.write(f"{self.__class__.__name__} ", end="")
        w.write("{")
        w.indent()
        for k, v in self.__dict__.items():
            for cls in self.__class__.mro():
                potential_prefix = f"_{cls.__name__}__"
                if k.startswith(potential_prefix):
                    k = k[len(potential_prefix):]
                    break
            w.write(f"\"{k}\": ", end="")
            if isinstance(v, Printable):
                w.add_from(str(v))
                w.buffer = w.buffer[:-1]+",\n"
            else:
                w.buffer += (f"\"{v}\",\n")
        w.buffer = w.buffer[:-2]+"\n"
        w.undent()
        w.write("}")
        return w.buffer


class Dictable(ABC):
    """an abstract class to mark an object that it supports the functions
    'to_dict' and 'from_dict' for other use in the library
    """
    @classmethod
    def from_dict(cls, dct: dict):
        """creates an object from relevant dict
        """
        return cls(**dct)

    def to_dict(self) -> dict:
        """returns a dictionary representation of object"""
        res = {}
        for k, v in self.__dict__.items():
            potential_prefix = f"_{self.__class__.__name__}__"
            if k.startswith(potential_prefix):
                k = k[len(potential_prefix):]
            if isinstance(v, Dictable):
                res[k] = v.to_dict()
            elif isinstance(v, Enum):
                res[k] = v.value
            else:
                res[k] = v
        return res


__all__ = [
    "OnlyPrivate",
    "IdEquality",
    "Printable",
    "Dictable"
]
