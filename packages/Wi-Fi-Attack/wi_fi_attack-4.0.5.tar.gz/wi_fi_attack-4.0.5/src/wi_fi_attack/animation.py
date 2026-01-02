import time
import random
from pyfiglet import Figlet
from termcolor import colored

class Animation:
    def animated_banner(text: str,author: str, frames: int = 15, delay: float = 0.08):
        f = Figlet(font="big")
        base = f.renderText(text)
        lines = base.splitlines()
        width = max(len(l) for l in lines)
        fire_colors = ["red", "yellow", "magenta"]

        for i in range(frames):
            pad = " " * (i % (width // 4 + 1))
            
            frame_lines = []
            for line in lines:
                color = random.choice(fire_colors)
                frame_lines.append(colored(pad + line, color))
            
            print("\n".join(frame_lines))
            time.sleep(delay)

            if i != frames - 1:
                print(f"\033[{len(lines)}F", end="")
        print(colored(author, "blue"),'\n')