import os
import random
import librosa
import soundfile as sf
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Text, Scrollbar
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

class AudioCombinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Combiner")
        
        # Set window size to 1920x1080 and center it
        window_width = 1920
        window_height = 1080
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width/2) - (window_width/2)
        y = (screen_height/2) - (window_height/2)
        
        # Set window size and position
        self.root.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')
        self.root.configure(bg='#000000')
        
        # Variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_filename = tk.StringVar(value="combined_output.mp3")
        self.num_files = tk.StringVar(value="20")
        self.status = tk.StringVar(value="Ready")
        
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
        
        # Process button with nice modern styling
        process_frame = tk.Frame(main_frame, bg='#000000')
        process_frame.pack(pady=(20, 40))
        
        process_btn = CustomButton(process_frame,
                                 text="Process",
                                 command=self.process_audio,
                                 width=200,
                                 height=60)
        process_btn.pack()
        
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
    
    def process_audio(self):
        try:
            input_folder = self.input_folder.get()
            output_folder = self.output_folder.get()
            
            # Naudojame numeruojamą pavadinimą
            output_filename = f"Exported_Mix_{self.export_counter}.mp3"
            tracklist_filename = f"TimeStamps_Exported_Mix_{self.export_counter}.txt"
            
            # Validate number of files
            try:
                num_files = int(self.num_files.get())
                if num_files <= 0:
                    messagebox.showerror("Error", "Number of songs must be positive!")
                    return
            except ValueError:
                messagebox.showerror("Error", "Number of songs must be a number!")
                return
            
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
                
            if num_files > len(mp3_files):
                messagebox.showwarning("Warning", 
                    f"Selected number of songs ({num_files}) is greater than available files ({len(mp3_files)}). "
                    f"Using all available files.")
                num_files = len(mp3_files)
                
            # Update status
            self.status.set("Processing...")
            self.root.update()
            
            # Sukurti tracklist'o kintamuosius
            self.tracklist = []
            current_position_ms = 0
            
            # Atsitiktinai pasirinkti failus
            selected_files = random.sample(mp3_files, num_files)
            
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