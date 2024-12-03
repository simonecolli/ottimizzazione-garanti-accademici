# %%
import pandas as pd
import openpyxl
import re

path_ns_coperture = "dataset/coperture.xlsx"
path_ns_docenti = "dataset/docenti.xlsx"

path_coperture = "dataset/coperture_sanitized.xlsx"
path_docenti = "dataset/docenti_sanitized.xlsx"


def aggiorna_cod_tipo_corso(row):
    descrizione = row['Des. Corso di Studio']
    tipo_corso = row['Cod. Tipo Corso']
    descrizione = descrizione.lower()
    tipo_corso = tipo_corso.lower()

    # TODO aggiungere LT a orient. profess.
    # Regole di aggiornamento
    if re.search(r'(?i)(?=.*serviz)(?=.*social)', descrizione):
        if tipo_corso == 'lt':
            return 'LTSS'
        elif tipo_corso == 'lm':
            return 'LMSS'
    elif 'scienze motorie' in descrizione and tipo_corso == 'lt':
        return 'LTSM'
    elif 'professione sanitaria' in descrizione and tipo_corso == 'lt':
        return 'LTPS'
    elif 'infermieristic' in descrizione and tipo_corso == 'lm':
        return 'LMI'
    
    elif re.search(r'(?i)(?=.*scienz)(?=.*motor)', descrizione) and tipo_corso == 'lm':
        return 'LMSM'
    
    raise ValueError(f"Valore non mappato: {descrizione.lower()}, {tipo_corso.lower()}")

# %%
def sanitize_docenti():
    df = pd.read_excel(path_ns_docenti, engine="openpyxl", dtype=str)
    # rimozioni .
    df["Matricola"] = df["Matricola"].str.replace(".", "")
    # rimozioni ,
    df["Matricola"] = df["Matricola"].str.replace(",", "")
    
    # print(df)
    df["Matricola"] = df["Matricola"].astype(int)
    df["Matricola"] = df["Matricola"].astype(str)
    # salvataggio
    df.to_excel(path_docenti, index=False)
    
# %%
def sanitize_coperture():
    df = pd.read_excel(path_ns_coperture, engine="openpyxl", dtype=str)
    # print(df)
    # Rimuovere le righe che hanno il campo matricola vuoto
    df = df.dropna(subset=["Matricola"])
    # print(df)
    df["Matricola"] = df["Matricola"].astype(int)
    # print(df)
    df["Matricola"] = df["Matricola"].astype(str)
    # astype
    matricole = pd.read_excel(path_docenti, engine="openpyxl", dtype=str)["Matricola"]
    # print(matricole)
    df = df[df["Matricola"].isin(matricole)]
    
    # Sostituzione l con lt
    df.loc[df["Cod. Tipo Corso"].str.lower() == "l", "Cod. Tipo Corso"] = "LT"
    
    stringhe_da_cercare = ["professione sanitaria", "scienze motorie", "infermieristic"]
    
    regex = "|".join(stringhe_da_cercare)
    regex_ss = r'(?i)(?=.*serviz)(?=.*social)'
    regex_sm = r'(?i)(?=.*scienz)(?=.*motor)'
    
    filtered_df = df[
        (df["Des. Corso di Studio"].str.contains(regex, na=False, flags=re.IGNORECASE)) |
        (df["Des. Corso di Studio"].str.contains(regex_ss, na=False, flags=re.IGNORECASE)) |
        (df["Des. Corso di Studio"].str.contains(regex_sm, na=False, flags=re.IGNORECASE))
    ]
    
    filtered_df["Cod. Tipo Corso"] = filtered_df.apply(aggiorna_cod_tipo_corso, axis=1)
    
    keys = ["Cod. Corso di Studio", "Cod. Tipo Corso"]
    
    filtered_df = filtered_df[keys].drop_duplicates(subset=['Cod. Corso di Studio'])
    
    # filtered_df.to_csv('filtered_data.csv', index=False)
    
    mapping = filtered_df.set_index("Cod. Corso di Studio")["Cod. Tipo Corso"].to_dict()
    
    # print(mapping)
    
    df["Cod. Tipo Corso"] = df["Cod. Corso di Studio"].map(mapping).fillna(df["Cod. Tipo Corso"])
    
    df.to_excel(path_coperture, index=False)
# %%
def sanitize():
    sanitize_docenti()
    sanitize_coperture()

# %%
if __name__ == "__main__":
    sanitize()
# %%
