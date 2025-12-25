import enum
import os
import struct
from io import BytesIO

from loguru import logger


# Magic bytes of any serialized files
STREAM_MAGIC = 0xACED

# Only protocol version supported by javaobj
STREAM_VERSION = 0x05


def is_java_serialized(input_stream: bytes) -> bool:
    """判断是否为java序列化后的值
    
    Args:
        input_stream: 需判断的值

    Returns:
        bool
        
    """
    input_stream = BytesIO(input_stream)

    length = struct.calcsize(">HH")
    ba = input_stream.read(length)

    if len(ba) != length:
        return False

    (magic, version) = struct.unpack(">HH", ba)

    if magic != STREAM_MAGIC or version != STREAM_VERSION:
        return False

    return True


def to_str(data, encoding="UTF-8"):
    """
    Converts the given parameter to a string.
    Returns the first parameter if it is already an instance of ``str``.

    Args: 
        data: A string
        encoding: The encoding of data
        
    Returns:
        The corresponding string
        
    """
    if isinstance(data, str):
        # Nothing to do
        return data

    return str(data, encoding)


def hexdump(src: bytes, start_offset: int = 0, length: int = 16) -> str:
    """
    Prepares an hexadecimal dump string

    Args: 
        src: A string containing binary data
        start_offset: The start offset of the source
        length: Length of a dump line
        
    Returns:
        A dump string
        
    """
    hex_filter = "".join(
        (len(repr(chr(x))) == 3) and chr(x) or "." for x in range(256)
    )
    pattern = "{{0:04X}}   {{1:<{0}}}  {{2}}\n".format(length * 3)

    # Convert raw data to str (Python 3 compatibility)
    src = to_str(src, "latin-1")

    result = []
    for i in range(0, len(src), length):
        s = src[i: i + length]
        hexa = " ".join("{0:02X}".format(ord(x)) for x in s)
        printable = s.translate(hex_filter)
        result.append(pattern.format(i + start_offset, hexa, printable))
    return "".join(result)


class StreamCodeDebug:
    """
    Codes utility methods
    """

    @staticmethod
    def op_id(op_id: int) -> str:
        """
        Returns the name of the given OP Code

        Args: 
            op_id: OP Code
            
        Returns:
            Name of the OP Code
        """
        try:
            return TerminalCode(op_id).name
        except ValueError:
            return "<unknown TC:{0}>".format(op_id)


class TerminalCode(enum.IntEnum):
    """
    Stream type Codes
    """

    TC_NULL = 0x70
    TC_STRING = 0x74
    TC_ENDBLOCKDATA = 0x78
    TC_LONGSTRING = 0x7C


class TypeCode(enum.IntEnum):
    """
    Type definition chars (typecode)
    """

    # Primitive types
    TYPE_BYTE = ord("B")  # 0x42
    TYPE_CHAR = ord("C")  # 0x43
    TYPE_DOUBLE = ord("D")  # 0x44
    TYPE_FLOAT = ord("F")  # 0x46
    TYPE_INTEGER = ord("I")  # 0x49
    TYPE_LONG = ord("J")  # 0x4A
    TYPE_SHORT = ord("S")  # 0x53
    TYPE_BOOLEAN = ord("Z")  # 0x5A
    # Object types
    TYPE_OBJECT = ord("L")  # 0x4C
    TYPE_ARRAY = ord("[")  # 0x5B


class JavaString(str):
    """
    Represents a Java String
    """

    def __hash__(self):
        return str.__hash__(self)

    def __eq__(self, other):
        if not isinstance(other, str):
            return False
        return str.__eq__(self, other)


class JavaDeSerializeHelper:
    """
    Deserializes a Java serialization stream
    """

    def __init__(self, stream: bytes, encoding: str):
        """
        
        Args:
            stream: bytes, stream to be deserialized
            encoding: if not utf-8 encoded, provided for specific encoding

        """
        # Check stream
        if stream is None:
            raise IOError("No input stream given")
        # Prepare the association Terminal Symbol -> Reading method
        self.opmap = {
            TerminalCode.TC_NULL: self.do_null,
            TerminalCode.TC_STRING: self.do_string,
            TerminalCode.TC_LONGSTRING: self.do_string_long,
            TerminalCode.TC_ENDBLOCKDATA: self.do_null,
        }
        self.object_stream = BytesIO(stream)
        self.encoding = encoding or 'UTF-8'
        self.read_magic_bytes()

    def read_magic_bytes(self):
        length = struct.calcsize(">HH")
        self.object_stream.read(length)

    def _read_struct(self, unpack):
        """
        Reads from the input stream, using struct

        Args:
            unpack: An unpack format string
            
        Returns:
            The result of struct.unpack (tuple)
            
        Raises:
            RuntimeError: End of stream reached during unpacking
            
        """
        length = struct.calcsize(unpack)
        ba = self.object_stream.read(length)

        if len(ba) != length:
            raise RuntimeError(
                "Stream has been ended unexpectedly while unmarshaling."
            )

        return struct.unpack(unpack, ba)

    def read_object(self, ignore_remaining_data=False):
        """
        Reads an object from the input stream

        Args:
            ignore_remaining_data: If True, don't log an debug when
                                      unused trailing bytes are remaining
                                      
        Returns:
            The unmarshalled object
            
        Raises:
            Exception: Any exception that occurred during unmarshalling
            
        """
        try:
            _, res = self._read_and_exec_opcode()

            position_bak = self.object_stream.tell()
            the_rest = self.object_stream.read()
            if not ignore_remaining_data and len(the_rest) != 0:  # pragma: no cover
                logger.warning(
                    "Warning!!!!: Stream still has {0} bytes left. "
                    "Enable debug mode of logging to see the hexdump.".format(
                        len(the_rest)
                    )
                )
                logger.warning("\n{0}".format(hexdump(the_rest)))
            else:
                logger.warning("Java Object unmarshalled successfully!")

            self.object_stream.seek(position_bak)
            return res
        except Exception:
            self._oops_dump_state(ignore_remaining_data)
            raise

    def _read_and_exec_opcode(self, expect=None):
        """
        Reads the next opcode, and executes its handler

        Args:
            expect: A list of expected opcodes
            
        Returns:
            A tuple: (opcode, result of the handler)
            
        Raises:
            IOError: Read opcode is not one of the expected ones
            RuntimeError: Unknown opcode
            
        """
        position = self.object_stream.tell()
        (opid,) = self._read_struct(">B")

        if expect and opid not in expect:  # pragma: no cover
            raise IOError(
                "Unexpected opcode 0x{0:X} -- {1} "
                "(at offset 0x{2:X})".format(
                    opid, StreamCodeDebug.op_id(opid), position
                )
            )

        try:
            handler = self.opmap[opid]
        except KeyError:
            raise RuntimeError(
                "Unknown OpCode in the stream: 0x{0:X} "
                "(at offset 0x{1:X})".format(opid, position)
            )
        else:
            return opid, handler()

    def _read_string(self, length_fmt="H"):
        """
        Reads a serialized string

        Args:
            length_fmt: Structure format of the string length (H or Q)
            
        Returns:
            The deserialized string
            
        Raises:
            RuntimeError: Unexpected end of stream
            
        """
        (length,) = self._read_struct(">{0}".format(length_fmt))
        ba = self.object_stream.read(length)
        return to_str(ba, self.encoding)

    def do_string(self) -> str:
        """
        Handles a TC_STRING opcode

        Returns:
            A String
            
        """
        logger.warning("[string]")
        ba = JavaString(self._read_string())
        return ba

    def do_string_long(self) -> str:
        """
        Handles a TC_LONGSTRING opcode

        Returns:
            A String
            
        """
        logger.warning("[long string]")
        ba = JavaString(self._read_string("Q"))
        return ba

    @staticmethod
    def do_null() -> None:
        """
        Handles a TC_NULL opcode
        
        Returns:
            Always None
            
        """
        return None

    def _oops_dump_state(self, ignore_remaining_data=False):
        """
        Log a deserialization debug

        Args:
            ignore_remaining_data: If True, don't log an debug when
                                      unused trailing bytes are remaining
                                      
        """
        logger.warning("==Oops state dump" + "=" * (30 - 17))
        logger.warning(
            "Stream seeking back at -16 byte "
            "(2nd line is an actual position!):"
        )

        # Do not use a keyword argument
        self.object_stream.seek(-16, os.SEEK_CUR)
        position = self.object_stream.tell()
        the_rest = self.object_stream.read()

        if not ignore_remaining_data and len(the_rest) != 0:
            logger.warning(
                "Warning!!!!: Stream still has {0} bytes left:\n{1}".format(
                    len(the_rest), hexdump(the_rest, position)
                )
            )

        logger.warning("=" * 30)
