import tkinter as tk

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("Settings")
        self.geometry("300x200")
        
        self.label_port = tk.Label(self, text="Port:")
        self.label_port.pack(pady=10)
        
        self.entry_port = tk.Entry(self)
        self.entry_port.pack()
        
        self.btn_save = tk.Button(self, text="Save", command=self.save_settings)
        self.btn_save.pack(pady=10)
        
    def save_settings(self):
        port = self.entry_port.get()
        # Save the settings or perform further actions
        print("Saving settings. Port:", port)
        self.destroy()

# Usage Example
if __name__ == "__main__":
    root = tk.Tk()
    
    def open_settings_dialog():
        settings_dialog = SettingsDialog(root)
        settings_dialog.grab_set()
    
    btn_settings = tk.Button(root, text="Open Settings", command=open_settings_dialog)
    btn_settings.pack(pady=20)
    
    root.mainloop()
