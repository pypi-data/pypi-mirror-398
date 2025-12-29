from .test import *
from rich import print as printc

if __name__ == '__main__':
    printc(f'[gold1]{read_file("test.txt")}[/gold1]')
