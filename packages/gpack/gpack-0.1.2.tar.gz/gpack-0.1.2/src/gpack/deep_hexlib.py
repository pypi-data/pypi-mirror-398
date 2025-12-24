def to_signed_byte(n, fullbit=False):
    if fullbit:  # 16-битный режим
        if n < -32768 or n > 32767:
            raise ValueError(f"Number {n} out of range for 16-bit signed")
        if n < 0:
            return (65536 + n) & 0xFFFF  # 16-битный дополнительный код
        else:
            return n & 0xFFFF
    else:  # 8-битный режим
        if n < -128 or n > 127:
            raise ValueError(f"Number {n} out of range for 8-bit signed")
        if n < 0:
            return (256 + n) & 0xFF
        else:
            return n & 0xFF

def text2hex(text_string, bin=False):
    """
    Преобразует текстовую строку в hex-строку
    :param text_string: текстовая строка (например: "Hello", "A")
    :return: hex-строка (например: "48656c6c6f")
    """
    
    if not bin:
        if not isinstance(text_string, str):
            raise TypeError("Input must be string")
        
    # Преобразуем текст в байты (используем UTF-8 кодировку)
        binary_data = text_string.encode('utf-8')
    if bin:
        return text_string.hex()
    else:
        return binary_data.hex()

def hex2text(hex_input, bin=False, pad_if_needed=False):
    """
    Преобразует hex-строку или число в текстовую строку или байты
    :param hex_input: hex-строка (например: "48656c6c6f", "41 42 43") или число
    :param bin: Если True, возвращает байты вместо строки
    :param pad_if_needed: Если True, добавляет ведущий ноль для выравнивания длины
    :return: текстовая строка или байты
    """
    if isinstance(hex_input, int):
        # Если входное значение - число, преобразуем в hex
        hex_string = hex(hex_input)[2:]
    elif isinstance(hex_input, str):
        # Убираем пробелы и другие не-hex символы
        hex_string = ''.join(c for c in hex_input if c in '0123456789abcdefABCDEF')
    else:
        raise TypeError("Input must be string or integer")
    
    # Выравниваем длину при необходимости
    if pad_if_needed and len(hex_string) % 2 != 0:
        hex_string = '0' + hex_string
    
    if len(hex_string) % 2 != 0:
        raise ValueError("Hex string must have even length")
    
    # Преобразуем hex в байты
    binary_data = bytes.fromhex(hex_string)
    
    if bin:
        return binary_data
    else:
        return binary_data.decode('utf-8')

# Примеры использования
if __name__ == "__main__":
    # Пример 1: text2hex
    print("=== text2hex примеры ===")
    print(f"text2hex('A') = '{text2hex('A')}'")
    print(f"text2hex('Hello') = '{text2hex('Hello')}'")
    print(f"text2hex('ABC') = '{text2hex('ABC')}'")
    
    # Пример 2: hex2text
    print("\n=== hex2text примеры ===")
    print(f"hex2text('41') = '{hex2text('41')}'")
    print(f"hex2text('48656c6c6f') = '{hex2text('48656c6c6f')}'")
    print(f"hex2text('41 42 43') = '{hex2text('41 42 43')}'")
    print(f"hex2text('414243') = '{hex2text('414243')}'")
    
    # Пример 3: Взаимная конвертация
    print("\n=== Взаимная конвертация ===")
    original = "Test Data"
    hex_str = text2hex(original)
    restored = hex2text(hex_str)
    
    print(f"Оригинал: '{original}'")
    print(f"В hex: '{hex_str}'")
    print(f"Восстановлено: '{restored}'")
    print(f"Совпадает: {original == restored}")
    
    # Пример 4: Работа с русским текстом
    print("\n=== Работа с русским текстом ===")
    russian_text = "Привет"
    hex_russian = text2hex(russian_text)
    restored_russian = hex2text(hex_russian)
    
    print(f"Русский текст: '{russian_text}'")
    print(f"В hex: '{hex_russian}'")
    print(f"Восстановлено: '{restored_russian}'")
    
    # Пример 5: Специальные символы
    print("\n=== Специальные символы ===")
    special_text = "Hello! @#$%^&*()_+123"
    hex_special = text2hex(special_text)
    restored_special = hex2text(hex_special)
    
    print(f"Спецсимволы: '{special_text}'")
    print(f"В hex: '{hex_special}'")
    print(f"Восстановлено: '{restored_special}'")
    
    # Пример 6: Интерактивный режим
    print("\n=== Интерактивный режим ===")
    while True:
        choice = input("\nВыберите действие:\n1. Текст -> HEX\n2. HEX -> Текст\n3. Выход\n> ")
        
        if choice == '1':
            text_input = input("Введите текст: ")
            try:
                hex_result = text2hex(text_input)
                print(f"HEX результат: {hex_result}")
            except Exception as e:
                print(f"Ошибка: {e}")
                
        elif choice == '2':
            hex_input = input("Введите HEX: ")
            try:
                text_result = hex2text(hex_input)
                print(f"Текст результат: {text_result}")
            except Exception as e:
                print(f"Ошибка: {e}")
                
        elif choice == '3':
            print("Выход")
            break
            
        else:
            print("Неверный выбор")