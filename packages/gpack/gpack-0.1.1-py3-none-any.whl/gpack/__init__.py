import builtins
import ast
from .Converter import binary2decimal,decimal2binary,hex2binary,binary2hex
from .deep_hexlib import text2hex,hex2text

__version__ = "0.1.1"
__all__ = ['binary2decimal', 'decimal2binary', 'hex2binary', 'binary2hex', 'text2hex', 'hex2text','pack','unpack']

class gpack_func_str(str):
    def pack(self,arg,count):
        arg = arg.replace(" ","")
        endian = "little"
        if arg[0].lower()=="b" or arg[0]==">":
            endian = "big"
            arg = arg[1:]
        if arg[0].lower()=="l" or arg[0]=="<":
            endian = "little"
            arg = arg[1:]
        if arg[0].lower()=="s":
            if endian=="little":
                return self.encode().ljust(count,b"\x00")
            else:
                return self.encode().ljust(count,b"\x00")[::-1]
        elif arg[0] == "i" or arg[0] == "I":
            num = int(self)
            size = count
            
            # Проверка диапазона для signed/unsigned
            if arg[0] == "I":  # signed
                max_val = 2**(size*8-1) - 1
                min_val = -2**(size*8-1)
            else:  # unsigned "I"
                max_val = 2**(size*8) - 1
                min_val = 0
                
            if num < min_val or num > max_val:
                raise ValueError(f"Value {num} out of range for {size} bytes")
            
            # Обработка отрицательных чисел для signed
            if arg[0] == "I" and num < 0:
                num = (1 << (size * 8)) + num
            
            # Прямое преобразование в байты
            result = bytearray()
            for i in range(size):
                if endian == "little":
                    # Младшие байты first
                    result.append((num >> (i * 8)) & 0xFF)
                else:
                    # Старшие байты first  
                    result.append((num >> ((size - 1 - i) * 8)) & 0xFF)
            
            return bytes(result)
        else:
            raise Exception("Arguments not found!")
class gpack_func_bytes(bytes):
    def pack(self,arg,count):
        arg = arg.replace(" ","")
        endian = "little"
        if arg[0].lower()=="b" or arg[0]==">":
            endian = "big"
            arg = arg[1:]
        elif arg[0].lower()=="l" or arg[0]=="<":
            endian = "little"
            arg = arg[1:]
        if arg[0].lower()=="n":
            if endian=="little":
                return self.ljust(count,b"\x00")
            else:
                return self.ljust(count,b"\x00")[::-1]
        else:
            raise Exception("Arguments not found!")
    def unpack(self,args,*counts):
        args = args.replace(" ","")
        fullself = self
        selfcount = 0
        oldselfcount = 0
        count = 0
        count_offset = 0
        endian = "little"
        localreturn = []
        for i in range(len(args)):
            arg = args[i]
            if arg[0].lower()=="b" or arg[0].lower()=="l" or arg[0]==">" or arg[0]=="<":
                count = 0
                count_offset += 1
            else:
                count = counts[i-count_offset]
            selfcount+=count
            self = fullself[oldselfcount:selfcount]
            if arg[0].lower()=="b" or arg[0]==">":
                endian = "big"
            elif arg[0].lower()=="l" or arg[0]=="<":
                endian = "little"
            elif arg[0].lower()=="s":
                if endian=="little":
                    localreturn.append([self.replace(b"\x00",b"").decode()[i:i+count] for i in range(0, len(self.replace(b"\x00",b"")), count)][0])
                else:
                    localself = self[::-1].replace(b"\x00",b"")
                    localreturn.append([localself.decode()[i:i+count] for i in range(0, len(localself), count)][0])
            elif arg[0].lower()=="n":
                if endian=="little":
                    localreturn.append([self[i:i+count] for i in range(0, len(self), count)][0])
                else:
                    localself = self[::-1]
                    localreturn.append([localself[i:i+count] for i in range(0, len(self), count)][0])
            elif arg[0].lower()=="o":
                localreturn.append(self[0]==1)
            elif arg[0]=="i": 
                if endian=="little":
                    localself = self[::-1]
                    internal = []
                    for i in [localself[i:i+count] for i in range(0, len(self), count)]:
                        internal.append(binary2decimal(hex2binary(text2hex(i,True))))
                    localreturn.append(internal[0])
                else:
                    localself = self
                    internal = []
                    for i in [localself[i:i+count] for i in range(0, len(self), count)]:
                        internal.append(binary2decimal(hex2binary(text2hex(i,True))))
                    localreturn.append(internal[0])
            elif arg[0] == "I":
                if endian == "little":
                    localself = self[::-1]
                    internal = []
                    for i in [localself[i:i+count] for i in range(0, len(self), count)]:
                        num = binary2decimal(hex2binary(text2hex(i, True)))
                        max_unsigned = 2**(count*8)
                        if num >= 2**(count*8-1):
                            num = num - max_unsigned
                        internal.append(num)
                    localreturn.append(internal[0])
                else:
                    localself = self
                    internal = []
                    for i in [localself[i:i+count] for i in range(0, len(self), count)]:
                        num = binary2decimal(hex2binary(text2hex(i, True)))
                        max_unsigned = 2**(count*8)
                        if num >= 2**(count*8-1):
                            num = num - max_unsigned
                        internal.append(num)
                    localreturn.append(internal[0])
                
            else:
                raise Exception("Arguments not found!")
            if not arg[0].lower()=="b" or not arg[0].lower()=="l":
                oldselfcount+=count
        return localreturn

class gpack_func_list(list):
    def pack(self,args,*counts):
        args = args.replace(" ","")
        fullself = self
        self_index = 0
        count = 0
        count_offset = 0
        localreturn = b""
        endian = "little"
        for i in range(len(args)):
            arg = args[i]
            if arg[0].lower()=="b" or arg[0].lower()=="l" or arg[0]=="<" or arg[0]==">":
                count = 0
                count_offset += 1
            else:
                count = counts[i-count_offset]
            
            you_are_need_to_fix_this_problem = fullself[self_index]
            #print(you_are_need_to_fix_this_problem, self_index, count, arg, i-count_offset)
            if arg[0].lower()=="b" or arg[0]==">":
                endian = "big"
            elif arg[0].lower()=="l" or arg[0]=="<":
                endian = "little"
            elif arg[0].lower()=="n":
                if endian=="little":
                    localreturn+=you_are_need_to_fix_this_problem.ljust(count,b"\x00")
                    self_index += 1
                else:
                    localreturn+=you_are_need_to_fix_this_problem.ljust(count,b"\x00")[::-1]
                    self_index += 1
            elif arg[0].lower() == "o":
                localreturn+=b"\x01" if you_are_need_to_fix_this_problem else b"\x00"
                self_index += 1
            elif arg[0].lower()=="s":
                if endian=="little":
                    localreturn+=str(you_are_need_to_fix_this_problem).encode().ljust(count,b"\x00")
                else:
                    localreturn+=str(you_are_need_to_fix_this_problem).encode().ljust(count,b"\x00")[::-1]
                self_index += 1
            elif arg[0] == "i" or arg[0] == "I":
                num = int(you_are_need_to_fix_this_problem)
                size = count
                
                # Проверка диапазона для signed/unsigned
                if arg[0] == "I":  # signed
                    max_val = 2**(size*8-1) - 1
                    min_val = -2**(size*8-1)
                else:  # unsigned "I"
                    max_val = 2**(size*8) - 1
                    min_val = 0
                    
                if num < min_val or num > max_val:
                    raise ValueError(f"Value {num} out of range for {size} bytes")
                
                # Обработка отрицательных чисел для signed
                if arg[0] == "I" and num < 0:
                    num = (1 << (size * 8)) + num
                
                # Прямое преобразование в байты
                result = bytearray()
                for j in range(size):
                    if endian == "little":
                        # Младшие байты first
                        result.append((num >> (j * 8)) & 0xFF)
                    else:
                        # Старшие байты first  
                        result.append((num >> ((size - 1 - j) * 8)) & 0xFF)
                
                localreturn+=bytes(result)
                self_index += 1
            else:
                raise Exception("Arguments not found!")
        return localreturn

class gpack_func_bool:
    def __init__(self, value=False, count=None):
        self._value = bool(value)
    
    def pack(self, arg, count=None):
        arg = arg.replace(" ","")
        endian = "little"
        if arg[0].lower() == "b" or arg[0]==">":
            endian = "big"
            arg = arg[1:]
        elif arg[0].lower() == "l" or arg[0]=="<":
            endian = "little"
            arg = arg[1:]
        if arg[0].lower() == "o":
            return b"\x01" if self._value else b"\x00"
        else:
            raise Exception("Arguments not found!")
    
    def __bool__(self):
        return self._value
    
    def __repr__(self):
        return repr(self._value)

def pack(data, format_str, *sizes):
    if isinstance(data, str):
        return gpack_func_str(data).pack(format_str, *sizes)
    elif isinstance(data, list):
        return gpack_func_list(data).pack(format_str, *sizes)
    elif isinstance(data, bytes):
        return gpack_func_bytes(data).pack(format_str, *sizes)
    elif isinstance(data, bool):
        return gpack_func_bool(data).pack(format_str, *sizes)
    else:
        return gpack_func_list([data]).pack(format_str, *sizes)

def unpack(data, format_str, *sizes):
    if isinstance(data, bytes):
        result = gpack_func_bytes(data).unpack(format_str, *sizes)
        return result[0] if len(result) == 1 else result
    else:
        raise TypeError("Unpack requires bytes data")
import sys
import traceback
import os
import ast
import builtins

class SimpleCompiler:
    def __init__(self):
        self.original_compile = builtins.compile
        self.transforming = False
    
    def __call__(self, source, filename, mode, flags=0, dont_inherit=False, optimize=-1, **_):
        return self.compile(source, filename, mode, flags, dont_inherit, optimize)
    
    def compile(self, source, filename, mode, flags=0, dont_inherit=False, optimize=-1):
        if (self.transforming or 
            not isinstance(source, str) or
            mode not in ['exec', 'single'] or
            any(x in filename for x in ['<frozen', '<string>', 'ast.py', 'traceback.py'])):
            return self.original_compile(source, filename, mode, flags, dont_inherit, optimize)
        
        try:
            self.transforming = True
            tree = ast.parse(source, filename, mode)
            
            class Transformer(ast.NodeTransformer):
                def __init__(self):
                    super().__init__()
                    self.in_comparison = False
                    self.in_assignment = False
                
                def visit_Constant(self, node):
                    # Don't transform boolean literals in comparisons or assignments
                    if isinstance(node.value, bool) and (self.in_comparison or self.in_assignment):
                        return node
                    
                    if isinstance(node.value, str):
                        return ast.Call(
                            func=ast.Name(id='gpack_func_str', ctx=ast.Load()),
                            args=[node],
                            keywords=[]
                        )
                    elif isinstance(node.value, bytes):
                        return ast.Call(
                            func=ast.Name(id='gpack_func_bytes', ctx=ast.Load()),
                            args=[node],
                            keywords=[]
                        )
                    elif isinstance(node.value, list):
                        # Only wrap list literals
                        return ast.Call(
                            func=ast.Name(id='gpack_func_list', ctx=ast.Load()),
                            args=[node],
                            keywords=[]
                        )
                    elif isinstance(node.value, bool):
                        # Transform boolean literals to wrapped versions
                        return ast.Call(
                            func=ast.Name(id='gpack_func_bool', ctx=ast.Load()),
                            args=[node],
                            keywords=[]
                        )
                    return node
                
                def visit_List(self, node):
                    # Transform list literals like [1, 2, 3]
                    node = self.generic_visit(node)
                    return ast.Call(
                        func=ast.Name(id='gpack_func_list', ctx=ast.Load()),
                        args=[ast.List(elts=node.elts, ctx=node.ctx)],
                        keywords=[]
                    )
                
                def visit_Dict(self, node):
                    # Don't transform the entire dict, just visit its contents
                    node = self.generic_visit(node)
                    return node
                
                def visit_Name(self, node):
                    # Don't transform True/False in comparisons or assignments
                    if node.id in ['True', 'False'] and isinstance(node.ctx, ast.Load):
                        if self.in_comparison or self.in_assignment:
                            return node
                        # Transform to wrapped boolean
                        return ast.Call(
                            func=ast.Name(id='gpack_func_bool', ctx=ast.Load()),
                            args=[ast.Constant(value=True if node.id == 'True' else False)],
                            keywords=[]
                        )
                    return node
                
                def visit_Compare(self, node):
                    old_in_comparison = self.in_comparison
                    self.in_comparison = True
                    node = self.generic_visit(node)
                    self.in_comparison = old_in_comparison
                    return node
                
                def visit_Assign(self, node):
                    old_in_assignment = self.in_assignment
                    self.in_assignment = True
                    node = self.generic_visit(node)
                    self.in_assignment = old_in_assignment
                    return node
                
                def visit_AugAssign(self, node):
                    old_in_assignment = self.in_assignment
                    self.in_assignment = True
                    node = self.generic_visit(node)
                    self.in_assignment = old_in_assignment
                    return node
                
                def visit_Call(self, node):
                    # Check if this is a gpack function call that should return wrapped objects
                    if isinstance(node.func, ast.Attribute):
                        # Handle method calls on gpack objects
                        node.func.value = self.visit(node.func.value)
                        
                        # Wrap gpack objects for method calls
                        if (isinstance(node.func.value, ast.Call) and
                            isinstance(node.func.value.func, ast.Name) and
                            node.func.value.func.id.startswith('gpack_func_')):
                            node.func.value = ast.Call(
                                func=ast.Name(id='_gpack_wrapper', ctx=ast.Load()),
                                args=[node.func.value],
                                keywords=[]
                            )
                        elif (isinstance(node.func.value, ast.Name) and
                              node.func.value.id == 'gpack'):
                            # This is a call like gpack.hex2text()
                            # We need to wrap the result
                            node = ast.Call(
                                func=ast.Name(id='_gpack_wrapper', ctx=ast.Load()),
                                args=[node],
                                keywords=[]
                            )
                    elif isinstance(node.func, ast.Name):
                        # Check if this is a gpack function directly
                        if node.func.id in ['gpack_func_str', 'gpack_func_bytes', 
                                          'gpack_func_list', 'gpack_func_bool']:
                            # Already wrapped by our transformer
                            pass
                        elif node.func.id == 'gpack':
                            # This shouldn't happen, but just in case
                            node = ast.Call(
                                func=ast.Name(id='_gpack_wrapper', ctx=ast.Load()),
                                args=[node],
                                keywords=[]
                            )
                    
                    return self.generic_visit(node)
                
                def visit_Subscript(self, node):
                    node = self.generic_visit(node)
                    
                    if (isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Name) and
                        node.value.func.id.startswith('gpack_func_')):
                        return ast.Call(
                            func=ast.Name(id='_gpack_wrapper', ctx=ast.Load()),
                            args=[node],
                            keywords=[]
                        )
                    return node
                
                def visit_BinOp(self, node):
                    # Handle binary operations like +
                    node = self.generic_visit(node)
                    
                    # Check if either operand is a gpack object
                    left_is_gpack = (isinstance(node.left, ast.Call) and
                                   isinstance(node.left.func, ast.Name) and
                                   node.left.func.id.startswith('gpack_func_'))
                    right_is_gpack = (isinstance(node.right, ast.Call) and
                                    isinstance(node.right.func, ast.Name) and
                                    node.right.func.id.startswith('gpack_func_'))
                    
                    if left_is_gpack or right_is_gpack:
                        # Wrap the result of binary operations involving gpack objects
                        return ast.Call(
                            func=ast.Name(id='_gpack_wrapper', ctx=ast.Load()),
                            args=[node],
                            keywords=[]
                        )
                    return node
                
                def visit_Attribute(self, node):
                    # Handle attribute access on gpack objects
                    node = self.generic_visit(node)
                    
                    if (isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Name) and
                        node.value.func.id.startswith('gpack_func_')):
                        # Wrap gpack object attribute access
                        return ast.Call(
                            func=ast.Name(id='_gpack_wrapper', ctx=ast.Load()),
                            args=[node],
                            keywords=[]
                        )
                    return node
            
            tree = Transformer().visit(tree)
            ast.fix_missing_locations(tree)
            code = self.original_compile(tree, filename, mode, flags, dont_inherit, optimize)
            self.transforming = False
            return code
            
        except Exception as e:
            self.transforming = False
            return self.original_compile(source, filename, mode, flags, dont_inherit, optimize)

def _gpack_wrapper(obj):
    """Wrap objects to ensure they have gpack methods."""
    # If obj is a bytes object from gpack functions, wrap it
    if isinstance(obj, bytes):
        # Check if this is already a gpack-wrapped bytes object
        if hasattr(obj, '_is_gpack') and obj._is_gpack:
            return obj
        
        # Create a wrapped bytes object
        class GpackBytes(bytes):
            _is_gpack = True
            
            def pack(self, *args, **kwargs):
                return gpack_func_bytes(self).pack(*args, **kwargs)
            
            def unpack(self, *args, **kwargs):
                return gpack_func_bytes(self).unpack(*args, **kwargs)
            
            def __add__(self, other):
                result = super().__add__(other)
                return _gpack_wrapper(result)
            
            def __radd__(self, other):
                result = super().__radd__(other)
                return _gpack_wrapper(result)
        
        return GpackBytes(obj)
    
    # If obj is a bool, wrap it
    elif isinstance(obj, bool):
        return gpack_func_bool(obj)
    
    # If obj is a string, wrap it
    elif isinstance(obj, str):
        return gpack_func_str(obj)
    
    # If obj is a list, wrap it
    elif isinstance(obj, list):
        return gpack_func_list(obj)
    
    # If obj is a gpack function call result, execute it
    elif isinstance(obj, ast.AST):
        # This shouldn't happen at runtime
        return obj
    
    # Return obj as-is if it's already a gpack object or we can't wrap it
    return obj

# Initialize the compiler
compiler = SimpleCompiler()
builtins.compile = compiler

# Create wrapped boolean values
class BoolWrapper:
    def __init__(self, value):
        self._value = bool(value)
        self._is_gpack = True
    
    @property
    def _gpack_instance(self):
        if not hasattr(self, '_gpack_inst'):
            self._gpack_inst = gpack_func_bool(self._value)
        return self._gpack_inst
    
    @_gpack_instance.setter
    def _gpack_instance(self, value):
        self._gpack_inst = value
    
    def pack(self, *args, **kwargs):
        return self._gpack_instance.pack(*args, **kwargs)
    
    def __bool__(self):
        return self._value
    
    def __eq__(self, other):
        if isinstance(other, BoolWrapper):
            return self._value == other._value
        elif isinstance(other, bool):
            return self._value == other
        return NotImplemented
    
    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
    
    def __hash__(self):
        return hash(self._value)
    
    def __repr__(self):
        return repr(self._value)
    
    def __str__(self):
        return str(self._value)
    
    def __lt__(self, other):
        if isinstance(other, (bool, BoolWrapper)):
            other_val = other._value if isinstance(other, BoolWrapper) else other
            return self._value < other_val
        return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, (bool, BoolWrapper)):
            other_val = other._value if isinstance(other, BoolWrapper) else other
            return self._value <= other_val
        return NotImplemented
    
    def __gt__(self, other):
        if isinstance(other, (bool, BoolWrapper)):
            other_val = other._value if isinstance(other, BoolWrapper) else other
            return self._value > other_val
        return NotImplemented
    
    def __ge__(self, other):
        if isinstance(other, (bool, BoolWrapper)):
            other_val = other._value if isinstance(other, BoolWrapper) else other
            return self._value >= other_val
        return NotImplemented

TRUE = BoolWrapper(True)
FALSE = BoolWrapper(False)

# Store in globals and builtins
globals_dict = globals()
globals_dict['gpack_func_str'] = gpack_func_str
globals_dict['gpack_func_bytes'] = gpack_func_bytes
globals_dict['gpack_func_list'] = gpack_func_list
globals_dict['gpack_func_bool'] = gpack_func_bool
globals_dict['_gpack_wrapper'] = _gpack_wrapper
globals_dict['TRUE'] = TRUE
globals_dict['FALSE'] = FALSE

builtins.gpack_func_str = gpack_func_str
builtins.gpack_func_bytes = gpack_func_bytes
builtins.gpack_func_list = gpack_func_list
builtins.gpack_func_bool = gpack_func_bool
builtins._gpack_wrapper = _gpack_wrapper
builtins.TRUE = TRUE
builtins.FALSE = FALSE

# Also wrap the gpack module functions
import gpack as original_gpack

class GpackModuleWrapper:
    def __init__(self, original_module):
        self._original = original_module
        self._is_gpack = True
    
    def __getattr__(self, name):
        attr = getattr(self._original, name)
        if callable(attr):
            def wrapped_func(*args, **kwargs):
                result = attr(*args, **kwargs)
                # Wrap the result if it's bytes, str, bool, or list
                return _gpack_wrapper(result)
            return wrapped_func
        return attr
    
    def __call__(self, *args, **kwargs):
        # Handle if someone tries to call the module itself
        return self._original(*args, **kwargs)

# Replace the gpack module in sys.modules
sys.modules['gpack'] = GpackModuleWrapper(original_gpack)
# Update builtins and globals
builtins.gpack = sys.modules['gpack']
globals_dict['gpack'] = sys.modules['gpack']

# Auto-run for scripts
if (len(sys.argv) > 0 and 
    not sys.argv[0].endswith('gpack.py') and 
    os.path.exists(sys.argv[0]) and
    not getattr(builtins, '_gpack_auto_run', False)):
    
    builtins._gpack_auto_run = True
    
    try:
        with open(sys.argv[0], 'r', encoding="utf-8") as f:
            source = f.read()
        
        code = compile(source, sys.argv[0], 'exec')
        
        exec_ns = {
            '__name__': '__main__', 
            '__file__': sys.argv[0],
            'gpack_func_str': gpack_func_str,
            'gpack_func_bytes': gpack_func_bytes,
            'gpack_func_list': gpack_func_list,
            'gpack_func_bool': gpack_func_bool,
            '_gpack_wrapper': _gpack_wrapper,
            'TRUE': TRUE,
            'FALSE': FALSE,
            'gpack': sys.modules['gpack']
        }
        
        exec(code, exec_ns)
        
    except Exception as e:
        exc_info = traceback.format_exc()
        lines = exc_info.split('\n')
        if len(lines) > 5:
            print(lines[0])
            print('\n'.join(lines[4:]))
        else:
            print(exc_info)
    
    sys.exit(0)