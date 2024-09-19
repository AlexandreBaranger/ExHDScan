import os
import json
from datetime import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import ctypes

def get_available_drives():
    """Retourne une liste des lecteurs disponibles sur Windows."""
    drives = []
    bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if bitmask & 1:
            drives.append(f"{letter}:\\")
        bitmask >>= 1
    return drives

# Fonction pour scanner un répertoire donné et trouver les doublons par nom, taille et date
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
                            pass  # Ignorer les fichiers inaccessibles

                found_items[dir_name].append({
                    "path": full_path,
                    "creation_date": creation_date,
                    "size": folder_size
                })
            except Exception as e:
                print(f"Erreur lors de l'accès au dossier {full_path}: {e}")
        
        # Vérification des fichiers .zip
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

# Fonction pour écrire les résultats dans un fichier JSON
def write_to_json(found_items, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(found_items, f, ensure_ascii=False, indent=4)

# Fonction pour ouvrir les emplacements dans Windows Explorer
def open_in_explorer(paths):
    for path in paths:
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showwarning("Chemin non trouvé", f"Le chemin {path} n'existe pas.")

# Interface graphique pour afficher les résultats
def show_results(found_items, total_count, root_window):
    # Création d'une nouvelle fenêtre pour les résultats
    result_window = tk.Toplevel(root_window)
    result_window.title("Résultats du scan")
    result_window.configure(bg='#1c1c1c')  # Fond gris très foncé
    result_window.geometry('800x600')

    # Texte de résultats
    result_text = scrolledtext.ScrolledText(result_window, bg='#1c1c1c', fg='white', font=("Helvetica", 12))
    result_text.pack(fill=tk.BOTH, expand=True)

    result_text.insert(tk.END, f"Nombre total de dossiers et fichiers zip en doublon trouvés: {total_count}\n\n")
    
    for item_name, item_data in found_items.items():
        if len(item_data) > 1:  # Afficher uniquement les éléments en doublon
            result_text.insert(tk.END, f"==== Doublons trouvés pour: {item_name} ====\n", "highlight")
            paths = [info['path'] for info in item_data]  # Récupérer les chemins des doublons
            
            for info in item_data:
                result_text.insert(tk.END, f"    Chemin: {info['path']}\n")
                result_text.insert(tk.END, f"    Date de création: {info['creation_date']}\n")
                result_text.insert(tk.END, f"    Taille: {info['size']} octets\n")

            # Bouton pour ouvrir les emplacements des doublons
            open_button = tk.Button(result_window, text="Ouvrir les emplacements", command=lambda p=paths: open_in_explorer(p), bg='#333333', fg='white', font=("Helvetica", 10))
            result_text.window_create(tk.END, window=open_button)
            result_text.insert(tk.END, "\n------------------------------\n\n", "separator")

# Fonction principale pour gérer le processus de scan
def start_scan(selected_drives, output_label, root_window):
    def scan():
        found_items = defaultdict(list)

        try:
            for disk in selected_drives:
                if os.path.exists(disk):
                    scan_directory(disk, found_items)
            # Filtrer pour ne conserver que les dossiers ou fichiers zip avec les mêmes caractéristiques (nom, taille, date)
            duplicate_items = {k: v for k, v in found_items.items() if len(v) > 1}

            # Enregistrer les résultats dans un fichier JSON
            write_to_json(duplicate_items, 'duplicate_items.json')

            # Calculer le nombre total d'éléments trouvés
            total_count = sum(len(v) for v in duplicate_items.values())

            # Mettre à jour l'interface avec les résultats
            show_results(duplicate_items, total_count, root_window)

            # Mettre à jour le label de statut
            output_label.config(text=f"Scan terminé. {total_count} doublons trouvés.", fg="green")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors du scan: {e}")
            output_label.config(text="Erreur lors du scan.", fg="red")

    # Démarrer le scan dans un nouveau thread pour ne pas bloquer l'interface
    scan_thread = threading.Thread(target=scan)
    scan_thread.start()

# Fonction pour lancer le scan via le bouton
def on_scan_button_click(drives_var, output_label, root_window):
    # Récupérer les disques sélectionnés
    selected_drives = [drive for drive, var in drives_var.items() if var.get()]
    if not selected_drives:
        messagebox.showwarning("Aucun disque sélectionné", "Veuillez sélectionner au moins un disque à scanner.")
        return
    # Mettre à jour le label de statut
    output_label.config(text="Scan en cours...", fg="yellow")
    # Lancer le scan
    start_scan(selected_drives, output_label, root_window)

# Interface graphique principale
def create_main_window():
    root = tk.Tk()
    root.title("Scanner de Dossiers et Fichiers ZIP Doublons")
    root.configure(bg='#1c1c1c')  # Fond gris très foncé
    root.geometry('600x400')

    # Titre
    title_label = tk.Label(root, text="Scanner de Dossiers et Fichiers ZIP Doublons", bg='#1c1c1c', fg='white', font=("Helvetica", 16))
    title_label.pack(pady=10)

    # Cadre pour les lecteurs
    drives_frame = tk.LabelFrame(root, text="Sélectionnez les disques à scanner", bg='#1c1c1c', fg='white')
    drives_frame.pack(padx=20, pady=10, fill="both", expand=True)

    # Obtenir les lecteurs disponibles
    available_drives = get_available_drives()

    # Variables pour les checkboxes
    drives_var = {}
    for drive in available_drives:
        var = tk.BooleanVar(value=True)  # Par défaut, tous les disques sont sélectionnés
        chk = tk.Checkbutton(drives_frame, text=drive, variable=var, bg='#1c1c1c', fg='white', selectcolor='#1c1c1c', activebackground='#1c1c1c', activeforeground='white')
        chk.pack(anchor='w', padx=10, pady=2)
        drives_var[drive] = var

    # Bouton de scan
    scan_button = tk.Button(root, text="Scanner", command=lambda: on_scan_button_click(drives_var, output_label, root), bg='#333333', fg='white', font=("Helvetica", 12), padx=10, pady=5)
    scan_button.pack(pady=10)

    # Label pour le statut
    output_label = tk.Label(root, text="", bg='#1c1c1c', fg='white', font=("Helvetica", 12))
    output_label.pack(pady=5)

    return root

if __name__ == "__main__":
    main_window = create_main_window()
    main_window.mainloop()
