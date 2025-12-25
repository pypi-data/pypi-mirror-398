import tkinter as tk


class MyGUI:
    def __init__(self, window_name="My Window"):
        self.root = tk.Tk()
        self.root.title(window_name)
        self.widgets = {}


    def make_label(
        self,
        label_text="Hello World",
        label_number=0,
        fg="black",
        bg="white",
        label_width=30,
        label_height=2,
    ):
        label = tk.Label(
            self.root,
            text=label_text,
            font=("Arial", 15),
            width=label_width,
            height=label_height,
            fg=fg,
            bg=bg,
        )
        label.grid(row=label_number, column=0, pady=5)
        self.widgets[f"label_{label_number}"] = label
        return label


    def make_button(
        self,
        button_text="Click",
        button_number=0,
        button_command=None,
        fg="black",
        bg="lightgray",
        button_width=30,
        button_height=2,
    ):
        button = tk.Button(
            self.root,
            text=button_text,
            font=("Arial", 15),
            width=button_width,
            height=button_height,
            fg=fg,
            bg=bg,
            activebackground="blue",
            activeforeground="black",
            command=button_command,
        )
        button.grid(row=button_number, column=0, pady=5)
        self.widgets[f"button_{button_number}"] = button
        return button


    def make_entry(self, entry_number=0, entry_width=30, fg="black", bg="white"):
        entry = tk.Entry(self.root, font=("Arial", 15), width=entry_width, fg=fg, bg=bg)
        entry.grid(row=entry_number, column=0, pady=5)
        self.widgets[f"entry_{entry_number}"] = entry
        return entry


    def delete_widget(self, widget_number, widget_type):
        key = f"{widget_type}_{widget_number}"
        if key not in self.widgets:
            raise ValueError(f"No widget created with key {key}")
        self.widgets[key].destroy()
        del self.widgets[key]


    def delete_all(self):
        for widget in list(self.widgets.values()):
            widget.destroy()
        self.widgets.clear()


    def get_output(self, entry_number=0):
        key = f"entry_{entry_number}"
        if key not in self.widgets:
            raise ValueError(f"No entry with number {entry_number}")
        entry = self.widgets[key]
        if not isinstance(entry, tk.Entry):
            raise TypeError("This widget is not an Entry")
        return entry.get()


    def run(self):
        self.root.mainloop()
