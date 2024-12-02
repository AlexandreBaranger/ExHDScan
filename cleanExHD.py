import os
import json
from datetime import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading

def show_popups(root):
    popups = []

    def create_popup(index):
        if index >= len(popups):
            root.deiconify()
            return
        popup = tk.Toplevel(root)
        popup.geometry("1600x600")
        popup.configure(bg='#1c1c1c') 
        popup.overrideredirect(True)
        popup.attributes("-topmost", True) 
        label = tk.Label(popup, text=popups[index], font=("Helvetica", 52), fg='white', bg='#1c1c1c')
        label.pack(expand=True)
        popup.after(3000, lambda: (popup.destroy(), create_popup(index + 1)))
    root.withdraw()
    create_popup(0)

def scan_directory(directory, found_items, progress_callback=None):
    for root, dirs, files in os.walk(directory):
        # Vérification des dossiers
        for dir_name in dirs:
            full_path = os.path.join(root, dir_name)
            try:
                creation_time = os.path.getctime(full_path)
                creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                folder_size = 0
                for dirpath, dirnames, filenames in os.walk(full_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        try:
                            folder_size += os.path.getsize(fp)
                        except:
                            pass

                found_items[dir_name].append({
                    "path": full_path,
                    "creation_date": creation_date,
                    "size": folder_size
                })
            except Exception as e:
                print(f"Erreur lors de l'accès au dossier {full_path}: {e}")
        
        for file in files:
            if file.endswith('.zip'):
                full_path = os.path.join(root, file)
                try:
                    creation_time = os.path.getctime(full_path)
                    creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                    file_size = os.path.getsize(full_path)

                    found_items[file].append({
                        "path": full_path,
                        "creation_date": creation_date,
                        "size": file_size
                    })
                except Exception as e:
                    print(f"Erreur lors de l'accès au fichier {full_path}: {e}")
        
        if progress_callback:
            progress_callback()

def write_to_json(found_items, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(found_items, f, ensure_ascii=False, indent=4)

def open_in_explorer(paths):
    for path in paths:
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showwarning("Chemin non trouvé", f"Le chemin {path} n'existe pas.")

def show_results(found_items, total_count, root_window):
    result_window = tk.Toplevel(root_window)
    result_window.title("Résultats du scan")
    result_window.configure(bg='#1c1c1c')
    result_window.geometry('800x600')
    result_text = scrolledtext.ScrolledText(result_window, bg='#1c1c1c', fg='white', font=("Helvetica", 12))
    result_text.pack(fill=tk.BOTH, expand=True)
    result_text.insert(tk.END, f"Nombre total de dossiers et fichiers zip en doublon trouvés: {total_count}\n\n")    
    for item_name, item_data in found_items.items():
        if len(item_data) > 1:
            result_text.insert(tk.END, f"==== Doublons trouvés pour: {item_name} ====\n", "highlight")
            paths = [info['path'] for info in item_data]            
            for info in item_data:
                result_text.insert(tk.END, f"    Chemin: {info['path']}\n")
                result_text.insert(tk.END, f"    Date de création: {info['creation_date']}\n")
                result_text.insert(tk.END, f"    Taille: {info['size']} octets\n")
            open_button = tk.Button(result_window, text="Ouvrir les emplacements", command=lambda p=paths: open_in_explorer(p), bg='#333333', fg='white', font=("Helvetica", 10))
            result_text.window_create(tk.END, window=open_button)
            result_text.insert(tk.END, "\n------------------------------\n\n", "separator")

def start_scan(selected_folders, output_label, root_window):
    def scan():
        found_items = defaultdict(list)

        try:
            for folder in selected_folders:
                if os.path.exists(folder):
                    scan_directory(folder, found_items)
            duplicate_items = {k: v for k, v in found_items.items() if len(v) > 1}
            write_to_json(duplicate_items, 'duplicate_items.json')
            total_count = sum(len(v) for v in duplicate_items.values())
            show_results(duplicate_items, total_count, root_window)
            output_label.config(text=f"Scan terminé. {total_count} doublons trouvés.", fg="green")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors du scan: {e}")
            output_label.config(text="Erreur lors du scan.", fg="red")
    scan_thread = threading.Thread(target=scan)
    scan_thread.start()

def on_scan_button_click(folders_var, output_label, root_window):
    selected_folders = folders_var
    if not selected_folders:
        messagebox.showwarning("Aucun dossier sélectionné", "Veuillez sélectionner au moins un dossier à scanner.")
        return
    
    output_label.config(text="Scan en cours...", fg="yellow")
    start_scan(selected_folders, output_label, root_window)

def select_folders(folders_var, output_label, folder_listbox):
    selected_folder = filedialog.askdirectory(mustexist=True)
    if selected_folder:
        folders_var.append(selected_folder)
        folder_listbox.insert(tk.END, selected_folder)
        output_label.config(text=f"Dossier ajouté: {selected_folder}", fg="green")

def create_main_window():
    root = tk.Tk()
    root.title("Scanner de Dossiers et Fichiers ZIP Doublons")
    root.configure(bg='#1c1c1c') 
    root.geometry('600x400')
    root.after(1000, lambda: show_popups(root))
    title_label = tk.Label(root, text="Scanner de Dossiers et Fichiers ZIP Doublons", bg='#1c1c1c', fg='white', font=("Helvetica", 16))
    title_label.pack(pady=10)
    folders_var = []
    folder_listbox = tk.Listbox(root, bg='#333333', fg='white', font=("Helvetica", 12))
    folder_listbox.pack(padx=20, pady=10, fill="both", expand=True)
    select_folder_button = tk.Button(root, text="Sélectionner des dossiers", command=lambda: select_folders(folders_var, output_label, folder_listbox), bg='#333333', fg='white', font=("Helvetica", 12), padx=10, pady=5)
    select_folder_button.pack(pady=10)
    scan_button = tk.Button(root, text="Scanner", command=lambda: on_scan_button_click(folders_var, output_label, root), bg='#333333', fg='white', font=("Helvetica", 12), padx=10, pady=5)
    scan_button.pack(pady=10)
    output_label = tk.Label(root, text="", bg='#1c1c1c', fg='white', font=("Helvetica", 12))
    output_label.pack(pady=5)
    return root

if __name__ == "__main__":
    main_window = create_main_window()
    main_window.mainloop()
