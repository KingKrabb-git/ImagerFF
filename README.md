# 🕵️‍♂️ ImagerFF  
*A Digital Forensics Image Extraction and Metadata Analysis Tool*  

## 📖 Overview  
**ImagerFF** is a digital forensics application designed to simplify the process of analyzing image metadata. Built in Python, the tool provides a graphical interface that allows investigators, students, and IT professionals to extract, store, and review EXIF metadata (including GPS coordinates) from image files while maintaining the integrity of original evidence.  

The application focuses on **accessibility**, **accuracy**, and **chain-of-custody preservation**, offering a user-friendly alternative to complex or costly commercial forensic software.  

---

## ⚙️ Features  
- 📁 **Folder Import:** Select a folder containing image files for automatic processing.  
- 🔒 **Evidence Backup:** Automatically creates a backup of all imported images to preserve original data.  
- 🧠 **Metadata Extraction:** Parses EXIF data such as timestamp, camera model, and GPS coordinates.  
- 🗺️ **Map Visualization:** Displays photo locations on an interactive map (if GPS data is available).  
- 💾 **Database Integration:** Stores extracted metadata in a SQLight database for organized review and reporting.  
- 🧩 **Simple GUI:** Built with Tkinter for intuitive use and accessibility.  

---

## 🖥️ Technology Stack  
- **Language:** Python  
- **Libraries:** Tkinter, Pillow, ExifRead, mysql-connector-python, folium (for mapping)  
- **Database:** MySQL  
- **Platform:** Cross-platform (Windows, Linux, macOS)  

---

## 🚀 Installation & Setup  

1. **Clone this repository**  
   ```bash
   git clone https://github.com/kylerabb/ImagerFF.git
   cd ImagerFF
