from tkinter import Tk, Menu


def start(ar):
    root = Tk()
    root.geometry("600x600")
    menubar = Menu(root)
    menud = {}
    for menu, submenu, cmd in ar:
        if menu not in menud:
            menud[menu] = Menu(menubar, tearoff=0)
        menud[menu].add_command(label=submenu, command=cmd)
    for menu in menud:
        menubar.add_cascade(label=menu, menu=menud[menu])
    root.config(menu=menubar)
    root.mainloop()
