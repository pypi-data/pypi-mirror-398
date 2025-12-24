# **An analogue of Struct for python and even better!**!

Installing:
```python
pip install gpack
```

Example usage:

```python
import gpack 
"1234".pack("bi",2)
```

GPack replaces the python compiler for improved and convenient operation.

> b - Big-Endian
> 
> l - Little-Endian
> 
> i - Int
> 
> I - Signed Int
> 
> s - String
> 
> o - Bool
> 
> n - Bytes
>
> \> - Big-endian
>
> \< - Little-endian

More usage:

```python
test_data = [123, -123, "aboba", b"aboba", 1234, True, False, 321]
import gpack
packed = test_data.pack("bilIsniooi", 1, 1, 5, 10, 5, 1, 1, 2)

unpacked = packed.unpack("bi lI s n i o o i", 1, 1, 5, 10, 5, 1, 1, 2)
print(unpacked)

[123, -123, 'aboba', b'aboba\x00\x00\x00\x00\x00', 1234, True, False, 321]
```

**You can use the spaces for ease of use**

**Format Specifiers with sizes**

Numbers after formats specify sizes in bytes:

```python
# Pack string (5 bytes) + int (4 bytes) + bool (1 byte)
packed = ["hello", 123, True].pack("s i o", 5, 4, 1)

# Unpack with same sizes
unpacked = packed.unpack("s i o", 5, 4, 1)
```
