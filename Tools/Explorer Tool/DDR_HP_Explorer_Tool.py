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
        
        # --- NEW REMOVE BUTTON ---
        self.btn_remove = ctk.CTkButton(self.sidebar, text="Remove Selected", fg_color="#e74c3c", command=self.remove_file)
        self.btn_remove.pack(pady=5, padx=20)
        
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
        if data.startswith(b'WII ') or data.startswith(b'WII\x00'): return ".bin"
        snippet = data[:128]
        if b"ZMS" in snippet: return ".zms"
        if b"ZMB" in snippet: return ".zmb"
        if b"ZAB" in snippet: return ".zab"
        if b"TEB" in snippet: return ".teb"
        if b"CAE_WII" in snippet: return ".cae"
        if b"ZAR" in snippet: return ".zar"
        if b"THP" in snippet: return ".thp"
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

    def load_file_from_path(self, path):
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
        if path: self.load_file_from_path(path)

    def on_select(self, event):
        selection = self.file_list.curselection()
        if not selection: return
        self.btn_replace.configure(state="normal")
        self.btn_extract_one.configure(state="normal")
        idx = selection[0]
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

    def remove_file(self):
        selection = self.file_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a file to remove first!")
            return
        
        idx = selection[0]
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove file {idx:03d}?\nThis cannot be undone until you reload.")
        if confirm:
            # Remove from memory
            del self.raw_data_cache[idx]
            del self.files_metadata[idx]
            
            # Refresh the listbox to update IDs
            self.file_list.delete(0, tk.END)
            for i, meta in enumerate(self.files_metadata):
                ext = meta[2].upper()
                self.file_list.insert(tk.END, f"{i:03d} | [MODIFIED/REMOVED] {ext} | {meta[1]} bytes")
            
            self.hex_view.delete("1.0", "end")
            self.status_bar.configure(text=f"File removed from memory. Total: {len(self.raw_data_cache)}")

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

    def remove_file(self):
        selection = self.file_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a file to remove!")
            return
        
        idx = selection[0]
        # Get the text before deleting so we know exactly what we are confirming
        file_text = self.file_list.get(idx)
        
        confirm = messagebox.askyesno("Confirm", f"Remove {file_text}?")
        if confirm:
            # 1. Remove from data caches
            del self.raw_data_cache[idx]
            del self.files_metadata[idx]
            
            # 2. Fully refresh the list to prevent tag shifting
            self.file_list.delete(0, tk.END)
            for i, meta in enumerate(self.files_metadata):
                ext = meta[2].upper()
                self.file_list.insert(tk.END, f"{i:03d} | [REMAINING] {ext} | {meta[1]} bytes")
            
            self.hex_view.delete("1.0", "end")
            self.status_bar.configure(text="File removed from memory.")

    def save_modified_bin(self):
        if not self.original_path: return
        save_path = filedialog.asksaveasfilename(defaultextension=".bin", initialfile="MODDED_" + os.path.basename(self.original_path))
        if not save_path: return

        new_count = len(self.raw_data_cache)
        
        with open(self.original_path, 'rb') as orig:
            # 1. Determine original data start
            orig.seek(16)
            orig_data_start = struct.unpack('>I', orig.read(4))[0]
            
            # 2. Calculate required space for the NEW pointer table
            # 16 bytes (Header) + (new_count * 8 bytes for pointers)
            required_table_space = 16 + (new_count * 8)
            
            # 3. Check if we need to shift the data start to avoid corruption
            # We add a 64-byte buffer per file for potential names
            new_data_start = orig_data_start
            if required_table_space + (new_count * 64) > orig_data_start:
                # Align to 0x800 for safety (standard for many Wii archives)
                new_data_start = (required_table_space + (new_count * 64) + 0x7FF) & ~0x7FF

            # Read the original magic/header 
            orig.seek(0)
            full_header_and_names = bytearray(orig.read(orig_data_start))

        with open(save_path, 'wb') as out_f:
            # 4. Update Header: Count (0x08) and Data Start (inside the table at 0x10)
            full_header_and_names[8:12] = struct.pack('>I', new_count)
            
            # 5. Write the (possibly expanded) Header block
            out_f.write(full_header_and_names)
            if len(full_header_and_names) < new_data_start:
                out_f.write(b'\x00' * (new_data_start - len(full_header_and_names)))

            # 6. Rebuild the Pointer Table starting at 0x10
            out_f.seek(16)
            current_pos = new_data_start
            data_payload = b""

            for data in self.raw_data_cache:
                sz = len(data)
                # Write new offset and size to the table
                out_f.write(struct.pack('>II', current_pos, sz))
                
                # Append data and maintain 32-byte alignment
                data_payload += data
                pad = (32 - (sz % 32)) % 32
                data_payload += b'\x00' * pad
                current_pos += (sz + pad)

            # 7. Write the data payload at the calculated start offset
            out_f.seek(new_data_start)
            out_f.write(data_payload)

        messagebox.showinfo("Success", ".bin saved!")
        self.load_file_from_path(save_path)

if __name__ == "__main__":
    app = DDRExplorerTool()
    app.mainloop()
