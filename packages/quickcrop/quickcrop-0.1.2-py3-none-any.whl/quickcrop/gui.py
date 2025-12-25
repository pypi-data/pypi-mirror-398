from tkinter import Tk, ttk


class MainWindow(Tk):
    def setup(self):
        frm = ttk.Frame(self, padding=10)
        frm.grid()
        ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
        ttk.Button(frm, text="Quit", command=self.destroy).grid(column=1, row=0)

    def run(self):
        self.setup()
        self.mainloop()


def main():
    app = MainWindow()
    app.run()
