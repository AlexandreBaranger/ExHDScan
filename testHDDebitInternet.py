import os
import time
import psutil
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

def convertir_gbps_en_mo_s(vitesse_gbps):
    """Convertit une vitesse en Gbps en Mo/s."""
    return (vitesse_gbps * 1000) / 8

def verifier_compatibilite_connexion(vitesse_mo_s):
    """Vérifie la compatibilité avec des connexions Internet de 2.5, 5 et 10 Gbps."""
    vitesses_gbps = [2.5, 5, 10]
    messages = []

    for vitesse_gbps in vitesses_gbps:
        vitesse_min_mo_s = convertir_gbps_en_mo_s(vitesse_gbps)
        if vitesse_mo_s >= vitesse_min_mo_s:
            messages.append(f"✅ Compatible avec une connexion de {vitesse_gbps} Gb/s "
                            f"(minimum requis : {vitesse_min_mo_s:.2f} Mo/s)")
        else:
            messages.append(f"❌ Non compatible avec une connexion de {vitesse_gbps} Gb/s "
                            f"(minimum requis : {vitesse_min_mo_s:.2f} Mo/s)")
    return "\n".join(messages)

def surveiller_temperature_disque():
    """Surveille la température des disques si disponible."""
    try:
        for disk in psutil.disk_partitions():
            usage = psutil.disk_usage(disk.mountpoint)
            if 'sd' in disk.device or 'nvme' in disk.device:
                temp = psutil.sensors_temperatures().get('nvme', None)
                if temp:
                    return temp[0].current  # Retourne la température du disque
        return "Température non disponible"
    except Exception as e:
        return f"Erreur de lecture de la température: {e}"

def test_vitesse_ecriture_continue(chemin_dossier, taille_mo=1000, taille_bloc_mo=100):
    """
    Teste la vitesse d'écriture en écrivant progressivement des blocs de données.

    Arguments :
    chemin_dossier (str) : Dossier où le fichier temporaire sera écrit.
    taille_mo (int) : Taille totale du fichier de test en Mo.
    taille_bloc_mo (int) : Taille de chaque bloc écrit en Mo.

    Retourne :
    float : La vitesse moyenne d'écriture en Mo/s.
    """
    fichier_test = os.path.join(chemin_dossier, "test_ecriture_continue.tmp")
    taille_bloc_octets = taille_bloc_mo * 1024 * 1024
    donnees = os.urandom(taille_bloc_octets)
    try:
        debut = time.time()
        ecrit_total = 0
        with open(fichier_test, "wb") as f:
            while ecrit_total < taille_mo * 1024 * 1024:
                f.write(donnees)
                f.flush()
                os.fsync(f.fileno())
                ecrit_total += taille_bloc_octets
                temps_ecoule = time.time() - debut
                vitesse_actuelle = (ecrit_total / (1024 * 1024)) / temps_ecoule
                temperature = surveiller_temperature_disque()
                print(f"Progression : {ecrit_total / (1024 * 1024):.2f} Mo écrits, "
                      f"vitesse actuelle : {vitesse_actuelle:.2f} Mo/s, Température : {temperature}°C")
        fin = time.time()
        temps_total = fin - debut
        vitesse_moyenne = taille_mo / temps_total
        return vitesse_moyenne
    except Exception as e:
        print(f"Erreur lors du test d'écriture : {e}")
        return None
    finally:
        if os.path.exists(fichier_test):
            os.remove(fichier_test)
def main():
    root = tk.Tk()
    root.withdraw()
    taille_mo = simpledialog.askinteger(
        "Taille du fichier",
        "Entrez la taille du fichier de test en Mo (par ex. 1000) :",
        minvalue=100,
        initialvalue=1000
    )
    if taille_mo is None:
        messagebox.showinfo("Annulation", "Le test a été annulé.")
        return
    chemin_dossier = filedialog.askdirectory(title="Sélectionnez un dossier pour le test")
    if not chemin_dossier:
        messagebox.showinfo("Annulation", "Le test a été annulé.")
        return
    messagebox.showinfo("Début du test", f"Test en cours avec un fichier de {taille_mo} Mo...")
    vitesse_ecriture = test_vitesse_ecriture_continue(chemin_dossier, taille_mo)
    if vitesse_ecriture:
        compatibilite = verifier_compatibilite_connexion(vitesse_ecriture)
        messagebox.showinfo(
            "Résultat du test",
            f"Vitesse moyenne d'écriture : {vitesse_ecriture:.2f} Mo/s\n\n{compatibilite}"
        )
    else:
        messagebox.showerror("Erreur", "Une erreur s'est produite lors du test d'écriture.")
if __name__ == "__main__":
    main()
