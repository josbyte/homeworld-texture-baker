import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox, ttk
from PIL import Image, ImageTk, ImageOps
from colorsys import hsv_to_rgb
import os
import json

class TeamColorizerApp:
    def load_presets_from_json(self, filename="faction_color_presets_named.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, filename)
        try:
            with open(path, "r") as f:
                presets = json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {path}")
            return []
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        result = []
        for entry in presets:
            p = hex_to_rgb(entry["primary"])
            s = hex_to_rgb(entry["secondary"])
            result.append((p, s, entry["faction"]))
        return result
    
    def __init__(self, root):
        self.root = root
        self.root.title("Homeworld Team Colorizer")
        self.root.geometry("1200x1100")
        self.root.resizable(True, True)
        self.root.configure(bg='#1a1a1a')
        presets = self.load_presets_from_json()
        for p, s, name in presets[:5]:
            print(name, "->", p, s)
        self.colors = {
            'bg_primary': '#0a0a0a',
            'bg_secondary': '#1a1a1a',
            'bg_card': '#2a2a2a',
            'accent_primary': '#6366f1',
            'accent_secondary': '#8b5cf6',
            'accent_success': '#10b981',
            'accent_warning': '#f59e0b',
            'accent_error': '#ef4444',
            'text_primary': '#ffffff',
            'text_secondary': '#d1d5db',
            'text_muted': '#9ca3af',
            'border': '#4b5563',
            'hover': '#374151'
        }
        self.bc_image = None
        self.team_image = None
        self.mask_image = None
        self.glow_image = None
        self.badge_image = None
        self.output_image = None
        self.glow_output_image = None
        self.bc_loaded = tk.StringVar(value="Not loaded ")
        self.team_loaded = tk.StringVar(value="Not loaded ")
        self.mask_loaded = tk.StringVar(value="Not loaded ")
        self.glow_loaded = tk.StringVar(value="Not loaded ")
        self.badge_loaded = tk.StringVar(value="Not loaded ")
        self.color1 = (220, 38, 127)
        self.color2 = (33, 150, 243)
        self.presets = {}
        self.presets_loaded_file = None
        self.preset_target = tk.StringVar()
        self.badge_placement = None
        self.badge_rotation = 0
        self.badge_alpha = 255
        self.mode = tk.StringVar()
        self.primary_team_color = (255, 0, 0)  # Default red for primary team regions
        self.secondary_team_color = (0, 0, 255)  # Default blue for secondary team regions
        self.bc_title = "BC Texture"
        self.setup_ui()
        self.mode.set("Homeworld 3")
        self.load_presets_from_file()

    def rgb_to_hsv(self, r, g, b):
        import colorsys
        return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

    def hex_to_rgb_tuple(self, hex_color):
        h = hex_color.lstrip('#')
        if len(h) != 6:
            raise ValueError("Invalid hex color")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    
    def normalize_hex(self, h):
        if not isinstance(h, str):
            return '#000000'
        h = h.strip()
        if not h:
            return '#000000'
        if not h.startswith('#'):
            h = '#' + h
        if len(h) == 4:
            r = h[1]*2; g = h[2]*2; b = h[3]*2
            h = f'#{r}{g}{b}'
        return h.lower()

    def pick_color_gimp_style(self, initial_color, callback):
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Color")
        dialog.geometry("450x500")
        dialog.configure(bg=self.colors['bg_card'])
        dialog.transient(self.root)
        dialog.grab_set()
        r, g, b = [c/255 for c in initial_color]
        h, s, v = self.rgb_to_hsv(r, g, b)
        hue_var = tk.DoubleVar(value=h)
        sat_var = tk.DoubleVar(value=s)
        val_var = tk.DoubleVar(value=v)
        selected_color = [initial_color]
        preview = tk.Canvas(dialog, width=100, height=50, bg=self.rgb_to_hex(initial_color))
        preview.pack(pady=10)
        sb_canvas = tk.Canvas(dialog, width=256, height=256)
        sb_canvas.pack(pady=10)
        def draw_sb():
            width, height = 256, 256
            if not hasattr(sb_canvas, 'image'):
                sb_canvas.image = tk.PhotoImage(width=width, height=height)
                sb_canvas.create_image((0,0), image=sb_canvas.image, anchor='nw')
            rows = []
            for y in range(height):
                row_colors = []
                v_val = 1 - y / (height-1)
                for x in range(width):
                    s_val = x / (width-1)
                    r_, g_, b_ = hsv_to_rgb(hue_var.get(), s_val, v_val)
                    row_colors.append(f'#{int(r_*255):02x}{int(g_*255):02x}{int(b_*255):02x}')
                rows.append("{" + " ".join(row_colors) + "}")
            sb_canvas.image.put(" ".join(rows))
        draw_sb()
        def sb_click(event):
            x = max(0, min(255, event.x))
            y = max(0, min(255, event.y))
            s = x / 255
            v = 1 - y / 255
            sat_var.set(s)
            val_var.set(v)
            r_, g_, b_ = hsv_to_rgb(hue_var.get(), s, v)
            selected_color[0] = (int(r_*255), int(g_*255), int(b_*255))
            preview.config(bg=self.rgb_to_hex(selected_color[0]))
        sb_canvas.bind("<Button-1>", sb_click)
        sb_canvas.bind("<B1-Motion>", sb_click)
        tk.Label(dialog, text="Hue").pack()
        hue_canvas = tk.Canvas(dialog, width=256, height=20, bg=self.colors['bg_card'], highlightthickness=1, highlightcolor=self.colors['border'])
        hue_canvas.pack(pady=5)
        def draw_hue():
            width = 256
            for x in range(width):
                h = x / (width - 1)
                r, g, b = hsv_to_rgb(h, 1, 1)
                color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
                hue_canvas.create_line(x, 0, x, 20, fill=color)
        def update_hue_marker():
            hue_canvas.delete("marker")
            x = int(hue_var.get() * 255)
            hue_canvas.create_polygon(x-5, 20, x+5, 20, x, 25, fill='white', outline='black', tags="marker")
        draw_hue()
        update_hue_marker()
        def hue_click(event):
            x = max(0, min(255, event.x))
            h = x / 255
            hue_var.set(h)
            update_hue_marker()
            draw_sb()
            r_, g_, b_ = hsv_to_rgb(h, sat_var.get(), val_var.get())
            selected_color[0] = (int(r_*255), int(g_*255), int(b_*255))
            preview.config(bg=self.rgb_to_hex(selected_color[0]))
        hue_canvas.bind("<Button-1>", hue_click)
        hue_canvas.bind("<B1-Motion>", hue_click)
        btn_frame = tk.Frame(dialog, bg=self.colors['bg_card'])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="OK", command=lambda: [callback(selected_color[0]), dialog.destroy()]).pack(side=tk.RIGHT)

    def create_modern_file_button(self, parent, label_text, command, accent_color):
        frame = ttk.Frame(parent, style='Card.TFrame')
        frame.pack(fill=tk.X, pady=(0, 10))
        icon_label = ttk.Label(frame, text="📁", style='Body.TLabel', font=('Helvetica', 14))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        text_label = ttk.Label(frame, text=label_text, style='Body.TLabel')
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        btn = ttk.Button(frame, text="Load", command=command, style='Secondary.TButton')
        btn.pack(side=tk.RIGHT)
        status_label = ttk.Label(frame, textvariable=self.get_status_var(label_text), style='Status.TLabel')
        status_label.pack(side=tk.RIGHT, padx=(15, 0))
        if "BC" in label_text:
            self.bc_text_label = text_label
            self.bc_button = btn
            self.bc_status_label = status_label
        elif "MASK" in label_text:
            self.mask_button = btn
            self.mask_status_label = status_label
            self.mask_button_frame = frame
        elif "GLOW" in label_text:
            self.glow_button = btn
            self.glow_status_label = status_label
            self.glow_button_frame = frame
        return frame

    def create_modern_color_picker(self, parent, text, initial_color, command, column=0, row=0):
        frame = ttk.Frame(parent, style='Card.TFrame')
        frame.grid(row=row, column=column, padx=(0, 5) if column == 0 else (5, 0), pady=(0, 10), sticky="nsew")
        canvas = tk.Canvas(frame, width=40, height=40, bg=self.rgb_to_hex(initial_color),
                          highlightthickness=2, highlightcolor=self.colors['accent_primary'],
                          highlightbackground=self.colors['border'])
        canvas.pack(side=tk.LEFT, padx=(0, 8))
        color_label = ttk.Label(frame, text=text, style='Body.TLabel', font=('Helvetica', 10, 'bold'))
        color_label.pack(side=tk.LEFT, padx=(0, 5))
        btn = ttk.Button(frame, text="Choose", command=command, style='Secondary.TButton')
        btn.pack(side=tk.LEFT, fill=tk.X)
        if "Primary" in text and "Team" not in text:
            self.color1_canvas = canvas
        elif "Secondary" in text and "Team" not in text:
            self.color2_canvas = canvas
        elif "Primary Team" in text:
            self.primary_team_canvas = canvas
        elif "Secondary Team" in text:
            self.secondary_team_canvas = canvas
        return frame
    

    def create_presets_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Faction Presets", padding=15, style='Card.TFrame')
        frame.pack(fill=tk.X, pady=(0, 15))
        top_row = ttk.Frame(frame, style='Card.TFrame')
        top_row.pack(fill=tk.X, pady=(0, 8))
        load_btn = ttk.Button(top_row, text="Load Presets", command=self.load_presets_via_dialog, style='Secondary.TButton')
        load_btn.pack(side=tk.LEFT)
        self.presets_file_label = ttk.Label(top_row, text="(no presets loaded)", style='Status.TLabel')
        self.presets_file_label.pack(side=tk.LEFT, padx=(10, 0))
        search_row = ttk.Frame(frame, style='Card.TFrame')
        search_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(search_row, text="Search:", style='Body.TLabel').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.search_var.trace_add("write", self.filter_presets)
        list_frame = ttk.Frame(frame, style='Card.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.presets_listbox = tk.Listbox(list_frame, activestyle='none', height=8)
        self.presets_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.presets_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.presets_listbox.config(yscrollcommand=scrollbar.set)
        self.presets_listbox.bind("<<ListboxSelect>>", self.on_preset_select)
        self.presets_listbox.bind("<Double-Button-1>", self.on_preset_double_click)
        right_ctrl = ttk.Frame(frame, style='Card.TFrame')
        right_ctrl.pack(fill=tk.X, pady=(8, 0))
        return frame

    def load_presets_via_dialog(self):
        path = filedialog.askopenfilename(title="Select presets JSON", filetypes=[("JSON","*.json"),("All files","*.*")])
        if path:
            ok = self.load_presets_from_file(path)
            if ok:
                messagebox.showinfo("Presets Loaded", f"Presets loaded from:\n{path}")
            else:
                messagebox.showerror("Load Error", "Failed to load presets from the selected file.")

    def load_presets_from_file(self, path=None):
        candidates = []
        if path:
            candidates.append(path)
        candidates.extend([
            "faction_color_presets_named.json",
            "faction_color_presets.json",
            "./faction_color_presets_named.json",
            "/mnt/data/faction_color_presets_named.json"
        ])
        for p in candidates:
            if not p:
                continue
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    loaded = {}
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, dict):
                                ph = self.normalize_hex(v.get("primary") or v.get("primary_hex") or v.get("p") or "")
                                sh = self.normalize_hex(v.get("secondary") or v.get("secondary_hex") or v.get("s") or "")
                                if ph and sh:
                                    loaded[k] = (ph, sh)
                    elif isinstance(data, list):
                        for item in data:
                            if not isinstance(item, dict):
                                continue
                            name = item.get("faction") or item.get("name") or item.get("key")
                            ph = self.normalize_hex(item.get("primary") or item.get("primary_hex") or "")
                            sh = self.normalize_hex(item.get("secondary") or item.get("secondary_hex") or "")
                            if name and ph and sh:
                                loaded[name] = (ph, sh)
                    if not loaded:
                        messagebox.showwarning("Presets", f"The file {p} was read but contains no recognizable pairs.")
                        continue
                    self.presets = loaded
                    self.presets_loaded_file = p
                    self.presets_file_label.config(text=os.path.basename(p))
                    self.populate_presets_listbox()
                    return True
                except Exception as e:
                    messagebox.showerror("Error loading presets", str(e))
                    return False
        return False

    def populate_presets_listbox(self):
        self.presets_listbox.delete(0, tk.END)
        names = list(self.presets.keys())
        for name in names:
            self.presets_listbox.insert(tk.END, name)

    def filter_presets(self, *args):
        search = self.search_var.get().lower()
        self.presets_listbox.delete(0, tk.END)
        for name in self.presets:
            if search in name.lower():
                self.presets_listbox.insert(tk.END, name)

    def on_preset_select(self, event):
        sel = self.presets_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        name = self.presets_listbox.get(idx)
        ph, sh = self.presets.get(name, ("#000000", "#000000"))

    def on_preset_double_click(self, event):
        sel = self.presets_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        name = self.presets_listbox.get(idx)
        if hasattr(self, 'apply_preset_by_name') and callable(self.apply_preset_by_name):
            self.apply_preset_by_name(name)
        else:
            print(f"Error: apply_preset_by_name method is not available or not callable.")

    def apply_selected_preset(self):
        sel = self.presets_listbox.curselection()
        if not sel:
            messagebox.showwarning("No selection", "Select a faction first.")
            return
        name = self.presets_listbox.get(sel[0])
        self.apply_preset_by_name(name)

    def apply_preset_by_name(self, name):
        if name not in self.presets:
            messagebox.showerror("Error", "Preset not found.")
            return
        preset = self.presets[name]
        ph, sh = preset
        target = self.preset_target.get()
        rgb = self.hex_to_rgb_tuple(ph)
        self.set_color1(rgb)
        rgb = self.hex_to_rgb_tuple(sh)
        self.set_color2(rgb)

    def get_status_var(self, label_text):
        if "BC" in label_text:
            return self.bc_loaded
        elif "TEAM" in label_text:
            return self.team_loaded
        elif "MASK" in label_text:
            return self.mask_loaded
        elif "BADGE" in label_text:
            return self.badge_loaded
        return None

    def setup_ui(self):
        self.setup_modern_styles()
        self.create_mode_selector()
        self.create_main_layout()
        self.on_mode_change()  # Initialize based on default mode

    def setup_modern_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TFrame', background=self.colors['bg_card'])
        style.configure('Card.TFrame', background=self.colors['bg_card'], relief='flat')
        style.configure('Header.TFrame', background=self.colors['bg_secondary'])
        style.configure('Title.TLabel',
                        background=self.colors['bg_primary'],
                        foreground=self.colors['text_primary'],
                        font=('Helvetica', 24, 'bold'))
        style.configure('Subtitle.TLabel',
                        background=self.colors['bg_card'],
                        foreground=self.colors['text_secondary'],
                        font=('Helvetica', 14))
        style.configure('Section.TLabel',
                        background=self.colors['bg_card'],
                        foreground=self.colors['text_primary'],
                        font=('Helvetica', 16, 'bold'))
        style.configure('Body.TLabel',
                        background=self.colors['bg_card'],
                        foreground=self.colors['text_secondary'],
                        font=('Helvetica', 11))
        style.configure('Status.TLabel',
                        background=self.colors['bg_card'],
                        foreground=self.colors['text_muted'],
                        font=('Helvetica', 10))
        style.configure('Primary.TButton',
                        font=('Helvetica', 11, 'bold'),
                        padding=(20, 12),
                        relief='flat',
                        borderwidth=0)
        style.configure('Secondary.TButton',
                         font=('Helvetica', 10),
                         padding=(16, 10),
                         relief='flat',
                         borderwidth=0,
                         background=self.colors['bg_secondary'],
                         foreground=self.colors['text_secondary'])
        style.map('Primary.TButton',
                 background=[('active', self.colors['accent_primary']),
                           ('pressed', self.colors['accent_primary']),
                           ('!active', self.colors['accent_primary'])],
                 foreground=[('active', 'white'), ('!active', 'white')],
                 relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        style.map('Secondary.TButton',
                 background=[('active', self.colors['hover']),
                           ('pressed', self.colors['hover']),
                           ('!active', self.colors['bg_secondary'])],
                 foreground=[('active', self.colors['text_primary']),
                           ('!active', self.colors['text_secondary'])],
                 relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        style.configure('Horizontal.TProgressbar',
                       background=self.colors['accent_primary'],
                       troughcolor=self.colors['bg_secondary'],
                       borderwidth=0,
                       lightcolor=self.colors['accent_primary'],
                       darkcolor=self.colors['accent_primary'])

    def create_mode_selector(self):
        frame = ttk.Frame(self.root, style='Card.TFrame', padding=10)
        frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))
        label = ttk.Label(frame, text="Mode:", style='Body.TLabel')
        label.pack(side=tk.LEFT)
        combo = ttk.Combobox(frame, textvariable=self.mode, values=["Homeworld 3", "Homeworld Remastered"], state="readonly")
        combo.pack(side=tk.LEFT, padx=(10, 0))
        self.mode.trace_add("write", self.on_mode_change)

    def on_mode_change(self, *args):
        mode = self.mode.get()
        if mode == "Homeworld Remastered":
            self.bc_title = "DIFF Texture"
            self.bc_text_label.config(text="DIFF Texture")
            self.bc_title_label.config(text="DIFF Texture")
            self.mask_button_frame.pack_forget()
            self.mask_frame.grid_remove()
            self.glow_button_frame.pack(fill=tk.X, pady=(0, 10))
            self.team_hint_label.grid(row=1, column=0, columnspan=2, pady=(5, 5), sticky="w")
            self.primary_team_picker.grid(row=2, column=0, padx=(0, 5), pady=(0, 10), sticky="nsew")
            self.secondary_team_picker.grid(row=2, column=1, padx=(5, 0), pady=(0, 10), sticky="nsew")
            self.glow_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
            self.mask_frame.grid_remove()
        else:
            self.bc_title = "BC Texture"
            self.bc_text_label.config(text="BC Texture")
            self.bc_title_label.config(text="BC Texture")
            self.glow_button_frame.pack_forget()
            self.mask_button_frame.pack(fill=tk.X, pady=(0, 10))
            self.mask_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
            self.team_hint_label.grid_remove()
            self.primary_team_picker.grid_remove()
            self.secondary_team_picker.grid_remove()
            self.glow_frame.grid_remove()
        self.root.update_idletasks()

    def create_header(self):
        header_frame = ttk.Frame(self.root, style='Header.TFrame', padding=20)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame = ttk.Frame(header_frame, style='Header.TFrame')
        title_frame.pack(side=tk.LEFT)
        status_frame = ttk.Frame(header_frame, style='Header.TFrame')
        status_frame.pack(side=tk.RIGHT)
        self.status_indicators = {}

    def create_status_indicator(self, parent, name, var):
        frame = ttk.Frame(parent, style='Header.TFrame')
        frame.pack(side=tk.RIGHT, padx=(0, 15))
        dot = tk.Canvas(frame, width=12, height=12, bg=self.colors['bg_primary'], highlightthickness=0)
        dot.pack(side=tk.LEFT, padx=(0, 8))
        label = ttk.Label(frame, text=f"{name}:", style='Body.TLabel')
        label.pack(side=tk.LEFT)
        value_label = ttk.Label(frame, textvariable=var, style='Status.TLabel')
        value_label.pack(side=tk.LEFT, padx=(5, 0))
        return {'dot': dot, 'label': value_label}

    def create_main_layout(self):
        main_frame = ttk.Frame(self.root, style='Modern.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        left_panel = self.create_left_panel(main_frame)
        right_panel = self.create_right_panel(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def create_left_panel(self, parent):
        panel = ttk.Frame(parent, style='Card.TFrame', padding=20)
        texture_frame = ttk.LabelFrame(panel, text="Texture Management", padding=15, style='Card.TFrame')
        texture_frame.pack(fill=tk.X, pady=(0, 20))
        self.create_modern_file_button(texture_frame, "BC Texture", self.load_bc, self.colors['accent_success'])
        self.create_modern_file_button(texture_frame, "TEAM Texture", self.load_team, self.colors['accent_primary'])
        self.create_modern_file_button(texture_frame, "MASK Texture", self.load_mask, self.colors['accent_warning'])
        self.create_modern_file_button(texture_frame, "GLOW Texture", self.load_glow, self.colors['accent_warning'])
        self.create_modern_file_button(texture_frame, "BADGE Image", self.load_badge, self.colors['accent_error'])
        color_frame = ttk.LabelFrame(panel, text="Team Colors", padding=15, style='Card.TFrame')
        color_frame.pack(fill=tk.X, pady=(0, 20))
        color_frame.grid_columnconfigure(0, weight=1)
        color_frame.grid_columnconfigure(1, weight=1)
        self.create_modern_color_picker(color_frame, "Primary Color", self.color1, self.pick_color1, column=0, row=0)
        self.create_modern_color_picker(color_frame, "Secondary Color", self.color2, self.pick_color2, column=1, row=0)
        self.team_hint_label = ttk.Label(color_frame, text="💡 Click on TEAM texture preview to auto-pick team colors, right and left click for each one.", style='Body.TLabel', font=('Helvetica', 9))
        self.team_hint_label.grid(row=1, column=0, columnspan=2, pady=(5, 5), sticky="w")
        self.primary_team_picker = self.create_modern_color_picker(color_frame, "Primary Team", self.primary_team_color, self.pick_primary_team_color, column=0, row=2)
        self.secondary_team_picker = self.create_modern_color_picker(color_frame, "Secondary Team", self.secondary_team_color, self.pick_secondary_team_color, column=1, row=2)
        self.create_presets_panel(panel)
        action_frame = ttk.Frame(panel, padding=2, style='Card.TFrame')
        action_frame.pack(fill=tk.X, pady=(0, 0))
        action_frame_row = ttk.Frame(action_frame, style='Card.TFrame')
        action_frame_row.pack(fill=tk.X, pady=(0, 0))
        apply_btn = tk.Button(action_frame_row, text="🎨 Apply Team Color", command=self.apply_team_color, bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'], activebackground=self.colors['hover'], activeforeground=self.colors['text_primary'], font=('Helvetica', 10), relief='flat', borderwidth=0, highlightthickness=0, padx=16, pady=10)
        apply_btn.pack(side=tk.LEFT, padx=(0, 5))
        place_badge_btn = tk.Button(action_frame_row, text="🛡️ Place Badge", command=self.start_place_badge, bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'], activebackground=self.colors['hover'], activeforeground=self.colors['text_primary'], font=('Helvetica', 10), relief='flat', borderwidth=0, highlightthickness=0, padx=16, pady=10)
        place_badge_btn.pack(side=tk.LEFT, padx=(5, 5))
        save_btn = tk.Button(action_frame_row, text="💾 Save Result", command=self.save_output, bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'], activebackground=self.colors['hover'], activeforeground=self.colors['text_primary'], font=('Helvetica', 10), relief='flat', borderwidth=0, highlightthickness=0, padx=16, pady=10)
        save_btn.pack(side=tk.LEFT, padx=(5, 0))
        return panel

    def create_right_panel(self, parent):
        panel = ttk.Frame(parent, style='Card.TFrame', padding=20)
        preview_frame = ttk.LabelFrame(panel, text="Texture Previews", padding=15, style='Card.TFrame')
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.create_preview_grid(preview_frame)
        return panel

    def create_preview_grid(self, parent):
        self.preview_frames = {}
        bc_frame = self.create_preview_frame(parent, "BC Texture")
        bc_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        team_frame = self.create_preview_frame(parent, "TEAM Texture")
        team_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        mask_frame = self.create_preview_frame(parent, "MASK Texture")
        mask_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        result_frame = self.create_preview_frame(parent, "Result")
        result_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        glow_frame = self.create_preview_frame(parent, "Glow Texture")
        glow_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.glow_frame = glow_frame
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

    def create_preview_frame(self, parent, title):
        frame = ttk.Frame(parent, style='Card.TFrame', relief='flat')
        title_label = ttk.Label(frame, text=title, style='Section.TLabel')
        title_label.pack(pady=(0, 10))
        canvas = tk.Canvas(frame, width=200, height=150,
                          bg=self.colors['bg_secondary'],
                          highlightthickness=1,
                          highlightcolor=self.colors['border'],
                          highlightbackground=self.colors['border'])
        canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        canvas.create_text(100, 75, text="No preview",
                          fill=self.colors['text_muted'],
                          font=('Helvetica', 10))
        self.preview_frames[title] = canvas
        if title == "BC Texture":
            self.bc_title_label = title_label
        elif title == "MASK Texture":
            self.mask_title_label = title_label
            self.mask_frame = frame
        elif title == "Glow Texture":
            self.glow_title_label = title_label
        return frame

    def rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % rgb

    def load_bc(self):
        path = filedialog.askopenfilename(
            title=f"Select {self.bc_title}",
            filetypes=[
                ("All supported formats", "*.png *.jpg *.jpeg *.bmp *.bmpp *.tga *.dds *.tiff *.tif *.gif *.webp"),
                ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("BMP", "*.bmp *.bmpp"),
                ("TGA", "*.tga"), ("DDS", "*.dds"), ("TIFF", "*.tiff *.tif"),
                ("Other", "*.gif *.webp"), ("All files", "*.*")
            ]
        )
        if path:
            try:
                self.bc_image = Image.open(path).convert("RGBA")
                filename = os.path.basename(path)
                self.bc_loaded.set(f"✅ {filename}")
                self.update_preview("BC Texture", self.bc_image)
                self.show_success_message("BC texture loaded successfully", filename)
            except Exception as e:
                self.show_error_message("Failed to load BC texture", str(e))

    def load_team(self):
        path = filedialog.askopenfilename(
            title="Select TEAM Texture",
            filetypes=[
                ("All supported formats", "*.png *.jpg *.jpeg *.bmp *.bmpp *.tga *.dds *.tiff *.tif *.gif *.webp"),
                ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("BMP", "*.bmp *.bmpp"),
                ("TGA", "*.tga"), ("DDS", "*.dds"), ("TIFF", "*.tiff *.tif"),
                ("Other", "*.gif *.webp"), ("All files", "*.*")
            ]
        )
        if path:
            try:
                self.team_image = Image.open(path).convert("RGBA")
                filename = os.path.basename(path)
                self.team_loaded.set(f"✅ {filename}")
                self.update_preview("TEAM Texture", self.team_image)
                self.show_success_message("TEAM texture loaded successfully", filename)
            except Exception as e:
                self.show_error_message("Failed to load TEAM texture", str(e))

    def load_mask(self):
        path = filedialog.askopenfilename(
            title="Select MASK Texture",
            filetypes=[
                ("All supported formats", "*.png *.jpg *.jpeg *.bmp *.bmpp *.tga *.dds *.tiff *.tif *.gif *.webp"),
                ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("BMP", "*.bmp *.bmpp"),
                ("TGA", "*.tga"), ("DDS", "*.dds"), ("TIFF", "*.tiff *.tif"),
                ("Other", "*.gif *.webp"), ("All files", "*.*")
            ]
        )
        if path:
            try:
                self.mask_image = Image.open(path).convert("RGBA")
                filename = os.path.basename(path)
                self.mask_loaded.set(f"✅ {filename}")
                self.update_preview("MASK Texture", self.mask_image)
                self.show_success_message("MASK texture loaded successfully", filename)
            except Exception as e:
                self.show_error_message("Failed to load MASK texture", str(e))

    def load_glow(self):
        path = filedialog.askopenfilename(
            title="Select GLOW Texture",
            filetypes=[
                ("All supported formats", "*.png *.jpg *.jpeg *.bmp *.bmpp *.tga *.dds *.tiff *.tif *.gif *.webp"),
                ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("BMP", "*.bmp *.bmpp"),
                ("TGA", "*.tga"), ("DDS", "*.dds"), ("TIFF", "*.tiff *.tif"),
                ("Other", "*.gif *.webp"), ("All files", "*.*")
            ]
        )
        if path:
            try:
                self.glow_image = Image.open(path).convert("RGBA")
                filename = os.path.basename(path)
                self.glow_loaded.set(f"✅ {filename}")
                self.update_preview("Glow Texture", self.glow_image)
                self.show_success_message("GLOW texture loaded successfully", filename)
            except Exception as e:
                self.show_error_message("Failed to load GLOW texture", str(e))

    def load_badge(self):
        path = filedialog.askopenfilename(
            title="Select Badge Image",
            filetypes=[
                ("All supported formats", "*.png *.jpg *.jpeg *.bmp *.bmpp *.tga *.dds *.tiff *.tif *.gif *.webp"),
                ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("BMP", "*.bmp *.bmpp"),
                ("TGA", "*.tga"), ("DDS", "*.dds"), ("TIFF", "*.tiff *.tif"),
                ("Other", "*.gif *.webp"), ("All files", "*.*")
            ]
        )
        if path:
            try:
                self.badge_image = Image.open(path).convert("RGBA")
                filename = os.path.basename(path)
                self.badge_loaded.set(f"✅ {filename}")
                self.show_success_message("Badge image loaded successfully", filename)
            except Exception as e:
                self.show_error_message("Failed to load Badge image", str(e))

    def update_preview(self, preview_name, image):
        if preview_name not in self.preview_frames:
            return
        canvas = self.preview_frames[preview_name]
        canvas.delete("all")
        if image:
            # Use actual canvas dimensions
            canvas_width = canvas.winfo_width() if canvas.winfo_width() else 200
            canvas_height = canvas.winfo_height() if canvas.winfo_height() else 150
            image_ratio = image.width / image.height
            preview_ratio = canvas_width / canvas_height
            if image_ratio > preview_ratio:
                new_width = canvas_width
                new_height = int(canvas_width / image_ratio)
            else:
                new_height = canvas_height
                new_width = int(canvas_height * image_ratio)
            thumbnail = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            thumbnail_tk = ImageTk.PhotoImage(thumbnail)
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=thumbnail_tk)
            canvas.image = thumbnail_tk
            canvas.thumbnail = thumbnail  # Store for color picking
            canvas.x_offset = x_offset
            canvas.y_offset = y_offset
            canvas.scale_x = image.width / new_width
            canvas.scale_y = image.height / new_height
            info_text = f"{image.width}×{image.height}"
            canvas.create_text(canvas_width // 2, canvas_height - 15,
                              text=info_text,
                              fill=self.colors['text_muted'],
                              font=('Helvetica', 8),
                              anchor=tk.CENTER)
            if preview_name == "TEAM Texture" and self.mode.get() != "Homeworld 3":
                canvas.bind("<Button-1>", lambda e: self.pick_team_color(e, "primary"))
                canvas.bind("<Button-3>", lambda e: self.pick_team_color(e, "secondary"))
            if preview_name == "Result":
                self.preview_width = new_width
                self.preview_height = new_height
                self.preview_x_offset = x_offset
                self.preview_y_offset = y_offset
                self.preview_scale_x = image.width / new_width
                self.preview_scale_y = image.height / new_height

    def pick_team_color(self, event, type):
        canvas = event.widget
        if not hasattr(canvas, 'thumbnail'):
            return
        # Get click position relative to image
        x = event.x - canvas.x_offset
        y = event.y - canvas.y_offset
        if x < 0 or y < 0 or x >= canvas.thumbnail.width or y >= canvas.thumbnail.height:
            return
        # Get original coordinates
        orig_x = int(x * canvas.scale_x)
        orig_y = int(y * canvas.scale_y)
        # Get color from team_image
        if self.team_image:
            color = self.team_image.getpixel((orig_x, orig_y))
            if len(color) == 4:
                color = color[:3]  # ignore alpha
            if type == "primary":
                self.primary_team_color = color
                if self.mode.get() == "Homeworld 3":
                    self.primary_team_display.config(bg=self.rgb_to_hex(color))
                else:
                    self.update_color_preview(self.primary_team_canvas, color)
            elif type == "secondary":
                self.secondary_team_color = color
                if self.mode.get() == "Homeworld 3":
                    self.secondary_team_display.config(bg=self.rgb_to_hex(color))
                else:
                    self.update_color_preview(self.secondary_team_canvas, color)

    def show_success_message(self, title, message):
        messagebox.showinfo(f"✅ {title}", message)

    def show_error_message(self, title, message):
        messagebox.showerror(f"❌ {title}", message)

    def pick_color1(self):
        self.pick_color_gimp_style(self.color1, lambda c: self.set_color1(c))

    def pick_color2(self):
        self.pick_color_gimp_style(self.color2, lambda c: self.set_color2(c))

    def pick_primary_team_color(self):
        self.pick_color_gimp_style(self.primary_team_color, lambda c: self.set_primary_team_color(c))

    def pick_secondary_team_color(self):
        self.pick_color_gimp_style(self.secondary_team_color, lambda c: self.set_secondary_team_color(c))


    def set_color1(self, color):
        self.color1 = color
        self.update_color_preview(self.color1_canvas, self.color1)

    def set_color2(self, color):
        self.color2 = color
        self.update_color_preview(self.color2_canvas, self.color2)

    def set_primary_team_color(self, color):
        self.primary_team_color = color
        self.update_color_preview(self.primary_team_canvas, self.primary_team_color)

    def set_secondary_team_color(self, color):
        self.secondary_team_color = color
        self.update_color_preview(self.secondary_team_canvas, self.secondary_team_color)

    def update_color_preview(self, canvas, color):
        hex_color = self.rgb_to_hex(color)
        canvas.config(bg=hex_color)
        canvas.config(highlightcolor=self.colors['accent_primary'],
                     highlightbackground=self.colors['border'])

    def apply_team_color(self):
        if self.bc_image is None or self.team_image is None:
            self.show_warning_message("Load BC and TEAM textures first")
            return
        self.show_progress_dialog("Applying Team Colors", "Processing textures...")
        try:
            result_image = self.process_team_color()
            self.output_image = result_image
            if self.mode.get() == "Homeworld Remastered" and self.glow_image is not None:
                self.generate_glow_texture()
                self.update_preview("Glow Texture", self.glow_output_image)
            self.update_preview("Result", result_image)
            self.hide_progress_dialog()
            self.show_success_message("Team Color Applied", "Colorization completed successfully!")
        except Exception as e:
            self.hide_progress_dialog()
            self.show_error_message("Processing Error", f"Failed to apply team color: {str(e)}")

    def process_team_color(self):
        width, height = self.bc_image.size
        if self.team_image.size != self.bc_image.size:
            self.team_image = self.team_image.resize((width, height))
        if self.mask_image and self.mask_image.size != self.bc_image.size:
            self.mask_image = self.mask_image.resize((width, height))
        bc_pixels = self.bc_image.load()
        team_pixels = self.team_image.load()
        mask_pixels = self.mask_image.load() if self.mask_image else None
        output = Image.new("RGBA", (width, height))
        output_pixels = output.load()
        for y in range(height):
            for x in range(width):
                bc_r, bc_g, bc_b, bc_a = bc_pixels[x, y]
                factor = self.get_mask_factor(x, y, mask_pixels)
                if self.mode.get() == "Homeworld Remastered":
                    r, g, b, a = team_pixels[x, y]
                    if r > 240 and g > 240 and b < 20:  # yellow
                        factor = 0.0
                t = team_pixels[x, y][0] / 255.0  # Use red channel for interpolation
                team_r = int(self.color1[0] * (1 - t) + self.color2[0] * t)
                team_g = int(self.color1[1] * (1 - t) + self.color2[1] * t)
                team_b = int(self.color1[2] * (1 - t) + self.color2[2] * t)
                colored_r = int(team_r * (bc_r / 255 * 0.75 + 0.25))
                colored_g = int(team_g * (bc_g / 255 * 0.75 + 0.25))
                colored_b = int(team_b * (bc_b / 255 * 0.75 + 0.25))
                final_r = int(bc_r * (1 - factor) + colored_r * factor)
                final_g = int(bc_g * (1 - factor) + colored_g * factor)
                final_b = int(bc_b * (1 - factor) + colored_b * factor)
                output_pixels[x, y] = (final_r, final_g, final_b, bc_a)
        return output

    def get_mask_factor(self, x, y, mask_pixels):
        if not mask_pixels:
            return 1.0
        r, g, b, a = mask_pixels[x, y]
        return a / 255.0

    def generate_glow_texture(self):
        if not self.glow_image or not self.output_image:
            return
        width, height = self.output_image.size
        if self.glow_image.size != (width, height):
            self.glow_image = self.glow_image.resize((width, height), Image.Resampling.LANCZOS)
        glow_pixels = self.glow_image.load()
        output_pixels = self.output_image.load()
        glow_output = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow_output_pixels = glow_output.load()
        for y in range(height):
            for x in range(width):
                gr, gg, gb, ga = glow_pixels[x, y]
                if gg > 128:  # Green channel indicates glow
                    or_, og, ob, oa = output_pixels[x, y]
                    glow_output_pixels[x, y] = (or_, og, ob, 255)
        self.glow_output_image = glow_output

    def start_place_badge(self):
        if not self.badge_image:
            self.show_warning_message("Load Badge first")
            return
        if not self.output_image:
            self.show_warning_message("Apply Team Color first")
            return
        self.open_badge_placement_window()

    def open_badge_placement_window(self):
        # Create Toplevel without fullscreen (it will center over the main window)
        self.badge_window = tk.Toplevel(self.root)
        self.badge_window.title("Badge Placement")
        self.badge_window.configure(bg=self.colors['bg_primary'])
        self.badge_window.transient(self.root)
        self.badge_window.grab_set()

        # Forzar layout del root para obtener medidas reales
        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        # If for some reason root has very small size, fall back to screen measurements (but reduced)
        if root_w < 100 or root_h < 100:
            screen_w = self.badge_window.winfo_screenwidth()
            screen_h = self.badge_window.winfo_screenheight()
            root_w = int(screen_w * 0.8)
            root_h = int(screen_h * 0.8)
            root_x = int((screen_w - root_w) / 2)
            root_y = int((screen_h - root_h) / 2)

        # Window slightly smaller than the main window (doesn't occupy multiple screens)
        win_w = max(600, int(root_w * 0.95))
        win_h = max(400, int(root_h * 0.9))
        pos_x = root_x + (root_w - win_w) // 2
        pos_y = root_y + (root_h - win_h) // 2
        self.badge_window.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        # Frame para el canvas
        canvas_frame = ttk.Frame(self.badge_window, style='Card.TFrame')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        # Reserve part of the height for buttons/instructions
        canvas_width = win_w
        canvas_height = int(win_h * 0.78)

        self.badge_canvas = tk.Canvas(canvas_frame, width=canvas_width, height=canvas_height,
                                      bg=self.colors['bg_secondary'], highlightthickness=0)
        self.badge_canvas.pack(fill=tk.BOTH, expand=True)

        # Force layout to get real measurements and calculate exact scale
        self.badge_window.update_idletasks()
        actual_cw = self.badge_canvas.winfo_width()
        actual_ch = self.badge_canvas.winfo_height()

        # Scaling of the output image within the canvas
        output_ratio = self.output_image.width / self.output_image.height
        canvas_ratio = actual_cw / actual_ch
        if output_ratio > canvas_ratio:
            display_width = actual_cw
            display_height = int(actual_cw / output_ratio)
        else:
            display_height = actual_ch
            display_width = int(actual_ch * output_ratio)

        output_resized = self.output_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        self.output_tk = ImageTk.PhotoImage(output_resized)

        # Center the image within the canvas using the real dimensions
        x_offset = (actual_cw - display_width) // 2
        y_offset = (actual_ch - display_height) // 2
        self.badge_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.output_tk)

        # Save real factors/offsets to transform coordinates later
        self.badge_scale_x = self.output_image.width / display_width
        self.badge_scale_y = self.output_image.height / display_height
        self.badge_canvas_x_offset = x_offset
        self.badge_canvas_y_offset = y_offset
        self.badge_display_width = display_width
        self.badge_display_height = display_height

        # Initialize badge location and size (20% of display, centered)
        badge_width = int(display_width * 0.2)
        badge_height = int(badge_width * (self.badge_image.height / self.badge_image.width))
        badge_x = x_offset + (display_width - badge_width) // 2
        badge_y = y_offset + (display_height - badge_height) // 2
        self.badge_placement = [badge_x, badge_y, badge_width, badge_height]

        # Show badge and handles
        self.update_badge_preview()

        # Bindings to move / resize
        self.badge_canvas.bind("<Button-1>", self.start_drag)
        self.badge_canvas.bind("<B1-Motion>", self.do_drag)
        self.badge_canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.badge_canvas.bind("<Button-3>", self.start_resize)
        self.badge_canvas.bind("<B3-Motion>", self.do_resize)
        self.badge_canvas.bind("<ButtonRelease-3>", self.stop_resize)

        # Instructions (always visible below the canvas)
        instr_frame = ttk.Frame(self.badge_window, style='Card.TFrame')
        instr_frame.pack(fill=tk.X, pady=(2, 4), padx=10)
        instr_text = tk.Text(instr_frame, bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                              font=('Helvetica', 10), relief='flat', wrap=tk.WORD, height=3)
        instr_text.pack(fill=tk.X, padx=6, pady=6)
        instructions = ("Instructions:\n"
                        "- Left-click and drag to move the badge.\n"
                        "- Right-click and drag a corner to resize (keeps aspect ratio).\n"
                        "- Use the rotation slider to rotate the badge.\n"
                        "- Use the alpha slider to adjust badge transparency.\n"
                        "- Click 'Apply' to confirm or 'Cancel' to discard.")
        instr_text.insert(tk.END, instructions)
        instr_text.config(state=tk.DISABLED, height=3)

        # Rotation control
        rotation_frame = ttk.Frame(self.badge_window, style='Card.TFrame')
        rotation_frame.pack(fill=tk.X, pady=(2, 4), padx=10)
        ttk.Label(rotation_frame, text="Rotation:", style='Body.TLabel').pack(side=tk.LEFT, padx=(0,10))
        self.rotation_scale = tk.Scale(rotation_frame, from_=0, to=360, orient=tk.HORIZONTAL, command=self.update_rotation)
        self.rotation_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Alpha control
        alpha_frame = ttk.Frame(self.badge_window, style='Card.TFrame')
        alpha_frame.pack(fill=tk.X, pady=(2, 4), padx=10)
        ttk.Label(alpha_frame, text="Alpha:", style='Body.TLabel').pack(side=tk.LEFT, padx=(0,10))
        self.alpha_scale = tk.Scale(alpha_frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.update_alpha)
        self.alpha_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.alpha_scale.set(self.badge_alpha)

        # Buttons at the bottom
        btn_frame = ttk.Frame(self.badge_window, style='Card.TFrame')
        btn_frame.pack(fill=tk.X, pady=(0, 12), padx=10, side=tk.BOTTOM)
        ttk.Button(btn_frame, text="Apply", command=self.apply_badge, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.badge_window.destroy, style='Secondary.TButton').pack(side=tk.LEFT, padx=5)

        # Flags for interaction
        self.dragging = False
        self.resizing = False
        self.drag_start_x = 0
        self.drag_start_y = 0

    def update_badge_preview(self):
        if not self.badge_placement:
            return
        x, y, w, h = self.badge_placement
        # Constrain within canvas
        canvas_width = self.badge_canvas.winfo_width()
        canvas_height = self.badge_canvas.winfo_height()
        x = max(0, min(x, canvas_width - w))
        y = max(0, min(y, canvas_height - h))
        self.badge_placement[0] = x
        self.badge_placement[1] = y
        
        rotated_badge = self.badge_image.rotate(self.badge_rotation, expand=False)
        badge_resized = rotated_badge.resize(
            (int(w), int(h)),
            Image.Resampling.LANCZOS
        )
        badge_with_alpha = self.apply_alpha_to_badge(badge_resized)
        self.badge_tk = ImageTk.PhotoImage(badge_with_alpha)
        self.badge_canvas.delete("badge")
        self.badge_canvas.create_image(x, y, anchor=tk.NW, image=self.badge_tk, tags="badge")
        self.badge_canvas.delete("handles")
        handle_size = 8
        corners = [
            (x, y), (x + w, y), (x, y + h), (x + w, y + h)
        ]
        for cx, cy in corners:
            self.badge_canvas.create_rectangle(
                cx - handle_size//2, cy - handle_size//2,
                cx + handle_size//2, cy + handle_size//2,
                fill=self.colors['accent_primary'], tags="handles"
            )

    def start_drag(self, event):
        x, y, w, h = self.badge_placement
        if x <= event.x <= x + w and y <= event.y <= y + h:
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def do_drag(self, event):
        if not self.dragging:
            return
        x, y, w, h = self.badge_placement
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        new_x = x + dx
        new_y = y + dy
        canvas_width = self.badge_canvas.winfo_width()
        canvas_height = self.badge_canvas.winfo_height()
        new_x = max(0, min(new_x, canvas_width - w))
        new_y = max(0, min(new_y, canvas_height - h))
        self.badge_placement[0] = new_x
        self.badge_placement[1] = new_y
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.update_badge_preview()

    def stop_drag(self, event):
        self.dragging = False

    def start_resize(self, event):
        x, y, w, h = self.badge_placement
        handle_size = 8
        corners = [
            (x, y), (x + w, y), (x, y + h), (x + w, y + h)
        ]
        for i, (cx, cy) in enumerate(corners):
            if abs(event.x - cx) < handle_size and abs(event.y - cy) < handle_size:
                self.resizing = i + 1
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                break

    def do_resize(self, event):
        if not self.resizing:
            return
        x, y, w, h = self.badge_placement
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        aspect_ratio = self.badge_image.width / self.badge_image.height
        min_size = 50
        canvas_width = self.badge_canvas.winfo_width()
        canvas_height = self.badge_canvas.winfo_height()
        if self.resizing == 1:  # top-left
            new_w = max(min_size, min(w - dx, x + w - min_size))
            new_h = int(new_w / aspect_ratio)
            if new_h >= min_size:
                self.badge_placement[0] = x + dx
                self.badge_placement[1] = y + dy * (self.badge_image.height / self.badge_image.width)
                self.badge_placement[2] = new_w
                self.badge_placement[3] = new_h
        elif self.resizing == 2:  # top-right
            new_w = max(min_size, min(w + dx, canvas_width - x - min_size))
            new_h = int(new_w / aspect_ratio)
            if new_h >= min_size:
                self.badge_placement[1] = y + dy * (self.badge_image.height / self.badge_image.width)
                self.badge_placement[2] = new_w
                self.badge_placement[3] = new_h
        elif self.resizing == 3:  # bottom-left
            new_w = max(min_size, min(w - dx, x + w - min_size))
            new_h = int(new_w / aspect_ratio)
            if new_h >= min_size:
                self.badge_placement[0] = x + dx
                self.badge_placement[2] = new_w
                self.badge_placement[3] = new_h
        elif self.resizing == 4:  # bottom-right
            new_w = max(min_size, min(w + dx, canvas_width - x - min_size))
            new_h = int(new_w / aspect_ratio)
            if new_h >= min_size:
                self.badge_placement[2] = new_w
                self.badge_placement[3] = new_h
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.update_badge_preview()

    def stop_resize(self, event):
        self.resizing = False

    def update_rotation(self, value):
        self.badge_rotation = int(value)
        self.update_badge_preview()

    def update_alpha(self, value):
        self.badge_alpha = int(value)
        self.update_badge_preview()

    def apply_alpha_to_badge(self, image):
        if self.badge_alpha >= 255:
            return image
        badge_copy = image.copy()
        pixels = badge_copy.load()
        alpha_factor = self.badge_alpha / 255.0
        for y in range(badge_copy.height):
            for x in range(badge_copy.width):
                r, g, b, a = pixels[x, y]
                new_a = int(a * alpha_factor)
                pixels[x, y] = (r, g, b, new_a)
        return badge_copy

    def apply_badge(self):
        if not self.output_image or not self.badge_image:
            return
        x, y, w, h = self.badge_placement
        orig_x = int((x - self.badge_canvas_x_offset) * self.badge_scale_x)
        orig_y = int((y - self.badge_canvas_y_offset) * self.badge_scale_y)
        orig_w = int(w * self.badge_scale_x)
        orig_h = int(h * self.badge_scale_y)
        if orig_w < 10 or orig_h < 10:
            self.badge_window.destroy()
            return
        rotated_badge = self.badge_image.rotate(self.badge_rotation, expand=False)
        badge_resized = rotated_badge.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
        badge_final = self.apply_alpha_to_badge(badge_resized)
        self.output_image.paste(badge_final, (orig_x, orig_y), badge_final if badge_final.mode == 'RGBA' else None)
        self.update_preview("Result", self.output_image)
        self.badge_window.destroy()

    def show_progress_dialog(self, title, message):
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title(title)
        self.progress_window.geometry("400x150")
        self.progress_window.configure(bg=self.colors['bg_card'])
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        content_frame = ttk.Frame(self.progress_window, style='Card.TFrame', padding=30)
        content_frame.pack(fill=tk.BOTH, expand=True)
        progress_label = ttk.Label(content_frame, text=message, style='Body.TLabel', font=('Helvetica', 12))
        progress_label.pack(pady=(0, 20))
        self.progress_bar = ttk.Progressbar(content_frame, mode='indeterminate', style='Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        self.progress_bar.start()
        self.root.update()

    def hide_progress_dialog(self):
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()

    def show_warning_message(self, message):
        messagebox.showwarning("⚠️ Warning", message)

    def save_output(self):
        if not self.output_image:
            self.show_warning_message("No result to save. Apply Team Color first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp"),
                ("TGA", "*.tga"), ("TIFF", "*.tiff"), ("All files", "*.*")
            ]
        )
        if path:
            try:
                self.output_image.save(path)
                filename = os.path.basename(path)
                message = f"Result saved as:\n{filename}"
                if self.mode.get() == "Homeworld Remastered" and self.glow_output_image:
                    base, ext = os.path.splitext(path)
                    glow_path = base + '_glow' + ext
                    self.glow_output_image.save(glow_path)
                    glow_filename = os.path.basename(glow_path)
                    message += f"\nGlow saved as:\n{glow_filename}"
                self.show_success_message("File Saved", message)
            except Exception as e:
                self.show_error_message("Save Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TeamColorizerApp(root)
    root.mainloop()