import tkinter as tk

class TorrentList(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.torrents = []
        
        self.listbox = tk.Listbox(self, width=50)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        
        self.btn_remove = tk.Button(self, text="Remove", command=self.remove_torrent)
        self.btn_remove.pack(side=tk.BOTTOM, pady=10)
        
    def add_torrent(self, torrent_name):
        self.torrents.append(torrent_name)
        self.listbox.insert(tk.END, torrent_name)
        
    def remove_torrent(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            self.listbox.delete(selected_index)
            del self.torrents[selected_index[0]]

# Usage Example
if __name__ == "__main__":
    root = tk.Tk()
    root.title("BitTorrent Application")
    
    torrent_list = TorrentList(root)
    torrent_list.pack(fill=tk.BOTH, expand=True)
    
    torrent_list.add_torrent("Torrent 1")
    torrent_list.add_torrent("Torrent 2")
    torrent_list.add_torrent("Torrent 3")
    
    root.mainloop()
