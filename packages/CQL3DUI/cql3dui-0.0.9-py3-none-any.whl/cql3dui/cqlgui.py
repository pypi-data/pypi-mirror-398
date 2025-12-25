import sys
import os, re
import yaml
import f90nml
import subprocess
import threading
import shutil
import datetime
import darkdetect
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from tkinter.scrolledtext import ScrolledText
from ttkbootstrap import Style
import json, ast
from pathlib import Path
from collections import OrderedDict
import platform
MODIFIER = "Command" if platform.system() == "Darwin" else "Control"

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from netCDF4 import Dataset

import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

# Ensure matplotlib uses the correct backend for Tkinter
matplotlib.use("TkAgg")

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.id = None
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)
        self.widget.bind('<ButtonPress>', self.leave)
        
    def enter(self, event=None):
        """Schedule showing the tooltip."""
        self.id = self.widget.after(100, self.show_tooltip)
        
    def leave(self, event=None):
        """Hide the tooltip."""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self.hide_tooltip()
        
    def show_tooltip(self):
        """Display the tooltip."""
        if self.tooltip:
            return
            
        # Get widget position
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Create label with text
        label = tk.Label(self.tooltip, text=self.text, justify='left', borderwidth=1)
                        #background="#ffffe0", relief='solid', borderwidth=1,
                        #font=("TkDefaultFont", 9))
        label.pack()
        
        # Make sure tooltip stays on top
        self.tooltip.wm_attributes("-topmost", True)
        
    def hide_tooltip(self):
        """Destroy the tooltip window."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class CQL3D_GUI(tk.Tk):
    def __init__(self, yaml_file):
        super().__init__()
        self.yaml_file = yaml_file
        self.data = {}
        self.widgets = {}  # Map variable name -> widget object
        self.form_rows = {}  # Map variable name -> (label, field, frame, layout_method)
        self.tooltips = {}  # Store tooltip objects
        self.start_ind = {} # Start index vector needed for f90nml
        self.highlight_enabled = True # Start with highlight enabled
        self.highlight_var = tk.BooleanVar(value=self.highlight_enabled)
        self.last_searched_var = []
        self.shared_sash_x = 745 # Initial divider location
        self.last_successful_nc_path = None
        self.invisible = []
        self.subgroup_tracking = {}
        self._debounce_timer = None
        
        # self.base_dir = Path.cwd()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder_dir = Path.cwd()#self.base_dir
        
        # Load subgroup information (cqlinput_help text)
        self.sginfo = os.path.join(self.base_dir, 'sginfo')
        
        if darkdetect.theme() == 'Dark':
            self.style = Style(theme='darkly') # GUI style
            self.highlight_background = 'white'
            self.highlight_foreground = 'black'
        else:
            self.style = Style(theme='flatly') # GUI style
            self.highlight_background = 'black'
            self.highlight_foreground = 'white'
        
        #self.style = Style(theme='darkly') # GUI style
        self.title("CQL3D Namelist Editor") # GUI title
        self.geometry("1300x900") # GUI size
        
        # Initialize paths
        self.executable_path = None
        self.current_file = None
        self.additional_files = None
        
        # Load json configuration
        self.config_file = os.path.join(self.base_dir, ".cql3d_gui_config.json")
        self.jconfig = self.load_jconfig()
        
        # Apply loaded configuration
        if self.jconfig:
            # Only set if the key exists and is not None
            if 'executable_path' in self.jconfig and self.jconfig['executable_path']:
                self.executable_path = self.jconfig['executable_path']
            if 'last_namelist' in self.jconfig and self.jconfig['last_namelist']:
                self.current_file = self.jconfig['last_namelist']
            if 'last_aux_file' in self.jconfig and self.jconfig['last_aux_file']:
                self.additional_files = self.jconfig['last_aux_file']
        
        # Load YAML Configuration
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YAML file:\n{e}")
            sys.exit(1)
            
        self.start_ind = self.config['start_ind']
        self.gorder = self.config['gorder']
        
        # 1. Keep track of subgroup order from YAML
        self.subgroup_defs = self.config.get('subgroups', {})
        self.subgroup_info = self.config.get('subgroupinfo', {})
        
        # 2. Create a reverse lookup: variable -> subgroup_name
        self.var_to_subgroup = {}
        for sg_name, var_list in self.subgroup_defs.items():
            for v in var_list:
                self.var_to_subgroup[v] = sg_name
            
        self.init_ui()
        self.apply_defaults()
        self.trigger_dependency_check()

    def init_ui(self):
        """Initialize the main UI components."""
        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Toolbar / Action Area (top) ---
        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        load_btn = ttk.Button(toolbar, text="Import Namelist", command=self.import_namelist)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = ttk.Button(toolbar, text="Export Namelist", command=self.export_namelist)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        
        # Create the progress bar (indeterminate mode = bouncing)
        self.progress = ttk.Progressbar(toolbar, mode='indeterminate', length=200)
        

        # Position it (adjust row/column to fit your layout)
        # We use grid() here, but you can use pack() if your layout uses that.
        # We immediately hide it so it doesn't show up on startup.
        self.progress.pack(side=tk.RIGHT)
        self.progress.pack_forget()  # Hides the widget but remembers settings
                
        # --- Notebook (Tabs) ---
        self.notebook = ttk.Notebook(main_container)
        # keep right-panel in sync when switching tabs
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        gui_config = self.config.get('gui_configuration', {})
        tab_structure = gui_config.get('tab_structure', [])
        
        placed_variables = set()
        
        # 1. Build tabs defined in YAML
        for tab_def in tab_structure:
            tab_name = tab_def.get('name', 'Unknown')
            groups = tab_def.get('groups', [])
            filters = tab_def.get('filters', None)
            
            tab_widget = self.create_tab_content(groups, filters, placed_variables)
            self.notebook.add(tab_widget, text=tab_name)
        
        # 2. Catch-all tab for anything missed
        # Collect remaining variables grouped by their Namelist Group
        remaining_vars_by_group = {}
        all_groups = self.config.get('namelist_groups', {})
        
        has_remaining = False
        for g_name, g_data in all_groups.items():
            for v_name in g_data.get('variables', {}):
                if v_name not in placed_variables:
                    if g_name not in remaining_vars_by_group:
                        remaining_vars_by_group[g_name] = []
                    remaining_vars_by_group[g_name].append(v_name)
                    has_remaining = True
        
        if has_remaining:
        
            tab_name = "Misc/Unsorted"#tab_def.get('name', 'Unknown')
            groups = [key for key in remaining_vars_by_group]
            filters = None
            
            tab_widget = self.create_tab_content(groups, filters, placed_variables)
            self.notebook.add(tab_widget, text=tab_name)
        
        # --- Execution Control Area (bottom) ---
        exec_frame = ttk.LabelFrame(main_container, text="CQL3D Execution", padding=10)
        exec_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Create a frame for the buttons
        button_frame = ttk.Frame(exec_frame)
        button_frame.pack(fill=tk.X)
        
        file_btn = ttk.Button(
            button_frame,
            text="Aux. File Folder",
            command=self.aux_file_folder,
            #width=20
        )
        file_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Load Executable Button
        self.load_exec_btn = ttk.Button(
            button_frame, 
            text="Load CQL3D Executable", 
            command=self.load_executable,
            #width=20
        )
        self.load_exec_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Executable path display
        self.exec_path_label = ttk.Label(button_frame,text="No executable loaded", foreground="gray")
        self.exec_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Plot Results Button
        self.plot_btn = ttk.Button(button_frame,text="Plot Results",command=self.plot_results,state="normal",width=15)
        self.plot_btn.pack(side=tk.RIGHT,padx=5)
        
        # Run CQL3D Button
        self.run_btn = ttk.Button(button_frame,text="Run CQL3D",command=self.run_cql3d,state="disabled",width=15)
        self.run_btn.pack(side=tk.RIGHT,padx=5)
        
        #nc_filepath = Path(self.get_nc_filename())
        #if nc_filepath.is_file(): self.plot_btn.config(state="normal")
        
        if self.executable_path is not None:
            self.exec_path_label.config(text=f"Loaded: {os.path.basename(self.executable_path)}")
            self.run_btn.config(state="normal")
        
        # Add tooltips
        ToolTip(self.load_exec_btn, "Load a CQL3D executable file to run simulations")
        ToolTip(self.run_btn, "Save current namelist as 'cqlinput' and run CQL3D \n (requires CQL3D executable to be loaded)")
        ToolTip(self.plot_btn, "Plot results from NetCDF file \n (requires NetCDF file in current working directory)")
        
    def create_tab_content(self, group_names, filters, placed_variables):
        """Creates a tab page with a split view that resizes with the window."""

        # 1. Direct Tab Container
        tab = ttk.Frame(self.notebook)
        # Ensure the tab stretches its contents
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)

        # 2. The Split View (PanedWindow)
        # Parent this DIRECTLY to 'tab', not a scrollable frame.
        content_split = ttk.PanedWindow(tab, orient="horizontal", style="Thick.TPanedwindow")
        
        # Grid it to fill the entire tab area
        content_split.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # --- Sash Position Logic (Preserved from your code) ---
        
        def get_sash_position(widget):
            try: return widget.sash_coord(0)[0]
            except Exception:
                try: return widget.sashpos(0)
                except Exception: return None

        def set_sash_position(widget, pos):
            if pos is None: return
            try: widget.sash_place(0, pos, 0)
            except Exception:
                try: widget.sashpos(0, pos)
                except Exception: pass

        def _enforce_on_resize(event):
            # Only enforce if we have a saved position and widget is essentially "ready"
            if getattr(self, 'shared_sash_x', None) and event.widget == content_split:
                current = get_sash_position(content_split)
                # If sash gets reset to 0 or weirdly huge, restore it.
                if current and abs(current - self.shared_sash_x) > 50:
                     set_sash_position(content_split, self.shared_sash_x)

        content_split.bind("<Configure>", _enforce_on_resize)

        def _save_sash_pos(event):
            pos = get_sash_position(content_split)
            if pos is not None:
                self.shared_sash_x = pos
        
        content_split.bind("<ButtonRelease-1>", _save_sash_pos)

        def _restore_sash_pos(event):
            if hasattr(self, 'shared_sash_x') and self.shared_sash_x is not None:
                content_split.update_idletasks()
                current_width = content_split.winfo_width()
                if current_width > self.shared_sash_x:
                    set_sash_position(content_split, self.shared_sash_x)
            else:
                # Default 60/40 split if no history
                content_split.update_idletasks()
                w = content_split.winfo_width()
                if w > 1:
                    set_sash_position(content_split, int(w * 0.6))

        content_split.bind("<Map>", _restore_sash_pos)


        # --- LEFT PANEL (Variables) ---
        
        left_outer = ttk.Frame(content_split)
        content_split.add(left_outer, weight=3) # weight determines resize priority

        left_outer.rowconfigure(0, weight=1)
        left_outer.columnconfigure(0, weight=1)

        left_canvas = tk.Canvas(left_outer, highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(left_outer, orient="vertical", command=left_canvas.yview)

        left_canvas.grid(row=0, column=0, sticky="nsew")
        left_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 5))
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_inner = ttk.Frame(left_canvas)
        left_window = left_canvas.create_window((0, 0), window=left_inner, anchor="nw")

        def _sync_left_width(event):
            # Force the inner frame to match the canvas width so variables don't get cut off
            left_canvas.itemconfig(left_window, width=event.width)
        
        left_canvas.bind("<Configure>", _sync_left_width)

        def _configure_left(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        
        left_inner.bind("<Configure>", _configure_left)
        
        self.setup_mouse_scroll(left_canvas, left_inner)


        # --- RIGHT PANEL (Info/Help) ---
        
        right_outer = ttk.Frame(content_split)
        content_split.add(right_outer, weight=2)

        right_outer.rowconfigure(0, weight=0) # Toggle row (fixed height)
        right_outer.rowconfigure(1, weight=1) # Info box (expands)
        right_outer.columnconfigure(0, weight=1)
        right_outer.columnconfigure(1, weight=0)

        # Toggle/Search Frame
        toggle_frame = ttk.Frame(right_outer)
        toggle_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 0))

        def toggle_highlight():
            self.highlight_enabled = self.highlight_var.get()
            # ... (Your existing toggle logic) ...
            try:
                tab_ref = self.notebook.nametowidget(self.notebook.select())
                info_panel = getattr(tab_ref, "info_panel", None)
            except Exception: return

            if info_panel:
                for var_name, winfo in self.widgets.items():
                    w = winfo.get('widget')
                    if w and w.focus_get() == w:
                        sg = self.var_to_subgroup.get(var_name, "_general")
                        self.update_info_panel(sg, var_name)
                        break

        ttk.Checkbutton(toggle_frame, text="Highlight variable",
                        variable=self.highlight_var, command=toggle_highlight).pack(side=tk.LEFT)

        # Info Text Widget
        info_scrollbar = ttk.Scrollbar(right_outer, orient="vertical")
        info_scrollbar.grid(row=1, column=1, sticky="ns")

        info_widget = tk.Text(right_outer, wrap=tk.WORD, yscrollcommand=info_scrollbar.set, width=50)
        info_widget.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        info_widget.config(state="disabled")
        
        info_scrollbar.config(command=info_widget.yview)
        
        # Attach references to tab
        tab.info_panel = info_widget
        
        # --- Search/Nav Controls (Your existing code) ---
        match_label = ttk.Label(toggle_frame, text="0 / 0", font=("TkDefaultFont", 9, "italic"))
        match_label.pack(side=tk.RIGHT, padx=5)
        tab.match_count_label = match_label

        self.next_btn = ttk.Button(toggle_frame, text="→", width=3, command=lambda: self.navigate_search(1))
        self.next_btn.pack(side=tk.RIGHT, padx=2)

        self.prev_btn = ttk.Button(toggle_frame, text="←", width=3, command=lambda: self.navigate_search(-1))
        self.prev_btn.pack(side=tk.RIGHT, padx=2)

        # Bindings
        self.notebook.bind_all("<KeyPress-Up>", self._focus_prev_widget)
        self.notebook.bind_all("<KeyPress-Down>", self._focus_next_widget)
        tab.bind_all("<Shift-KeyPress-Right>", lambda e: self.navigate_search(1))
        tab.bind_all("<Shift-KeyPress-Left>", lambda e: self.navigate_search(-1))
        self.bind_all(f"<{MODIFIER}-Left>", lambda e: self._switch_tab(-1))
        self.bind_all(f"<{MODIFIER}-Right>", lambda e: self._switch_tab(1))

        # --- POPULATE VARIABLES  ---
        namelist_groups = self.config.get("namelist_groups", {})
        for g_name in group_names:
            if g_name not in namelist_groups: continue
            group_vars = namelist_groups[g_name].get("variables", {})
            vars_to_process = [v for v in group_vars if filters is None or v in filters]
            self.create_group_content(left_inner, g_name, vars_to_process, placed_variables)

        # --- INITIALIZATION ---
        # (This block populates the info panel on load)
        for var_name, winfo in self.widgets.items():
             w = winfo.get("widget")
             if w and w.winfo_ismapped():
                 sg = self.var_to_subgroup.get(var_name, "_general")
                 self.update_info_panel(sg, var_name)
                 break

        return tab
        
    def create_group_content(self, parent_frame, group_name, variables_list, placed_variables):
        """
        Organizes variables into Subgroups and renders them.
        Returns True if any variables were added, False otherwise.
        """
        # 1. Filter variables that have already been placed or are invalid
        valid_vars = [v for v in variables_list if v not in placed_variables]
        if not valid_vars:
            return False

        # Create the Main Group LabelFrame (e.g., "SETUP")
        group_data = self.config['namelist_groups'].get(group_name, {})
        gb = ttk.LabelFrame(parent_frame, text=group_name.upper(), padding=5)
        gb.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # Initialize the tracking list for THIS specific group container
        self.subgroup_tracking[gb] = []
        
        # Description Tooltip for Group
        if 'description' in group_data:
            desc = group_data['description']
            if desc:
                ToolTip(gb, desc)
                # Optional: Add a subtitle label
                lbl = ttk.Label(gb, text=desc, font=('TkDefaultFont', 9, 'italic'))
                lbl.pack(anchor='w', padx=5)

        # 2. Bucket variables: Subgroup -> [list of vars]
        # We use the order defined in self.subgroup_defs for keys
        buckets = {k: [] for k in self.subgroup_defs.keys()}
        buckets['_general'] = [] # For vars not in any subgroup

        for v in valid_vars:
            sg = self.var_to_subgroup.get(v)
            if sg and sg in buckets:
                buckets[sg].append(v)
            else:
                buckets['_general'].append(v)

        # 3. Render "_general" variables first (those without a subgroup)
        if buckets['_general']:
            gen_frame = ttk.Frame(gb)
            gen_frame.pack(fill=tk.X, pady=2)
            
            # Add to tracking for THIS group
            self.subgroup_tracking[gb].append(('_general', gen_frame))
            
            for i, v in enumerate(buckets['_general']):
                self.create_variable_row(group_name, v, gen_frame, i, 'grid')
                placed_variables.add(v)

        # 4. Render Subgroups
        for sg_name, vars in buckets.items():
            if sg_name == '_general' or not vars:
                continue
            
            # Create a container for the subgroup
            sg_frame = ttk.LabelFrame(gb, text=sg_name)
            
            # Add to tracking for THIS group
            self.subgroup_tracking[gb].append((sg_name, sg_frame))
            
            # Initial pack
            sg_frame.pack(fill=tk.X, padx=5, pady=5)
            
            for i, v in enumerate(vars):
                self.create_variable_row(group_name, v, sg_frame, i, 'grid')
                placed_variables.add(v)
        return True

    def create_variable_row(self, group, var_name, parent_frame, row_index, layout_method='grid'):
        """Creates the Label + Widget pair and adds to the form."""
        full_path = f"{group}.{var_name}"
        var_data = self.config['namelist_groups'][group]['variables'][var_name]
        
        # Create frame for this row
        frame = ttk.Frame(parent_frame)
        
        if layout_method == 'grid':
            frame.grid(row=row_index, column=0, sticky='ew', padx=5, pady=2)
            parent_frame.grid_columnconfigure(0, weight=1)
        else:  # pack
            frame.pack(fill=tk.X, padx=5, pady=2, anchor='w')
        
        # Tooltip / Description
        desc = var_data.get('description', var_name)
        #units = var_data.get('units', '')
        #if units: desc += f" ({units})"
        
        # Label
        label = ttk.Label(frame, text=var_name, width=25, anchor='e')
        label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add tooltip to label
        if desc:
            ToolTip(label, desc)
        
        # Create Widget based on type/options
        widget = None
        options = var_data.get('options')
        
        # 1. Combobox for Options
        if options:
            widget = ttk.Combobox(frame, state='readonly')
            
            # Populate values
            if isinstance(options, list):
                widget['values'] = [str(opt) for opt in options]
                options_text = "Options:\n" + "\n".join([f"  • {opt}" for opt in options])
            elif isinstance(options, dict):
                widget['values'] = [f"{key}: {val}" for key, val in options.items()]
                widget.option_keys = list(options.keys())
                options_text = "Options:\n" + "\n".join([f"  • {key}: {val}" for key, val in options.items()])

            if desc: options_text = desc + "\n\n" + options_text
            ToolTip(widget, options_text)
            
            # State Management
            widget.selection_active = False

            # INTERCEPT Arrow Keys at the widget level to prevent menu opening
            widget.bind('<Down>', self._focus_next_widget)
            widget.bind('<Up>', self._focus_prev_widget)

            # Toggle mode on Enter
            widget.bind('<Return>', lambda e, w=widget: self._toggle_combobox_mode(e, w))
            
            # Reset mode on selection or losing focus
            widget.bind('<<ComboboxSelected>>', lambda e, w=widget: [
                setattr(w, 'selection_active', False),
                self.trigger_dependency_check(),
                _activate_info()
            ], add='+')

            widget.bind("<FocusOut>", lambda e, w=widget: setattr(w, 'selection_active', False), add='+')
            
        # 2. Standard Types
        else:
            widget = ttk.Entry(frame)
            # Add tooltip to entry widget
            if desc: ToolTip(widget, desc)
            
#            default = var_data.get('default', '')
#            widget.insert(0, "e.g. 1.0, 2.0, 3.0")
            
            # Add basic placeholder
#            if 'array' in var_data.get('type', ''):
#                widget.insert(0, "e.g. 1.0, 2.0, 3.0")
#                #widget.configure(foreground='grey')
#                
#                def on_focus_in(event):
#                    if widget.get() == "e.g. 1.0, 2.0, 3.0":
#                        widget.delete(0, tk.END)
#                        #widget.configure(foreground='black')
#                
#                def on_focus_out(event):
#                    if not widget.get():
#                        widget.insert(0, "e.g. 1.0, 2.0, 3.0")
#                        #widget.configure(foreground='grey')
#                
#                widget.bind('<FocusIn>', on_focus_in)
#                widget.bind('<FocusOut>', on_focus_out)
            
            # Bind change event
            widget.bind('<KeyRelease>', lambda e, v=var_name: self.trigger_dependency_check())
        
        widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Store references
        self.widgets[var_name] = {'widget': widget, 'data': var_data, 'group': group}
        
        
        # Determine subgroup for this variable
        sg = self.var_to_subgroup.get(var_name, "_general")

        def _activate_info(event=None, sg=sg, v=var_name):
            # call update (safe wrapper)
            try:
                self.update_info_panel(sg, v)
            except Exception as e:
                print("update_info_panel error:", e)

        # Bind focus/click events to update right panel
        try: widget.bind("<FocusIn>", _activate_info, add='+')
        except Exception: pass

        try: label.bind("<Button-1>", _activate_info, add='+')
        except Exception: pass

        # Combobox selection should also update
        if isinstance(widget, ttk.Combobox):
            try: widget.bind("<<ComboboxSelected>>", _activate_info, add='+')
            except Exception: pass
                    
        
        # Store layout item references for hiding/showing, including layout method
        self.form_rows[var_name] = {
            'label': label,
            'widget': widget, 
            'frame': frame,
            'layout_method': layout_method,
            'parent': parent_frame,
            'row_index': row_index
        }
        
    def setup_mouse_scroll(self, canvas, scrollable_frame):
        """Enables mousewheel scrolling with boundary checks to prevent over-scrolling."""
        
        def _on_mousewheel(event):
            if not canvas.winfo_exists(): return
            
            # Get current scroll position (returns tuple, e.g., (0.0, 1.0))
            # top=0.0 means top is visible, bottom=1.0 means bottom is visible
            top, bottom = canvas.yview()
            
            # Determine scroll direction and magnitude
            scroll_dir = 0
            
            # Windows & macOS
            if hasattr(event, 'delta') and event.delta:
                if abs(event.delta) >= 120:
                    scroll_dir = int(-1 * (event.delta / 120))
                else:
                    scroll_dir = -1 if event.delta > 0 else 1
            
            # Linux (Button-4 is up, Button-5 is down)
            elif event.num == 4:
                scroll_dir = -1
            elif event.num == 5:
                scroll_dir = 1
            
            # --- BOUNDARY CHECK ---
            # If trying to scroll UP (dir < 0) but already at top (top <= 0), stop.
            if scroll_dir < 0 and top <= 0:
                return
            
            # If trying to scroll DOWN (dir > 0) but already at bottom (bottom >= 1), stop.
            if scroll_dir > 0 and bottom >= 1.0:
                return
                
            canvas.yview_scroll(scroll_dir, "units")

        def _bind_to_mousewheel(event):
            # Bind globally when mouse enters
            # "add=True" ensures we don't overwrite other bindings if they exist
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            # Unbind globally when mouse leaves
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        # Apply bindings
        scrollable_frame.bind('<Enter>', _bind_to_mousewheel)
        scrollable_frame.bind('<Leave>', _unbind_from_mousewheel)
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
    def _toggle_combobox_mode(self, event, widget):
        """Toggle between moving focus and selecting values."""
        widget.selection_active = not widget.selection_active
        
        if widget.selection_active:
            # Visually open the list ONLY when Enter is pressed
            widget.event_generate('<Down>')
        
        return "break"

    def _focus_next_widget(self, event):
        # The widget that triggered the event
        current = event.widget

        # If it's a combobox and we ARE in selection mode,
        # return None to let the default 'Down' behavior (scroll list) happen.
        if isinstance(current, ttk.Combobox) and getattr(current, 'selection_active', False):
            return None

        # Otherwise, move focus and return "break" to stop the menu from opening.
        try:
            target = current.tk_focusNext()
            target.focus_set()
            self._ensure_widget_visible(target)
        except:
            pass
        return "break"

    def _focus_prev_widget(self, event):
        current = event.widget

        if isinstance(current, ttk.Combobox) and getattr(current, 'selection_active', False):
            return None
            
        try:
            target = current.tk_focusPrev()
            target.focus_set()
            self._ensure_widget_visible(target)
        except:
            pass
        return "break"
        
    def _ensure_widget_visible(self, widget):
        """
        Robustly scrolls to ensure the widget is visible, handling deeply nested widgets.
        """
        # 1. Climb up to find the Scrollable Frame (immediate child of a Canvas)
        canvas = None
        scrollable_frame = None
        
        parent = widget.master
        while parent:
            # Check if this parent's master is a Canvas
            if isinstance(parent.master, tk.Canvas):
                scrollable_frame = parent
                canvas = parent.master
                break
            parent = parent.master
            
        # If we didn't find a canvas in the ancestry, stop.
        if not canvas:
            return

        # 2. Calculate the widget's position relative to the Top of the Scrollable Frame
        # We use winfo_rooty() (screen Y) to avoid issues with relative coordinates in nested frames.
        try:
            widget_offset_y = widget.winfo_rooty() - scrollable_frame.winfo_rooty()
        except TypeError:
            # Handle cases where widgets might not be fully mapped yet
            return

        widget_height = widget.winfo_height()
        frame_height = scrollable_frame.winfo_height()

        if frame_height == 0:
            return

        # 3. Calculate target fractions (0.0 to 1.0)
        pad = 20  # Add a little padding
        target_top = (widget_offset_y - pad) / frame_height
        target_bottom = (widget_offset_y + widget_height + pad) / frame_height

        # 4. Get current scroll position
        top_vis, bot_vis = canvas.yview()

        # 5. Scroll only if needed
        if target_top < top_vis:
            # Widget is above the view -> Align top
            canvas.yview_moveto(target_top)
        elif target_bottom > bot_vis:
            # Widget is below the view -> Align bottom
            view_height = bot_vis - top_vis
            canvas.yview_moveto(target_bottom - view_height)
    
    def load_subgroup_text(self, subgroup_name):
        """Load text from sginfo/<filename> if present in YAML subgroupinfo."""
        filename = self.subgroup_info.get(subgroup_name)
        if not filename:
            return f"No subgroup info available for {subgroup_name}"

        # Ensure extension
        if not filename.endswith(".txt"):
            filename = filename + ".txt"
        
        sginfo = self.sginfo
        path = Path(sginfo) / filename
        try:
            return path.read_text()
        except Exception:
            return f"Missing subgroup info file: {path}"
            
    def update_info_panel(self, subgroup, variable):
        """
        Update the right-hand info panel for the current tab with the subgroup text,
        and highlight occurrences of `variable` inside that text.
        """
        try:
            tab = self.notebook.nametowidget(self.notebook.select())
            info_panel = getattr(tab, "info_panel", None)
            count_label = getattr(tab, "match_count_label", None)
        except Exception: return

        if info_panel is None: return

        # Load subgroup filename from YAML mapping
        filename = self.subgroup_info.get(subgroup)
        sginfo = self.sginfo
        if filename and not filename.endswith(".txt"):
            filename = filename + ".txt"
        if filename:
            path = Path(sginfo) / filename
        else:
            path = Path(sginfo) / "_general.txt"
        #path = Path("sginfo") / (filename or "")

        if path.exists():
            try:
                text = path.read_text()
            except Exception as e:
                text = f"Error reading subgroup file {path}:\n{e}"
        else:
            text = f"No subgroup info found for '{subgroup}'.\nExpected: {path}"

        self.last_searched_var = variable
        self.search_indices = []

        info_panel.config(state="normal")
        info_panel.delete("1.0", tk.END)
        info_panel.insert("1.0", text)

        # 1. Configure Tags
        info_panel.tag_configure("highlight", background=self.highlight_background, foreground=self.highlight_foreground)
        info_panel.tag_configure("current_match", background="yellow", foreground="black", relief="solid", borderwidth=1)
        
        # 2. Set Priority (current_match > highlight)
        info_panel.tag_lower("highlight")
        info_panel.tag_raise("current_match")

        if self.highlight_enabled and variable:
            start = "1.0"
            while True:
                idx = info_panel.search(variable, start, nocase=True, stopindex=tk.END)
                if not idx: break
                end = f"{idx}+{len(variable)}c"
                info_panel.tag_add("highlight", idx, end)
                self.search_indices.append(idx)
                start = end
                
        # If highlighting is disabled, clear the search state and reset label
        if not self.highlight_enabled or not variable:
            self.search_indices = []
            self.current_search_index = -1
            if count_label:
                count_label.config(text="0 / 0")
            # (Optional: call navigate_search(0) to clear highlights)
            return

        # 3. Reset and Navigate
        if self.search_indices:
            self.current_search_index = 0
            self.navigate_search(0)
        else:
            self.current_search_index = -1
            if count_label: count_label.config(text="0 / 0")

        info_panel.config(state="disabled")
        
    def navigate_search(self, direction):
        """
        direction: 1 for next (Right), -1 for previous (Left), 0 to refresh
        """
        # 1. Get the current tab and its specific widgets
        try:
            tab_id = self.notebook.select()
            tab = self.notebook.nametowidget(tab_id)
            info_panel = getattr(tab, "info_panel", None)
            count_label = getattr(tab, "match_count_label", None)
        except Exception:
            return "break"

        # 2. Handle cases where no matches exist or feature is disabled
        if not hasattr(self, 'search_indices') or not self.search_indices or not getattr(self, 'last_searched_var', None):
            if count_label:
                count_label.config(text="0 / 0")
            return "break"

        # 3. Update current index with wrap-around logic
        self.current_search_index += direction
        if self.current_search_index >= len(self.search_indices):
            self.current_search_index = 0
        elif self.current_search_index < 0:
            self.current_search_index = len(self.search_indices) - 1
            
        # Update the correct label
        if count_label:
            count_label.config(text=f"{self.current_search_index + 1} / {len(self.search_indices)}")

        # 4. Perform Visual Updates
        target_idx = self.search_indices[self.current_search_index]
        var_len = len(self.last_searched_var)
        end_idx = f"{target_idx}+{var_len}c"

        info_panel.config(state="normal")
        
        # Remove previous active highlight and apply new one
        info_panel.tag_remove("current_match", "1.0", tk.END)
        info_panel.tag_add("current_match", target_idx, end_idx)
        
        # Ensure current_match is visible above the standard highlight
        info_panel.tag_raise("current_match")
        
        # Scroll the text widget to the found instance
        info_panel.see(target_idx)
        
        info_panel.config(state="disabled")
        
        # Returning "break" prevents the default behavior (moving the text cursor)
        return "break"
        
    def _switch_tab(self, direction):
        """
        direction: 1 for right, -1 for left
        """
        num_tabs = self.notebook.index("end")
        if num_tabs <= 1:
            return "break"

        current_idx = self.notebook.index(self.notebook.select())
        new_idx = (current_idx + direction) % num_tabs
        
        # 1. Switch the tab
        self.notebook.select(new_idx)
        
        # 2. FORCE REFRESH: This fixes the "no-load until mouse move" issue
        self.update_idletasks()
        
        # 3. Set focus so arrow keys work immediately
        # We use a slight delay to ensure the focus engine is ready for the new tab
        self.after(50, self._focus_first_widget_in_tab)
        
        return "break"

    def _focus_first_widget_in_tab(self):
        """Finds the first variable widget in the current tab and focuses it."""
        for var_name, winfo in self.widgets.items():
            w = winfo.get('widget')
            if w and w.winfo_ismapped():
                w.focus_set()
                break
            
    def on_tab_changed(self, event):
        """Called when notebook tab changes; initialize the right info panel for the new tab."""
        # Force the tab to render its children so winfo_ismapped() works correctly
        self.update_idletasks()
    
        try:
            tab = self.notebook.nametowidget(self.notebook.select())
        except Exception:
            return

        info_panel = getattr(tab, "info_panel", None)
        if info_panel is None:
            return

        # Find the first visible variable widget in this tab and use it to initialize info panel
        for var_name, winfo in self.widgets.items():
            w = winfo.get('widget')
            if not w:
                continue
            # winfo_ismapped is True for widgets that are currently packed/gridded in visible tab
            if w.winfo_ismapped():
                sg = self.var_to_subgroup.get(var_name, "_general")
                self.update_info_panel(sg, var_name)
                return

        # fallback: clear panel
        info_panel.config(state="normal")
        info_panel.delete("1.0", tk.END)
        info_panel.config(state="disabled")

    # --- Set/Get Widget Value Functions ---

    def apply_defaults(self):
        """Populate widgets with default values from YAML."""
        groups = self.config.get('namelist_groups', {})
        for g_name, g_data in groups.items():
            for v_name, v_data in g_data.get('variables', {}).items():
                if v_name in self.widgets:
                    options = v_data.get('options')
                    if options: default = v_data.get('default')
                    else: default = ""
                    #default = v_data.get('default')
                    self.set_widget_value(v_name, default)

    def set_widget_value(self, var_name, value):
        """Helper to safely set value to widget."""
        if var_name not in self.widgets:
            return
            
        widget_info = self.widgets[var_name]
        widget = widget_info['widget']
        
        if value is None:
            value = ""
        
        if isinstance(widget, ttk.Combobox): # If options
            # Try to find the text
            widget_values = widget['values']
            if isinstance(widget_values, tuple):
                widget_values = list(widget_values)
            
            if hasattr(widget, 'option_keys'):
                # Using dict options
                if str(value) in widget.option_keys:
                    index = widget.option_keys.index(str(value))
                    widget.current(index)
                else:
                    # Try to match display value
                    for i, display_val in enumerate(widget['values']):
                        if str(value) in display_val:
                            widget.current(i)
                            break
            else:
                # List options
                if str(value) in widget_values:
                    widget.set(str(value))
                else:
                    # Try partial match
                    for val in widget_values:
                        if str(value) in val:
                            widget.set(val)
                            break
        
        elif isinstance(widget, ttk.Entry): # If no options
            widget.delete(0, tk.END)
            if isinstance(value, list):
            
                #text = ", ".join(map(str, value))
                text = str(value)
                widget.insert(0, text[1:-1])
            else:
                widget.insert(0, str(value))
            
            # Update placeholder appearance
            #if not str(value) and "array" in widget_info['data'].get('type', ''):
                #widget.configure(foreground='grey')
                #widget.insert(0, "e.g. 1.0, 2.0, 3.0")
            #else:
                #widget.configure(foreground='black')

    def get_widget_value(self, var_name):
        """Helper to get value from widget in correct type."""
        if var_name not in self.widgets:
            return None
            
        widget_info = self.widgets[var_name]
        widget = widget_info['widget']
        var_type = widget_info['data'].get('type', 'string')
        
        #val = None
        val = widget.get()
        if isinstance(widget, ttk.Combobox): # If options
            #val = widget.get()
            # Remove label description if present "[0] description" -> "0"
            if val and ':' in val:
                # Check if we have option_keys stored
                if hasattr(widget, 'option_keys'):
                    index = widget.current()
                    if index >= 0 and index < len(widget.option_keys):
                        val = widget.option_keys[index]
                else:
                    # Fallback: try to extract key
                    parts = val.split(':')
                    if parts:
                        val = parts[0].strip()
        #else: # If no options
            #val = widget.get()
            # Check if it's placeholder text
            #if val == "e.g. 1.0, 2.0, 3.0":
            #    val = ""
        
        # Check if value is empty/blank
        if val is None or (isinstance(val, str) and not val.strip()):
            return None
        
        # Type conversion
        try:
            if 'integer' in var_type and 'array' not in var_type: # type = integer
                return int(val)
            elif 'float' in var_type and 'array' not in var_type: # type = float
                return float(val)
            elif 'complex' in var_type and 'array' not in var_type: # type = complex
                return complex(val)
            elif 'string' in var_type and 'array' not in var_type: # type = string
                return str(val)
            elif 'array' in var_type:
                #return json.loads(val)
                # Basic csv parsing
                if not val or not val.strip():
                    return None  # Return None for empty arrays
                parts = [x.strip() for x in val.split(',')]
                # Filter out empty strings
                parts = [p for p in parts if p]
                if not parts:  # If all parts were empty
                    return None
                if 'integer' in var_type:
                    return [int(p) for p in parts] # type = integer_array
                elif 'float' in var_type:
                    return [float(p) for p in parts] # type = float_array
                elif 'complex' in var_type:
                    return [complex(p) for p in parts] # type = complex_array
                elif 'string' in var_type:
                    #return [str(p) for p in parts] # type = string_array
                    #val = [f.strip() for f in val.split(',')]
                    return ast.literal_eval('['+val+']') # type = string_array
                #return parts
            return [str(val)]
        except ValueError:
            try:
                return json.loads('['+val+']') # try json conversion
            except ValueError:
                try:
                    return ast.literal_eval('['+val+']') # try ast conversion
                except ValueError:
                    return val # Return raw string if conversion fails
                    
                    
    # --- Dependency Enforcement Functions ---

    def trigger_dependency_check(self):
        """Evaluates show/hide rules defined in YAML."""
        
        if self._debounce_timer is not None:
            self.after_cancel(self._debounce_timer)
        
        # 2. Schedule the ACTUAL check to run in 50ms
        # This acts as a buffer. If 10 events come in within 50ms,
        # only the last one will trigger the layout update.
        self._debounce_timer = self.after(50, self.execute_dependency_check)
        
    def execute_dependency_check(self):
        """
        The actual logic that was previously in trigger_dependency_check.
        Runs only after the user stops interacting for 50ms.
        """
        self._debounce_timer = None # Reset timer ID
        
        # Safety: If window was closed during the 50ms wait
        try:
            if not self.winfo_exists(): return
        except Exception:
            return
        
        rules = self.config.get('gui_configuration', {}).get('dependency_triggers', {}).get('show_hide_rules', [])
        
        for rule in rules:
            condition = rule.get('if')
            if not condition: continue
            
            # Evaluate condition
            is_met = self.evaluate_condition(condition)
            
            # Apply Actions
            if is_met:
                self.process_actions(rule.get('show'), True)
                self.process_actions(rule.get('hide'), False)
                
                # 'set' action
                set_actions = rule.get('set', [])
                for action in set_actions:
                    self.execute_assignment(action)
                
            else:
                # If condition NOT met, reverse show/hide
                self.process_actions(rule.get('show'), False)
                self.process_actions(rule.get('hide'), True)
                
        self.update_subgroup_visibility()

    def update_subgroup_visibility(self):
        """
        Smart Update: Checks if changes are actually needed before touching the GUI.
        Eliminates flickering when typing or editing values that don't alter layout.
        """
        if not hasattr(self, 'subgroup_tracking'):
            return

        for parent_gb, subgroups in self.subgroup_tracking.items():
            
            # --- STEP 1: CALCULATE DESIRED STATE ---
            # We determine which subgroups SHOULD be visible right now.
            desired_visible_frames = []
            
            for name, frame in subgroups:
                # Check if any children are managed (visible) rows
                children = frame.winfo_children()
                has_visible_children = False
                for child in children:
                    if child.grid_info(): # If child has grid info, it is visible
                        has_visible_children = True
                        break
                
                if has_visible_children:
                    desired_visible_frames.append(frame)

            # --- STEP 2: CHECK CURRENT STATE ---
            # We look at what is ACTUALLY packed in the GUI right now.
            # parent_gb.pack_slaves() returns widgets in their visual order.
            
            # Filter slaves to only include the subgroups we are tracking
            # (ignores tooltips or other labels inside the group box)
            known_subgroups_set = {frame for name, frame in subgroups}
            current_visible_frames = [
                w for w in parent_gb.pack_slaves()
                if w in known_subgroups_set
            ]

            # --- STEP 3: COMPARE AND ACT ---
            # If the lists are identical, the GUI is already perfect. DO NOTHING.
            if desired_visible_frames == current_visible_frames:
                continue

            # If we reach here, the layout is wrong.
            # NOW we perform the "Unpack/Repack" to fix it.
            
            # 1. Hide all known subgroups (Reset)
            for name, frame in subgroups:
                frame.pack_forget()

            # 2. Show only the ones that should be visible (in correct order)
            for name, frame in subgroups:
                if frame in desired_visible_frames:
                    frame.pack(fill='x', padx=5, pady=5)
                
    def evaluate_condition(self, condition_str):
        """
        Recursive safe evaluator.
        Handles 'or', 'and', and basic comparisons (==, !=, >, <, >=, <=).
        """
        condition_str = condition_str.strip()

        # --- 1. Handle logical OR (Lowest Precedence) ---
        # If any part is true, the whole thing is true.
        if ' or ' in condition_str:
            parts = condition_str.split(' or ')
            return any(self.evaluate_condition(p) for p in parts)

        # --- 2. Handle logical AND (Higher Precedence) ---
        # All parts must be true.
        if ' and ' in condition_str:
            parts = condition_str.split(' and ')
            return all(self.evaluate_condition(p) for p in parts)

        # --- 3. Base Case: Single Comparison (Your existing logic) ---
        try:
            # Note: Order matters! Check >= and <= before > and < to avoid partial matches
            ops = ["==", "!=", ">=", "<=", ">", "<"]
            op = None
            for o in ops:
                if o in condition_str:
                    op = o
                    break
            
            if not op: return False

            lhs, rhs = condition_str.split(op, 1) # Split only on the first occurrence
            lhs = lhs.strip()
            rhs = rhs.strip().strip("'").strip('"')

            current_val = self.get_widget_value(lhs)
            
            # Handle None values gracefully
            if current_val is None:
                current_val_str = ""
            else:
                current_val_str = str(current_val)
            
            # String comparisons
            if op == "==": return current_val_str == rhs
            if op == "!=": return current_val_str != rhs
            
            # Numeric comparisons
            try:
                n_lhs = float(current_val) if current_val is not None else 0.0
                n_rhs = float(rhs)
                
                if op == ">": return n_lhs > n_rhs
                if op == "<": return n_lhs < n_rhs
                if op == ">=": return n_lhs >= n_rhs
                if op == "<=": return n_lhs <= n_rhs
            except (ValueError, TypeError):
                return False

        except Exception:
            return False
            
        return False

    def process_actions(self, targets, visible):
        if not targets:
            return
        if isinstance(targets, str):
            targets = [targets]
        
        for var_name in targets:
            if var_name in self.form_rows:
                row_info = self.form_rows[var_name]
                frame = row_info['frame']
                layout_method = row_info['layout_method']
                
                if visible:
                    if var_name in self.invisible:
                        self.invisible.remove(var_name)
                    if layout_method == 'grid':
                        frame.grid(row=row_info['row_index'], column=0, sticky='ew', padx=5, pady=2)
                    else:  # pack
                        frame.pack(fill=tk.X, padx=5, pady=2, anchor='w')
                else:
                    if var_name not in self.invisible:
                        self.invisible.append(var_name)
                    if layout_method == 'grid':
                        frame.grid_remove()
                    else:  # pack
                        frame.pack_forget()

    def execute_assignment(self, assign_str):
        """Handle set: ['symtrap = disabled']"""
        if "=" not in assign_str:
            return
        lhs, rhs = assign_str.split('=')
        lhs = lhs.strip()
        rhs = rhs.strip().strip("'").strip('"')
        self.set_widget_value(lhs, rhs)

    # --- Helper Functions to load, save, and update json configuration file ---
        
    def load_jconfig(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                #print(f"Loaded configuration from {self.config_file}")
                return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
        return {}  # Return empty dict, not None
    
    def save_jconfig(self):
        """Save configuration to file"""
        try:
            # Load existing config first to preserve values we're not currently updating
            existing_config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as f:
                        existing_config = json.load(f)
                except:
                    existing_config = {}
            
            # Update only the values we want to change
            config = existing_config.copy()  # Start with existing config
            
            # Only update executable_path if it's not None
            if self.executable_path is not None:
                config['executable_path'] = self.executable_path
            
            # Only update last_namelist if it's not None
            if self.current_file is not None:
                config['last_namelist'] = self.current_file
                
            # Only update last_aux_file if it's not None
            if self.additional_files is not None:
                config['last_aux_file'] = self.additional_files
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            #print(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def update_jconfig(self, key, value):
        """Update a specific configuration value"""
        if not hasattr(self, 'jconfig'):
            self.jconfig = {}
        
        self.jconfig[key] = value
        self.save_jconfig()

    # --- I/O Functions ---
    
    def aux_file_folder(self):
        #Load Namelist
        initial_dir = None
        if self.additional_files:
            initial_dir = Path(self.additional_files)
            
        # Open the directory selection dialog
        folder_path = filedialog.askdirectory(
        title="Choose Auxiliary File Folder",
        initialdir=initial_dir,
        mustexist=True # Ensures the user cannot type a non-existent folder
        )

        # Check if the user cancelled
        if not folder_path:
            return

        # Update variable and config
        self.additional_files = folder_path
        self.update_jconfig('last_aux_file', folder_path)

    def import_namelist(self):
        #Load Namelist
        initial_dir = None#
        if self.current_file:
            initial_dir = Path(self.current_file)
               
            fname = filedialog.askopenfilename(
                    title="Open Namelist",
                    initialdir = initial_dir.parent,
                    initialfile = initial_dir.suffix
                    #filetypes=[("Namelist Files", "*.nml *.txt"), ("All Files", "*.*")]
                )
        else:
            fname = filedialog.askopenfilename(title="Open Namelist")
        if not fname:
            return
        self.current_file = fname
        self.update_jconfig('last_namelist', fname)
        
        fname1 = fname+'.tmp'
        self.patch_cqlinput(fname,fname1)
        
        self.apply_defaults()
        
        #Try reading namelist with f90nml package
        try:
            nml = f90nml.read(fname1)
            os.remove(fname1)
            
            nml_dict = nml.todict()
            nml1 = {} # Initialize dict
            start_ind = {} # Initialize dict
            vars_greater_than_1 = {}
            
            for group, content in nml_dict.items():
                if group not in start_ind: start_ind[group] = {}  # Initialize group
                if group not in nml1: nml1[group] = {}  # Initialize group
                for key, val in content.items():
                    if key == '_start_index':
                        start_ind[group][key] = val
                        for var_name, index in val.items():
                            if any(x > 1 for x in index):
                                vars_greater_than_1[var_name] = index[0]
                    else:
                        nml1[group][key] = val
                        
            self.start_ind = self.start_ind | start_ind
            
            def deep_prepend(structure, value):
                # Check if this is the bottom level (a list, but its contents are NOT lists)
                # We check structure[0] to see if the first item is a list or a number
                if isinstance(structure, list) and structure and not isinstance(structure[0], list):
                    return value + structure
                
                # If it's still a list of lists, recurse deeper
                if isinstance(structure, list):
                    return [deep_prepend(item, value) for item in structure]
                
                return structure
            
            # Flatten structure slightly for mapping
            for group, content in nml1.items():
                for key, val in content.items():
                    if key in self.widgets:
                        if key in vars_greater_than_1:
                            try:
                                default = self.config['namelist_groups'][group]['variables'][key]['default']
                            except Exception:
                                default = 0
                            if not isinstance(default,list): default = [default]
                            if len(default)<vars_greater_than_1[key]-1:
                                if len(default)>0: defval = default[0]
                                else: defval = 0
                            else: defval = default[0:vars_greater_than_1[key]-1]
                            val = deep_prepend(val,defval)
                            start_ind[group]['_start_index'][key][0]=1
                            #default = self.config['namelist_groups'][group]['variables'][key]]['default']
                            #for i in range(vars_greater_than_1[key]-1):
                                
                        self.set_widget_value(key, val)
            
            self.after(10, self.trigger_dependency_check)
            
            nc_filepath = Path(self.get_nc_filename())
            if nc_filepath.is_file(): self.plot_btn.config(state="normal")
            
            messagebox.showinfo("Success", f"Loaded {fname}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not read namelist:\n{e}")

    def export_namelist(self):
        initial_dir = None
        if self.current_file:
            initial_dir = Path(self.current_file)
               
            fname = filedialog.asksaveasfilename(
                    title="Save Namelist",
                    initialdir = initial_dir.parent,
                    initialfile = initial_dir.suffix
                    #filetypes=[("Namelist Files", "*.nml *.txt"), ("All Files", "*.*")]
                )
        else:
            fname = filedialog.asksaveasfilename(title="Save Namelist")
        
        if not fname: return
        
        self.current_file = fname
        self.update_jconfig('last_namelist', fname)
        try:
            self.write_namelist(fname)
            messagebox.showinfo("Success", f"Saved to {fname}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not write namelist:\n{e}")

    def write_namelist(self, fname):
        self.trigger_dependency_check()
        output_nml = {}
        
        for var_name, info in self.widgets.items():
            
            # If variable is invisible, skip it
            #if var_name in self.invisible:
            #    continue
                
            # --- Standard processing continues below ---
            group = info['group']
            val = self.get_widget_value(var_name)

            if val is None:
                continue
            if isinstance(val, list) and len(val) == 0:
                continue
            if isinstance(val, str) and not val.strip():
                continue

            if group not in output_nml:
                output_nml[group] = {}

            output_nml[group][var_name] = val

        # Merge values and start indices
        start_ind = self.start_ind
        nml2 = {}
        for group, content in output_nml.items():
            nml2[group] = output_nml[group] | start_ind.get(group, {})

        gorder = self.gorder
        nml2 = {key: nml2[key] for key in gorder if key in nml2}
        nml2 = OrderedDict(nml2)

        f90nml.write(nml2, fname, force=True)
        with open(fname, 'a') as f:
            f.write("end\n")
            f.write("end\n")
            f.write("end\n")
            f.write("LEAVE\n")
            f.write("THESE\n")
            f.write("HERE!\n")
            
    def patch_cqlinput(self, input_file, output_file):
        with open(input_file, 'r') as f:
            content = f.read()

        # Regex to find "var(digits) ="
        # Capture 1: Var name
        # Capture 2: Indices content (e.g. "1" or "1, 2")
        pattern = re.compile(r'(\b[a-zA-Z0-9_]+)\s*\(\s*(\d+(?:\s*,\s*\d+)*)\s*\)\s*=', re.MULTILINE)
        
        def count_values(value_string):
            """
            Parses a Fortran value string to count the number of elements.
            """
            # Remove comments
            lines = value_string.splitlines()
            clean_lines = []
            for line in lines:
                if '!' in line:
                    line = line.split('!')[0]
                clean_lines.append(line)
            
            full_str = " ".join(clean_lines).strip()
            
            if not full_str:
                return 0

            # Regex tokens: Strings, Multipliers (51*), or Values
            token_pattern = re.compile(r"""
                '[^']*' |        # Single quoted string
                "[^"]*" |        # Double quoted string
                \b\d+\*[^\s,]* | # Multiplier (e.g. 50*1.0 or 50*)
                [^,\s]+          # Normal value (numbers, scientific notation, bools)
            """, re.VERBOSE)
            
            tokens = token_pattern.findall(full_str)
            
            count = 0
            for token in tokens:
                # Check for multipliers like 5*1.0
                if '*' in token and not (token.startswith("'") or token.startswith('"')):
                    try:
                        parts = token.split('*')
                        if parts[0]:
                            multiplier = int(parts[0])
                            count += multiplier
                        else:
                            count += 1
                    except ValueError:
                        count += 1
                else:
                    count += 1
                    
            return count

        def replacement_function(match):
            var_name = match.group(1) # Case sensitive preservation
            indices_str = match.group(2)
            start_pos = match.end()

            # Note: We REMOVED the "if var_name in target_vars" check.
            # Now it applies to ANY variable with indices and multiple values.

            remainder = content[start_pos:]
            
            # IMPROVED Regex for finding the end of the current assignment.
            # 1. strictly looks for a variable name starting with a LETTER to avoid
            #    matching scientific notation like "7.75e+06" as a variable.
            # 2. Looks for &end or / (namelist terminators)
            next_assign_match = re.search(r'\b[a-zA-Z][a-zA-Z0-9_]*\s*(\([^)]*\))?\s*=|&end|/', remainder)
            
            if next_assign_match:
                rhs_chunk = remainder[:next_assign_match.start()]
            else:
                rhs_chunk = remainder

            n_values = count_values(rhs_chunk)

            # If only 1 value, keep as is (e.g. A(1)=0.5 is fine)
            if n_values <= 1:
                return match.group(0)

            # Logic to construct new indices
            dims = [x.strip() for x in indices_str.split(',')]
            
            # Fortran is column-major, but usually we fill the FIRST dimension
            # when providing a list of numbers.
            first_dim_val = int(dims[0])
            end_dim_val = first_dim_val + n_values - 1
            
            # Update the first dimension to be a range
            dims[0] = f"{first_dim_val}:{end_dim_val}"
            
            # Join back: "1,1" -> "1:100,1"
            new_indices = ",".join(dims)

            return f"{var_name}({new_indices})="

        new_content = pattern.sub(replacement_function, content)

        with open(output_file, 'w') as f:
            f.write(new_content)
            
            
    # --- CQL3D Execution Functions ---

    def load_executable(self):
        """Load a CQL3D executable file."""
        initial_dir = None
        if self.executable_path:
           initial_dir = os.path.dirname(self.executable_path)
           
        fname = filedialog.askopenfilename(
            title="Select CQL3D Executable",
            initialdir=initial_dir
            #filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        
        if not fname:
            return
        
        # Check if file exists and is executable
        if not os.path.exists(fname):
            messagebox.showerror("Error", f"File does not exist: {fname}")
            return
        
        # On Unix-like systems, check if file is executable
        if os.name != 'nt':  # Not Windows
            if not os.access(fname, os.X_OK):
                messagebox.showwarning("Warning", f"File may not be executable: {fname}")
        
        self.executable_path = fname
        self.update_jconfig('executable_path', fname)
        self.exec_path_label.config(text=f"Loaded: {os.path.basename(fname)}")
        self.run_btn.config(state="normal")
        messagebox.showinfo("Success", f"CQL3D executable loaded: {fname}")

    def _stage_file(self, filename, run_folder, target_name=None):
        """
        Helper to link or copy a required file into the run folder.
        Searches in self.additional_files first, then current working directory.
        """
        if not filename:
            return

        # If no target name is provided, use the original filename
        if target_name is None:
            target_name = os.path.basename(filename)

        # Determine the source directory
        # Priority: 1. Absolute Path provided, 2. self.additional_files, 3. os.getcwd()
        if os.path.isabs(filename):
            src_path = filename
        else:
            search_dir = os.getcwd() # Default
            if hasattr(self, 'additional_files') and self.additional_files:
                if os.path.exists(self.additional_files):
                    search_dir = self.additional_files
            
            src_path = os.path.join(search_dir, filename)

        # Destination path inside the run folder
        dst_path = os.path.join(run_folder, target_name)

        # Check existence
        if not os.path.exists(src_path):
            #print(f"Warning: Required auxiliary file not found: {src_path}")
            return # Or raise error/messagebox depending on strictness

        # Clean slate: Remove existing destination file/link
        if os.path.exists(dst_path) or os.path.islink(dst_path):
            try:
                os.remove(dst_path)
            except OSError:
                pass

        # Link or Copy
        try:
            os.symlink(src_path, dst_path)
        except OSError:
            try:
                shutil.copy2(src_path, dst_path)
            except Exception as e:
                print(f"Error staging file {filename}: {e}")

    def run_cql3d(self):
        """Create a new run folder, save input there, stage aux files, and run CQL3D."""
        if not self.executable_path:
            messagebox.showerror("Error", "No CQL3D executable loaded.")
            return

        exe_abs_path = os.path.abspath(self.executable_path)
        
        if not os.path.exists(exe_abs_path):
            messagebox.showerror("Error", f"Executable not found: {exe_abs_path}")
            return

        # --- PHASE 1: Prepare Folder and Input Files ---
        
        # 1. Create a unique directory for this run
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_folder = os.path.join(self.folder_dir, "runs", f"run_{timestamp}")
        
        try:
            os.makedirs(run_folder, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Error", f"Could not create run directory:\n{e}")
            return

        # 2. Save 'cqlinput' INSIDE the new folder
        output_file_path = os.path.join(run_folder, "cqlinput")
        self.write_namelist(output_file_path)

        # --- PHASE 2: Stage Auxiliary Files ---
        # Based on namelist settings, move required files into the run folder.

        # A. Equilibrium Files
        eqmod = self.get_widget_value('eqmod')
        if eqmod == 'enabled':
            eqsource = self.get_widget_value('eqsource')
            
            if eqsource == 'eqdsk':
                # Default filename is 'eqdsk' unless 'eqdskin' is specified [cite: 1081]
                eqdskin = self.get_widget_value('eqdskin') or 'eqdsk'
                self._stage_file(eqdskin, run_folder)
                
            elif eqsource == 'tsc':
                # TSC requires 'tscinp' [cite: 1090]
                self._stage_file('tscinp', run_folder)
                
            elif eqsource == 'topeol':
                # Topeol requires 'topeol' file [cite: 1082]
                self._stage_file('topeol', run_folder)

        # B. Restart Files
        nlrestrt = self.get_widget_value('nlrestrt')
        if nlrestrt == 'enabled':
            # Requires text file 'distrfunc' [cite: 51]
            self._stage_file('distrfunc', run_folder)
        elif nlrestrt in ['ncdfdist', 'ncregrid']:
            # Requires netcdf file 'distrfunc.nc' [cite: 53, 59]
            # Note: Often users have a mnemonic.nc, but code looks for distrfunc.nc
            # You might need logic to ask user for the specific source file,
            # here we assume a file named 'distrfunc.nc' exists in source dir.
            self._stage_file('distrfunc.nc', run_folder)

        # C. Initial Distribution (FPLD)
        # Check for fpld_dsk requirement (if fpld array has -1 or -2) [cite: 341]
        fpld_vals = self.get_widget_value('fpld')
        # Assuming fpld_vals returns a list or can be checked for presence of -1/-2
        if fpld_vals:
            # Simple check if any value triggers the file requirement
            if any(str(v) in ['-1.0', '-2.0', '-1', '-2'] for v in str(fpld_vals).split(',')):
                 self._stage_file('fpld_dsk', run_folder)

        # D. RF / Ray Tracing Files
        if self.get_widget_value('urfmod') == 'enabled':
            # A. Explicit file list (e.g., netcdf files)
            rffile_val = self.get_widget_value('rffile')
            
            if rffile_val:
                files = []
                # Case 1: It's already a list (what caused your error)
                if isinstance(rffile_val, list):
                    files = [str(f).strip() for f in rffile_val if str(f).strip()]
                
                # Case 2: It's a string (e.g., "file1.nc, file2.nc")
                elif isinstance(rffile_val, str):
                    files = [f.strip() for f in rffile_val.split(',') if f.strip()]

                # Stage the files
                for f in files:
                    self._stage_file(f, run_folder)
            
            # B. Legacy text files
            if self.get_widget_value('ech') == 'enabled':
                self._stage_file('rayech', run_folder)
            if self.get_widget_value('lh') == 'enabled':
                self._stage_file('raylh', run_folder)
            if self.get_widget_value('fw') == 'enabled':
                self._stage_file('rayfw', run_folder)

        # E. External Diffusion Coefficients [cite: 1195, 1204]
        rdcmod = self.get_widget_value('rdcmod')
        if rdcmod in ['format1', 'aorsa']:
            rdcfile = self.get_widget_value('rdcfile') or 'du0u0_input'
            self._stage_file(rdcfile, run_folder)
        elif rdcmod == 'format2':
            # Requires multiple files, usually handled by user ensuring they exist,
            # but we can try to stage the base ones if known.
            self._stage_file('du0u0_grid', run_folder)
            # Note: Format2 also requires du0u0_rnnn files which are dynamic.

        # F. Loss Cone File [cite: 645]
        # lossmode is an array, check if any entry is 'frm_file'
        lossmode_vals = self.get_widget_value('lossmode')
        if lossmode_vals and 'frm_file' in str(lossmode_vals):
             lossfile = self.get_widget_value('lossfile') or 'prompt_loss.txt'
             self._stage_file(lossfile, run_folder)
             
        # G. PGPLOT grfont.dat
        self._stage_file('grfont.dat', run_folder)

        # --- PHASE 3: Start Background Thread ---
        
        self.plot_btn.config(state="disabled")
        self.run_btn.config(state="disabled")
        self.progress.pack(side=tk.RIGHT, padx=10)
        self.progress.start(10)

        self.current_run_folder = run_folder

        thread = threading.Thread(
            target=self._run_subprocess_thread,
            args=(exe_abs_path, run_folder)
        )
        thread.daemon = True
        thread.start()


    def _run_subprocess_thread(self, exe_path, run_folder):
        """Runs the subprocess inside the specific run folder."""
        try:
            process = subprocess.Popen(
                [exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                cwd=run_folder  # <--- Crucial: Runs inside the new folder
            )
            
            stdout, stderr = process.communicate()
            
            # Pass run_folder back to the finished handler
            self.plot_btn.after(0, self._on_cql3d_finished, stdout, stderr, process.returncode, None, run_folder)
            
        except Exception as e:
            self.plot_btn.after(0, self._on_cql3d_finished, None, None, None, e, run_folder)

    def _on_cql3d_finished(self, stdout, stderr, returncode, exception, run_folder):
        """Clean up UI and show results."""
        
        self.progress.stop()
        self.progress.pack_forget()
        self.run_btn.config(state="normal")
        
        if exception:
            messagebox.showerror("Error", f"Error running CQL3D:\n{exception}")
            return

        # Check for NC file INSIDE the run folder
        # self.get_nc_filename() likely returns just "cql3d.nc" or similar
        nc_filename = self.get_nc_filename()
        nc_filepath = os.path.join(run_folder, nc_filename)
        
        if os.path.isfile(nc_filepath):
            self.plot_btn.config(state="normal")
            # OPTIONAL: Save this full path so your Plot button knows exactly what to open
            self.last_successful_nc_path = nc_filepath
        
        self.show_execution_output(stdout, stderr, returncode)
        
    def show_execution_output(self, stdout, stderr, returncode):
        """Show execution output in a window"""
        output_window = tk.Toplevel(self)
        output_window.title("CQL3D Execution Output")
        output_window.geometry("800x600")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(output_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Stdout tab
        stdout_frame = ttk.Frame(notebook)
        notebook.add(stdout_frame, text="Standard Output")
        
        stdout_text = scrolledtext.ScrolledText(stdout_frame, wrap=tk.WORD, font=("Courier", 10))
        stdout_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        stdout_text.insert(tk.END, stdout if stdout else "No output")
        
        # Stderr tab
        stderr_frame = ttk.Frame(notebook)
        notebook.add(stderr_frame, text="Standard Error")
        
        stderr_text = scrolledtext.ScrolledText(stderr_frame, wrap=tk.WORD, font=("Courier", 10))
        stderr_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        stderr_text.insert(tk.END, stderr if stderr else "No errors")
        
        # Status information at the bottom
        status_frame = ttk.Frame(output_window)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Return code display
        if returncode == 0:
            status_text = f"Execution completed successfully (return code: {returncode})"
            status_color = "green"
            #self.status_var.set("CQL3D completed successfully")
        else:
            status_text = f"Execution failed (return code: {returncode})"
            status_color = "red"
            #self.status_var.set("CQL3D execution failed")
        
        status_label = ttk.Label(status_frame, text=status_text, foreground=status_color)
        status_label.pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Save Output",
                  command=lambda: self.save_output_to_file(stdout, stderr)).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Close",
                  command=output_window.destroy).pack(side=tk.LEFT, padx=2)

    def save_output_to_file(self, stdout, stderr):
        """Save execution output to a file"""
        filename = filedialog.asksaveasfilename(
            title="Save Output As"
            #defaultextension=".txt",
            #filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("=== CQL3D Standard Output ===\n")
                    f.write(stdout if stdout else "No output\n")
                    f.write("\n=== CQL3D Standard Error ===\n")
                    f.write(stderr if stderr else "No errors\n")
                
                messagebox.showinfo("Saved", f"Output saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save output:\n{str(e)}")
                
    # --- Plot Results Functions ---
    
    def get_nc_filename(self):
        """Get the .nc filename from mnemonic in Setup0"""
        try:
            var_name = 'mnemonic'
            mnemonic = self.get_widget_value(var_name)
            
            # Remove quotes if present
            if mnemonic.startswith("'") and mnemonic.endswith("'"):
                mnemonic = mnemonic[1:-1]
            
            return f"{mnemonic}.nc"
        except:
            return "cql3d.nc"

    def plot_results(self):
        """Plot NetCDF file from output."""
        # 1. Try to get the path from the last run
        # getattr(obj, name, default) prevents a crash if the variable doesn't exist yet
        nc_file = getattr(self, 'last_successful_nc_path', None)

        # 2. Fallback: If no recent run, check the current directory (legacy/restart behavior)
        if not nc_file or not os.path.exists(nc_file):
            nc_fn = self.get_nc_filename()
            nc_file = os.path.join(os.getcwd(), nc_fn)

        # 3. Final check before launching plotter
        if os.path.exists(nc_file):
            root = tk.Toplevel()
            app = CQL3DPlotterApp(root, nc_file)
            # Note: You generally don't need root.mainloop() for a Toplevel window
            # if your main app is already running a mainloop.
        else:
            root = tk.Toplevel()
            app = CQL3DPlotterApp(root, None)
            #messagebox.showerror("Error", f"Could not find output file:\n{nc_file}")
        
        
class CQL3DPlotterApp:
    def __init__(self, root, nc_file):
        self.root = root
        self.root.title("CQL3D NetCDF Plotter")
        self.root.geometry("1200x900")

        # --- Data Storage ---
        self.nc_data = None
        self.filename = nc_file
        
        # --- Default Parameters ---
        self.params = {
            'time_step': tk.IntVar(value=-1), # -1 means last step
            'rho_min': tk.DoubleVar(value=0.0),
            'rho_max': tk.DoubleVar(value=1.0),
            'species_index': tk.IntVar(value=0), # 0-based index
            'radial_start': tk.IntVar(value=0),  # Range Start
            'radial_end': tk.IntVar(value=0),    # Range End
            'plot_type': tk.StringVar(value='contour'), # 'contour' or 'mesh'
            'plot_trapped_boundaries': tk.BooleanVar(value=True),
            'log_scale': tk.BooleanVar(value=True),
            'use_latex': tk.BooleanVar(value=False),
            'ucmx_scale': tk.DoubleVar(value=1.0), # Momentum limit
        }

        # --- Constants ---
        self.clight = 2.99792458e10
        self.ergtkev = 1.6022e-09
        
        if nc_file is not None:
            self.nc_data = Dataset(self.filename, 'r', format='NETCDF4')

        self._init_ui()

    def _init_ui(self):
        # Top Frame: File Loading (Top of the entire window)
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        btn_load = ttk.Button(top_frame, text="Load .nc File", command=self.load_file)
        btn_load.pack(side=tk.LEFT, padx=5)
        
        self.lbl_file = ttk.Label(top_frame, text="No file loaded")
        self.lbl_file.pack(side=tk.LEFT, padx=10)

        # Main Layout: Left Control Panel, Right Plot Area
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Left Panel: Controls ---
        control_frame = ttk.Frame(main_pane, padding="5", width=300)
        main_pane.add(control_frame, weight=1)

        # --- TOP PANEL: Settings (Permanent) ---
        settings_frame = ttk.LabelFrame(control_frame, text="Settings", padding="5")
        settings_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_frame, text="Time Step Index (-1 for last):").pack(anchor=tk.W)
        ttk.Entry(settings_frame, textvariable=self.params['time_step']).pack(fill=tk.X)
        
        ttk.Label(settings_frame, text="Species Index (0, 1...):").pack(anchor=tk.W)
        ttk.Entry(settings_frame, textvariable=self.params['species_index']).pack(fill=tk.X)
        
        ttk.Label(settings_frame, text="Momentum Limit (u/c max):").pack(anchor=tk.W)
        ttk.Entry(settings_frame, textvariable=self.params['ucmx_scale']).pack(fill=tk.X)
        
        #ttk.Checkbutton(settings_frame, text="Use LaTeX Rendering", variable=self.params['use_latex']).pack(pady=5, anchor=tk.W)

        # --- BOTTOM PANEL: Notebook for Plot Actions ---
        nb = ttk.Notebook(control_frame)
        nb.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Tab 1: 1D Profiles (vs Rho)
        tab_profiles = ttk.Frame(nb)
        nb.add(tab_profiles, text="1D Profiles")
        
        ttk.Label(tab_profiles, text="Available Profiles").pack(pady=5)
        
        self.profile_buttons = [
            ("Current Density (J_tor)", self.plot_current_tor),
            ("FSA Current (<j_par>)", self.plot_current_fsa),
            ("Density (n0)", self.plot_density),
            ("Energy (Midplane)", self.plot_energy),
            ("RF Power (Damping)", self.plot_rf_power),
            ("Fusion Power", self.plot_fusion_power),
        ]
        
        for text, cmd in self.profile_buttons:
            btn = ttk.Button(tab_profiles, text=text, command=cmd)
            btn.pack(fill=tk.X, pady=2, padx=5)

        # Tab 2: Distribution Functions (vs Velocity)
        tab_2d = ttk.Frame(nb)
        nb.add(tab_2d, text="2D Dist / Cuts")
        
        # Radial Range Selection
        rad_frame = ttk.LabelFrame(tab_2d, text="Radial Surface Index Range")
        rad_frame.pack(fill=tk.X, padx=5, pady=10)
        
        r_sub = ttk.Frame(rad_frame)
        r_sub.pack(fill=tk.X, pady=5)
        
        ttk.Label(r_sub, text="Start:").pack(side=tk.LEFT, padx=5)
        self.spin_rad_start = ttk.Spinbox(r_sub, from_=0, to=100, width=5, textvariable=self.params['radial_start'])
        self.spin_rad_start.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(r_sub, text="End:").pack(side=tk.LEFT, padx=5)
        self.spin_rad_end = ttk.Spinbox(r_sub, from_=0, to=100, width=5, textvariable=self.params['radial_end'])
        self.spin_rad_end.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(tab_2d, text="Plot Style:").pack(pady=(10, 0))
        ttk.Radiobutton(tab_2d, text="Contour", variable=self.params['plot_type'], value='contour').pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(tab_2d, text="Mesh (3D)", variable=self.params['plot_type'], value='mesh').pack(anchor=tk.W, padx=10)
        
        ttk.Checkbutton(tab_2d, text="Log Scale", variable=self.params['log_scale']).pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Checkbutton(tab_2d, text="Trapped/Passing Boundaries", variable=self.params['plot_trapped_boundaries']).pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Button(tab_2d, text="Plot 2D Distribution", command=self.plot_distribution).pack(fill=tk.X, pady=10, padx=5)
        #ttk.Button(tab_2d, text="Plot Pitch Angle Cuts", command=self.plot_cuts).pack(fill=tk.X, pady=2, padx=5)
        
        ttk.Separator(tab_2d, orient='horizontal').pack(fill='x', pady=10)
        ttk.Button(tab_2d, text="Plot Fpar (Superimposed)", command=self.plot_fpar).pack(fill=tk.X, pady=2, padx=5)

        # --- Right Panel: Plot Canvas ---
        self.plot_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(self.plot_frame, weight=4)

        # Initialize empty figure
        self.fig = plt.Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        
        # Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Extract basics to set limits
        if self.filename is not None:
            if 'lrz' in self.nc_data.variables:
                lrz = self.nc_data.variables['lrz'][:].item()
                self.spin_rad_start.config(to=lrz-1)
                self.spin_rad_end.config(to=lrz-1)
                self.spin_rad_end.set(lrz-1)
            self.lbl_file.config(text=os.path.basename(self.filename))

    def load_file(self):
        filename = filedialog.askopenfilename(filetypes=[("NetCDF Files", "*.nc"), ("All Files", "*.*")])
        if not filename:
            return
        
        try:
            self.nc_data = Dataset(filename, 'r', format='NETCDF4')
            self.filename = filename
            self.lbl_file.config(text=os.path.basename(filename))
            
            # Extract basics to set limits
            if 'lrz' in self.nc_data.variables:
                lrz = self.nc_data.variables['lrz'][:].item()
                self.spin_rad_start.config(to=lrz-1)
                self.spin_rad_end.config(to=lrz-1)
                self.spin_rad_end.set(lrz-1)
                
            self.status("File loaded successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def status(self, msg):
        print(f"[Status] {msg}")

    def _setup_plot(self, dim=2):
        self.fig.clear()
        if self.params['use_latex'].get():
            plt.rc('text', usetex=True)
        else:
            plt.rc('text', usetex=False)
            
        if dim == 3:
            ax = self.fig.add_subplot(111, projection='3d')
        else:
            ax = self.fig.add_subplot(111)
            ax.grid(True)
        return ax

    def _get_time_index(self):
        t_idx = self.params['time_step'].get()
        times = self.nc_data.variables['time'][:]
        if t_idx < 0:
            return len(times) - 1
        return min(t_idx, len(times) - 1)

    # ==========================================
    # 1D PROFILE PLOTTING METHODS
    # ==========================================

    def plot_current_tor(self):
        if not self.nc_data: return
        try:
            ax = self._setup_plot()
            rya = self.nc_data.variables['rya'][:]
            curtor = self.nc_data.variables['curtor'][:] # (time, lr)
            
            t_idx = self._get_time_index()
            J = curtor[t_idx, :]
            
            ax.plot(rya, J, 'r-', linewidth=2)
            ax.set_xlabel(r'$\rho$')
            ax.set_ylabel(r'$J_{tor}$ $(A/cm^2)$')
            ax.set_title(f"Toroidal Current Profile (t={t_idx})")
            ax.set_xlim(self.params['rho_min'].get(), self.params['rho_max'].get())
            self.canvas.draw()
        except KeyError as e:
            messagebox.showerror("Data Error", f"Variable not found: {e}")

    def plot_current_fsa(self):
        if not self.nc_data: return
        try:
            ax = self._setup_plot()
            rya = self.nc_data.variables['rya'][:]
            curr = self.nc_data.variables['curr'][:]
            k = self.params['species_index'].get()
            t_idx = self._get_time_index()

            if curr.ndim == 3: J = curr[t_idx, k, :]
            else: J = curr[t_idx, :]
                
            J = J * 10.0 # Convert to kA/m^2
            ax.plot(rya, J, 'b-', linewidth=2)
            ax.set_xlabel(r'$\rho$')
            ax.set_ylabel(r'$<j_{||}>_{FSA}$ $(kA/m^2)$')
            ax.set_title(f"FSA Parallel Current (Species {k})")
            ax.set_xlim(self.params['rho_min'].get(), self.params['rho_max'].get())
            self.canvas.draw()
        except Exception as e: messagebox.showerror("Error", str(e))

    def plot_density(self):
        if not self.nc_data: return
        try:
            ax = self._setup_plot()
            rya = self.nc_data.variables['rya'][:]
            reden = self.nc_data.variables['density'][:]
            k = self.params['species_index'].get()
            t_idx = self._get_time_index()
            
            if reden.ndim == 3: den = reden[t_idx, :, k]
            else: den = reden[t_idx, :]

            ax.plot(rya, den, 'g-', linewidth=2)
            ax.set_xlabel(r'$\rho$')
            ax.set_ylabel(r'$n_0$ $(cm^{-3})$')
            ax.set_title(f"Midplane Density (Species {k})")
            ax.set_xlim(self.params['rho_min'].get(), self.params['rho_max'].get())
            self.canvas.draw()
        except Exception as e: messagebox.showerror("Error", str(e))

    def plot_energy(self):
        if not self.nc_data: return
        try:
            ax = self._setup_plot()
            rya = self.nc_data.variables['rya'][:]
            energym = self.nc_data.variables['energym'][:]
            k = self.params['species_index'].get()
            t_idx = self._get_time_index()
            
            if energym.ndim == 3:
                if energym.shape[1] == len(rya): en = energym[t_idx, :, k]
                else: en = energym[t_idx, k, :]
            else: en = energym[t_idx, :]

            ax.plot(rya, en, 'm-', linewidth=2)
            ax.set_xlabel(r'$\rho$')
            ax.set_ylabel(r'Energy $(keV)$')
            ax.set_title("Midplane Energy")
            ax.set_xlim(self.params['rho_min'].get(), self.params['rho_max'].get())
            self.canvas.draw()
        except Exception as e: messagebox.showerror("Error", str(e))

    def plot_rf_power(self):
        if not self.nc_data: return
        try:
            if 'rfpwr' not in self.nc_data.variables:
                messagebox.showinfo("Info", "No RF Power data found.")
                return

            ax = self._setup_plot()
            rya = self.nc_data.variables['rya'][:]
            rfpwr = self.nc_data.variables['rfpwr'][:]
            t_idx = self._get_time_index()
            
            mrfn = rfpwr.shape[1] - 3
            rf_sum = np.sum(rfpwr[t_idx, 0:mrfn, :], axis=0) * 1000.0
            
            ax.plot(rya, rf_sum, 'r-', linewidth=2)
            ax.set_xlabel(r'$\rho$')
            ax.set_ylabel(r'$P_{RF}$ $(kW/m^3)$')
            ax.set_title("Total RF Power Density")
            ax.set_xlim(self.params['rho_min'].get(), self.params['rho_max'].get())
            self.canvas.draw()
        except Exception as e: messagebox.showerror("Error", str(e))

    def plot_fusion_power(self):
        if not self.nc_data: return
        try:
            if 'fuspwrv' not in self.nc_data.variables:
                messagebox.showinfo("Info", "No Fusion Power data found.")
                return
            ax = self._setup_plot()
            rya = self.nc_data.variables['rya'][:]
            fuspwrv = self.nc_data.variables['fuspwrv'][:]
            if fuspwrv.shape[0] > 0: ax.plot(rya, fuspwrv[0, :], 'r-', label='D-T')
            if fuspwrv.shape[0] > 2: ax.plot(rya, fuspwrv[2, :], 'b-', label='D-D (p)')
            ax.legend()
            ax.set_xlabel(r'$\rho$')
            ax.set_ylabel(r'$P_{fus}$ $(W/cm^3)$')
            ax.set_title("Fusion Power Density")
            ax.set_xlim(self.params['rho_min'].get(), self.params['rho_max'].get())
            self.canvas.draw()
        except Exception as e: messagebox.showerror("Error", str(e))

    # ==========================================
    # 2D DISTRIBUTION PLOTTING
    # ==========================================

    def plot_distribution(self):
        if not self.nc_data: return
        
        start = self.params['radial_start'].get()
        end = self.params['radial_end'].get()
        if end < start: end = start
        
        # Check if we are plotting a Single Surface or a Range
        if start == end:
            # --- Single Surface: Plot in Main Window ---
            self.fig.clear()
            
            # Setup Axes based on type
            style = self.params['plot_type'].get()
            if style == 'mesh':
                ax = self.fig.add_subplot(111, projection='3d')
            else:
                ax = self.fig.add_subplot(111)
            
            # Draw
            try:
                self._generate_dist_plot(start, ax)
                self.canvas.draw()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to plot lr={start}: {e}")
                print(e)
        else:
            # --- Range: Open Scanning Window ---
            self._spawn_scan_window(start, end)

    def _generate_dist_plot(self, lr, ax):
        """
        Calculates data for radial index 'lr' and draws it on the provided axes 'ax'.
        """
        # 1. Prepare Data
        k = self.params['species_index'].get()
        
        # Load variables
        x = self.nc_data.variables['x'][:]
        y = self.nc_data.variables['y'][lr, :]
        full_f = self.nc_data.variables['f'][:]
        
        # Handle dimensions
        if full_f.ndim == 4: f_data = full_f[k, lr, :, :]
        elif full_f.ndim == 3: f_data = full_f[lr, :, :]
        else: return

        # Log Scale
        if self.params['log_scale'].get():
            # Avoid log(0)
            f_data = np.where(f_data <= 0, 1e-100, f_data)
            Z = np.log10(f_data)
            lbl = r'$log_{10}(f)$'
        else:
            Z = f_data
            lbl = r'$f$'

        # Coordinate transformation
        unorm = self.nc_data.variables['vnorm'][:].item()
        ucmx_scale = self.params['ucmx_scale'].get()
        
        cos_y = np.cos(y); sin_y = np.sin(y)
        X_grid = np.outer(x, cos_y) * (unorm/self.clight)
        Y_grid = np.outer(x, sin_y) * (unorm/self.clight)
        
        # Cutoff based on ucmx
        limit_idx = np.searchsorted(x * (unorm/self.clight), ucmx_scale)
        X_plot = X_grid[:limit_idx, :]
        Y_plot = Y_grid[:limit_idx, :]
        Z_plot = Z[:limit_idx, :]
        
        # Title
        rho_val = self.nc_data.variables['rya'][lr]
        title = f"Dist Func (rho={rho_val:.3f}, idx={lr})"

        # 2. Draw Plot
        style = self.params['plot_type'].get()
        
        if style == 'mesh':
            # 3D Mesh Plot
            ax.plot_surface(X_plot, Y_plot, Z_plot, cmap=cm.jet, rstride=1, cstride=1)
            ax.set_zlabel(lbl)
        else:
            # 2D Contour Plot
            levels = np.linspace(np.min(Z_plot), np.max(Z_plot), 25)
            cp = ax.contour(X_plot, Y_plot, Z_plot, levels=levels, cmap=cm.jet)
            # Add boundary circle
            theta = np.linspace(0, 2*np.pi, 100)
            ax.plot(ucmx_scale*np.cos(theta), ucmx_scale*np.sin(theta), 'k--', linewidth=1)
            # Plot passed/trapping boundaries
            if self.params['plot_trapped_boundaries']:
                try:
                    itl = int(self.nc_data.variables['itl'][lr]) - 1
                    itu = int(self.nc_data.variables['itu'][lr]) - 1
                    
                    if itl >= 0 and itu >= 0 and itl < len(y) and itu < len(y):
                        pchl = y[itl]  # Lower trapped-passing boundary
                        pchu = y[itu]  # Upper trapped-passing boundary
                        
                        # Calculate boundary curves
                        x_boundary = x * (unorm / self.clight)
                        x_lower = x_boundary * np.cos(pchl)
                        y_lower = x_boundary * np.sin(pchl)
                        x_upper = x_boundary * np.cos(pchu)
                        y_upper = x_boundary * np.sin(pchu)
                        
                        # Plot boundaries
                        ax.plot(x_lower, y_lower, 'm--', linewidth=1.5,
                               label='TP boundary')
                        ax.plot(x_upper, y_upper, 'm--', linewidth=1.5)
                except Exception as e:
                    print(f"  Could not plot TP boundaries: {e}")
                    
            ax.set_aspect('equal')
            ax.set_xlim(-ucmx_scale, ucmx_scale)
            ax.set_ylim(0, ucmx_scale)
            # Note: Colorbar handling in dynamic windows is tricky;
            # we skip adding a new colorbar every frame to avoid stacking them.

        ax.set_xlabel(r'$u_{||}/c$')
        ax.set_ylabel(r'$u_{\perp}/c$')
        ax.set_title(title)
        
    def _spawn_scan_window(self, start, end):
        """Creates a popup window with a slider to scan through surfaces."""
        
        # Create Toplevel Window
        top = tk.Toplevel(self.root)
        top.title(f"Scanning Surfaces {start} - {end}")
        top.geometry("700x600")
        
        # Set focus to this window so it catches keyboard events immediately
        top.focus_set()

        # --- Control Frame (Top) ---
        ctrl_frame = ttk.Frame(top, padding="5")
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(ctrl_frame, text="Select Surface Index:").pack(side=tk.LEFT, padx=5)

        # Slider (Scale)
        current_idx = tk.IntVar(value=start)
        
        def on_slider_update(val):
            # 'val' comes in as a string from the Scale widget
            idx = int(float(val))
            update_plot(idx)

        slider = tk.Scale(ctrl_frame, from_=start, to=end, orient=tk.HORIZONTAL,
                          variable=current_idx, command=on_slider_update, length=400)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # --- Plot Canvas (Bottom) ---
        fig_scan = plt.Figure(figsize=(6, 5), dpi=100)
        canvas_scan = FigureCanvasTkAgg(fig_scan, master=top)
        
        # Add Toolbar
        toolbar = NavigationToolbar2Tk(canvas_scan, top)
        toolbar.update()
        canvas_scan.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Update Function
        def update_plot(idx):
            fig_scan.clear()
            
            style = self.params['plot_type'].get()
            if style == 'mesh':
                ax = fig_scan.add_subplot(111, projection='3d')
            else:
                ax = fig_scan.add_subplot(111)
            
            try:
                self._generate_dist_plot(idx, ax)
                canvas_scan.draw()
            except Exception as e:
                print(f"Error plotting index {idx}: {e}")

        # --- Keyboard Navigation Logic ---
        def move_left(event):
            idx = current_idx.get()
            if idx > start:
                new_idx = idx - 1
                current_idx.set(new_idx) # Update variable (moves slider)
                update_plot(new_idx)     # Update plot

        def move_right(event):
            idx = current_idx.get()
            if idx < end:
                new_idx = idx + 1
                current_idx.set(new_idx) # Update variable (moves slider)
                update_plot(new_idx)     # Update plot

        # Bind Keys to the Window
        top.bind('<Left>', move_left)
        top.bind('<Right>', move_right)

        # Initial Plot
        update_plot(start)

    def plot_cuts(self):
        if not self.nc_data: return
        ax = self._setup_plot()
        lr = self.params['radial_start'].get() # Use start index
        k = self.params['species_index'].get()
        
        x = self.nc_data.variables['x'][:]
        unorm = self.nc_data.variables['vnorm'][:].item()
        y = self.nc_data.variables['y'][lr, :]
        
        full_f = self.nc_data.variables['f'][:]
        if full_f.ndim == 4: f_data = full_f[k, lr, :, :]
        else: f_data = full_f[lr, :, :]
            
        indices = [0, int(len(y)/4), int(len(y)/2), int(3*len(y)/4), len(y)-1]
        u_axis = x * (unorm / self.clight)
        
        for idx in indices:
            if idx < len(y):
                cut = f_data[idx, :]
                angle_deg = y[idx] * 180.0 / np.pi
                cut = np.where(cut <= 0, 1e-100, cut)
                ax.plot(u_axis, cut, label=f'{angle_deg:.1f}°')

        ax.set_yscale('log')
        ax.set_xlabel(r'$u/c$')
        ax.set_ylabel(r'$f$')
        ax.set_title(f"Cuts of f at rho index {lr}")
        ax.legend()
        self.canvas.draw()

    def plot_fpar(self):
        if not self.nc_data: return
        try:
            if 'fl' not in self.nc_data.variables:
                messagebox.showinfo("Info", "Variable 'fl' (Fpar) not found.")
                return

            ax = self._setup_plot()
            fl = self.nc_data.variables['fl'][:]
            xl = self.nc_data.variables['xl'][:]
            unorm = self.nc_data.variables['vnorm'][:].item()
            
            start = self.params['radial_start'].get()
            end = self.params['radial_end'].get()
            if end < start: end = start

            u_par_c = xl * (unorm / self.clight)
            ucmx = self.params['ucmx_scale'].get()

            # Set scale first
            is_log = self.params['log_scale'].get()
            if is_log: ax.set_yscale('log')

            # Loop through range and plot superimposed
            for lr in range(start, end + 1):
                if fl.ndim == 2:
                    fl_lr = fl[lr, :]
                elif fl.ndim == 3:
                    t_idx = self._get_time_index()
                    fl_lr = fl[t_idx, lr, :]
                
                # Filter zeros for log
                if is_log:
                    fl_max = np.max(fl_lr)
                    if fl_max > 0: fl_lr = np.maximum(fl_lr, fl_max / 1.0e7)

                # Get rho for legend
                rho_val = self.nc_data.variables['rya'][lr]
                ax.plot(u_par_c, fl_lr, linewidth=1.5, label=f'rho={rho_val:.2f}')

            ax.set_xlabel(r'$u_{||}/c$')
            ax.set_ylabel(r'$F_{||}$')
            ax.set_title(f"Parallel Distribution (Range {start}-{end})")
            ax.set_xlim(-ucmx, ucmx)
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.legend(fontsize='small')

            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot Fpar: {e}")

def main():
    # Get the folder where this script is currently installed
    package_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the full path to the yaml file
    yaml_path = os.path.join(package_dir, 'cqlyaml.yaml')
        
    #yaml_path = "cqlyaml.yaml"
    if not os.path.exists(yaml_path):
        print(f"Error: {yaml_path} not found. Please place it in the same directory.")
        sys.exit(1)
    app = CQL3D_GUI(yaml_path)
    app.mainloop()
    
if __name__ == "__main__":
    main()
