from typing import BinaryIO, Optional
from io import BytesIO, SEEK_END


METADATA_MAGIC_BYTES = b'\xAF\x1B\xB1\xFA'

OFFSET_LOOKUP_TABLE_OFFSET = 8
OFFSET_LOOKUP_TABLE_SIZE = 12
OFFSET_STRING_LITERAL_DATA_OFFSET = 16
OFFSET_STRING_LITERAL_DATA_SIZE = 20

SIZE_LOOKUP_TABLE_ITEM = 8
SIZE_STRING_DATA_ALIGNMENT = 4


class StringLiteral:
    def __init__(self, index: int, offset: int, length: int, value: bytes) -> None:
        """Create a new StringLiteral

        Args:
            index (int): Index of string literal in lookup table
            offset (int): Offset of string value in string data region
            length (int): Length of string value in string data region
            value (bytes): Raw data of the string literal
        """
        self._index = index
        self._offset = offset
        self._length = length
        self._value = value
        self._patched_value: Optional[bytes] = None
    
    @property
    def index(self) -> int:
        """Index in lookup table
        """
        return self._index
    
    @property
    def offset(self) -> int:
        """Data offset in metadata file before patching
        """
        return self._offset
    
    @property
    def length(self) -> int:
        """Length of the original literal bytes
        """
        return self._length
    
    @property
    def original_bytes(self) -> bytes:
        """Get the original data
        """
        return self._value
    
    @property
    def original_string(self) -> str:
        """Get the original data as decoded string
        """
        cached_string = getattr(self, '_cached_string', None)
        if cached_string:
            return cached_string
        cached_string = self.original_bytes.decode(encoding='utf-8', errors='ignore')
        setattr(self, '_cached_string', cached_string)
        return cached_string
    
    def patch(self, value: Optional[str | bytes] = None):
        """Patch this string literal with given 

        Args:
            value (Optional[str  |  bytes], optional): The value after patching. Or None to cancel the patch.
        """
        if value is None:
            self._patched_value = None
            return
        if isinstance(value, str):
            value = value.encode(encoding='utf-8', errors='ignore')
        self._patched_value = bytes(value)
        
    def is_patched(self) -> bool:
        """Is patch set
        """
        return self._patched_value is not None
    
    def get_patched_bytes(self) -> Optional[bytes]:
        """Get the patched data
        """
        return self._patched_value
    
    def get_patched_string(self) -> Optional[str]:
        """Get the patched data as decoded string
        """
        value = self._patched_value
        if value:
            return value.decode(encoding='utf-8', errors='ignore')
        return None
        

class StringsPatcher:
    """Extractor and Pacther for il2cpp metadata files
    """
    
    def __init__(self, f: BinaryIO | bytes):
        if isinstance(f, bytes) or isinstance(f, memoryview) or isinstance(f, bytearray):
            f = BytesIO(f)
        self.f = f
        self._literals: list[StringLiteral] = []
        self._check_size_for_header()
        self._check_magic_number()
        self._extract()
    
    @property
    def literals(self) -> list[StringLiteral]:
        return self._literals.copy()
    
    def _check_size_for_header(self):
        size = self.f.seek(0, SEEK_END)
        if size < OFFSET_STRING_LITERAL_DATA_SIZE + 4:
            raise ValueError('invalid file size for header')
        self._file_size = size
    
    def _check_magic_number(self):
        self.f.seek(0)
        if self.f.read(4) != METADATA_MAGIC_BYTES:
            raise ValueError('invalid magic number')
    
    def _read_int_at(self, offset: int = -1) -> int:
        if offset != -1:
            self.f.seek(offset)
        return int.from_bytes(self.f.read(4), byteorder='little')
    
    def _extract(self):
        self._lookup_table_offset = self._read_int_at(OFFSET_LOOKUP_TABLE_OFFSET)
        self._lookup_table_size = self._read_int_at(OFFSET_LOOKUP_TABLE_SIZE)
        self._string_data_offset = self._read_int_at(OFFSET_STRING_LITERAL_DATA_OFFSET)
        self._string_data_size = self._read_int_at(OFFSET_STRING_LITERAL_DATA_SIZE)
        # Check length
        if self._file_size < max(self._lookup_table_offset + self._lookup_table_size,
                                 self._string_data_offset + self._string_data_size):
            raise ValueError('invalid file size')
        # Read string data
        self.f.seek(self._string_data_offset)
        str_data = self.f.read(self._string_data_size)
        # Read lookup table & Generate string literals
        self.f.seek(self._lookup_table_offset)
        for i in range(self._lookup_table_size // SIZE_LOOKUP_TABLE_ITEM):
            str_length = self._read_int_at()
            str_offset = self._read_int_at()
            self._literals.append(StringLiteral(i, str_offset, str_length, str_data[str_offset:str_offset+str_length]))
    
    def _generate_string_data(self) -> tuple[bytes, list[tuple[int, int]]]:
        out = BytesIO() # Bytes of string data region
        items = [] # (length, offset) item in lookup table

        offset = 0
        for literal in self._literals:
            data = literal.get_patched_bytes() or literal.original_bytes
            length = len(data)
            out.write(data)
            items.append((length, offset))
            offset += length

        # alignment
        pad_len = SIZE_STRING_DATA_ALIGNMENT - out.tell() % SIZE_STRING_DATA_ALIGNMENT
        if pad_len < SIZE_STRING_DATA_ALIGNMENT:
            out.write(b'\x00' * pad_len)

        return out.getvalue(), items
    
    def patch_literals(self, patches: dict[str, str | bytes]) -> int:
        """Patch dict key to dict value

        Args:
            patches (dict[str, str  |  bytes]): Key: Target string, Value: Patched string or bytes
        
        Returns:
            int: Applied patch count
        """
        count = 0
        for literal in self._literals:
            patched_value = patches.get(literal.original_string)
            if patched_value:
                literal.patch(patched_value)
                count += 1
        return count
    
    def generate_patched_file(self) -> bytes:
        """Generate patched metadata file

        Returns:
            bytes: Patched metadata file in bytes
        """
        str_data, items = self._generate_string_data()
        
        output = BytesIO()
        self.f.seek(0)
        output.write(self.f.read())
        
        output.seek(self._lookup_table_offset)
        for i in range(len(items)):
            item = items[i]
            output.write(item[0].to_bytes(length=4, byteorder='little'))
            output.write(item[1].to_bytes(length=4, byteorder='little'))
        
        if len(str_data) <= self._string_data_size:
            # Reuse the old string data region if space is enough
            output.seek(self._string_data_offset)
            output.write(str_data)
        else:
            output.seek(0, SEEK_END)
            data_offset = output.tell()
            output.write(str_data)
            output.seek(OFFSET_STRING_LITERAL_DATA_OFFSET)
            output.write(data_offset.to_bytes(length=4, byteorder='little'))
            output.seek(OFFSET_STRING_LITERAL_DATA_SIZE)
            output.write(len(str_data).to_bytes(length=4, byteorder='little'))
        
        return output.getvalue()
    
