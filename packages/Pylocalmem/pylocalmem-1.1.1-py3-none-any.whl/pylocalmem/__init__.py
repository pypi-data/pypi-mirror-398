import ctypes.wintypes, sys, re
from keystone import Ks, KS_ARCH_X86, KS_MODE_64

# Function declaration to avoid calling getprocaddress every function call
_GetModuleHandleW = ctypes.windll.kernel32.GetModuleHandleW
_VirtualProtect = ctypes.windll.kernel32.VirtualProtect
_VirtualAlloc = ctypes.windll.kernel32.VirtualAlloc
_VirtualFree = ctypes.windll.kernel32.VirtualFree
_CreateThread = ctypes.windll.kernel32.CreateThread
_WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
_CloseHandle = ctypes.windll.kernel32.CloseHandle
_FreeLibraryAndExitThread = ctypes.windll.kernel32.FreeLibraryAndExitThread
_CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
_Module32First = ctypes.windll.kernel32.Module32First
_Module32Next = ctypes.windll.kernel32.Module32Next

_GetModuleHandleW.restype = ctypes.c_void_p
_VirtualAlloc.restype = ctypes.c_void_p

PAGE_EXECUTE_READWRITE = 0x40
MEM_COMMIT = 0x1000
MEM_FREE = 0x10000
MEM_RESERVE = 0x2000
MEM_DECOMMIT = 0x4000
TH32CS_SNAPMODULE = 0x8

class LIST_ENTRY(ctypes.Structure):
    _fields_ = [("Flink", ctypes.c_void_p),
                ("Blink", ctypes.c_void_p)]


class UNICODE_STRING(ctypes.Structure):
    _fields_ = [("Length", ctypes.c_ushort),
                ("MaximumLength", ctypes.c_ushort),
                ("Buffer", ctypes.c_void_p)]


class LDR_DATA_TABLE_ENTRY(ctypes.Structure):
    _fields_ = [("InLoadOrderLinks", LIST_ENTRY),
                ("InMemoryOrderLinks", LIST_ENTRY),
                ("InInitializationOrderLinks", LIST_ENTRY),
                ("DllBase", ctypes.c_void_p),
                ("EntryPoint", ctypes.c_void_p),
                ("SizeOfImage", ctypes.c_uint),
                ("FullDllName", UNICODE_STRING),
                ("BaseDllName", UNICODE_STRING),]
    

class PEB_LDR_DATA(ctypes.Structure):
    _fields_ = [("Length", ctypes.c_uint32),
                ("Initialized", ctypes.c_ubyte),
                ("_pad1", ctypes.c_ubyte * 3),
                ("SsHandle", ctypes.c_void_p),
                ("InLoadOrderModuleList", LIST_ENTRY),
                ("InMemoryOrderModuleList", LIST_ENTRY),
                ("InInitializationOrderModuleList", LIST_ENTRY),
                ("EntryInProgress", ctypes.c_void_p),
                ("ShutdownInProgress", ctypes.c_ubyte),
                ("_pad2", ctypes.c_ubyte * 7),
                ("ShutdownThreadId", ctypes.c_void_p)]

class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [('nLength', ctypes.c_ulong),
                ('lpSecurityDescriptor', ctypes.c_void_p),
                ('bInheritHandle', ctypes.c_long)]

class IMAGE_DATA_DIRECTORY(ctypes.Structure):
    _fields_ = [
        ("VirtualAddress", ctypes.c_uint32),
        ("Size", ctypes.c_uint32),
    ]

class IMAGE_DOS_HEADER(ctypes.Structure):
    _fields_ = [
        ("e_magic", ctypes.c_uint16),
        ("e_cblp", ctypes.c_uint16),
        ("e_cp", ctypes.c_uint16),
        ("e_crlc", ctypes.c_uint16),
        ("e_cparhdr", ctypes.c_uint16),
        ("e_minalloc", ctypes.c_uint16),
        ("e_maxalloc", ctypes.c_uint16),
        ("e_ss", ctypes.c_uint16),
        ("e_sp", ctypes.c_uint16),
        ("e_csum", ctypes.c_uint16),
        ("e_ip", ctypes.c_uint16),
        ("e_cs", ctypes.c_uint16),
        ("e_lfarlc", ctypes.c_uint16),
        ("e_ovno", ctypes.c_uint16),
        ("e_res", ctypes.c_uint16 * 4),
        ("e_oemid", ctypes.c_uint16),
        ("e_oeminfo", ctypes.c_uint16),
        ("e_res2", ctypes.c_uint16 * 10),
        ("e_lfanew", ctypes.c_int32),
    ]
class IMAGE_OPTIONAL_HEADER(ctypes.Structure):
    _fields_ = [
        ("Magic", ctypes.c_uint16),
        ("MajorLinkerVersion", ctypes.c_uint8),
        ("MinorLinkerVersion", ctypes.c_uint8),
        ("SizeOfCode", ctypes.c_uint32),
        ("SizeOfInitializedData", ctypes.c_uint32),
        ("SizeOfUninitializedData", ctypes.c_uint32),
        ("AddressOfEntryPoint", ctypes.c_uint32),
        ("BaseOfCode", ctypes.c_uint32),
        ("ImageBase", ctypes.c_uint64),
        ("SectionAlignment", ctypes.c_uint32),
        ("FileAlignment", ctypes.c_uint32),
        ("MajorOperatingSystemVersion", ctypes.c_uint16),
        ("MinorOperatingSystemVersion", ctypes.c_uint16),
        ("MajorImageVersion", ctypes.c_uint16),
        ("MinorImageVersion", ctypes.c_uint16),
        ("MajorSubsystemVersion", ctypes.c_uint16),
        ("MinorSubsystemVersion", ctypes.c_uint16),
        ("Win32VersionValue", ctypes.c_uint32),
        ("SizeOfImage", ctypes.c_uint32),
        ("SizeOfHeaders", ctypes.c_uint32),
        ("CheckSum", ctypes.c_uint32),
        ("Subsystem", ctypes.c_uint16),
        ("DllCharacteristics", ctypes.c_uint16),
        ("SizeOfStackReserve", ctypes.c_uint64),
        ("SizeOfStackCommit", ctypes.c_uint64),
        ("SizeOfHeapReserve", ctypes.c_uint64),
        ("SizeOfHeapCommit", ctypes.c_uint64),
        ("LoaderFlags", ctypes.c_uint32),
        ("NumberOfRvaAndSizes", ctypes.c_uint32),
        ("DataDirectory", IMAGE_DATA_DIRECTORY * 16),
    ]
class IMAGE_EXPORT_DIRECTORY(ctypes.Structure):
    _fields_ = [
        ("Characteristics", ctypes.c_uint32),
        ("TimeDateStamp", ctypes.c_uint32),
        ("MajorVersion", ctypes.c_uint16),
        ("MinorVersion", ctypes.c_uint16),
        ("Name", ctypes.c_uint32),
        ("Base", ctypes.c_uint32),
        ("NumberOfFunctions", ctypes.c_uint32),
        ("NumberOfNames", ctypes.c_uint32),
        ("AddressOfFunctions", ctypes.c_uint32),
        ("AddressOfNames", ctypes.c_uint32),
        ("AddressOfNameOrdinals", ctypes.c_uint32)
    ]


class MODULEENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.wintypes.DWORD),
                ("th32ModuleID", ctypes.wintypes.DWORD),
                ("th32ProcessID", ctypes.wintypes.DWORD),
                ("GlblcntUsage", ctypes.wintypes.DWORD),
                ("ProccntUsage", ctypes.wintypes.DWORD),
                ("modBaseAddr", ctypes.wintypes.LPBYTE),
                ("modBaseSize", ctypes.wintypes.DWORD),
                ("hModule", ctypes.wintypes.HMODULE),
                ("szModule", ctypes.wintypes.CHAR * 256),
                ("szExePath", ctypes.wintypes.CHAR * 260)]
    
class Process():
    def __init__(self):
        self.__exports = {}
        self.__ks = Ks(KS_ARCH_X86, KS_MODE_64)

    def write_bytes(self, address:int, new_bytes:bytes|tuple):
        """
        Writes bytes at a given address such as b0 01 c3 (mov al,01;ret;)

        Return value
        -
        If the function succeeds then the return is True otherwise its None
        
        """
        try:
            old_protect = ctypes.wintypes.DWORD()


            _VirtualProtect(ctypes.c_void_p(address), len(new_bytes), 0x40, ctypes.byref(old_protect)) # Make sure we can write to the address even if we cant (will fail on things like the peb meaning you still cant write to the peb for example you cant write to any python.exe strings in the peb if python.exe is the main running program)
            ctypes.memmove(ctypes.c_void_p(address), new_bytes, len(new_bytes))
            _VirtualProtect(ctypes.c_void_p(address), len(new_bytes), old_protect.value, ctypes.byref(old_protect))
        except:
            return None
        return True
    

    def write_ctype(self, address:int, ctype:ctypes.Structure):
        """
        Writes a specified ctype type's value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_bytes(address, ctypes.string_at(ctypes.byref(ctype), ctypes.sizeof(ctype)))
    
    def write_string(self, address:int, value, encoding='UTF-8'):
        """
        Writes a ctypes.c_string value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_bytes(address, value.encode(encoding))
    
    def write_short(self, address:int, value):
        """
        Writes a ctypes.c_short value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_short(value))

    def write_ushort(self, address:int, value):
        """
        Writes a ctypes.c_ushort value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_ushort(value))

    def write_longlong(self, address:int, value):
        """
        Writes a ctypes.c_longlong value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_longlong(value))

    def write_ulonglong(self, address:int, value):
        """
        Writes a ctypes.c_ulonglong value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_ulonglong(value))

    def write_long(self, address:int, value):
        """
        Writes a ctypes.c_long value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_long(value))

    def write_ulong(self, address:int, value):
        """
        Writes a ctypes.c_ulong value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_ulong(value))

    def write_int(self, address:int, value):
        """
        Writes a ctypes.c_int value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_int(value))

    def write_uint(self, address:int, value):
        """
        Writes a ctypes.c_uint value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_uint(value))

    def write_float(self, address:int, value):
        """
        Writes a ctypes.c_float value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_float(value))

    def write_double(self, address:int, value):
        """
        Writes a ctypes.c_double value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_double(value))

    def write_char(self, address:int, value):
        """
        Writes a ctypes.c_char value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_char(value))

    def write_uchar(self, address:int, value):
        """
        Writes a ctypes.c_ubyte value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_ubyte(value))

    def write_bool(self, address:int, value):
        """
        Writes a ctypes.c_bool value to a specified memory address. If the memory region is read-only, the function temporarily changes its protection to allow writing, then restores the original protection afterward.

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.write_ctype(address, ctypes.c_bool(value))

    def read_bytes(self, address:int, length:int):
        """
        Reads bytes from address and returns it as raw bytes object

        Return value
        -
        If the function succeeds the return value is nonzero

        """
        try:
            return (ctypes.c_char * length).from_address(address).raw
        except: # This isnt needed when using windows functions since they have their own error handling but since this is our own func we need error handling
            return None

    def read_ctype(self, address:int, ctype:ctypes.Structure):
        """
        Reads a ctype type such as a ctype.Structure and returns it as a structure object

        Return value
        -
        If the function succeeds the return value is nonzero

        """
        try:
            return ctypes.cast(address, ctypes.POINTER(ctype)).contents
        except:
            return None
        
    def read_string(self, address:int, length:int=50, encoding:str='UTF-8'):
        """
        Reads a string but cannot read a Utf-16 string so use read_bytes with a hard coded length or instead of Utf-
        
        Return value
        -
        If the function succeeds the return value is is the decoded string

        """
        buff = self.read_bytes(address, length)
        if buff:
            i = buff.find(b'\x00')
            if i != -1:
                buff = buff[:i]
            buff = buff.decode(encoding)
        return buff
    
    def read_unicode_string(self, address:int, length:int):
        """
        Reads a unicode string at a specified address given its length

        Return value
        -

        If the function succeeds the return value is the decoded unicode string
        
        """
        data = self.read_bytes(address, length)
        if not data:
            return None
        if len(data) % 2 != 0:
            data = data[:-1]
        return data.decode("utf-16-le", errors="ignore").rstrip("\x00")


    def read_short(self, address:int):
        """
        Reads a ctypes.c_short from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_short).value
    
    def read_ushort(self, address:int):
        """
        Reads a ctypes.c_ushort from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_ushort).value

    def read_longlong(self, address:int):
        """
        Reads a ctypes.c_longlong from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_longlong).value
    
    def read_ulonglong(self, address:int):
        """
        Reads a ctypes.c_ulonglong from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_ulonglong).value

    def read_long(self, address:int):
        """
        Reads a ctypes.c_long from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_long).value
    
    def read_ulong(self, address:int):
        """
        Reads a ctypes.c_ulong from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_ulong).value

    def read_int(self, address:int):
        """
        Reads a ctypes.c_int from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_int).value
    
    def read_uint(self, address:int):
        """
        Reads a ctypes.c_uint from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_uint).value

    def read_float(self, address:int):
        """
        Reads a ctypes.c_float from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_float).value
    

    def read_double(self, address:int):
        """
        Reads a ctypes.c_double from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_double).value

    def read_char(self, address:int):
        """
        Reads a ctypes.c_char from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_char).value.decode()
    
    def read_uchar(self, address:int):
        """
        Reads a ctypes.c_ubyte from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_ubyte).value

    def read_bool(self, address:int):
        """
        Reads a ctypes.c_bool from the specified address within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        
        """
        return self.read_ctype(address, ctypes.c_bool).value



    def __parse_module(self, module:str):
        """
        Parses a modules headers to be able to get function addresses/names

        This is an internal function
        -
        Return value
        -
        If the function succeeds the return value is a json dictionary containing the module information

        """
        module_base = self.get_module_handle(module)

        coff_offset = self.read_ctype(module_base, IMAGE_DOS_HEADER).e_lfanew

        rva = self.read_ctype(module_base + coff_offset + 0x18, IMAGE_OPTIONAL_HEADER).DataDirectory[0].VirtualAddress

        export_directory = self.read_ctype(module_base + rva, IMAGE_EXPORT_DIRECTORY)

        # Declare constants for reads
        address_of_names = module_base + export_directory.AddressOfNames
        address_of_ordinals = module_base + export_directory.AddressOfNameOrdinals
        address_of_functions = module_base + export_directory.AddressOfFunctions

        # Read all addresses/values in one go for each type to reduce calls to speed up code (original code would be reading each address + each ordinal + each function rva per iteration)
        # new code only reads the string of the function each iteration
        AddressArrayType = ctypes.c_uint32 * export_directory.NumberOfNames
        name_address_array = self.read_ctype(address_of_names, AddressArrayType)

        OrdinalsArrayType = ctypes.c_short * export_directory.NumberOfNames
        ordinals_array = self.read_ctype(address_of_ordinals, OrdinalsArrayType)

        FunctionsArrayType = ctypes.c_uint32 * export_directory.NumberOfFunctions
        functions_array = self.read_ctype(address_of_functions, FunctionsArrayType)

        exports = {}
        if len(name_address_array) == 64: # No exports (this is for some reason only needed when reading local addresses but works without this when using ReadProcessMemory)
            return None
        
        for i in range(len(name_address_array)):
            try:
                export_name = self.read_string(module_base + name_address_array[i], 256)
            except: # If read_string fails this means the pe file has no exports listed
                return exports
            export_ordinal = ordinals_array[i]
            export_rva = functions_array[export_ordinal]

            exports[export_name] = {'ordinal': export_ordinal, 'rva': export_rva}

        self.__exports[module.lower()] = exports
        
        return self.__exports[module.lower()]
    
    def get_modules(self):
        """
        Gets a list of modules using CreateToolhelp32Snapshot and also gets some values such as its full path, base of dll and size

        Return value
        -
        If the function succeeds the return value is a json object containing each dll's full path name, the base address and the size

        """
        modules = {}
        snapshot = _CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, 0)

        if snapshot:
            module = MODULEENTRY32()
            module.dwSize = ctypes.sizeof(module)
            _Module32First(snapshot, ctypes.byref(module))
            
            while True:
                module_name = module.szModule.decode().lower()
                module_path = module.szExePath.decode()
                modules[module_name] = {"Full path": module_path, "lpBaseOfDll": ctypes.cast(module.modBaseAddr, ctypes.c_void_p).value, "SizeOfImage": module.modBaseSize}
                module = MODULEENTRY32()
                module.dwSize = ctypes.sizeof(MODULEENTRY32)

                if not _Module32Next(snapshot, ctypes.byref(module)):
                    break

            _CloseHandle(snapshot)
        
        return modules
    
    def get_module_from_name(self, module:str):
        """
        Gets a module using CreateToolhelp32Snapshot and also gets some values such as its full path, base of dll and size

        Return value
        -
        If the function succeeds the return value is a json object containing the dll's full path name, the base address and the size

        """

        return self.get_modules().get(module)



    
    def get_modules_from_peb(self):
        """
        Gets the module names loaded within the process by walking the InMemoryOrderModulesList in the Ldr in the peb
        
        Requires write access
        -
        Return value
        -
        If the function succeeds the return value is the list of the currently loaded modules and various info.
        """
        
        
        address = self.get_peb()
        address = self.read_longlong(address + 0x18)
        address = self.read_longlong(address + 0x10)
        first_address = address
        modules = {}

        # Use structures to read the memory instead of reading offsets (this makes it run a couple milliseconds faster and makes the code more mutable and readable)
        while True:
            # Read the structure contents
            module_info = self.read_ctype(address, LDR_DATA_TABLE_ENTRY)
            
            # Set the address to the next module in the LIST_ENTRY
            address = self.read_longlong(address)

            # If the module name length is 0 that means theirs not actually a valid module here so we skip to the next module
            if not module_info.BaseDllName.Length:
                pass

            if module_info.BaseDllName.Buffer and module_info.BaseDllName.Length and module_info.FullDllName.Buffer and module_info.FullDllName.Length: # Apparently all of a sudden in this windows install sometimes we get a invalid buffer or invalid length so this wasnt needed before
                module_name = self.read_unicode_string(module_info.BaseDllName.Buffer, module_info.BaseDllName.Length)
                module_path = self.read_unicode_string(module_info.FullDllName.Buffer, module_info.FullDllName.Length)
            
            if address == first_address:
                break
            
            if not module_name in modules:
                modules[module_name] = {"Full path": module_path, "lpBaseOfDll": module_info.DllBase, "EntryPoint": module_info.EntryPoint, "SizeOfImage": module_info.SizeOfImage}

        return modules
    
    def get_all_exports(self):
        """
        Gets a list of all loaded modules and their exports

        Return value
        -
        If the function succeeds the return value is a json containing every found module and their exports name's rva's and ordinals 
        
        """
        modules = self.get_modules()
            
        for module in modules:
            self.__parse_module(module)
        
        return self.__exports
        
    def get_module_exports(self, module:str):
        """
        Gets a list of the specified modules exports

        Return value
        -
        If the function succeeds the return value is a json caontaining the module's export name's rva's and ordinals 
        
        """
        return self.__parse_module(module)

    def get_proc_address(self, module:str, function:str):
        """
        Gets the address of the specified function without calling GetProcAddress

        Return value
        -
        If the function suceeds the return value is the address of the function
        
        """
        module_base = self.get_module_handle(module)
        if self.__exports.get(module.lower()):
            return module_base + self.__exports.get(module.lower())[function]['rva']


        return module_base + self.__parse_module(module).get(function)['rva']
    
    def get_module_handle(self, module:str):
        """
        Gets the handle of a specified module

        Return value
        -
        If the function succeeds the return value is a nonzero
        
        """
        return _GetModuleHandleW(module)
    
    def get_peb(self):
        """
        Gets the address of the start of the peb

        Return value
        -
        If the function succeeds the return value is nonzero
        
        """
        peb_return = self.allocate(8)
        
        GET_PEB = f"""
            mov rax, gs:[0x60];
            mov [{hex(peb_return)}], rax;
            ret;
        """

        self.execute_code(GET_PEB)

        peb = self.read_longlong(peb_return)

        return peb

    
    def allocate(self, amount:int):
        """
        Allocates the specified amount of bytes within the process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        """
        buffer = _VirtualAlloc(None, amount, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
        return buffer
    
    def free(self, address:int):
        """
        Frees previously allocated memory at the specified address

        Return value
        -
        If the function succeeds, the return value is nonzero
        
        """
        return _VirtualFree(ctypes.c_void_p(address), 0, MEM_DECOMMIT)
    
    def execute_code(self, code:bytes|str):
        """
        Executes assembly in process given its machine code or bytes
        
        Once the code has executed and exited it will automatically be cleaned up

        Example
        -
        mov rax, gs:[0x60]; mov some_address, rax; ret


        Return value
        -
        If the function succeeds the return value is nonzero

        """
        if not isinstance(code, (bytes, str)):
            raise TypeError("Invalid parameter, only valid type is a string or bytes")
        
        if isinstance(code, str):
            code = self.assemble(code)

        assembly_address = self.allocate(len(code))
        self.write_bytes(assembly_address, code)
        self.start_thread(assembly_address)

        self.free(assembly_address)
        return True
    

    def execute_code_async(self, code:bytes|str):
        """
        Executes assembly in a process given its machine code or bytes asynchronously
        
        Will not deallocate memory when it finishes its thread

        Example
        -
        mov rax, gs:[0x60]; mov some_address, rax; ret

        Return value
        -
        If the function succeeds the return value is a list containing the thread handle and the address where the code is being executed at

        """

        if not isinstance(code, (bytes, str)):
            raise TypeError("Invalid parameter, only valid type is a string or bytes")
        
        if isinstance(code, str):
            code = self.assemble(code)

        assembly_address = self.allocate(len(code))
        self.write_bytes(assembly_address, code)

        thread = self.start_thread(assembly_address, _async=True)

        return (thread, assembly_address)




    def start_thread(self, address:int, params:int=0, _async:bool=False):
        """
        Starts a thread at the given address

        Return value
        -
        If the function succeeds the return value is either True or a handle to the thread that is running if _async=True
        
        """
        NULL_SECURITY_ATTRIBUTES = ctypes.cast(0, ctypes.POINTER(SECURITY_ATTRIBUTES))
        hThread = _CreateThread(NULL_SECURITY_ATTRIBUTES, 0, ctypes.c_void_p(address), params, 0)
        if not _async:
            _WaitForSingleObject(hThread, -1)
            _CloseHandle(hThread)
        else:
            return hThread

        return True

    def assemble(self, code:str):
        """
        Assembles 64 bit machine code into opcodes

        Return value
        -
        If the function succeeds the return value is a bytes object
        
        """
        return self.__ks.asm(code, as_bytes=True)[0]
    
    def hide_module(self, module:str):
        """
        Hides the specified module in process by removing it's flink and blink in the peb
        
        Requires write access
        -

        Return value
        -
        If the function succeeds the return value is nonzero

        """

        # This is put in a seperate function for nicer looking code
        def replace_flink_blink(_address):
            # Get current module's list entry
            entry = self.read_ctype(_address, LIST_ENTRY) # Replaced read_longlong calls with a single read ctype call also making the code a little nicer

            # Go to next module and replace its flink
            self.write_longlong(entry.Blink + 0x0, entry.Flink)

            # Go to next module and replace its blink
            self.write_longlong(entry.Flink + 0x8, entry.Blink)

            
        # Helper function for replacing multiple module list pointers
        def process_module_list(module_list, offset):
            modules = set()
            seen = set()

            while True:
                if module_list in seen:
                    raise MemoryError("The specified module could not be found or isn't present within the process or cannot be overridden")
                
                unicode_string_addr = module_list + offset
                unicode_string = self.read_ctype(unicode_string_addr, UNICODE_STRING)

                # Always set module_name fresh every iteration
                module_name = ""
                if unicode_string.Buffer and unicode_string.Length:
                    try:
                        module_name = self.read_unicode_string(unicode_string.Buffer, unicode_string.Length)
                    except:
                        module_name = ""

                modules.add(module_name)
                seen.add(module_list)

                # Case-insensitive match
                if module_name.lower() == module.lower():
                    replace_flink_blink(module_list)
                    break

                # Move to next module (LIST_ENTRY.Flink)
                module_list = self.read_longlong(module_list)

            return modules
            
            
            
        if not isinstance(module, str):
            raise TypeError("Wrong type, only allowed type is a string")
        

        address = self.read_longlong(self.get_peb() + 0x18)

        InLoadOrderModuleList = self.read_longlong(address + 0x10)
        InMemoryOrderModuleList = self.read_longlong(address + 0x20)
        InInitializationOrderModuleList = self.read_longlong(address + 0x30)

        process_module_list(InLoadOrderModuleList, 0x58)
        process_module_list(InMemoryOrderModuleList, 0x48)
        process_module_list(InInitializationOrderModuleList, 0x38)
        return True

    def hide_python(self):
        """
        Hides the currently loaded python dll in the peb

        Return value
        -
        If the function succeeds the return value is nonzero


        """
        one = self.hide_module('python{0}{1}.dll'.format(sys.version_info.major, sys.version_info.minor))
        two = self.hide_module('python{0}.dll'.format(sys.version_info.major))
        return (one, two) 
    
    def unload_module(self, module:str):
        """
        Unloads a module from process

        Return value
        -
        If the function succeeds the return value is nonzero
        
        """
        if not isinstance(module, str):
            raise TypeError("Wrong type, only allowed type is a string")
        
        _FreeLibraryAndExitThread(self.get_module_handle(module), 0)
        return True
    
    def pattern_scan_module(self, module:str, pattern:bytes, return_multiple:bool=False):
        """
        Scans a specified module for a match

        Return value
        -
        If the function succeeds the return value is the address at which the pattern was found
        
        """
        module_data = self.get_module_from_name(module)
        if not module_data:
            return None
        
        module_base = module_data.get('lpBaseOfDll')
        if not module_base:
            return None
        
        module_bytes = self.read_bytes(module_base, module_data.get('SizeOfImage'))
        if not module_bytes:
            return None
        
        found = None
        patt = re.compile(pattern)
        if return_multiple:
            found = patt.finditer(module_bytes)
            if found:
                found = [module_base + i.start() for i in found]
        else:
            found = patt.search(module_bytes)
            if found:
                found = module_base + found.start()

        return found


    def pattern_scan_all_modules(self, pattern:bytes, return_multiple:bool=False):
        """
        Scans a specified module for a match

        Return value
        -
        If the function succeeds the return value is the address at which the pattern was found
        
        """
        modules = self.get_modules()
        found = None
        for i in modules:
            data = self.pattern_scan_module(i, pattern, return_multiple)
            if data:
                found = data
                if not return_multiple:
                    break

        return found