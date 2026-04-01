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
        self.geometry("1000x600")

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
        # Flexible WII check: accepts 'WII ' or 'WII\x00'
        if data.startswith(b'WII ') or data.startswith(b'WII\x00'):
            return ".bin"
        
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
        
        with open(path, 'rb') as f:
            sig = f.read(4)
            # Support both common WII header variations
            if not (sig.startswith(b'WII ') or sig.startswith(b'WII\x00')):
                 messagebox.showerror("Error", f"Not a valid WII container. Header was: {sig.hex()}")
                 return
            
            self.original_path = path
            self.header_label.configure(text=f"Opened Archive: {os.path.basename(path)}")
            
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

        self.status_bar.configure(text=f"Loaded {os.path.basename(path)} | Total Files: {len(self.raw_data_cache)}")

    def on_select(self, event):
        if not self.file_list.curselection(): return
        self.btn_replace.configure(state="normal")
        self.btn_extract_one.configure(state="normal")
        idx = self.file_list.curselection()[0]
        self.hex_view.delete("1.0", "end")
        self.hex_view.insert("1.0", self.generate_hex_dump(self.raw_data_cache[idx]))

    def add_new_file(self):
        if not self.original_path: return
        path = filedialog.askopenfilename()
        if path:
            with open(path, 'rb') as f: data = f.read()
            idx = len(self.raw_data_cache)
            ext = self.detect_extension(data)
            self.raw_data_cache.append(bytearray(data))
            self.files_metadata.append([0, len(data), ext])
            self.file_list.insert(tk.END, f"{idx:03d} | [NEW] {ext.upper()} | {len(data)} bytes")

    def replace_file(self):
        selection = self.file_list.curselection()
        if not selection: return
        idx = selection[0]
        path = filedialog.askopenfilename()
        if path:
            with open(path, 'rb') as f: data = f.read()
            self.raw_data_cache[idx] = bytearray(data)
            self.files_metadata[idx][1] = len(data)
            self.files_metadata[idx][2] = self.detect_extension(data)
            self.file_list.delete(idx)
            self.file_list.insert(idx, f"{idx:03d} | [MODDED] {self.files_metadata[idx][2].upper()} | {len(data)} bytes")

    def extract_one(self):
        selection = self.file_list.curselection()
        if not selection: return
        idx = selection[0]
        ext = self.files_metadata[idx][2]
        path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"file_{idx:03d}{ext}")
        if path:
            with open(path, 'wb') as f: f.write(self.raw_data_cache[idx])

    def extract_all(self):
        if not self.raw_data_cache: return
        folder = filedialog.askdirectory()
        if folder:
            for i, data in enumerate(self.raw_data_cache):
                ext = self.files_metadata[i][2]
                with open(os.path.join(folder, f"{i:03d}{ext}"), 'wb') as f: f.write(data)
            messagebox.showinfo("Success", "Extracted!")

    def save_modified_bin(self):
        if not self.original_path: return
        save_path = filedialog.asksaveasfilename(defaultextension=".bin", initialfile="MODDED_" + os.path.basename(self.original_path))
        if not save_path: return

        with open(save_path, 'wb') as out_f:
            with open(self.original_path, 'rb') as orig:
                # 1. Get the original data start offset from the first table entry
                orig.seek(16)
                first_off = struct.unpack('>I', orig.read(4))[0]
                data_start_offset = first_off 
                
                # 2. Copy the entire header and filename table
                orig.seek(0)
                header_and_names = orig.read(data_start_offset)
            
            out_f.write(header_and_names)
            
            # 3. Update File Count at 0x08
            new_count = len(self.raw_data_cache)
            out_f.seek(8)
            out_f.write(struct.pack('>I', new_count))
            
            # 4. Rebuild the Table and Data with 32-byte alignment
            out_f.seek(16)
            current_pos = data_start_offset
            data_payload = b""

            for data in self.raw_data_cache:
                sz = len(data)
                # Write current offset and size to table
                out_f.write(struct.pack('>II', current_pos, sz))
                
                # Add data to payload
                data_payload += data
                
                # Align to 32-byte boundaries
                pad_len = (32 - (sz % 32)) % 32
                data_payload += b'\x00' * pad_len
                current_pos += (sz + pad_len)

            # 5. Write the actual data
            out_f.seek(data_start_offset)
            out_f.write(data_payload)

        # --- AUTO-RELOAD ---
        messagebox.showinfo("Success", ".bin saved! Reloading file...")
        self.load_file_from_path(save_path)

    def load_file_from_path(self, path):
        """Helper to handle the actual opening logic so it can be called by open_bin or save_modified_bin"""
        self.original_path = path
        self.header_label.configure(text=f"Opened: {os.path.basename(path)}")
        
        with open(path, 'rb') as f:
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
        
        self.status_bar.configure(text=f"Loaded {os.path.basename(path)} | Total Files: {len(self.raw_data_cache)}")

    def open_bin(self):
        path = filedialog.askopenfilename(filetypes=[("DDRHP2/5 .bin", "*.bin")])
        if path:
            self.load_file_from_path(path)
if __name__ == "__main__":
    app = DDRExplorerTool()
    app.mainloop()
