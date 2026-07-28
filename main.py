import tkinter as tk

from gui import KeyPresserGUI


def main():
    root = tk.Tk()

    app = KeyPresserGUI(root)

    root.mainloop()


if __name__ == "__main__":
    main()