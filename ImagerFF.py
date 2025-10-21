import os
import shutil
from datetime import datetime
from PIL import Image
import piexif
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox
from tkintermapview import TkinterMapView

#  BACKUP FUNCTION 
def make_backup(original: str, backup_folder: str | None = None) -> str:
    if not os.path.isfile(original):
        raise FileNotFoundError(f"Not a file: {original}")

    folder, filename = os.path.split(original)
    name, extension = os.path.splitext(filename)

    target_folder = folder if backup_folder is None else backup_folder
    os.makedirs(target_folder, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{name}_backup_{stamp}{extension}"
    backup_path = os.path.join(target_folder, backup_name)

    shutil.copy2(original, backup_path)
    return backup_path

#  GPS EXTRACTION 
def gps_data(exif_data):
    coordinates = exif_data.get("GPS", {})
    if not coordinates:
        return None, None

    def convert_coordinates(coord, ref):
        degree = coord[0][0] / coord[0][1]
        minute = coord[1][0] / coord[1][1]
        second = coord[2][0] / coord[2][1]
        value = degree + (minute / 60.0) + (second / 3600.0)
        return -value if ref in ['S', 'W'] else value

    lat = convert_coordinates(coordinates[2], coordinates[1].decode())
    lon = convert_coordinates(coordinates[4], coordinates[3].decode())
    return lat, lon

#  EXIF EXTRACTION 
def extraction(backup_path: str):
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    try:
        image = Image.open(backup_path)
        exif_bytes = image.info.get("exif")
    except Exception as e:
        raise RuntimeError(f"Cannot identify image file: {e}")

    if exif_bytes:
        exif_data = piexif.load(exif_bytes)
    else:
        exif_data = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

    datatime = exif_data["0th"].get(piexif.ImageIFD.DateTime, b"").decode("utf-8", errors="ignore") or "N/A"
    make = exif_data["0th"].get(piexif.ImageIFD.Make, b"").decode("utf-8", errors="ignore") or "N/A"
    model = exif_data["0th"].get(piexif.ImageIFD.Model, b"").decode("utf-8", errors="ignore") or "N/A"

    try:
        latitude, longitude = gps_data(exif_data)
    except Exception:
        latitude, longitude = None, None

    filename = os.path.basename(backup_path)

    conn = sqlite3.connect("imagerff.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            backup TEXT,
            datatime TEXT,
            make TEXT,
            model TEXT,
            latitude REAL,
            longitude REAL
        )
    """)

    cursor.execute("""
        INSERT INTO image_data (filename, backup, datatime, make, model, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (filename, backup_path, datatime, make, model, latitude, longitude))

    conn.commit()
    conn.close()

    return {
        "filename": filename,
        "backup": backup_path,
        "datatime": datatime,
        "make": make,
        "model": model,
        "latitude": latitude if latitude is not None else "N/A",
        "longitude": longitude if longitude is not None else "N/A"
    }

#  GUI DESIGN 
class ImagerFFApp:
    def __init__(self, root):
        self.root = root
        self.backup_file = None
        self.folder = None

        self.root.geometry("1200x1000")
        self.root.title("ImagerFF")
        root.configure(bg="#1e1e1e")

        tk.Label(root, text="ImagerFF", font=("OCR A Extended", 48, "bold"), fg="#24C2A2", bg="#1e1e1e").place(x=350, y=50)

        tk.Button(root, text="Choose Evidence Folder", font=("OCR A Extended", 20, "bold"), fg="#24C2A2", bg="#1e1e1e", command=self.on_choose_folder).place(x=70, y=555)
        tk.Button(root, text="Backup Image", font=("OCR A Extended", 20, "bold"), fg="#24C2A2", bg="#1e1e1e", command=self.on_import).place(x=70, y=625)
        tk.Button(root, text="Run Extraction", font=("OCR A Extended", 20, "bold"), fg="#24C2A2", bg="#1e1e1e", command=self.on_run).place(x=70, y=695)
        tk.Button(root, text="Refresh List", font=("OCR A Extended", 20, "bold"), fg="#24C2A2", bg="#1e1e1e", command=self.refresh_listbox).place(x=70, y=765)

        self.listbox = tk.Listbox(root, width=33, height=18, bg="#2a2a2a", fg="#eaeaea", font=("OCR A Extended", 14, "bold"))
        self.listbox.place(x=75, y=150)

        self.path_label = tk.Label(root, text="No file selected", fg="#eaeaea", bg="#1e1e1e")
        self.path_label.place(x=300, y=635)

        fields = ["Filename", "Backup Path", "Date Taken", "Make", "Model", "Latitude", "Longitude"]
        self.value_labels = []
        for i, field in enumerate(fields):
            tk.Label(root, text=field + ":", font=("OCR A Extended", 14, "bold"), fg="#24C2A2", bg="#1e1e1e", anchor="w").place(x=500, y=150 + i * 50, width=140)
            val_label = tk.Label(root, text="N/A", font=("Courier New", 14), fg="#eaeaea", bg="#2a2a2a", anchor="w", relief="sunken")
            val_label.place(x=650, y=150 + i * 50, width=400)
            self.value_labels.append(val_label)

# MAP WIDGET
        self.map_widget = TkinterMapView(root, width=650, height=450, corner_radius=0)
        self.map_widget.set_position(20, 0)
        self.map_widget.set_zoom(2)
        self.map_widget.place(x=500, y=550)
#FOLDER SELECTION
    def on_choose_folder(self):
        folder = filedialog.askdirectory(title="Select a folder with images")
        if not folder:
            return
        self.folder = folder
        self.refresh_listbox()
#REFRESH IMAGE FOLDER
    def refresh_listbox(self):
        if not self.folder:
            messagebox.showwarning("No folder", "Choose a folder first.")
            return
        self.listbox.delete(0, tk.END)
        exts = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp")
        for fname in os.listdir(self.folder):
            if fname.lower().endswith(exts):
                self.listbox.insert(tk.END, fname)
#IMPORT IMAGES
    def on_import(self):
        if not self.folder:
            messagebox.showwarning("No folder", "Choose a folder first.")
            return
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("No file", "Select a file from the list first.")
            return
        filename = self.listbox.get(selection)
        filepath = os.path.join(self.folder, filename)
        try:
            self.backup_file = make_backup(filepath, backup_folder=None)
            self.path_label.config(text=f"Backup Created")
            messagebox.showinfo("Backup", f"Backup created:\n{self.backup_file}")
        except Exception as e:
            messagebox.showerror("Backup error", str(e))
            self.backup_file = None

    def on_run(self):
        if not self.backup_file:
            messagebox.showwarning("No backup", "Import first to create a backup.")
            return
        try:
            meta = extraction(self.backup_file)
            self.update_metadata_labels(**meta)
            messagebox.showinfo("Success", f"EXIF data extracted and stored for:\n{self.backup_file}")
        except Exception as e:
            messagebox.showerror("Extraction Error", str(e))

    def update_metadata_labels(self, filename, backup, datatime, make, model, latitude, longitude):
        values = [filename, backup, datatime, make, model, str(latitude), str(longitude)]
        for label, value in zip(self.value_labels, values):
            label.config(text=value if value else "N/A")

        self.show_map(latitude, longitude)
#MAP DISPLAY
    def show_map(self, lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(15)
            self.map_widget.set_marker(lat, lon, text="📍 Photo Location")
        except Exception as e:
            self.map_widget.set_position(0, 0)
            self.map_widget.set_zoom(2)
            print("Map error:", e)

if __name__ == "__main__":
    root = tk.Tk()
    ImagerFFApp(root)
    root.mainloop()
