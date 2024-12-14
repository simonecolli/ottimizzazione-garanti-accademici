import os
import pandas as pd
import math

NUMERO_MINIMO_DI_INSEGNAMENTI = 9

class DatasetManager:
    """
    Classe per la gestione di file di dataset e la generazione di file ASP strutturati.
    """

    def __init__(self, dataset_path="dataset/"):
        """
        Inizializza la classe DatasetManager con il percorso della cartella contenente i file di dataset.
        :param dataset_path: Path alla cartella contenente i file di dataset (default: "dataset/").
        """
        self.dataset_path = dataset_path

    def get_departments(self):
        """
        Ottiene la lista dei dipartimenti basandosi sui file presenti nella cartella del dataset.
        :return: Una lista di dipartimenti (nomi dei file senza estensione).
        :raises FileNotFoundError: Se la cartella del dataset non esiste.
        """
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Errore: la cartella '{self.dataset_path}' non esiste.")

        departments = [
            os.path.splitext(filename)[0]
            for filename in os.listdir(self.dataset_path)
            if filename.endswith(".csv")
        ]
        return departments
    
    def get_courses(self):
        """
        Ottiene und dizionario {"codice_corso": "corso"} basandosi sui file presenti nella cartella del dataset.
        :return: Un dizionario di corsi.
        :raises FileNotFoundError: Se la cartella del dataset non esiste.
        """
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Errore: il file '{self.dataset_path}' non esiste.")
        
        df = pd.read_csv(self.dataset_path, dtype=str, sep=',')
        # print(df)
        return df.set_index("Cod. Corso di Studio")["Overview"].to_dict()
    
    def get_professors(self):
        """
        Ottiene und dizionario {"codice_corso": {"matricola"}} basandosi sui file presenti nella cartella del dataset.
        :return: Un dizionario di corsi: set_matricole.
        :raises FileNotFoundError: Se la cartella del dataset non esiste.
        """
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Errore: il file '{self.dataset_path}' non esiste.")
        
        with open(self.dataset_path) as f:
            # Skip prima riga
            f.readline()
            profs = dict()
            for line in f.readlines():
                code, mat = line.strip().split(",")
                if not code in profs:
                    profs[code] = set()
                
                profs[code].add(mat)
            return profs

    def get_sectors(self, SSD = None):
        """
        Ottiene la lista dei settori partendo da una lista di SSD.

        Ogni SSD è rappresentato nel formato "SETTORE/CODICE". Questa funzione estrae
        e restituisce solo la parte relativa al settore (prima del separatore '/').
        
        :param SSD: Una lista di stringhe rappresentanti i SSD. Ad esempio, ["INF/01", "MAT/03"].
        :type SSD: list[str], optional
        :return: Un set di settori se la lista passata come parametro è non vuota. 
                Ritorna un set vuoto se il parametro è None o vuoto.
        :rtype: set[str]

        :example:
        input: ["INF/01", "MAT/03", "FIS/07"]
        output: {"INF", "MAT", "FIS"}
        """
        if SSD:
            # print(SSD)
            items = set()
            for code in SSD:
                # Escludere None, NaN, o stringhe vuote
                if not code or not isinstance(code, str) or code.strip().lower() == 'nan':
                    continue
                # Estrae la parte prima di `/` per ogni elemento della lista
                spl = code.split('/')
                if len(spl) > 1:
                    items.add(spl[0])
            return items
        else:
            return set()
        
    def load_data(self, filename):
        """
        Legge i dati da un file di testo e li stampa.
        :param filename: Nome del file (senza estensione) da cui leggere i dati.
        :raises FileNotFoundError: Se il file specificato non esiste.
        :raises Exception: Per altri errori durante la lettura del file.
        """
        path = os.path.join(self.dataset_path, f'{filename}.csv')
        if not os.path.exists(path):
            raise FileNotFoundError(f"Errore: il file '{path}' non esiste.")

        try:
            with open(path, 'r') as file:
                content = file.read().strip()
                print(f"Contenuto di '{path}':")
                print(content)
        except Exception as e:
            raise Exception(f"Errore durante la lettura del file '{path}': {e}")

    def scrivi_ministeriali(self, df, filename):
        """
        Scrive i dati del DataFrame in un file ASP (.lp), organizzandoli per sezioni con eliminazione di duplicati.
        :param df: DataFrame contenente i dati da salvare. Deve contenere una colonna con il codice del corso,
                    il tipo di laurea secondo lo standard introdotto (ltss, lssm, ecc...), il numero di iscritti effettivi,
                    il numero massimo teorico (utilizzato per il calcolo della W)
        :param filename: Nome del file di output (senza estensione).
        :raises Exception: Per errori durante la scrittura del file.
        """
        
        output_dir = 'lp'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        comment_character = '% '
        filepath = os.path.join(output_dir, filename + '.lp')
        
        parametri_ministeriali_minimi = {
            "lt": (9, 5, 4, 2),
            "lm": (6, 4, 2, 1),
            "lm5": (15, 8, 7, 3),
            "lm6": (18, 10, 8, 4),
            "ltss": (5, 3, 2, 1),
            "ltsm": (5, 3, 2, 1),
            "ltps": (4, 2, 2, 1),
            "ltop": (4, 2, 2, 1),
            "lmss": (4, 2, 2, 1),
            "lmsm": (4, 2, 2, 1),
            "lmi": (3, 1, 2, 1)
        }

        try:
            with open(filepath, "w") as file:
                file.write(f"{comment_character} SEZIONE: Garanti minimi per corso (codice_corso, minimo_complessivo, docenti_ti, docenti_td, max_docenti_contratto)\n")

                # print(df)
                
                for _, row in df.iterrows():
                    tipo_corso = row["Cod. Tipo Corso"].lower()
                    codice_corso = row["Cod. Corso di Studio"]
                    
                    if tipo_corso in parametri_ministeriali_minimi:
                        minimo_complessivo, minimo_ti, massimo_td, massimo_contratti = parametri_ministeriali_minimi[tipo_corso]
                    else:
                        raise ValueError(f"Cod. Tipo Corso ({tipo_corso} ) non coerente per il corso {codice_corso}")
                    
                    if pd.isna(row['Immatricolati']):
                        pass
                    else:
                        immatricolati = int(row["Immatricolati"])

                        massimo_teorico = int(row["Massimo Teorico"])
                        w = (immatricolati / (1.0 * massimo_teorico)) - 1
                        
                        if w < 0:
                            w = 0

                        minimo_complessivo = math.floor(minimo_complessivo * (1 + w))
                        minimo_ti = math.floor(minimo_ti * (1 + w))
                        massimo_contratti = math.floor(massimo_contratti * (1 + w))

                    file.write(f"ministeriale({codice_corso}, {minimo_complessivo}, {minimo_ti}, {massimo_td}, {massimo_contratti}).\n")
            
            print(f"Dati salvati con successo in: {filepath}")
        except Exception as e:
            raise Exception(f"Errore durante il salvataggio dei dati su '{filepath}': {e}")
        
    def scrivi_coperture(self, df, filename):
        """
        Scrive i dati del DataFrame in un file ASP (.lp), organizzandoli per sezioni con eliminazione di duplicati.
        :param df: DataFrame contenente i dati da salvare.
        :param filename: Nome del file di output (senza estensione).
        :raises Exception: Per errori durante la scrittura del file.
        """
        # Crea la cartella 'lp' se non esiste
        output_dir = 'lp'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        comment_character = '% '
        # filepath = os.path.join(self.dataset_path, filename + '.lp')
        filepath = os.path.join(output_dir, filename + '.lp')

        # Set per tracciare valori già scritti
        docenti_aggiunti = set()
        corsi_aggiunti = set()
        tipi_corso_aggiunti = set()
        ssd_aggiunti = set()
        taf_aggiunti = set()

        # Rimuove eventuali NaN e converte i valori in numeri interi
        df['Cod. Corso di Studio'] = df['Cod. Corso di Studio'].fillna(0).astype(int)

        # Raggruppa per codice corso e conta le occorrenze
        conteggi = df['Cod. Corso di Studio'].value_counts()

        # Filtra il DataFrame mantenendo solo i codici corso con almeno 9 occorrenze
        codici_validi = conteggi[conteggi > NUMERO_MINIMO_DI_INSEGNAMENTI].index
        df = df[df['Cod. Corso di Studio'].isin(codici_validi)]

        print(conteggi)
        print(codici_validi)

        try:
            with open(filepath, 'w') as file:
                
                # Scrive la sezione dei tipi di corso
                file.write(f"{comment_character} SEZIONE: Tipi di Corso\n")
                for _, row in df.iterrows():
                    # Non posso usare le lettere in maiuscolo perchè possono essere scambiate per variabili e non atomi
                    tipo_corso = row['Cod. Tipo Corso'].lower()

                    if tipo_corso not in tipi_corso_aggiunti:
                        file.write(f"laurea({tipo_corso}).\n")
                        tipi_corso_aggiunti.add(tipo_corso)
                file.write("\n")

                # Scrive la sezione dei vari SSD
                file.write(f"{comment_character} SEZIONE: SSD\n")
                for _, row in df.iterrows():
                    
                    ssd = row['SSD'].split('/')
                    if len(ssd) < 2:
                        continue
                    
                    settore = ssd[0].lower()
                    settore = settore.replace('-', '')
                    numero = int(ssd[1])
                    
                    ssd = str(ssd)
                    if ssd not in ssd_aggiunti:
                        file.write(f"ssd({settore}, {numero}).\n")
                        ssd_aggiunti.add(ssd)
                file.write("\n")

                # Scrive la sezione dei TAF
                file.write(f"{comment_character} SEZIONE: TAF\n")
                for _, row in df.iterrows():
                    taf = row['TAF'].lower()

                    if taf not in taf_aggiunti:
                        # file.write(f"{comment_character} {nome_corso} ({codice_corso})\n")
                        file.write(f"taf({taf}).\n")
                        taf_aggiunti.add(taf)
                file.write("\n")

                # Scrive la sezione dei corsi
                file.write(f"{comment_character} SEZIONE: Corsi\n")
                for _, row in df.iterrows():
                    codice_corso = int(float(row['Cod. Corso di Studio']))
                    nome_corso = row['Des. Corso di Studio']

                    if codice_corso not in corsi_aggiunti:
                        file.write(f"{comment_character} {nome_corso} ({codice_corso})\n")
                        file.write(f"codice_corso({codice_corso}).\n")
                        corsi_aggiunti.add(codice_corso)
                file.write("\n")

                corsi_aggiunti = set()
                
                # Scrive le informazioni complete sui corsi
                file.write(f"{comment_character} SEZIONE: Informazioni Corsi\n")
                for _, row in df.iterrows():
                    codice_corso = int(float(row['Cod. Corso di Studio']))
                    prof = row['Cognome'] + " " + row['Nome']
                    tipo_corso = row['Cod. Tipo Corso'].lower()
                    
                    ssd = row['SSD'].split('/')
                    if len(ssd) < 2:
                        continue
                    settore = ssd[0].lower()
                    settore = settore.replace('-', '')
                    numero = int(ssd[1])
                    if codice_corso not in corsi_aggiunti:
                        file.write(f"{comment_character} Corso: {codice_corso} ({tipo_corso})\n")
                        file.write(f"corso({codice_corso}, {tipo_corso}, {settore}, {numero}) :- codice_corso({codice_corso}), laurea({tipo_corso}), ssd({settore}, {numero}).\n")
                        corsi_aggiunti.add(codice_corso)

                file.write("\n")
                
                
                # Scrive le relazioni tra corsi e docenti
                file.write(f"{comment_character} SEZIONE: Relazioni Corsi-Docenti\n")
                for _, row in df.iterrows():
                    if not row['Matricola'] or row['Matricola'] is None or row['Matricola'].lower() == 'nan':
                        continue
                    else:
                        matricola_docente = int(float(row['Matricola']))

                    codice_corso = int(float(row['Cod. Corso di Studio']))
                    nome_docente = row['Cognome'] + " " + row['Nome']
                    tipo_corso = row['Cod. Tipo Corso'].lower()
                    taf = row['TAF'].lower()

                    file.write(f"{comment_character} Corso: {codice_corso}, Docente: {nome_docente}\n")
                    file.write(f"cattedra({codice_corso}, {matricola_docente}, {tipo_corso}, {taf}) :- codice_corso({codice_corso}), matricola_docente({matricola_docente}), laurea({tipo_corso}), taf({taf}).\n")
                file.write("\n")

            print(f"Dati salvati con successo in: {filepath}")
        except Exception as e:
            raise Exception(f"Errore durante il salvataggio dei dati su '{filepath}': {e}")
    
    def scrivi_docenti(self, df, filename):
        """
        Scrive i dati del DataFrame in un file ASP (.lp), organizzandoli per sezioni con eliminazione di duplicati.
        :param df: DataFrame contenente i dati da salvare.
        :param filename: Nome del file di output (senza estensione).
        :raises Exception: Per errori durante la scrittura del file.
        """
        # Crea la cartella 'lp' se non esiste
        output_dir = 'lp'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        comment_character = '% '
        # filepath = os.path.join(self.dataset_path, filename + '.lp')
        filepath = os.path.join(output_dir, filename + '.lp')

        # Set per tracciare valori già scritti
        docenti_aggiunti = set()
        ssd_aggiunti = set()
        fascia_aggiunti = set()

        try:
            with open(filepath, 'w') as file:

                # Scrive la sezione dei vari SSD
                file.write(f"{comment_character} SEZIONE: SSD\n")
                for _, row in df.iterrows():
                    # Non posso usare le lettere in maiuscolo perchè possono essere scambiate per variabili e non atomi
                    ssd = row['SSD'].split('/')
                    settore = ssd[0].lower()
                    settore = settore.replace('-', '')
                    numero = int(ssd[1])
                    
                    ssd = str(ssd)
                    if ssd not in ssd_aggiunti:
                        file.write(f"ssd({settore}, {numero}).\n")
                        ssd_aggiunti.add(ssd)
                file.write("\n")

                # Scrive la sezione delle fasce dei contratti
                file.write(f"{comment_character} SEZIONE: FASCIE\n")
                for _, row in df.iterrows():
                    fascia = row['Fascia']
                    if 'ricercatore' in fascia.lower():
                        fascia = 'td'
                    else:
                        fascia = 'ti'

                    if fascia not in fascia_aggiunti:
                        file.write(f"fascia({fascia}).\n")
                        fascia_aggiunti.add(fascia)
                file.write("\n")

                # Scrive la sezione dei docenti
                file.write(f"{comment_character} SEZIONE: Docenti\n")
                for _, row in df.iterrows():
                    if not row['Matricola'] or row['Matricola'] is None or row['Matricola'].lower() == 'nan':
                        continue
                    else:
                        matricola_docente = int(float(row['Matricola']))
                    
                    ssd = row['SSD'].split('/')
                    settore = ssd[0].lower()
                    settore = settore.replace('-', '')
                    numero = int(ssd[1])
                    ssd = str(ssd)

                    nome_docente = row['Cognome e Nome']

                    if matricola_docente not in docenti_aggiunti:
                        file.write(f"{comment_character} {nome_docente} ({matricola_docente}), SSD caratterizzante: {settore}/{numero}\n")
                        file.write(f"matricola_docente({matricola_docente}).\n")
                        docenti_aggiunti.add(matricola_docente)
                docenti_aggiunti = set() # reset docenti aggiunti
                file.write("\n")

                # Scrive la sezione dei docenti
                file.write(f"{comment_character} SEZIONE: SSD caratterizzante dei docenti\n")
                for _, row in df.iterrows():
                    if not row['Matricola'] or row['Matricola'] is None or row['Matricola'].lower() == 'nan':
                        continue
                    else:
                        matricola_docente = int(float(row['Matricola']))
                    
                    fascia = row['Fascia']
                    if 'ricercatore' in fascia.lower():
                        fascia = 'td'
                    else:
                        fascia = 'ti'

                    ssd = row['SSD'].split('/')
                    settore = ssd[0].lower()
                    settore = settore.replace('-', '')
                    numero = int(ssd[1])
                    ssd = str(ssd)

                    nome_docente = row['Cognome e Nome']

                    if matricola_docente not in docenti_aggiunti:
                        file.write(f"{comment_character} {nome_docente} ({matricola_docente}), SSD caratterizzante: {settore}/{numero}\n")
                        file.write(f"docente({matricola_docente}, {fascia}, {settore}, {numero}) :- matricola_docente({matricola_docente}), fascia({fascia}), ssd({settore}, {numero}).\n")
                        docenti_aggiunti.add(matricola_docente)
                file.write("\n")

            print(f"Dati salvati con successo in: {filepath}")
        except Exception as e:
            raise Exception(f"Errore durante il salvataggio dei dati su '{filepath}': {e}")
        
    def scrivi_docenti_a_contratto(self, df, filename):
        """
        Scrive i dati del DataFrame in un file ASP (.lp), organizzandoli per sezioni con eliminazione di duplicati.
        :param df: DataFrame contenente i dati da salvare.
        :param filename: Nome del file di output (senza estensione).
        :raises Exception: Per errori durante la scrittura del file.
        """
        SKIP = True

        # Crea la cartella 'lp' se non esiste
        output_dir = 'lp'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        comment_character = '% '
        # filepath = os.path.join(self.dataset_path, filename + '.lp')
        filepath = os.path.join(output_dir, filename + '.lp')

        # Set per tracciare valori già scritti
        docenti_aggiunti = set()

        try:
            with open(filepath, 'w') as file:

                # Scrive la sezione delle fasce dei contratti
                file.write(f"{comment_character} SEZIONE: FASCIE\n")
                file.write(f"fascia(c).\n")
                file.write("\n")

                # Scrive la sezione dei docenti
                file.write(f"{comment_character} SEZIONE: Docenti\n")
                
                if SKIP:
                    file.write(f"jolly(1).\n")
                else:
                    for _, row in df.iterrows():
                        if not row['Matricola'] or row['Matricola'] is None or str(row['Matricola']).lower() == 'nan':
                            continue
                        else:
                            matricola_docente = int(float(row['Matricola']))

                        nome_docente = row['Cognome'] + " " + row['Nome']

                        if matricola_docente not in docenti_aggiunti:
                            file.write(f"{comment_character} {nome_docente} ({matricola_docente}), docente a contratto\n")
                            file.write(f"matricola_docente({matricola_docente}).\n")
                            file.write(f"jolly({matricola_docente}).\n")
                            docenti_aggiunti.add(matricola_docente)
                    docenti_aggiunti = set() # reset docenti aggiunti
                    file.write("\n")        

            print(f"Dati salvati con successo in: {filepath}")
        except Exception as e:
            raise Exception(f"Errore durante il salvataggio dei dati su '{filepath}': {e}")