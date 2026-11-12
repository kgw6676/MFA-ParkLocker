import tkinter as tk
from controller import Controller
from ui import ParkingUI

def main():
    controller = Controller()
    root = tk.Tk()
    ParkingUI(root, controller)
    root.mainloop()

if __name__ == '__main__':
    main()
