import os
import zipfile
import argparse
import pandas as pd
from pathlib import Path

def create_zip(zip_filename, files):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))

def find_and_zip_files(base_path):
    os.makedirs("zips", exist_ok=True)
    for root, dirs, files in os.walk(base_path):
        if root.endswith("Bundle/Resources/translations"):
            xliff_files = [os.path.join(root, f) for f in files if f.startswith("messages.") and f.endswith(".xliff")]
            if xliff_files:
                # Get the first level directory name
                first_level_dir = root.split(os.sep)[-3]
                zip_filename = os.path.join("zips", f"{first_level_dir}.zip")
                create_zip(zip_filename, xliff_files)
                print(f"Created {zip_filename} with {len(xliff_files)} files.")
                transform_zip_to_csv(zip_filename)

def extract_value(line):
    """Extraire la valeur entre "<![CDATA[" et "]]>" dans une ligne."""
    start_index = line.find('<![CDATA[') + len('<![CDATA[')
    end_index = line.find(']]>', start_index)
    return line[start_index:end_index]

def transform_zip_to_csv(zip_filename):
    os.makedirs("csv", exist_ok=True)
    csv_filename = 'csv/' + os.path.splitext(os.path.split(zip_filename)[-1])[0] + '.csv'

    # Extraire les fichiers XLIFF du fichier ZIP
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall("extracted_xliff")

    # Trouver tous les fichiers XLIFF dans le répertoire d'extraction
    xliff_files = [f for f in os.listdir("extracted_xliff") if f.endswith('.xliff')]

    # Créer un dictionnaire pour stocker les données CSV
    csv_data = {}

    # Parcourir tous les fichiers XLIFF et extraire les données
    for xliff_file in xliff_files:
        domain, lang = xliff_file.split('.')[:-1]
        with open(os.path.join("extracted_xliff", xliff_file), 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if '<source>' in line:
                    key = extract_value(line)
                    csv_data.setdefault(key, {'Domain': domain})
                elif '<target>' in line:
                    value = extract_value(line)
                    csv_data[key].setdefault(lang, []).append(value)

    # Regrouper les valeurs de csv_data pour n'avoir qu'une seule ligne par clé
    for key, values in csv_data.items():
        if len(values) > 1:
            for lang, value_list in values.items():
                if lang != 'Domain':
                    values[lang] = '; '.join(value_list)

    # Créer un DataFrame à partir des données regroupées
    df = pd.DataFrame(csv_data).T.reset_index().rename(columns={'index': 'Key'})
    df.to_csv(csv_filename, encoding='utf-8', index=False, header=True)

def main():
    parser = argparse.ArgumentParser(description="Create ZIP archives of messages.<lang>.xliff files.")
    parser.add_argument("base_path", help="The base path to start the search from.")
    args = parser.parse_args()

    find_and_zip_files(args.base_path)

    with pd.ExcelWriter("traductions.xlsx") as writer:
        for root, dirs, files in os.walk("csv/"):
            for file in files:
                if file.endswith(".csv"):
                    csv_filepath = os.path.join(root, file)
                    sheet_name = os.path.splitext(file)[0]
                    df = pd.read_csv(csv_filepath)
                    df.to_excel(writer, sheet_name=sheet_name, index=False, header=True)

if __name__ == "__main__":
    main()