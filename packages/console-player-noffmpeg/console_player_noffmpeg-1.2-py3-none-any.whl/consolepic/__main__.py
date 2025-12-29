import consoleplay as cp,sys
from colorama import Fore
__version__=cp.version
def main():
    if len(sys.argv)>1:
        print(cp.pic2terminal(sys.argv[1]),try_rgba=True)
    else:
        print(f"""╭───────────────────╮  ConsolePlay {cp.version}
│ {Fore.BLUE}│╲{Fore.RESET}                │  By: SystemFileB和其他贡献者们
│ {Fore.BLUE}│  ╲{Fore.RESET}              │  赞助: https://afdian.com/a/systemfileb
│ {Fore.BLUE}│    ╲{Fore.RESET}            │  Github: https://github.com/SystemFileB/console-player
│ {Fore.BLUE}│    ╱{Fore.RESET}            │  用法: python -m consolepic <图片路径>
│ {Fore.BLUE}│  ╱{Fore.RESET}              │
│ {Fore.BLUE}│╱      ───────{Fore.RESET}   │
╰───────────────────╯""")
        sys.exit(1)
if __name__=="__main__":
    main()