import builtins
import ast
from .Converter import binary2decimal,decimal2binary,hex2binary,binary2hex
from .deep_hexlib import text2hex,hex2text

__version__ = "0.1.3"
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
            if arg[0].lower()=="b" or arg[0].lower()=="l" or arg[0].lower()==">" or arg[0].lower()=="<":
                count = 0
                count_offset += 1
            else:
                count = counts[i-count_offset]
            selfcount+=count
            self = fullself[oldselfcount:selfcount]
            if arg[0].lower()=="b" or arg[0].lower()==">":
                endian = "big"
            elif arg[0].lower()=="l" or arg[0].lower()=="<":
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
is_alt=True
def setup():
    is_alt=False
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
                    def visit_Constant(self, node):
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
                            return ast.Call(
                                func=ast.Name(id='gpack_func_list', ctx=ast.Load()),
                                args=[node],
                                keywords=[]
                            )
                        #elif isinstance(node.value, bool):
                        #    return ast.Call(
                        #        func=ast.Name(id='gpack_func_bool', ctx=ast.Load()),
                        #        args=[node],
                        #        keywords=[]
                        #    )
                        return node
                    
                    def visit_List(self, node):
                        # Обрабатываем литералы списков [1, 2, 3]
                        return ast.Call(
                            func=ast.Name(id='gpack_func_list', ctx=ast.Load()),
                            args=[ast.List(elts=node.elts, ctx=node.ctx)],
                            keywords=[]
                        )
                    
                    def visit_Name(self, node):
                        # Обрабатываем встроенные константы True и False
                        if node.id in ['True', 'False'] and isinstance(node.ctx, ast.Load):
                            return ast.Call(
                                func=ast.Name(id='gpack_func_bool', ctx=ast.Load()),
                                args=[ast.Constant(value=True if node.id == 'True' else False)],
                                keywords=[]
                            )
                        return node
                    
                    def visit_Call(self, node):
                        # Обрабатываем вызовы методов у любых объектов
                        if isinstance(node.func, ast.Attribute):
                            # Оборачиваем ЛЮБОЕ выражение (переменные, срезы, вызовы функций и т.д.)
                            new_obj = ast.Call(
                                func=ast.Name(id='_gpack_wrapper', ctx=ast.Load()),
                                args=[node.func.value],
                                keywords=[]
                            )
                            node.func.value = new_obj
                        
                        return self.generic_visit(node)
                    
                    def visit_Subscript(self, node):
                        # Обрабатываем срезы и индексацию, чтобы они тоже возвращали обернутые объекты
                        node = self.generic_visit(node)
                        # Если это срез строки или байтов, оборачиваем результат
                        if (isinstance(node.value, (ast.Name, ast.Call, ast.Subscript)) and
                            isinstance(node.ctx, ast.Load)):
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

    # Функция-обертка для определения типа в runtime
    def _gpack_wrapper(obj):
        if isinstance(obj, bytes):
            return gpack_func_bytes(obj)
        elif isinstance(obj, str):
            return gpack_func_str(obj)
        elif isinstance(obj, list):
            return gpack_func_list(obj)
        elif isinstance(obj, bool):
            return gpack_func_bool(obj)
        return obj

    # Создаем альтернативные имена для boolean значений
    class BoolWrapper:
        def __init__(self, value):
            self._value = value
            self._gpack_instance = gpack_func_bool(value)
        
        def pack(self, *args, **kwargs):
            return self._gpack_instance.pack(*args, **kwargs)
        
        def __bool__(self):
            return self._value
        
        def __repr__(self):
            return repr(self._value)

    # Создаем обернутые версии boolean значений
    TRUE = BoolWrapper(True)
    FALSE = BoolWrapper(False)

    # Заменяем compile
    builtins.compile = SimpleCompiler()
    globals()['gpack_func_str'] = gpack_func_str
    globals()['gpack_func_bytes'] = gpack_func_bytes
    globals()['gpack_func_list'] = gpack_func_list
    globals()['gpack_func_bool'] = gpack_func_bool
    globals()['_gpack_wrapper'] = _gpack_wrapper
    globals()['TRUE'] = TRUE
    globals()['FALSE'] = FALSE
    builtins.gpack_func_str = gpack_func_str
    builtins.gpack_func_bytes = gpack_func_bytes
    builtins.gpack_func_list = gpack_func_list
    builtins.gpack_func_bool = gpack_func_bool
    builtins._gpack_wrapper = _gpack_wrapper
    builtins.TRUE = TRUE
    builtins.FALSE = FALSE

    # Автозапуск для скриптов
    import sys
    import os
    import traceback
    if (len(sys.argv) > 0 and 
        not sys.argv[0].endswith('gpack.py') and 
        os.path.exists(sys.argv[0]) and
        not getattr(builtins, '_gpack_auto_run', False)):
        
        builtins._gpack_auto_run = True
        with open(sys.argv[0], 'r', encoding="utf-8") as f:
            source = f.read()
        
        code = compile(source, sys.argv[0], 'exec')
        try: exec(code, {'__name__': '__main__', '__file__': sys.argv[0]})
        except Exception as e: print(traceback.format_exc().split('\n')[0]+"\n"+"\n".join(traceback.format_exc().split('\n')[4:]))
        sys.exit(0)