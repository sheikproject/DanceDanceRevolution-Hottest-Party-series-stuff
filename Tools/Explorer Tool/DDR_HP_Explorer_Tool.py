import os, struct
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DDRExplorerTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DDR Hottest Party Explorer Tool")
        self.geometry("1200x800")

        self.original_path = ""
        self.files_metadata = [] 
        self.raw_data_cache = [] 

        # DRAGGABLE PANELS
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#1a1a1a", sashwidth=4, sashrelief=tk.RAISED)
        self.paned_window.pack(fill="both", expand=True)

        # LEFT SIDEBAR
        self.sidebar = ctk.CTkFrame(self.paned_window, corner_radius=0)
        self.paned_window.add(self.sidebar, width=320)
        
        ctk.CTkButton(self.sidebar, text="Open .bin", command=self.open_bin).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Add New File", fg_color="#f39c12", command=self.add_new_file).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="Extract All", fg_color="#28a745", command=self.extract_all).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="Save Modified .bin", fg_color="#dc3545", command=self.save_modified_bin).pack(pady=20, padx=20)

        self.file_list = tk.Listbox(self.sidebar, bg="#1a1a1a", fg="#d1d1d1", selectbackground="#3b5998", font=("Consolas", 11), borderwidth=0, highlightthickness=0)
        self.file_list.pack(expand=True, fill="both", padx=10, pady=10)
        self.file_list.bind("<<ListboxSelect>>", self.on_select)

        # RIGHT MAIN PANEL
        self.main_content = ctk.CTkFrame(self.paned_window, corner_radius=0)
        self.paned_window.add(self.main_content)

        self.header_label = ctk.CTkLabel(self.main_content, text="No File Opened", font=("Arial", 16, "bold"), text_color="#5dade2")
        self.header_label.pack(pady=(15, 5))

        self.btn_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=5)
        
        self.btn_replace = ctk.CTkButton(self.btn_frame, text="Replace Selected", width=140, command=self.replace_file, state="disabled")
        self.btn_replace.pack(side="left", padx=10)

        self.btn_extract_one = ctk.CTkButton(self.btn_frame, text="Extract Selected", width=140, command=self.extract_one, state="disabled")
        self.btn_extract_one.pack(side="left", padx=10)

        self.hex_view = ctk.CTkTextbox(self.main_content, font=("Consolas", 13), wrap="none")
        self.hex_view.pack(expand=True, fill="both", padx=10, pady=10)

        self.status_bar = ctk.CTkLabel(self, text="Ready", anchor="w", padx=20, fg_color="#1a1a1a")
        self.status_bar.pack(side="bottom", fill="x")

    def detect_extension(self, data):
        snippet = data[:128]
        if b"ZMS" in snippet: return ".zms"
        if b"ZMB" in snippet: return ".zmb"
        if b"ZAB" in snippet: return ".zab"
        if b"TEB" in snippet: return ".teb"
        if b"CAE_WII" in snippet: return ".cae"
        if b"ZLB" in snippet: return ".zlb"
        if b"\x00\x20\xAF\x30" in snippet: return ".tpl"
        return ".bin"

    def generate_hex_dump(self, data):
        lines = []
        limit = min(len(data), 0x2000) 
        for i in range(0, limit, 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02X}" for b in chunk).ljust(47)
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            lines.append(f"{i:08X}:  {hex_part}  |{ascii_part}|")
        return "\n".join(lines)

    def open_bin(self):
        path = filedialog.askopenfilename(filetypes=[("DDRHP2/5 .bin", "*.bin")])
        if not path: return
        self.original_path = path
        self.header_label.configure(text=f"Opened Archive: {os.path.basename(path)}")
        self.refresh_ui_list()

    def refresh_ui_list(self):
        """Clears and re-populates the sidebar list based on current memory data."""
        with open(self.original_path, 'rb') as f:
            f.seek(8)
            count = struct.unpack('>I', f.read(4))[0]
            f.seek(16)
            self.file_list.delete(0, tk.END)
            self.files_metadata.clear()
            self.raw_data_cache.clear()
            
            for i in range(count):
                off, sz = struct.unpack('>II', f.read(8))
                old_pos = f.tell()
                f.seek(off)
                data = f.read(sz)
                ext = self.detect_extension(data)
                self.files_metadata.append([off, sz, ext])
                self.raw_data_cache.append(bytearray(data))
                self.file_list.insert(tk.END, f"{i:03d} | {ext.upper()} | {sz} bytes")
                f.seek(old_pos)
        self.status_bar.configure(text=f"Loaded {os.path.basename(self.original_path)} | Total Files: {len(self.raw_data_cache)}")

    def on_select(self, event):
        if not self.file_list.curselection(): return
        self.btn_replace.configure(state="normal")
        self.btn_extract_one.configure(state="normal")
        idx = self.file_list.curselection()[0]
        self.hex_view.delete("1.0", "end")
        self.hex_view.insert("1.0", self.generate_hex_dump(self.raw_data_cache[idx]))

    def add_new_file(self):
        if not self.original_path:
            messagebox.showwarning("Warning", "Open a .bin file first!")
            return
        path = filedialog.askopenfilename(title="Select a file to ADD to the .bin")
        if path:
            with open(path, 'rb') as f:
                new_data = f.read()
            idx = len(self.raw_data_cache)
            ext = self.detect_extension(new_data)
            self.raw_data_cache.append(bytearray(new_data))
            self.files_metadata.append([0, len(new_data), ext])
            self.file_list.insert(tk.END, f"{idx:03d} | [NEW] {ext.upper()} | {len(new_data)} bytes")
            self.status_bar.configure(text=f"Added 1 file | Total Files: {len(self.raw_data_cache)}")

    def replace_file(self):
        idx = self.file_list.curselection()[0]
        path = filedialog.askopenfilename()
        if path:
            with open(path, 'rb') as f: new_data = f.read()
            self.raw_data_cache[idx] = bytearray(new_data)
            self.files_metadata[idx][1] = len(new_data)
            self.files_metadata[idx][2] = self.detect_extension(new_data)
            self.file_list.delete(idx)
            ext = self.files_metadata[idx][2].upper()
            self.file_list.insert(idx, f"{idx:03d} | [MODDED {ext}] | {len(new_data)} bytes")
            self.on_select(None)

    def extract_one(self):
        idx = self.file_list.curselection()[0]
        ext = self.files_metadata[idx][2]
        path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"file_{idx:03d}{ext}")
        if path:
            with open(path, 'wb') as f: f.write(self.raw_data_cache[idx])

    def extract_all(self):
        folder = filedialog.askdirectory()
        if folder:
            for i, data in enumerate(self.raw_data_cache):
                ext = self.files_metadata[i][2]
                with open(os.path.join(folder, f"{i:03d}{ext}"), 'wb') as f: f.write(data)
            messagebox.showinfo("Success", "All files extracted!")

    def save_modified_bin(self):
        if not self.original_path: return
        save_path = filedialog.asksaveasfilename(defaultextension=".bin", initialfile="MODDED_" + os.path.basename(self.original_path))
        if not save_path: return

        with open(save_path, 'wb') as out_f:
            with open(self.original_path, 'rb') as orig:
                out_f.write(orig.read(8))
            out_f.write(struct.pack('>I', len(self.raw_data_cache)))
            out_f.write(b'\x00' * 4)

            table_start = 16
            table_size = len(self.raw_data_cache) * 8
            data_start_offset = 128 
            if table_start + table_size > data_start_offset:
                data_start_offset = (table_start + table_size + 0x3F) & ~0x3F

            current_offset = data_start_offset
            table_bytes = b""
            file_data_bytes = b""
            
            for data in self.raw_data_cache:
                table_bytes += struct.pack('>II', current_offset, len(data))
                file_data_bytes += data
                pad = (4 - (len(data) % 4)) % 4
                file_data_bytes += b'\x00' * pad
                current_offset += len(data) + pad
            
            out_f.write(table_bytes)
            padding_needed = data_start_offset - out_f.tell()
            if padding_needed > 0:
                out_f.write(b'\x00' * padding_needed)
            out_f.write(file_data_bytes)

        # Update Tool state to the new file and clear [NEW] tags
        self.original_path = save_path
        self.header_label.configure(text=f"Opened Archive: {os.path.basename(save_path)}")
        
        # Clear the listbox and re-show the actual saved data
        self.file_list.delete(0, tk.END)
        for i, meta in enumerate(self.files_metadata):
            ext = meta[2].upper()
            size = meta[1]
            self.file_list.insert(tk.END, f"{i:03d} | {ext} | {size} bytes")
        
        messagebox.showinfo("Success", ".bin Saved!")

if __name__ == "__main__":
    app = DDRExplorerTool()
    app.mainloop()
