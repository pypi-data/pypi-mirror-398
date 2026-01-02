import builtins
import ast
from .Converter import binary2decimal,decimal2binary,hex2binary,binary2hex
from .deep_hexlib import text2hex,hex2text

__version__ = "0.1.6"
__all__ = ['binary2decimal', 'decimal2binary', 'hex2binary', 'binary2hex', 'text2hex', 'hex2text','hex2decimal','pack','unpack']

def hex2decimal(i):
    return binary2decimal(hex2binary(i))
    
class gpack_func_str(str):
    def pack(self, arg, count=None):
        arg = arg.replace(" ", "")
        endian = "little"
        
        # Парсинг аргументов
        while arg:
            if arg[0].lower() in "bl<>":
                endian = "big" if arg[0].lower() in "b>" else "little"
                arg = arg[1:]
            elif arg[0].isdigit():
                count = int(arg[0])
                arg = arg[1:]
            elif arg[0].lower() == "s":
                arg = arg[1:]
                if count is None:
                    raise ValueError("Count not specified for string")
                if endian == "little":
                    return self.encode().ljust(count, b"\x00")
                else:
                    return self.encode().ljust(count, b"\x00")[::-1]
            elif arg[0].lower() in "iI":
                signed = arg[0] == "I"
                arg = arg[1:]
                if count is None:
                    raise ValueError("Count not specified for integer")
                
                num = int(self)
                size = count
                
                # Проверка диапазона
                if signed:  # signed
                    max_val = 2**(size*8-1) - 1
                    min_val = -2**(size*8-1)
                else:  # unsigned
                    max_val = 2**(size*8) - 1
                    min_val = 0
                    
                if num < min_val or num > max_val:
                    raise ValueError(f"Value {num} out of range for {size} bytes")
                
                # Обработка отрицательных чисел для signed
                if signed and num < 0:
                    num = (1 << (size * 8)) + num
                
                # Преобразование в байты
                result = bytearray()
                for i in range(size):
                    if endian == "little":
                        result.append((num >> (i * 8)) & 0xFF)
                    else:
                        result.append((num >> ((size - 1 - i) * 8)) & 0xFF)
                
                return bytes(result)
            else:
                raise ValueError(f"Unknown format specifier: {arg[0]}")

class gpack_func_bytes(bytes):
    def pack(self, arg, count=None):
        arg = arg.replace(" ", "")
        endian = "little"
        
        # Парсинг аргументов
        while arg:
            if arg[0].lower() in "bl<>":
                endian = "big" if arg[0].lower() in "b>" else "little"
                arg = arg[1:]
            elif arg[0].isdigit():
                count = int(arg[0])
                arg = arg[1:]
            elif arg[0].lower() == "n":
                arg = arg[1:]
                if count is None:
                    raise ValueError("Count not specified for bytes")
                if endian == "little":
                    return self.ljust(count, b"\x00")
                else:
                    return self.ljust(count, b"\x00")[::-1]
            else:
                raise ValueError(f"Unknown format specifier: {arg[0]}")
    
    def unpack(self, arg, *counts):
        arg = arg.replace(" ", "")
        result = []
        data = self
        pos = 0
        count_idx = 0
        endian = "little"
        current_count = None
        
        # Функция для парсинга count из аргумента или переданных значений
        def get_count():
            nonlocal count_idx, current_count
            if current_count is not None:
                count = current_count
                current_count = None
                return count
            elif count_idx < len(counts):
                count = counts[count_idx]
                count_idx += 1
                return count
            else:
                raise ValueError("Count not specified")
        
        i = 0
        while i < len(arg):
            ch = arg[i]
            
            if ch in "bl<>":
                endian = "big" if ch in "b>" else "little"
                i += 1
            elif ch.isdigit():
                # Собираем все цифры для числа
                num_start = i
                while i < len(arg) and arg[i].isdigit():
                    i += 1
                current_count = int(arg[num_start:i])
                continue
            elif ch == "s":
                i += 1
                count = get_count()
                if pos + count > len(data):
                    raise ValueError("Not enough data")
                
                chunk = data[pos:pos+count]
                pos += count
                
                if endian == "big":
                    chunk = chunk[::-1]
                
                # Убираем нулевые байты и декодируем
                text = chunk.rstrip(b"\x00").decode()
                result.append(text)
            
            elif ch == "n":
                i += 1
                count = get_count()
                if pos + count > len(data):
                    raise ValueError("Not enough data")
                
                chunk = data[pos:pos+count]
                pos += count
                
                if endian == "big":
                    chunk = chunk[::-1]
                
                result.append(chunk)
            
            elif ch == "o":
                i += 1
                count = get_count()
                if pos + count > len(data):
                    raise ValueError("Not enough data")
                
                chunk = data[pos:pos+count]
                pos += count
                
                # Булево значение: любой ненулевой байт = True
                result.append(any(chunk))
            
            elif ch in "iI":
                signed = ch == "I"
                i += 1
                count = get_count()
                if pos + count > len(data):
                    raise ValueError("Not enough data")
                
                chunk = data[pos:pos+count]
                pos += count
                
                # Преобразование байтов в число
                if endian == "little":
                    num = int.from_bytes(chunk, 'little')
                else:
                    num = int.from_bytes(chunk, 'big')
                
                # Преобразование signed если нужно
                if signed:
                    max_unsigned = 2**(count * 8)
                    if num >= 2**(count * 8 - 1):
                        num -= max_unsigned
                
                result.append(num)
            
            else:
                raise ValueError(f"Unknown format specifier: {ch}")
        
        return result

class gpack_func_list(list):
    def pack(self, arg, *counts):
        arg = arg.replace(" ", "")
        result = bytearray()
        data_idx = 0
        count_idx = 0
        endian = "little"
        current_count = None
        
        # Функция для парсинга count
        def get_count():
            nonlocal count_idx, current_count
            if current_count is not None:
                count = current_count
                current_count = None
                return count
            elif count_idx < len(counts):
                count = counts[count_idx]
                count_idx += 1
                return count
            else:
                raise ValueError("Count not specified")
        
        i = 0
        while i < len(arg):
            ch = arg[i]
            
            if ch in "bl<>":
                endian = "big" if ch in "b>" else "little"
                i += 1
            elif ch.isdigit():
                # Собираем все цифры для числа
                num_start = i
                while i < len(arg) and arg[i].isdigit():
                    i += 1
                current_count = int(arg[num_start:i])
                continue
            elif ch == "s":
                i += 1
                if data_idx >= len(self):
                    raise ValueError("Not enough data in list")
                
                count = get_count()
                value = str(self[data_idx])
                data_idx += 1
                
                packed = value.encode().ljust(count, b"\x00")
                if endian == "big":
                    packed = packed[::-1]
                result.extend(packed)
            
            elif ch == "n":
                i += 1
                if data_idx >= len(self):
                    raise ValueError("Not enough data in list")
                
                count = get_count()
                value = self[data_idx]
                if not isinstance(value, (bytes, bytearray)):
                    raise TypeError("Expected bytes for 'n' format")
                
                data_idx += 1
                packed = value.ljust(count, b"\x00")
                if endian == "big":
                    packed = packed[::-1]
                result.extend(packed)
            
            elif ch == "o":
                i += 1
                if data_idx >= len(self):
                    raise ValueError("Not enough data in list")
                
                count = get_count()
                value = bool(self[data_idx])
                data_idx += 1
                
                packed = b"\x01" if value else b"\x00"
                result.extend(packed.ljust(count, b"\x00"))
            
            elif ch in "iI":
                signed = ch == "I"
                i += 1
                if data_idx >= len(self):
                    raise ValueError("Not enough data in list")
                
                count = get_count()
                value = int(self[data_idx])
                data_idx += 1
                size = count
                
                # Проверка диапазона
                if signed:
                    max_val = 2**(size*8-1) - 1
                    min_val = -2**(size*8-1)
                else:
                    max_val = 2**(size*8) - 1
                    min_val = 0
                    
                if value < min_val or value > max_val:
                    raise ValueError(f"Value {value} out of range for {size} bytes")
                
                # Обработка отрицательных чисел
                if signed and value < 0:
                    value = (1 << (size * 8)) + value
                
                # Преобразование в байты
                packed = bytearray()
                for j in range(size):
                    if endian == "little":
                        packed.append((value >> (j * 8)) & 0xFF)
                    else:
                        packed.append((value >> ((size - 1 - j) * 8)) & 0xFF)
                
                result.extend(packed)
            
            else:
                raise ValueError(f"Unknown format specifier: {ch}")
        
        return bytes(result)

class gpack_func_bool:
    def __init__(self, value=False):
        self._value = bool(value)
    
    def pack(self, arg):
        arg = arg.replace(" ", "")
        endian = "little"
        
        i = 0
        while i < len(arg):
            ch = arg[i]
            
            if ch in "bl<>":
                endian = "big" if ch in "b>" else "little"
                i += 1
            elif ch.isdigit():
                # Пропускаем count для bool
                i += 1
            elif ch == "o":
                i += 1
                return b"\x01" if self._value else b"\x00"
            else:
                raise ValueError(f"Unknown format specifier: {ch}")
    
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
    globals()['is_alt']=False
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
                            # Преобразуем константу-список напрямую в gpack_func_list
                            return ast.Call(
                                func=ast.Name(id='gpack_func_list', ctx=ast.Load()),
                                args=[ast.Constant(value=node.value)],  # Или просто [node]
                                keywords=[]
                            )
                        return node
                    
                    def visit_List(self, node):
                        # Обрабатываем литералы списков [1, 2, 3]
                        self.generic_visit(node)  # Сначала обрабатываем элементы списка
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
                        # Трансформируем вызовы методов только для встроенных типов
                        if isinstance(node.func, ast.Attribute):
                            # Проверяем, является ли объект строкой, байтами или списком
                            # (или оберткой над ними)
                            node.func.value = self.visit(node.func.value)
                        
                        # Трансформируем все аргументы вызова
                        node.args = [self.visit(arg) for arg in node.args]
                        node.keywords = [self.visit(kw) for kw in node.keywords]
                        return node
                
                tree = Transformer().visit(tree)
                ast.fix_missing_locations(tree)
                code = self.original_compile(tree, filename, mode, flags, dont_inherit, optimize)
                self.transforming = False
                return code
                
            except Exception as e:
                self.transforming = False
                import traceback
                traceback.print_exc()
                return self.original_compile(source, filename, mode, flags, dont_inherit, optimize)

    # Убираем функцию _gpack_wrapper - она больше не нужна
    # Вместо этого мы напрямую используем gpack_func_* функции

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
        
        # Важно: делегируем все методы к встроенному bool
        def __eq__(self, other):
            return self._value == other
        
        def __str__(self):
            return str(self._value)

    # Создаем обернутые версии boolean значений
    TRUE = BoolWrapper(True)
    FALSE = BoolWrapper(False)

    # Заменяем compile
    builtins.compile = SimpleCompiler()
    globals()['gpack_func_str'] = gpack_func_str
    globals()['gpack_func_bytes'] = gpack_func_bytes
    globals()['gpack_func_list'] = gpack_func_list
    globals()['gpack_func_bool'] = gpack_func_bool
    globals()['TRUE'] = TRUE
    globals()['FALSE'] = FALSE
    builtins.gpack_func_str = gpack_func_str
    builtins.gpack_func_bytes = gpack_func_bytes
    builtins.gpack_func_list = gpack_func_list
    builtins.gpack_func_bool = gpack_func_bool
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
        try: 
            exec(code, {'__name__': '__main__', '__file__': sys.argv[0]})
        except Exception as e: 
            print(traceback.format_exc().split('\n')[0]+"\n"+"\n".join(traceback.format_exc().split('\n')[4:]))
        sys.exit(0)