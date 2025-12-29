from .test import *
from rich import print as printc


def main():
    printc(f'[gold1]{read_file("test.txt")}[/gold1]')


if __name__ == '__main__':
    main()
