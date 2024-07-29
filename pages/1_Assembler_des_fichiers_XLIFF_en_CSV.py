import streamlit as st
import pandas as pd
import os
import base64
from zipfile import ZipFile

st.set_page_config(page_title="Assembler des fichiers XLIFF en un fichier CSV", page_icon="📈")

def extract_value(line):
    """Extraire la valeur entre "<![CDATA[" et "]]>" dans une ligne."""
    start_index = line.find('<![CDATA[') + len('<![CDATA[')
    end_index = line.find(']]>', start_index)
    return line[start_index:end_index]

st.title('Assembler des fichiers XLIFF en un fichier CSV')

# Téléverser un fichier ZIP contenant les fichiers XLIFF
zip_file = st.file_uploader('Téléverser un fichier ZIP contenant les fichiers XLIFF :', type='zip')
if zip_file:
    zip_filename = zip_file.name
    csv_filename = os.path.splitext(zip_filename)[0] + '.csv'

    # Extraire les fichiers XLIFF du fichier ZIP
    with ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall()

    # Trouver tous les fichiers XLIFF dans le répertoire courant
    xliff_files = [f for f in os.listdir('.') if f.endswith('.xliff')]

    # Créer un dictionnaire pour stocker les données CSV
    csv_data = {}

    # Parcourir tous les fichiers XLIFF et extraire les données
    for xliff_file in xliff_files:
        domain, lang = xliff_file.split('.')[:-1]
        with open(xliff_file, 'r', encoding='utf-8') as f:
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

    # Télécharger le fichier CSV
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{csv_filename}">Télécharger le fichier CSV</a>'
    st.markdown(href, unsafe_allow_html=True)
    
    # Afficher le DataFrame
    st.write(df)

