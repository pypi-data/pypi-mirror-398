
import pyfiglet
import random
import os
import time
from termcolor import colored

def clean():
     os.system("clear" if os.name == "posix" else "cls")
def create_ascii_text():
    font_list = pyfiglet.FigletFont.getFonts()
    color_list = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    default_text = "Stealth Chopper"
    clean()
    font_choice = random.choice(font_list)
    color_choice = random.choice(color_list)
    ascii_art = pyfiglet.figlet_format(default_text, font=font_choice)
    for line in ascii_art.splitlines():
        print(colored(line, color_choice))
        time.sleep(0.05)
    author_text = "Author: @cyb2rS2c"
    for char in author_text:
        print(colored(char, 'red'), end='', flush=True)
        time.sleep(0.05)
    print("\n")
