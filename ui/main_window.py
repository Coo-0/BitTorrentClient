import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

class BitTorrentUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BitTorrent Application")

        # Create UI elements
        self.torrent_listbox = tk.Listbox(root)
        self.progress_label = tk.Label(root, text="Download Progress:")
        self.progress_bar = ttk.Progressbar(root, length=200)
        self.add_button = tk.Button(root, text="Add Torrent", command=self.add_torrent)
        self.start_button = tk.Button(root, text="Start Download", command=self.start_download)
        self.stop_button = tk.Button(root, text="Stop Download", command=self.stop_download)

        # Grid layout
        self.torrent_listbox.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        self.progress_label.grid(row=1, column=0, padx=10)
        self.progress_bar.grid(row=1, column=1, padx=10)
        self.add_button.grid(row=2, column=0, padx=10, pady=10)
        self.start_button.grid(row=2, column=1, padx=10, pady=10)
        self.stop_button.grid(row=2, column=2, padx=10, pady=10)

    def add_torrent(self):
        file_path = filedialog.askopenfilename(title="Select Torrent File", filetypes=(("Torrent Files", "*.torrent"),))
        # Logic to add the selected torrent file to the application
        if file_path:
            self.torrent_listbox.insert(tk.END, file_path)

    def start_download(self):
        selected_index = self.torrent_listbox.curselection()
        if selected_index:
            selected_torrent = self.torrent_listbox.get(selected_index)
            # Logic to start the download process for the selected torrent
            messagebox.showinfo("Start Download", f"Downloading: {selected_torrent}")
            self.progress_bar.start(10)  # Start progress bar animation

    def stop_download(self):
        selected_index = self.torrent_listbox.curselection()
        if selected_index:
            selected_torrent = self.torrent_listbox.get(selected_index)
            # Logic to stop the download process for the selected torrent
            messagebox.showinfo("Stop Download", f"Stopped Download: {selected_torrent}")
            self.progress_bar.stop()  # Stop progress bar animation

# Create the main application window
root = tk.Tk()

# Initialize the BitTorrentUI
bittorrent_ui = BitTorrentUI(root)

# Start the main event loop
root.mainloop()
