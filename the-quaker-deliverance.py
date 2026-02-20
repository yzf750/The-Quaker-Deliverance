import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
import threading
import time
import shutil
import fnmatch
from PIL import Image, ImageTk
import random
import re
import platform

try:
    from PIL import Image, ImageTk
except ImportError:
    import tkinter as tk
    from tkinter import messagebox
    import sys
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Dependency Missing", 
        "The 'Pillow' library is required for images.\n\n"
        "Please install it using:\n"
        "pip install Pillow\n\n"
        "On Linux (Ubuntu/Debian):\n"
        "sudo apt install python3-pil.imagetk")
    sys.exit(1)

CONFIG_FILE = "quake_launcher_config.json"

class QuakeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Quake Launcher")
        
        # 1. Load Data
        self.config = self.load_config()
        self._after_id = None
        self.active_theme_name = self.config.get("theme_name", "Quake Dark")
       
        self.themes = {
            "Quake Dark": {"bg": "#111111", "fg": "#ffffff", "select": "#880000"},
            "Classic Brown": {"bg": "#332211", "fg": "#ffcc00", "select": "#553311"},
            "Matrix": {"bg": "#000000", "fg": "#00ff00", "select": "#004400"},
            "High Contrast": {"bg": "#ffffff", "fg": "#000000", "select": "#0000ff"}
        }

        self.current_theme = self.themes.get(self.active_theme_name, self.themes["Quake Dark"])

        # 2. Initialize Variables
        self.font_size = self.config.get("font_size", 12)
        self.ui_font = ("Arial", self.font_size)
        self.exe_path = tk.StringVar(value=self.config.get("exe", ""))
        self.base_dir = tk.StringVar(value=self.config.get("base_dir", ""))
        self.skill_level = tk.StringVar(value=self.config.get("skill", "1"))
        self.mod_search_var = tk.StringVar()
        self.map_search_var = tk.StringVar()
        # self.extra_args = tk.StringVar(value=self.config.get("extra_args", ""))
        self.mod_extra_args = self.config.get("mod_extra_args", {})
        self.extra_args = tk.StringVar()
       
        self.all_mods = []
        self.all_maps = []
        self.map_titles = {}

        # Added missing original_maps to prevent is_blacklisted from crashing
        self.original_maps = ["base", "start", "exit"] 
        self.blacklist_from_config = self.config.get("blacklist", ["b_*", "*_h_", "wooden-*"])
        self.stop_screenshot_watch = threading.Event()
        self.current_img_path = None

        # 3. Setup UI
        self.setup_ui()

        self.root.after(10, self.apply_theme_to_ui)

        # 4. Context Menus
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete Screenshot", command=self.delete_current_screenshot)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open Previews Folder", command=self.open_previews_folder)

        self.mod_context_menu = tk.Menu(self.root, tearoff=0)
        self.mod_context_menu.add_command(label="Force Maps Rescan  (Clear Cache)", command=self.force_rescan_mod)
        self.mod_context_menu.add_command(label="Refresh Mods List", command=self.load_mods)

        # Add this near your other .trace_add calls in __init__
        self.skill_level.trace_add("write", lambda *args: self.on_map_select(None))

        # 5. Bindings
        self.img_label.bind("<Button-3>", self.show_context_menu)
        self.img_label.bind("<Button-2>", self.show_context_menu)
        self.mod_listbox.bind("<Button-3>", self.show_mod_context_menu)
        self.mod_listbox.bind("<Button-2>", self.show_mod_context_menu)
        
        # Search listeners
        self.mod_search_var.trace_add("write", lambda *args: self.filter_mods())
        self.map_search_var.trace_add("write", lambda *args: self.filter_maps())

        # 6. Finalize
        self.apply_theme_to_ui()
        if self.base_dir.get():
            self.load_mods()
            self.root.after(200, self.restore_last_selection)
        
        self.root.geometry(self.config.get("window_size", "1200x800"))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.restore_sashes)
        
        self.extra_args.trace_add("write", self.save_mod_cli)

    def setup_ui(self):
        # Config Frame
        path_frame = tk.LabelFrame(self.root, text="Configuration", padx=10, pady=10)
        path_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(path_frame, text="Engine:").grid(row=0, column=0, sticky="w")
        tk.Entry(path_frame, textvariable=self.exe_path).grid(row=0, column=1, padx=5, sticky="ew")
        tk.Button(path_frame, text="Browse", command=lambda: self.browse_file("exe")).grid(row=0, column=2)

        tk.Label(path_frame, text="Quake Root:").grid(row=1, column=0, sticky="w")
        tk.Entry(path_frame, textvariable=self.base_dir).grid(row=1, column=1, padx=5, sticky="ew")
        tk.Button(path_frame, text="Browse", command=self.browse_base).grid(row=1, column=2)
        
        self.settings_btn = tk.Button(path_frame, text="⚙ Settings", command=self.open_settings)
        self.settings_btn.grid(row=0, column=3, rowspan=2, padx=10, sticky="ns")
        path_frame.columnconfigure(1, weight=1)

        # Main Paned Window
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6)
        self.paned.pack(fill="both", expand=True, padx=10, pady=5)

        # Mod Column
        mod_col = tk.Frame(self.paned)
        tk.Label(mod_col, text="Mods", font=("Arial", 12, "bold")).pack()
        tk.Entry(mod_col, textvariable=self.mod_search_var).pack(fill="x")
        self.mod_listbox = tk.Listbox(mod_col, exportselection=False)
        self.mod_listbox.pack(fill="both", expand=True, pady=5)
        self.mod_listbox.bind('<<ListboxSelect>>', self.on_mod_select)

        # Map Column
        map_col = tk.Frame(self.paned)
        tk.Label(map_col, text="Maps", font=("Arial", 12, "bold")).pack()
        tk.Entry(map_col, textvariable=self.map_search_var).pack(fill="x")
        self.map_listbox = tk.Listbox(map_col, exportselection=False)
        self.map_listbox.pack(fill="both", expand=True, pady=5)
        self.map_listbox.bind('<<ListboxSelect>>', self.on_map_select)

        # Preview Column
        preview_col = tk.Frame(self.paned)
        self.preview_title = tk.Label(preview_col, text="Preview", font=("Arial", 12, "bold"), wraplength=300)
        self.preview_title.pack()
        
        self.img_container = tk.Frame(preview_col, bg="black", relief="ridge", bd=1)
        self.img_container.pack(pady=10, fill="both", expand=True)
        self.img_container.bind("<Configure>", self.on_container_resize)
        
        self.img_label = tk.Label(self.img_container, text="No Preview", bg="black", fg="#00ff00")
        self.img_label.pack(fill="both", expand=True)

        self.map_info_label = tk.Label(preview_col, text="Monsters: -- | Secrets: --", font=("Arial", 10, "bold"))
        self.map_info_label.pack(pady=5)

        ctrl_frame = tk.Frame(preview_col)
        ctrl_frame.pack(fill="x")

        tk.Label(ctrl_frame, text="Skill:").pack(side="left", padx=5)
        tk.OptionMenu(ctrl_frame, self.skill_level, "0", "1", "2", "3").pack(side="left")

        tk.Label(ctrl_frame, text="Extra CLI:").pack(side="left", padx=(15,5))
        tk.Entry(ctrl_frame, textvariable=self.extra_args, width=30).pack(side="left", fill="x", expand=True)

        self.paned.add(mod_col, width=250)
        self.paned.add(map_col, width=250)
        self.paned.add(preview_col, width=500)

        self.launch_btn = tk.Button(self.root, text="LAUNCH", bg="#800", fg="white", font=("Impact", 24), command=self.launch_game)
        self.launch_btn.pack(fill="x", padx=10, pady=10)

    def apply_theme_to_ui(self):
        self.root.configure(bg="white")
        # Recursively update, but only for the main app window
        self.update_widget_colors(self.root, self.current_theme)
            

    def update_widget_colors(self, parent, colors):
        for child in parent.winfo_children():
            # 1. Skip the settings popup
            if isinstance(child, tk.Toplevel):
                continue
            
            # 2. Skip internal Menu widgets (this is what causes the flickering)
            if isinstance(child, tk.Menu):
                continue

            try:
                if isinstance(child, tk.Listbox):
                    child.configure(
                        bg=colors["bg"], 
                        fg=colors["fg"], 
                        selectbackground=colors["select"],
                        font=self.ui_font
                    )
            
                elif isinstance(child, (tk.Frame, tk.LabelFrame, tk.PanedWindow)):
                    child.configure(bg="white")
                    if isinstance(child, tk.LabelFrame):
                        child.configure(fg="black")

                elif isinstance(child, tk.Label):
                    if child == self.img_label:
                        child.configure(bg="black", fg="#00ff00")
                    else:
                        child.configure(bg="white", fg="black")

                # Recursion
                self.update_widget_colors(child, colors)
            except Exception:
                pass

    def on_container_resize(self, event):
        if self.current_img_path:
            # Cancel any pending "High Quality" render
            if self._after_id: 
                self.root.after_cancel(self._after_id)
        
            # Perform an instant low-quality resize so it tracks your mouse smoothly
            self.render_image(self.current_img_path, fast=True)
        
            # Schedule the high-quality render for 300ms after you STOP resizing
            self._after_id = self.root.after(300, lambda: self.render_image(self.current_img_path, fast=False))

    def render_image(self, full_path, fast=False):

        # 0. Safety: If path is empty or file missing, exit early
        if not full_path or not os.path.exists(full_path):
            return

        try:
            # 1. Get container dimensions
            cont_w = self.img_container.winfo_width() - 10
            cont_h = self.img_container.winfo_height() - 10
            if cont_w < 50 or cont_h < 50: return
        
            # 2. Use cached image if available to save Disk I/O
            if hasattr(self, 'cached_image') and self.cached_image_path == full_path:
                img = self.cached_image
            else:
                img = Image.open(full_path)
                self.cached_image = img  # Store in memory
                self.cached_image_path = full_path

            # 3. Choose resampling quality
            # NEAREST is instant; LANCZOS is high quality but slow
            resample_type = Image.Resampling.NEAREST if fast else Image.Resampling.LANCZOS
        
            # 4. Resize and display
            img_copy = img.copy()
            img_copy.thumbnail((cont_w, cont_h), resample_type)
            photo = ImageTk.PhotoImage(img_copy)
        
            self.img_label.config(image=photo, text="")
            self.img_label.image = photo # Keep reference
        except Exception as e:
            print(f"Render error: {e}")

    def load_mods(self):
        self.mod_listbox.delete(0, tk.END)
        base = self.base_dir.get()
        if not os.path.exists(base): return
        
        found = []
        for d in os.listdir(base):
            if os.path.isdir(os.path.join(base, d)):
                found.append(d)
        self.all_mods = sorted(found)
        self.filter_mods()

    def filter_mods(self):
        query = self.mod_search_var.get().lower()
        self.mod_listbox.delete(0, tk.END)
        for m in self.all_mods:
            if query in m.lower(): self.mod_listbox.insert(tk.END, m)

    def filter_maps(self):
        query = self.map_search_var.get().lower()
        self.map_listbox.delete(0, tk.END)
        for m in self.all_maps:
            if query in m.lower(): self.map_listbox.insert(tk.END, m)

    def on_mod_select(self, event):
        sel = self.mod_listbox.curselection()
        if not sel: return
        m_name = self.mod_listbox.get(sel[0])
        m_path = os.path.join(self.base_dir.get(), m_name)
        
        # Clear the image cache so we don't show the old mod's image
        self.cached_image = None
        self.cached_image_path = None
        
        
        
        # self.preview_title.config(text=f"Mod: {m_name}")
        self.preview_title.config(text=f"Mod: {m_name}")
        self.map_info_label.config(text="Monsters: -- | Secrets: --")
        
        cache_path = os.path.join(m_path, "previews", "map_cache.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f: self.all_maps = json.load(f)
            self.filter_maps()
        else:
            self.start_new_scan(m_name, m_path)
        self.update_mod_image(m_name, m_path)
        self.extra_args.set(self.mod_extra_args.get(m_name, ""))

    def start_new_scan(self, mod_name, mod_path):
        self.map_listbox.delete(0, tk.END)
        self.map_listbox.insert(tk.END, "Scanning...")
        threading.Thread(target=self.scan_mod_files_worker, args=(mod_name, mod_path), daemon=True).start()

    def is_blacklisted(self, filename, mod_name):
        fn = filename.lower()
        if mod_name == "id1" and fn.replace('.bsp', '') in self.original_maps:
            return True
        # If it starts with b_, it's a brush model (junk)
        if fn.startswith('b_'):
            return True
        return False

    def scan_mod_files_worker(self, mod_name, mod_path):
        found_maps = set()
        if mod_name == "id1": 
            found_maps.add("(Default)")
        
        # 1. Search the Mod Root (Loose files)
        try:
            for f in os.listdir(mod_path):
                if f.lower().endswith('.bsp'):
                    full_path = os.path.join(mod_path, f)
                    with open(full_path, 'rb') as bsp_file:
                        if self.is_valid_bsp(bsp_file):
                            found_maps.add(f.lower().replace('.bsp', ''))
        except Exception: pass

        # 2. Deep Search the /maps subfolder (Recursion)
        maps_subdir = os.path.join(mod_path, "maps")
        if os.path.exists(maps_subdir):
            for root, dirs, files in os.walk(maps_subdir):
                for f in files:
                    if f.lower().endswith('.bsp'):
                        if not self.is_blacklisted(f, mod_name):
                            full_path = os.path.join(root, f)
                            try:
                                with open(full_path, 'rb') as bsp_file:
                                    if self.is_valid_bsp(bsp_file):
                                        # Only add the filename, not the path
                                        found_maps.add(f.lower().replace('.bsp', ''))
                            except Exception: continue
        
        # 3. PAK Search
        if os.path.exists(mod_path):
            for f in os.listdir(mod_path):
                if f.lower().endswith('.pak'):
                    pak_maps = self.get_maps_from_pak(os.path.join(mod_path, f))
                    for m in pak_maps:
                        if not self.is_blacklisted(m + ".bsp", mod_name):
                            found_maps.add(m)

        self.all_maps = sorted(list(found_maps))
        if not self.all_maps: self.all_maps = ["(Default)"]
        
        # Cache results
        p_dir = os.path.join(mod_path, "previews")
        os.makedirs(p_dir, exist_ok=True)
        with open(os.path.join(p_dir, "map_cache.json"), 'w') as f:
            json.dump(self.all_maps, f)
        
        self.root.after(0, self.filter_maps)

    # ... [Rest of your helper methods like get_maps_from_pak, launch_game, etc. remain the same] ...

    def is_valid_map(self, f, base_offset=0):
        try:
            import struct
            f.seek(base_offset)
            header = f.read(160)
            ent_off = struct.unpack('<I', header[4:8])[0]
            ent_size = struct.unpack('<I', header[8:12])[0]
            f.seek(base_offset + ent_off)
            chunk = f.read(ent_size).decode('ascii', errors='ignore')
            return any(x in chunk for x in ['info_player_start', 'info_player_deathmatch'])
        except: return False

    def get_maps_from_pak(self, pak_path):
        maps = []
        try:
            import struct
            with open(pak_path, 'rb') as f:
                header = f.read(12)
                if header[:4] != b'PACK': return []
                off, sz = struct.unpack('<II', header[4:12])
                f.seek(off)
                for _ in range(sz // 64):
                    ent = f.read(64)
                    full_name = ent[:56].split(b'\0')[0].decode('ascii', errors='ignore').lower()
                    
                    if full_name.endswith('.bsp'):
                        file_off = struct.unpack('<I', ent[56:60])[0]
                        # Capture current position to return after validation
                        back_pos = f.tell() 
                        if self.is_valid_bsp(f, file_off):
                            file_only = full_name.split('/')[-1].replace('.bsp', '')
                            maps.append(file_only)
                        f.seek(back_pos)
        except Exception as e:
            print(f"Error reading PAK: {e}")
        return maps

    def update_mod_image(self, mod_name, mod_path):
        # Look for mod.png or random preview
        for ext in ['.png', '.jpg']:
            p = os.path.join(mod_path, mod_name + ext)
            if os.path.exists(p):
                self.current_img_path = p
                self.render_image(p)
                return
        
        pre = os.path.join(mod_path, "previews")
        if os.path.exists(pre):
            imgs = [f for f in os.listdir(pre) if f.lower().endswith(('.png', '.jpg'))]
            if imgs:
                self.current_img_path = os.path.join(pre, random.choice(imgs))
                self.render_image(self.current_img_path)
                return
        self.img_label.config(image="", text="No Preview")
        self.current_img_path = None

    def on_map_select(self, event):


        # Clear cache before loading the new map preview
        self.cached_image = None
        self.cached_image_path = None


        # 1. Get the selected map name first
        sel = self.map_listbox.curselection()
        if not sel: 
            return
        map_name = self.map_listbox.get(sel[0])

        # 2. Get the selected mod name (or default to id1)
        mod_sel = self.mod_listbox.curselection()
        mod_name = self.mod_listbox.get(mod_sel[0]) if mod_sel else "id1"
        mod_path = os.path.join(self.base_dir.get(), mod_name)

        # 3. Now it is safe to use those variables
        title = self.get_map_title(mod_name, map_name)
        self.preview_title.config(text=title)

        # 4. Update the rest of the UI
        self.update_map_stats_display(mod_path, map_name)

        # Try finding image
        img_found = False
        for folder in ["previews", "maps"]:
            p_no_ext = os.path.join(mod_path, folder, map_name.lower())
            for ext in ['.png', '.jpg']:
                if os.path.exists(p_no_ext + ext):
                    self.current_img_path = p_no_ext + ext
                    self.render_image(self.current_img_path)
                    img_found = True
                    break
            if img_found: break
        
        if not img_found:
            self.img_label.config(image="", text="No Map Preview")
            self.current_img_path = None

    def show_context_menu(self, event):
        if self.current_img_path: self.context_menu.tk_popup(event.x_root, event.y_root)

    def show_mod_context_menu(self, event):
        idx = self.mod_listbox.nearest(event.y)
        self.mod_listbox.selection_clear(0, tk.END)
        self.mod_listbox.selection_set(idx)
        self.mod_context_menu.tk_popup(event.x_root, event.y_root)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f: return json.load(f)
        return {}

    def save_config(self):
        try:
            sashes = [self.paned.sash_coord(0)[0], self.paned.sash_coord(1)[0]]
        except:
            sashes = None

         # Current selections
        sel_mod = self.mod_listbox.curselection()
        last_mod = self.mod_listbox.get(sel_mod[0]) if sel_mod else None

        sel_map = self.map_listbox.curselection()
        last_map = self.map_listbox.get(sel_map[0]) if sel_map else None

        # Scroll positions (top fraction)
        mod_scroll = self.mod_listbox.yview()[0]
        map_scroll = self.map_listbox.yview()[0]

        data = {
            "exe": self.exe_path.get(),
            "base_dir": self.base_dir.get(),
            "skill": self.skill_level.get(),
            "font_size": self.font_size,
            "theme_name": self.active_theme_name,
            "window_size": self.root.winfo_geometry(),
            "sashes": sashes,
            "last_mod": last_mod,
            "last_map": last_map,
            "mod_scroll": mod_scroll,
            "map_scroll": map_scroll,
            "mod_extra_args": self.mod_extra_args
        }


        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)


    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("300x400")
        settings_win.configure(bg="#f0f0f0") # Standard light grey
        settings_win.grab_set()

        # Labels
        tk.Label(settings_win, text="UI Theme", bg="#f0f0f0", fg="black", font=("Arial", 10, "bold")).pack(pady=10)
        
        # Theme Menu
        theme_var = tk.StringVar(settings_win, value=self.active_theme_name)
        tk.OptionMenu(settings_win, theme_var, *self.themes.keys(), command=self.change_theme).pack()

        # Font Menu
        tk.Label(settings_win, text="Font Size", bg="#f0f0f0", fg="black", font=("Arial", 10, "bold")).pack(pady=10)
        size_var = tk.StringVar(settings_win, value=str(self.font_size))
        tk.OptionMenu(settings_win, size_var, "10", "12", "14", "16", "18", "20", command=self.change_font_size).pack()

        # THE BUTTON
        tk.Button(settings_win, text="CLOSE", width=15, bg="#ddd", fg="black", 
                  command=settings_win.destroy).pack(pady=30)

    def change_theme(self, name):
        self.active_theme_name = name
        self.current_theme = self.themes[name]
        self.apply_theme_to_ui()  # This updates the UI colors
        self.save_config()        # This writes it to the JSON

    def change_font_size(self, size):
        self.font_size = int(size)
        self.ui_font = ("Arial", self.font_size)
        self.apply_theme_to_ui()
        self.save_config()

    def browse_file(self, target):
        p = filedialog.askopenfilename()
        if p: self.exe_path.set(p); self.save_config()

    def browse_base(self):
        p = filedialog.askdirectory()
        if p: self.base_dir.set(p); self.load_mods(); self.save_config()

    def restore_sashes(self):
        s = self.config.get("sashes")
        if s:
            try: self.paned.sash_place(0, s[0], 0); self.paned.sash_place(1, s[1], 0)
            except: pass

    def on_close(self):
        self.save_config()
        self.root.destroy()

    def launch_game(self):
        exe = self.exe_path.get()
        if not os.path.exists(exe):
            return

        # Get selected mod
        sel_mod = self.mod_listbox.curselection()
        mod = self.mod_listbox.get(sel_mod[0]) if sel_mod else "id1"

        # Get selected map safely
        sel_map = self.map_listbox.curselection()
        if sel_map:
            map_n = self.map_listbox.get(sel_map[0])
        else:
            # Fallback to last saved map
            map_n = self.config.get("last_map", "(Default)")

        # Start screenshot watcher
        self.stop_screenshot_watch.clear()
        threading.Thread(
            target=self.watch_screenshots,
            args=(mod,),
            daemon=True
        ).start()

        # Build command
        cmd = [exe, "-game", mod, "+skill", self.skill_level.get()]

        if map_n and map_n != "(Default)":
            cmd.extend(["+map", map_n])

        # Add extra CLI parameters
        import shlex
        extra = self.mod_extra_args.get(mod, "").strip()

        if extra:
            cmd.extend(shlex.split(extra))

        print("Command line:", " ".join(cmd))

        # Save state before launching
        self.save_config()

        subprocess.Popen(cmd, cwd=os.path.dirname(exe))


    def force_rescan_mod(self):
        sel = self.mod_listbox.curselection()
        if not sel: return
        m_name = self.mod_listbox.get(sel[0])
        m_path = os.path.join(self.base_dir.get(), m_name)
        cache = os.path.join(m_path, "previews", "map_cache.json")
        if os.path.exists(cache): os.remove(cache)
        self.start_new_scan(m_name, m_path)

    def delete_current_screenshot(self):
        if self.current_img_path and os.path.exists(self.current_img_path):
            if messagebox.askyesno("Delete", "Delete this screenshot?"):
                os.remove(self.current_img_path)
                self.on_map_select(None)

    def open_previews_folder(self):
        sel = self.mod_listbox.curselection()
        if sel:
            p = os.path.join(self.base_dir.get(), self.mod_listbox.get(sel[0]), "previews")
            if os.path.exists(p):
                if platform.system() == "Windows": os.startfile(p)
                else: subprocess.Popen(["xdg-open", p])

    def is_valid_map_data(self, data_chunk):
        """Helper to check a byte chunk for playable spawn points."""
        try:
            # decode with latin-1 to avoid any UnicodeDecodeErrors from binary junk
            content = data_chunk.decode('latin-1', errors='ignore')
            # Look for any valid spawn point type
            valid_starts = ['info_player_start', 'info_player_deathmatch', 'info_player_coop']
            return any(start in content for start in valid_starts)
        except:
            return False

    def is_valid_bsp(self, f, offset=0):
        try:
            import struct
            f.seek(offset)
            magic = f.read(4)
            
            # --- Identify Format and Find Entity Lump ---
            ent_off, ent_size = None, None
            
            if magic == b'BSP2':
                # BSP2 (Modern Large)
                ent_off = struct.unpack('<I', f.read(4))[0]
                ent_size = struct.unpack('<I', f.read(4))[0]
            elif magic == b'2PSL':
                # 2PSL (64-bit Large)
                f.seek(offset + 8)
                ent_off = struct.unpack('<Q', f.read(8))[0]
                ent_size = struct.unpack('<Q', f.read(8))[0]
            else:
                # Standard BSP (Version 29)
                version = struct.unpack('<I', magic)[0]
                if version != 29: return False
                ent_off = struct.unpack('<I', f.read(4))[0]
                ent_size = struct.unpack('<I', f.read(4))[0]

            if not ent_off or ent_size == 0:
                return False

            # --- Jump directly to the Entity List ---
            f.seek(offset + ent_off)
            # Read the entity data (Up to 512KB for massive maps)
            entity_chunk = f.read(min(ent_size, 524288)).decode('latin-1', errors='ignore')
            
            # Must be a whole-word match to avoid partial string hits
            valid_starts = ['info_player_start', 'info_player_deathmatch', 'info_player_coop']
            return any(start in entity_chunk for start in valid_starts)
            
        except:
            return False

    def watch_screenshots(self, mod_name):
        """Threaded worker that watches for new screenshots in the mod root."""
        mod_path = os.path.join(self.base_dir.get(), mod_name)
        previews_path = os.path.join(mod_path, "previews")
        os.makedirs(previews_path, exist_ok=True)

        print(f"Watching for screenshots in: {mod_path}")
        
        while not self.stop_screenshot_watch.is_set():
            # Common Quake screenshot patterns (png, tga, jpg)
            #patterns = ["*.png", "*.tga", "*.jpg", "*.bmp"]
            patterns = ["vkquake*.png", "vkquake*.tga", "vkquake*.jpg", "vkquake*.bmp"]
            
            for pattern in patterns:
                for f in os.listdir(mod_path):
                    if fnmatch.fnmatch(f.lower(), pattern):
                        # Get current selected map
                        sel = self.map_listbox.curselection()
                        if not sel: continue
                        map_name = self.map_listbox.get(sel[0]).lower()
                        
                        full_old_path = os.path.join(mod_path, f)
                        extension = os.path.splitext(f)[1].lower()
                        new_name = f"{map_name}{extension}"
                        full_new_path = os.path.join(previews_path, new_name)

                        # Wait a moment for the game to finish writing the file
                        time.sleep(1) 
                        
                        try:
                            # Move and rename
                            shutil.move(full_old_path, full_new_path)
                            print(f"Captured screenshot: {new_name}")
                            
                            # Update the UI to show the new shot
                            self.root.after(0, lambda p=full_new_path: self.display_new_screenshot(p))
                        except Exception as e:
                            print(f"Error moving screenshot: {e}")
            
            time.sleep(2) # Poll every 2 seconds

    #def display_new_screenshot(self, path):
        #self.current_img_path = path
        #self.render_image(path)

    def display_new_screenshot(self, path):
        # Force the cache to clear so the new file is loaded from disk
        self.cached_image = None
        self.cached_image_path = None
    
        self.current_img_path = path
        self.render_image(path)



    def get_map_stats(self, entity_data, skill):
        """Counts monsters and secrets based on skill level bitmasks."""
        # Normalize skill input
        try:
            skill = int(skill)
        except:
            skill = 1

        # Find all monster entity blocks
        # This looks for the start of an entity { to the end }
        entities = re.findall(r'\{[^{}]*\}', entity_data)
        
        monster_count = 0
        secret_count = 0
        
        # Skill bitmasks
        # 256 = Not on Easy, 512 = Not on Normal, 1024 = Not on Hard
        exclude_bits = {0: 256, 1: 512, 2: 1024, 3: 1024}
        target_bit = exclude_bits.get(skill, 512)

        for ent in entities:
            # Check for Secrets
            if '"classname" "trigger_secret"' in ent:
                secret_count += 1
                continue
            
            # Check for Monsters
            if '"classname" "monster_' in ent:
                # Look for spawnflags
                sf_match = re.search(r'"spawnflags"\s+"(\d+)"', ent)
                if sf_match:
                    spawnflags = int(sf_match.group(1))
                    # If the "exclude" bit for this skill is set, don't count it
                    if spawnflags & target_bit:
                        continue
                
                monster_count += 1

        return monster_count, secret_count

    def update_map_stats_display(self, mod_path, map_name):
        """Coordinates the search for the map and updates the UI label."""
        self.map_info_label.config(text="Monsters: -- | Secrets: --")
        
        entity_text = ""
        # 1. Check Loose Files (in /maps or root)
        for folder in ["maps", ""]:
            bsp_path = os.path.join(mod_path, folder, f"{map_name}.bsp")
            if os.path.exists(bsp_path):
                with open(bsp_path, 'rb') as f:
                    entity_text = self.extract_entities_robust(f)
                break

        # 2. If not found loose, check PAKs
        if not entity_text:
            for f_name in os.listdir(mod_path):
                if f_name.lower().endswith('.pak'):
                    pak_path = os.path.join(mod_path, f_name)
                    entity_text = self.get_entities_from_pak(pak_path, map_name)
                    if entity_text: break

        if entity_text:
            # Get current skill from the StringVar
            current_skill = self.skill_level.get()
            m, s = self.get_map_stats(entity_text, current_skill)
            self.map_info_label.config(text=f"Skill {current_skill} | Monsters: {m} | Secrets: {s}")

    def extract_entities_robust(self, f, offset=0):
        """Extracts the full entity lump based on the BSP format."""
        try:
            import struct
            f.seek(offset)
            magic = f.read(4)
            
            ent_off, ent_size = None, None
            
            if magic == b'BSP2':
                ent_off = struct.unpack('<I', f.read(4))[0]
                ent_size = struct.unpack('<I', f.read(4))[0]
            elif magic == b'2PSL':
                f.seek(offset + 8)
                ent_off = struct.unpack('<Q', f.read(8))[0]
                ent_size = struct.unpack('<Q', f.read(8))[0]
            else:
                # Standard BSP (Version 29)
                f.seek(offset + 4) 
                ent_off = struct.unpack('<I', f.read(4))[0]
                ent_size = struct.unpack('<I', f.read(4))[0]

            if ent_off and ent_size > 0:
                f.seek(offset + ent_off)
                return f.read(ent_size).decode('latin-1', errors='ignore')
        except:
            pass
        return ""

    def get_entities_from_pak(self, pak_path, map_target):
        """Finds a map inside a PAK and returns its entity string."""
        try:
            import struct
            with open(pak_path, 'rb') as f:
                header = f.read(12)
                off, sz = struct.unpack('<II', header[4:12])
                f.seek(off)
                for _ in range(sz // 64):
                    ent = f.read(64)
                    filename = ent[:56].split(b'\0')[0].decode('ascii', errors='ignore').lower()
                    if filename.endswith(f"{map_target.lower()}.bsp"):
                        file_off = struct.unpack('<I', ent[56:60])[0]
                        return self.extract_entities_robust(f, file_off)
        except: pass
        return ""

    def save_mod_cli(self, *args):
        sel = self.mod_listbox.curselection()
        if not sel:
            return

        mod_name = self.mod_listbox.get(sel[0])
        self.mod_extra_args[mod_name] = self.extra_args.get()

        self.save_config()
        self.save_config()

    def get_map_title(self, mod_name, map_name):
        """Attempts to find the 'message' (title) of the map from its entity data."""
        if map_name == "(Default)":
            return f"Mod: {mod_name}"

        # We use .get() because base_dir is a Tkinter StringVar
        mod_path = os.path.join(self.base_dir.get(), mod_name)
        entity_text = ""

        # 1. Search loose files
        for folder in ["maps", ""]:
            bsp_path = os.path.join(mod_path, folder, f"{map_name}.bsp")
            if os.path.exists(bsp_path):
                try:
                    with open(bsp_path, 'rb') as f:
                        entity_text = self.extract_entities_robust(f)
                    break
                except Exception: continue

        # 2. Search PAKs if not found
        if not entity_text:
            try:
                for f_name in os.listdir(mod_path):
                    if f_name.lower().endswith('.pak'):
                        pak_path = os.path.join(mod_path, f_name)
                        entity_text = self.get_entities_from_pak(pak_path, map_name)
                        if entity_text: break
            except Exception: pass

        # 3. Extract the 'message' field
        if entity_text:
            match = re.search(r'"message"\s+"([^"]+)"', entity_text)
            if match:
                return match.group(1)

        # 4. Fallback to cleaned-up filename
        return map_name.replace('_', ' ').title()

    def restore_last_selection(self):
        last_mod = self.config.get("last_mod")
        last_map = self.config.get("last_map")
        mod_scroll = self.config.get("mod_scroll", 0)
        map_scroll = self.config.get("map_scroll", 0)

        if not last_mod:
            return

        # Restore mod selection
        for i in range(self.mod_listbox.size()):
            if self.mod_listbox.get(i) == last_mod:
                self.mod_listbox.selection_set(i)
                self.mod_listbox.event_generate("<<ListboxSelect>>")
                break

        # Restore mod scroll
        self.mod_listbox.yview_moveto(mod_scroll)

        # Restore map after maps load (async safe)
        def restore_map():
            if last_map:
                for i in range(self.map_listbox.size()):
                    if self.map_listbox.get(i) == last_map:
                        self.map_listbox.selection_set(i)
                        self.map_listbox.event_generate("<<ListboxSelect>>")
                        break

            # Restore map scroll
            self.map_listbox.yview_moveto(map_scroll)

        self.root.after(400, restore_map)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuakeLauncher(root)
    root.mainloop()
