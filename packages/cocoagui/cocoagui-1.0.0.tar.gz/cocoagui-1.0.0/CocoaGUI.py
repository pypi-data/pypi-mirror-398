import tkinter as tk
from tkinter import messagebox

class Window:
    """Main window class for the GUI"""
    def __init__(self, title="GUI Window", width=400, height=300):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        
    def run(self):
        """Start the GUI event loop"""
        self.root.mainloop()
    
    def close(self):
        """Close the window"""
        self.root.destroy()


class Button:
    """Simple button widget"""
    def __init__(self, parent, text="Button", command=None, x=10, y=10):
        self.widget = tk.Button(parent.root, text=text, command=command)
        self.widget.place(x=x, y=y)
    
    def move(self, x, y):
        """Move the button to a new position"""
        self.widget.place(x=x, y=y)


class Label:
    """Simple label widget for displaying text"""
    def __init__(self, parent, text="Label", x=10, y=10, size=12):
        self.widget = tk.Label(parent.root, text=text, font=("Arial", size))
        self.widget.place(x=x, y=y)
    
    def set(self, text):
        """Update the label text"""
        self.widget.config(text=text)
    
    def move(self, x, y):
        """Move the label to a new position"""
        self.widget.place(x=x, y=y)


class Input:
    """Simple text input box"""
    def __init__(self, parent, x=10, y=10, width=200, default=""):
        self.widget = tk.Entry(parent.root, width=width//8)
        self.widget.place(x=x, y=y)
        if default:
            self.widget.insert(0, default)
    
    def get(self):
        """Get the current text in the box"""
        return self.widget.get()
    
    def set(self, text):
        """Set the text in the box"""
        self.widget.delete(0, tk.END)
        self.widget.insert(0, text)
    
    def clear(self):
        """Clear the input box"""
        self.widget.delete(0, tk.END)


class TextArea:
    """Multi-line text area"""
    def __init__(self, parent, x=10, y=10, width=300, height=150):
        self.widget = tk.Text(parent.root, width=width//8, height=height//20)
        self.widget.place(x=x, y=y)
    
    def get(self):
        """Get all text from the area"""
        return self.widget.get("1.0", tk.END)
    
    def set(self, text):
        """Set the text in the area"""
        self.widget.delete("1.0", tk.END)
        self.widget.insert("1.0", text)
    
    def clear(self):
        """Clear the text area"""
        self.widget.delete("1.0", tk.END)


class CheckBox:
    """Simple checkbox widget"""
    def __init__(self, parent, text="Checkbox", x=10, y=10, checked=False):
        self.var = tk.BooleanVar(value=checked)
        self.widget = tk.Checkbutton(parent.root, text=text, variable=self.var)
        self.widget.place(x=x, y=y)
    
    def checked(self):
        """Check if the checkbox is checked"""
        return self.var.get()
    
    def check(self):
        """Check the checkbox"""
        self.var.set(True)
    
    def uncheck(self):
        """Uncheck the checkbox"""
        self.var.set(False)


# Helper functions
def alert(message, title="Alert"):
    """Show an alert dialog"""
    messagebox.showinfo(title, message)

def confirm(message, title="Confirm"):
    """Show a confirmation dialog, returns True/False"""
    return messagebox.askyesno(title, message)


# Example usage
if __name__ == "__main__":
    # Create window
    win = Window("My GUI App", 500, 400)
    
    # Add widgets - super simple!
    Label(win, "Enter your name:", x=20, y=20, size=14)
    
    name_input = Input(win, x=20, y=50, width=300)
    
    result_label = Label(win, "", x=20, y=120, size=12)
    
    def on_submit():
        name = name_input.get()
        if name:
            result_label.set(f"Hello, {name}!")
            alert(f"Welcome, {name}!")
        else:
            alert("Please enter a name!")
    
    Button(win, "Submit", command=on_submit, x=20, y=85)
    
    checkbox = CheckBox(win, "Remember me", x=20, y=160)
    
    def on_check_status():
        if checkbox.checked():
            result_label.set("Checkbox is checked!")
        else:
            result_label.set("Checkbox is not checked!")
    
    Button(win, "Check Status", command=on_check_status, x=20, y=190)
    
    textarea = TextArea(win, x=20, y=240, width=450, height=100)
    textarea.set("This is a multi-line text area...\nYou can type multiple lines here!")
    
    # Run the application
    win.run()