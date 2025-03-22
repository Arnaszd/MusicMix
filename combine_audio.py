import os
import random
import librosa
import soundfile as sf
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Text, Scrollbar, Listbox
from pathlib import Path
from pydub import AudioSegment
from pydub import silence as pydub_silence
import io
import math
import re

class StarryBackground(tk.Canvas):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(bg='#000000')
        self.stars = []
        self.tick = 0
        self.create_stars()
        self.animate_stars()

    def create_stars(self):
        # Create more stars for better effect
        for _ in range(150):
            x = random.randint(0, self.winfo_screenwidth())
            y = random.randint(0, self.winfo_screenheight())
            size = random.randint(1, 3)
            brightness = random.randint(30, 100) / 100
            star = self.create_oval(x, y, x+size, y+size, 
                                  fill='white', 
                                  outline='white')
            self.stars.append({'id': star, 'brightness': brightness})

    def animate_stars(self):
        try:
            for star in self.stars:
                brightness = (math.sin(self.tick / 50) + 1) / 2 * star['brightness']
                color_value = int(brightness * 255)
                color = f'#{color_value:02x}{color_value:02x}{color_value:02x}'
                self.itemconfig(star['id'], fill=color, outline=color)
            self.tick += 1
            self.after(50, self.animate_stars)
        except Exception as e:
            print(f"Animation error: {e}")

class CustomButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=120, height=40, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg='#000000', highlightthickness=0, **kwargs)
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        
        # Colors
        self.bg_color = '#1e1e1e'
        self.hover_color = '#2a2a2a'
        self.active_color = '#1e90ff'
        self.border_color = '#3a3a3a'
        self.text_color = 'white'
        
        # Create button
        self.rect = self.create_rectangle(0, 0, width, height, 
                                         fill=self.bg_color, 
                                         outline=self.border_color, 
                                         width=2,
                                         tags="button")
        self.text_obj = self.create_text(width//2, height//2, 
                                        text=text, 
                                        fill=self.text_color, 
                                        font=('Segoe UI', 12, 'bold'),
                                        tags="button")
        
        # Bind events
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        
    def on_hover(self, event):
        self.itemconfig(self.rect, fill=self.hover_color)
        
    def on_leave(self, event):
        self.itemconfig(self.rect, fill=self.bg_color)
        
    def on_press(self, event):
        self.itemconfig(self.rect, fill=self.active_color)
        
    def on_release(self, event):
        self.itemconfig(self.rect, fill=self.hover_color)
        if self.command:
            self.command()

class CustomEntry(tk.Frame):
    def __init__(self, parent, textvariable=None, width=60, **kwargs):
        super().__init__(parent, bg='#000000', highlightthickness=0, **kwargs)
        
        # Entry styling
        self.entry = tk.Entry(self,
                            textvariable=textvariable,
                            font=('Segoe UI', 12),
                            width=width,
                            bg='#2a2a2a',
                            fg='white',
                            insertbackground='white',
                            relief='flat',
                            highlightthickness=1,
                            highlightbackground='#1e90ff',
                            highlightcolor='#1e90ff',
                            bd=10)
        self.entry.pack(fill='both', expand=True)

class ModernSongSelector(tk.Toplevel):
    def __init__(self, parent, input_folder, selected_callback, current_selected_songs=None):
        super().__init__(parent)
        self.title("Song Selection")
        self.parent = parent
        self.input_folder = input_folder
        self.selected_callback = selected_callback
        
        # Variables
        self.all_songs = []  # all mp3 files in folder
        self.selected_songs = []  # selected songs
        self.previously_selected_songs = current_selected_songs or []  # store previously selected songs
        
        # Set window state to maximized
        self.state('zoomed')
        self.configure(bg='#000000')
        
        # Create starry background like the main page
        self.background = StarryBackground(self)
        self.background.place(relwidth=1, relheight=1)
        
        # Create UI
        self.create_widgets()
        
        # Load songs
        self.load_songs()
        
        # Restore previously selected songs if any
        if self.previously_selected_songs:
            self.restore_selected_songs()
        
    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self, bg='#121212', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Header
        title_label = tk.Label(main_frame,
                           text="Select Songs and Order",
                           font=('Segoe UI', 18, 'bold'),
                           fg='#1e90ff',
                           bg='#121212')
        title_label.pack(pady=(0, 20))
        
        # Search field
        search_frame = tk.Frame(main_frame, bg='#121212')
        search_frame.pack(fill='x', pady=(0, 10))
        
        search_icon = tk.Label(search_frame, text="🔍", font=('Segoe UI', 12), fg='white', bg='#121212')
        search_icon.pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_songs)
        
        search_entry = tk.Entry(search_frame,
                              textvariable=self.search_var,
                              font=('Segoe UI', 12),
                              bg='#2a2a2a',
                              fg='white',
                              insertbackground='white',
                              relief='flat',
                              highlightthickness=1,
                              highlightbackground='#1e90ff',
                              highlightcolor='#1e90ff')
        search_entry.pack(side='left', fill='x', expand=True)
        
        # Upper container (song list)
        list_frame = tk.Frame(main_frame, bg='#121212')
        list_frame.pack(fill='both', expand=True, pady=10)
        
        # Left side - all songs
        left_frame = tk.Frame(list_frame, bg='#121212')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        songs_label = tk.Label(left_frame, 
                            text="Available Songs", 
                            font=('Segoe UI', 14, 'bold'), 
                            fg='white', 
                            bg='#121212')
        songs_label.pack(anchor='w', pady=(0, 5))
        
        songs_frame = tk.Frame(left_frame, bg='#1e1e1e', bd=0)
        songs_frame.pack(fill='both', expand=True)
        
        self.songs_listbox = tk.Listbox(songs_frame,
                                     bg='#1e1e1e',
                                     fg='white',
                                     selectbackground='#1e90ff',
                                     font=('Segoe UI', 12),
                                     bd=0,
                                     highlightthickness=0,
                                     activestyle='none',
                                     selectmode=tk.MULTIPLE)
        self.songs_listbox.pack(side='left', fill='both', expand=True)
        
        songs_scrollbar = tk.Scrollbar(songs_frame, command=self.songs_listbox.yview)
        songs_scrollbar.pack(side='right', fill='y')
        self.songs_listbox.config(yscrollcommand=songs_scrollbar.set)
        
        # Middle part - control buttons
        mid_frame = tk.Frame(list_frame, bg='#121212')
        mid_frame.pack(side='left', padx=10)
        
        add_btn = CustomButton(mid_frame, text="→", command=self.add_selected_songs, width=50, height=40)
        add_btn.pack(pady=5)
        
        remove_btn = CustomButton(mid_frame, text="←", command=self.remove_selected_songs, width=50, height=40)
        remove_btn.pack(pady=5)
        
        # Right side - selected songs with control buttons
        right_frame = tk.Frame(list_frame, bg='#121212')
        right_frame.pack(side='left', fill='both', expand=True, padx=(10, 0))
        
        playlist_label = tk.Label(right_frame, 
                               text="Selected Songs", 
                               font=('Segoe UI', 14, 'bold'), 
                               fg='white', 
                               bg='#121212')
        playlist_label.pack(anchor='w', pady=(0, 5))
        
        # Container for playlist and order buttons
        playlist_control_frame = tk.Frame(right_frame, bg='#121212')
        playlist_control_frame.pack(fill='both', expand=True)
        
        # Playlist frame
        playlist_frame = tk.Frame(playlist_control_frame, bg='#1e1e1e', bd=0)
        playlist_frame.pack(side='left', fill='both', expand=True)
        
        self.playlist_listbox = tk.Listbox(playlist_frame,
                                        bg='#1e1e1e',
                                        fg='white',
                                        selectbackground='#1e90ff',
                                        font=('Segoe UI', 12),
                                        bd=0,
                                        highlightthickness=0,
                                        activestyle='none')
        self.playlist_listbox.pack(side='left', fill='both', expand=True)
        
        playlist_scrollbar = tk.Scrollbar(playlist_frame, command=self.playlist_listbox.yview)
        playlist_scrollbar.pack(side='right', fill='y')
        self.playlist_listbox.config(yscrollcommand=playlist_scrollbar.set)
        
        # Order control buttons - moved to be next to the selected songs box
        order_frame = tk.Frame(playlist_control_frame, bg='#121212', padx=10)
        order_frame.pack(side='left', fill='y')
        
        move_up_btn = CustomButton(order_frame, text="↑ Up", command=self.move_up, width=120, height=40)
        move_up_btn.pack(pady=5)
        
        move_down_btn = CustomButton(order_frame, text="↓ Down", command=self.move_down, width=120, height=40)
        move_down_btn.pack(pady=5)
        
        move_top_btn = CustomButton(order_frame, text="↑↑ Top", command=self.move_to_top, width=120, height=40)
        move_top_btn.pack(pady=5)
        
        move_bottom_btn = CustomButton(order_frame, text="↓↓ Bottom", command=self.move_to_bottom, width=120, height=40)
        move_bottom_btn.pack(pady=5)
        
        shuffle_btn = CustomButton(order_frame, text="🔀 Shuffle", command=self.shuffle_playlist, width=120, height=40)
        shuffle_btn.pack(pady=5)
        
        # Bottom buttons
        bottom_frame = tk.Frame(main_frame, bg='#121212')
        bottom_frame.pack(fill='x', pady=(20, 0))
        
        confirm_btn = CustomButton(bottom_frame, 
                                text="✅ Confirm", 
                                command=self.confirm_selection, 
                                width=200, 
                                height=50)
        confirm_btn.pack(side='left', padx=10)
        
        cancel_btn = CustomButton(bottom_frame, 
                               text="❌ Cancel", 
                               command=self.cancel, 
                               width=150, 
                               height=50)
        cancel_btn.pack(side='left', padx=10)
    
        # Information label
        self.info_label = tk.Label(main_frame,
                                text="Selected: 0 songs",
                                font=('Segoe UI', 12),
                                fg='#1e90ff',
                                bg='#121212')
        self.info_label.pack(pady=(10, 0))
    
    def load_songs(self):
        """Užkrauna visas MP3 dainas iš pasirinkto aplanko"""
        if not self.input_folder or not os.path.exists(self.input_folder):
            messagebox.showerror("Klaida", "Prašome pasirinkti įvesties aplanką!")
            self.destroy()
            return
            
        # Išvalyti sąrašus
        self.all_songs = []
        self.songs_listbox.delete(0, tk.END)
        
        # Gauti sąrašą MP3 failų
        mp3_files = [f for f in os.listdir(self.input_folder) if f.lower().endswith('.mp3')]
        
        # Sukurti dainos objektus
        for mp3_file in mp3_files:
            display_name = self.clean_filename(mp3_file)
            self.all_songs.append({"filename": mp3_file, "display": display_name})
            self.songs_listbox.insert(tk.END, display_name)
    
    def filter_songs(self, *args):
        """Filtruoja dainas pagal paieškos tekstą"""
        search_text = self.search_var.get().lower()
        
        # Išvalyti sąrašą
        self.songs_listbox.delete(0, tk.END)
        
        # Pridėti filtruotas dainas
        for song in self.all_songs:
            if search_text in song["display"].lower():
                self.songs_listbox.insert(tk.END, song["display"])
    
    def add_selected_songs(self):
        """Prideda pasirinktas dainas į grojaraštį"""
        selected_indices = self.songs_listbox.curselection()
        
        if not selected_indices:
            return
            
        # Eiti per visus pasirinktus indeksus
        for index in selected_indices:
            display_name = self.songs_listbox.get(index)
            
            # Rasti atitinkamą failą
            for song in self.all_songs:
                if song["display"] == display_name and song["filename"] not in self.selected_songs:
                    self.selected_songs.append(song["filename"])
                    self.playlist_listbox.insert(tk.END, display_name)
                    break
        
        # Atnaujinti informacijos etiketę
        self.update_info_label()
    
    def remove_selected_songs(self):
        """Pašalina pasirinktas dainas iš grojaraščio"""
        selected_indices = self.playlist_listbox.curselection()
        
        if not selected_indices:
            return
            
        # Eiti per indeksus nuo galo, kad išvengti indeksų pokyčių
        for index in sorted(selected_indices, reverse=True):
            filename = self.selected_songs[index]
            self.selected_songs.pop(index)
            self.playlist_listbox.delete(index)
        
        # Atnaujinti informacijos etiketę
        self.update_info_label()
    
    def move_up(self):
        """Perkelia pasirinktą dainą aukštyn"""
        selected = self.playlist_listbox.curselection()
        
        if not selected or selected[0] == 0:
            return
            
        idx = selected[0]
        
        # Išsaugoti pasirinktos dainos duomenis
        filename = self.selected_songs[idx]
        display_name = self.playlist_listbox.get(idx)
        
        # Pašalinti iš dabartinės pozicijos
        self.selected_songs.pop(idx)
        self.playlist_listbox.delete(idx)
        
        # Įterpti naujoje pozicijoje
        new_idx = idx - 1
        self.selected_songs.insert(new_idx, filename)
        self.playlist_listbox.insert(new_idx, display_name)
        
        # Pažymėti dainą naujoje pozicijoje
        self.playlist_listbox.selection_clear(0, tk.END)
        self.playlist_listbox.selection_set(new_idx)
        self.playlist_listbox.see(new_idx)
    
    def move_down(self):
        """Perkelia pasirinktą dainą žemyn"""
        selected = self.playlist_listbox.curselection()
        
        if not selected or selected[0] == self.playlist_listbox.size() - 1:
            return
            
        idx = selected[0]
        
        # Išsaugoti pasirinktos dainos duomenis
        filename = self.selected_songs[idx]
        display_name = self.playlist_listbox.get(idx)
        
        # Pašalinti iš dabartinės pozicijos
        self.selected_songs.pop(idx)
        self.playlist_listbox.delete(idx)
        
        # Įterpti naujoje pozicijoje
        new_idx = idx + 1
        self.selected_songs.insert(new_idx, filename)
        self.playlist_listbox.insert(new_idx, display_name)
        
        # Pažymėti dainą naujoje pozicijoje
        self.playlist_listbox.selection_clear(0, tk.END)
        self.playlist_listbox.selection_set(new_idx)
        self.playlist_listbox.see(new_idx)
    
    def move_to_top(self):
        """Perkelia pasirinktą dainą į sąrašo viršų"""
        selected = self.playlist_listbox.curselection()
        
        if not selected or selected[0] == 0:
            return
            
        idx = selected[0]
        
        # Išsaugoti pasirinktos dainos duomenis
        filename = self.selected_songs[idx]
        display_name = self.playlist_listbox.get(idx)
        
        # Pašalinti iš dabartinės pozicijos
        self.selected_songs.pop(idx)
        self.playlist_listbox.delete(idx)
        
        # Įterpti naujoje pozicijoje
        new_idx = 0
        self.selected_songs.insert(new_idx, filename)
        self.playlist_listbox.insert(new_idx, display_name)
        
        # Pažymėti dainą naujoje pozicijoje
        self.playlist_listbox.selection_clear(0, tk.END)
        self.playlist_listbox.selection_set(new_idx)
        self.playlist_listbox.see(new_idx)
    
    def move_to_bottom(self):
        """Perkelia pasirinktą dainą į sąrašo apačią"""
        selected = self.playlist_listbox.curselection()
        
        if not selected or selected[0] == self.playlist_listbox.size() - 1:
            return
            
        idx = selected[0]
        
        # Išsaugoti pasirinktos dainos duomenis
        filename = self.selected_songs[idx]
        display_name = self.playlist_listbox.get(idx)
        
        # Pašalinti iš dabartinės pozicijos
        self.selected_songs.pop(idx)
        self.playlist_listbox.delete(idx)
        
        # Įterpti naujoje pozicijoje
        self.selected_songs.append(filename)
        self.playlist_listbox.insert(tk.END, display_name)
        
        # Pažymėti dainą naujoje pozicijoje
        new_idx = self.playlist_listbox.size() - 1
        self.playlist_listbox.selection_clear(0, tk.END)
        self.playlist_listbox.selection_set(new_idx)
        self.playlist_listbox.see(new_idx)
    
    def shuffle_playlist(self):
        """Sumaišo dainų tvarką atsitiktine tvarka"""
        if len(self.selected_songs) < 2:
                return
                
        # Išsaugoti dabartinę dainų tvarką
        current_order = list(zip(self.selected_songs, 
                               [self.playlist_listbox.get(i) for i in range(self.playlist_listbox.size())]))
        
        # Sumaišyti tvarką
        random.shuffle(current_order)
        
        # Atnaujinti sąrašus
        self.selected_songs = [item[0] for item in current_order]
        self.playlist_listbox.delete(0, tk.END)
        
        for item in current_order:
            self.playlist_listbox.insert(tk.END, item[1])
    
    def update_info_label(self):
        """Atnaujina informacijos etiketę"""
        count = len(self.selected_songs)
        self.info_label.config(text=f"Selected: {count} songs")
    
    def confirm_selection(self):
        """Patvirtina pasirinktų dainų tvarką"""
        if not self.selected_songs:
            messagebox.showwarning("Warning", "You haven't selected any songs!")
            return
                
        # Perduoti pasirinktų dainų sąrašą
        self.selected_callback(self.selected_songs)
        self.destroy()
    
    def cancel(self):
        """Atšaukia dainų pasirinkimą"""
        self.destroy()
    
    def clean_filename(self, filename):
        """Suformuoja gražų dainos pavadinimą iš failo pavadinimo"""
        # Pašalinti .mp3 plėtinį
        name = os.path.splitext(filename)[0]
        
        # Pašalinti numeraciją iš pradžios
        name = re.sub(r'^\d+[\.\-\s_]+', '', name)
        
        # Pakeisti _ ir - simbolius tarpais
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Pašalinti kelis tarpus iš eilės
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()

    def restore_selected_songs(self):
        """Atkuria anksčiau pasirinktas dainas iš saugomo sąrašo"""
        # Pridėti anksčiau pasirinktas dainas į naują sąrašą
        for filename in self.previously_selected_songs:
            # Rasti atitinkamą display_name pagal filename
            display_name = None
            for song in self.all_songs:
                if song["filename"] == filename:
                    display_name = song["display"]
                    break
            
            # Jei radome display_name, pridėti į pasirinktųjų sąrašą
            if display_name:
                self.selected_songs.append(filename)
                self.playlist_listbox.insert(tk.END, display_name)
        
        # Atnaujinti informacijos etiketę
        self.update_info_label()

class AudioCombinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Combiner")
        
        # Set to maximize mode
        self.root.state('zoomed')
        self.root.configure(bg='#000000')
        
        # Variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_filename = tk.StringVar(value="combined_output.mp3")
        self.num_files = tk.StringVar(value="20")
        self.status = tk.StringVar(value="Ready")
        
        # Song selection
        self.selected_songs = []
        self.use_selected_songs = tk.BooleanVar(value=False)
        
        # Tracklist variables
        self.tracklist = []
        self.save_tracklist = tk.BooleanVar(value=True)
        
        # Track export count
        self.export_counter_file = "export_counter.txt"
        self.export_counter = self.load_export_counter()
        
        # Create starry background
        self.background = StarryBackground(self.root)
        self.background.place(relwidth=1, relheight=1)
        
        # Create widgets
        self.create_widgets()
        
    def create_widgets(self):
        # Main container with glassmorphism effect
        main_frame = tk.Frame(self.root, bg='#000000')
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title with glow effect
        title_frame = tk.Frame(main_frame, bg='#000000')
        title_frame.pack(pady=(0, 60))
        
        # Glowing title effect
        glow_title = tk.Label(title_frame, 
                            text="Audio Combiner",
                            font=('Segoe UI', 48, 'bold'),
                            fg='#1e90ff',
                            bg='#000000')
        glow_title.pack()
        
        title_label = tk.Label(title_frame, 
                             text="Audio Combiner",
                             font=('Segoe UI', 46, 'bold'),
                             fg='white',
                             bg='#000000')
        title_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Container for inputs
        inputs_frame = tk.Frame(main_frame, bg='#000000')
        inputs_frame.pack(fill='both', padx=20, pady=20)
        
        # Input selection with nice styling
        input_label = tk.Label(inputs_frame, 
                             text="Select Input Folder:",
                             font=('Segoe UI', 14),
                             fg='white',
                             bg='#000000')
        input_label.pack(anchor='w', pady=(0, 5))
        
        input_frame = tk.Frame(inputs_frame, bg='#000000')
        input_frame.pack(fill='x', pady=(0, 25))
        
        # Custom styled entry
        input_entry = CustomEntry(input_frame,
                                textvariable=self.input_folder,
                                width=60)
        input_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Custom styled button
        browse_input_btn = CustomButton(input_frame,
                                      text="Browse",
                                      command=self.browse_input,
                                      width=120,
                                      height=46)
        browse_input_btn.pack(side='left')
        
        # Output selection with nice styling
        output_label = tk.Label(inputs_frame,
                              text="Output Folder:",
                              font=('Segoe UI', 14),
                              fg='white',
                              bg='#000000')
        output_label.pack(anchor='w', pady=(0, 5))
        
        output_frame = tk.Frame(inputs_frame, bg='#000000')
        output_frame.pack(fill='x', pady=(0, 25))
        
        # Custom styled entry
        output_entry = CustomEntry(output_frame,
                                 textvariable=self.output_folder,
                                 width=60)
        output_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Custom styled button
        browse_output_btn = CustomButton(output_frame,
                                       text="Browse",
                                       command=self.browse_output_folder,
                                       width=120,
                                       height=46)
        browse_output_btn.pack(side='left')
        
        # Number of songs with nice styling
        num_files_frame = tk.Frame(inputs_frame, bg='#000000')
        num_files_frame.pack(fill='x', pady=(0, 40))
        
        num_files_label = tk.Label(num_files_frame,
                                 text="Number of Songs:",
                                 font=('Segoe UI', 14),
                                 fg='white',
                                 bg='#000000')
        num_files_label.pack(side='left', padx=(0, 10))
        
        # Custom styled small entry
        num_files_entry = tk.Entry(num_files_frame,
                                 textvariable=self.num_files,
                                 font=('Segoe UI', 14),
                                 width=10,
                                 bg='#2a2a2a',
                                 fg='white',
                                 insertbackground='white',
                                 relief='flat',
                                 highlightthickness=1,
                                 highlightbackground='#1e90ff',
                                 highlightcolor='#1e90ff',
                                 bd=10)
        num_files_entry.pack(side='left')
        
        # Modern progress bar
        progress_frame = tk.Frame(main_frame, bg='#000000')
        progress_frame.pack(fill='x', pady=(20, 10))
        
        self.progress = ttk.Progressbar(progress_frame,
                                      style='TProgressbar',
                                      length=800,
                                      mode='determinate')
        self.progress.pack(fill='x')
        
        # Style for the progressbar
        style = ttk.Style()
        style.configure("TProgressbar", 
                      thickness=20, 
                      troughcolor='#1e1e1e',
                      background='#1e90ff')
        
        # Status with modern styling
        status_frame = tk.Frame(main_frame, bg='#000000')
        status_frame.pack(pady=(0, 30))
        
        status_label = tk.Label(status_frame,
                              textvariable=self.status,
                              font=('Segoe UI', 14),
                              fg='#1e90ff',
                              bg='#000000')
        status_label.pack()
        
        # Tracklist checkbox with custom styling
        checkbox_frame = tk.Frame(main_frame, bg='#000000')
        checkbox_frame.pack(pady=(10, 30))
        
        self.tracklist_check_var = tk.IntVar(value=1)
        tracklist_check = tk.Checkbutton(checkbox_frame,
                                        text="Create Tracklist",
                                        variable=self.tracklist_check_var,
                                        font=('Segoe UI', 14),
                                        fg='white',
                                        bg='#000000',
                                        selectcolor='#2a2a2a',
                                        activeforeground='white',
                                        activebackground='#000000')
        tracklist_check.pack()
        
        # Song selection button
        songs_selection_frame = tk.Frame(main_frame, bg='#000000')
        songs_selection_frame.pack(pady=(0, 20))
        
        # Checkbox for using selected songs
        self.use_selected_check = tk.Checkbutton(songs_selection_frame,
                                        text="Use Selected Songs",
                                        variable=self.use_selected_songs,
                                        font=('Segoe UI', 14),
                                        fg='white',
                                        bg='#000000',
                                        selectcolor='#2a2a2a',
                                        activeforeground='white',
                                        activebackground='#000000')
        self.use_selected_check.pack()
        
        # Selection button
        select_songs_btn = CustomButton(songs_selection_frame,
                                       text="Select Songs",
                                       command=self.open_song_selection,
                                       width=180,
                                       height=50)
        select_songs_btn.pack(pady=10)
        
        # Selected songs label
        self.selected_count_label = tk.Label(songs_selection_frame,
                                          text="Selected songs: 0",
                                          font=('Segoe UI', 12),
                                          fg='white',
                                          bg='#000000')
        self.selected_count_label.pack()
        
        # Bottom frame for process button and custom song
        bottom_frame = tk.Frame(main_frame, bg='#000000')
        bottom_frame.pack(fill='x', pady=(20, 40))
        
        # Process button
        process_btn = CustomButton(bottom_frame,
                                 text="Process",
                                 command=self.process_audio,
                                 width=200,
                                 height=60)
        process_btn.pack(side='left')
        
        # Custom song button (bottom right)
        custom_song_btn = CustomButton(bottom_frame,
                                     text="Add Custom Song",
                                     command=self.add_custom_song,
                                     width=200,
                                     height=60)
        custom_song_btn.pack(side='right', padx=20)
        
    def open_song_selection(self):
        """Opens song selection window"""
        input_folder = self.input_folder.get()
        
        if not input_folder:
            messagebox.showerror("Error", "Please select input folder!")
            return
            
        if not os.path.exists(input_folder):
            messagebox.showerror("Error", "Input folder does not exist!")
            return
            
        # Open modern song selector and pass currently selected songs
        song_selection = ModernSongSelector(self.root, input_folder, 
                                          self.update_selected_songs,
                                          current_selected_songs=self.selected_songs)
        
    def update_selected_songs(self, selected_songs):
        """Updates selected songs list from song selection window"""
        self.selected_songs = selected_songs
        self.selected_count_label.config(text=f"Selected songs: {len(selected_songs)}")
        
        # Automatically enable selected songs
        if selected_songs:
            self.use_selected_songs.set(True)
            
    def add_custom_song(self):
        """Adds a custom song to the selection"""
        custom_file = filedialog.askopenfilename(
            title="Select Custom MP3 File",
            filetypes=[("MP3 Files", "*.mp3")]
        )
        
        if custom_file:
            # Extract just the filename, not the full path
            file_name = os.path.basename(custom_file)
            
            # Copy file to input folder if needed
            input_folder = self.input_folder.get()
            if input_folder:
                # Check if we should copy the file
                if os.path.dirname(custom_file) != input_folder:
                    try:
                        import shutil
                        shutil.copy2(custom_file, os.path.join(input_folder, file_name))
                        messagebox.showinfo("Success", f"File '{file_name}' copied to input folder")
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not copy file: {str(e)}")
            
            # Add to selected songs
            if file_name not in self.selected_songs:
                self.selected_songs.append(file_name)
                self.selected_count_label.config(text=f"Selected songs: {len(self.selected_songs)}")
                self.use_selected_songs.set(True)
    
    def process_audio(self):
        try:
            input_folder = self.input_folder.get()
            output_folder = self.output_folder.get()
            
            # Naudojame numeruojamą pavadinimą
            output_filename = f"Exported_Mix_{self.export_counter}.mp3"
            tracklist_filename = f"TimeStamps_Exported_Mix_{self.export_counter}.txt"
            
            if not input_folder or not output_folder:
                messagebox.showerror("Error", "Please select input and output folders!")
                return
                
            if not os.path.exists(input_folder):
                messagebox.showerror("Error", "Input folder does not exist!")
                return
                
            # Get list of MP3 files
            mp3_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.mp3')]
            
            if not mp3_files:
                messagebox.showerror("Error", "No MP3 files found in the input folder!")
                return
            
            # Pasirinkti dainas
            if self.use_selected_songs.get() and self.selected_songs:
                # Naudoti pasirinktas dainas
                selected_files = self.selected_songs
                num_files = len(selected_files)
            else:
                # Validate number of files for random selection
                try:
                    num_files = int(self.num_files.get())
                    if num_files <= 0:
                        messagebox.showerror("Error", "Number of songs must be positive!")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Number of songs must be a number!")
                    return
                    
                if num_files > len(mp3_files):
                    messagebox.showwarning("Warning", 
                        f"Selected number of songs ({num_files}) is greater than available files ({len(mp3_files)}). "
                        f"Using all available files.")
                    num_files = len(mp3_files)
                
                # Atsitiktinai pasirinkti failus
                selected_files = random.sample(mp3_files, num_files)
            
            # Update status
            self.status.set("Processing...")
            self.root.update()
            
            # Sukurti tracklist'o kintamuosius
            self.tracklist = []
            current_position_ms = 0
            
            # Inicializuoti bendrą audio
            combined_segment = None
            
            # Atnaujinti pažangos juostą
            self.progress['maximum'] = len(selected_files)
            self.progress['value'] = 0
            
            # Apdoroti kiekvieną failą
            for i, file in enumerate(selected_files):
                file_path = os.path.join(input_folder, file)
                self.status.set(f"Processing: {file}")
                self.progress['value'] = i + 1
                self.root.update()
                
                # Gauti dainos pavadinimą (be .mp3 plėtinio)
                song_name = os.path.splitext(file)[0]
                
                # Pašalinti numeraciją iš dainos pavadinimo (pvz., "15. ", "42. ", ir t.t.)
                song_name = self.remove_numbering(song_name)
                
                # Įkelti garso failą naudojant pydub tiesiogiai
                audio_segment = AudioSegment.from_file(file_path, format="mp3")
                
                # Pašalinti tylą naudojant pydub
                self.status.set(f"Removing silence: {file}")
                self.root.update()
                
                # Pašalinti tylą iš pradžios ir pabaigos
                audio_segment = trim_silence_with_pydub(audio_segment)
                
                # Skaičiuoti tracklist'o laiko žymas
                minutes = current_position_ms // 60000
                seconds = (current_position_ms % 60000) // 1000
                timestamp = f"{minutes:02d}:{seconds:02d}"
                
                # Pridėti dainos informaciją į tracklist'ą
                tracklist_entry = f"{timestamp} {song_name} (Hyper Demon Remix)"
                self.tracklist.append(tracklist_entry)
                
                # Pridėti į bendrą audio su persidengimais
                if combined_segment is None:
                    combined_segment = audio_segment
                else:
                    # Taikyti 1 sekundės persidengimą jungiant segmentus
                    combined_segment = combined_segment.append(audio_segment, crossfade=1000)
                    # Atnaujinti laiko poziciją atsižvelgiant į persidengimą
                    current_position_ms += len(audio_segment) - 1000
                
                # Jei tai pirmas failas, tiesiog pridedam ilgį
                if i == 0:
                    current_position_ms = len(audio_segment)
            
            # Užtikrinti, kad išvesties aplankas egzistuoja
            os.makedirs(output_folder, exist_ok=True)
            
            # Sukonstruoti pilną išvesties kelią
            output_file = os.path.join(output_folder, output_filename)
            
            # Sukurti tracklist tekstą
            tracklist_text = "\n".join(self.tracklist)
            
            # Visada išsaugoti tracklist į failą
            tracklist_file = os.path.join(output_folder, tracklist_filename)
            with open(tracklist_file, "w", encoding="utf-8") as f:
                f.write(tracklist_text)
            
            # Eksportuoti į MP3 su 320kbps ir 44100 Hz sample rate
            self.status.set("Exporting to MP3...")
            self.root.update()
            combined_segment = combined_segment.set_frame_rate(44100)  # Nustatyti sample rate į 44100 Hz
            combined_segment.export(output_file, format="mp3", bitrate="320k", parameters=["-ar", "44100"])
            
            # Padidinti ir išsaugoti eksportavimo skaitliuką
            self.export_counter += 1
            self.save_export_counter()
            
            self.status.set("Processing complete!")
            
            # Rodyti sėkmės pranešimą su tracklist informacija
            success_message = (f"Successfully combined {num_files} songs with 1s crossfades!\n\n"
                              f"MP3 file saved to: {output_file}\n"
                              f"Tracklist saved to: {tracklist_file}")
            
            messagebox.showinfo("Success", success_message)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status.set("Error occurred!")
        finally:
            self.progress['value'] = 0

    def remove_numbering(self, song_name):
        """
        Pašalina numeraciją iš dainos pavadinimo.
        Pvz., "15. Dainos pavadinimas" => "Dainos pavadinimas"
        """
        # Pašalina bet kokį skaičių su tašku ir tarpu 
        # (pvz., "15. ", "123. ", ir t.t.)
        cleaned_name = re.sub(r'^\d+\.\s+', '', song_name)
        # Pašalina bet kokį skaičių pradžioje (pvz., "15 ", "123 ", ir t.t.)
        cleaned_name = re.sub(r'^\d+\s+', '', cleaned_name)
        return cleaned_name

    def browse_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)
            
    def browse_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)
            
    def load_export_counter(self):
        """Įkelti eksportavimo skaitliuką iš failo arba pradėti nuo 1"""
        try:
            if os.path.exists(self.export_counter_file):
                with open(self.export_counter_file, "r") as f:
                    return int(f.read().strip())
            return 1
        except:
            return 1
    
    def save_export_counter(self):
        """Išsaugoti eksportavimo skaitliuką į failą"""
        try:
            with open(self.export_counter_file, "w") as f:
                f.write(str(self.export_counter))
        except:
            pass

def trim_silence_with_pydub(audio_segment, silence_threshold=-40, min_silence_len=100):
    """
    Pašalina tylą iš garso pradžios ir pabaigos naudojant pydub biblioteką,
    kuri yra patikimesnė už librosa tylos aptikimui.
    
    Parametrai:
        audio_segment: pydub.AudioSegment objektas
        silence_threshold: tylos slenkstis decibelais (rekomenduojama -40 dB)
        min_silence_len: minimali tylos trukmė milisekundėmis
    """
    try:
        # Aptikti ne tylos dalis
        non_silent_ranges = pydub_silence.detect_nonsilent(
            audio_segment,
            min_silence_len=min_silence_len,
            silence_thresh=silence_threshold
        )
        
        # Jei nerasta jokių ne tylių segmentų, grąžinti nepakeistą garso segmentą
        if not non_silent_ranges:
            return audio_segment
        
        # Apkarpyti garso failą - palikti tik dalį nuo pirmo iki paskutinio ne tylaus segmento
        start_trim = non_silent_ranges[0][0]
        end_trim = non_silent_ranges[-1][1]
        
        return audio_segment[start_trim:end_trim]
    
    except Exception as e:
        print(f"Klaida pašalinant tylą: {e}")
        # Jei įvyko klaida, grąžinti originalų audio
        return audio_segment

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioCombinerGUI(root)
    root.mainloop() 