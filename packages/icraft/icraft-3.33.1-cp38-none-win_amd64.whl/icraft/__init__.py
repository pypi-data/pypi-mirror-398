import os
import sys

if sys.platform.startswith('win'):
    try:
        os.add_dll_directory(r'C:\Icraft\CLI\bin')
    except:
        ...
