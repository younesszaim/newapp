# LCR Adjustments — Flask + Streamlit

Cette version reconstruit progressivement l'application LCR existante avec :

- Flask pour l'API HTTP ;
- Streamlit pour l'interface utilisateur ;
- PostgreSQL avec `psycopg2` pour conserver la même base de données.

## Étape 1 — démarrer le squelette

Depuis le dossier `flask_streamlit_app` :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Terminal 1 — API Flask :

```bash
source .venv/bin/activate
python -m api.app
```

Terminal 2 — interface Streamlit :

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Ouvrez ensuite `http://localhost:8501`. L'écran doit afficher
« API Flask connectée ».

La documentation Swagger de l'API est accessible à l'adresse :

```text
http://127.0.0.1:5000/apidocs
```

Vous pouvez y ouvrir `GET /api/health`, cliquer sur **Try it out**, puis sur
**Execute** pour tester l'endpoint sans utiliser `curl`.

## Structure

```text
flask_streamlit_app/
├── api/
│   ├── __init__.py
│   └── app.py          # API Flask
├── .env.example        # exemple sans mot de passe réel
├── requirements.txt
└── streamlit_app.py    # interface Streamlit
```

## Étape 2 — connexion PostgreSQL et dates d'arrêté

Dans `.env`, remplacez la valeur d'exemple de `DATABASE_URL` par votre vraie
chaîne de connexion PostgreSQL. Ne commitez jamais ce fichier.

Une fois Flask redémarré :

- `GET /api/asofdates` retourne les dates disponibles ;
- Swagger permet de tester le endpoint depuis `/apidocs` ;
- Streamlit affiche ces dates dans le sélecteur « Date d'arrêté ».

La prochaine étape ajoutera les versions disponibles pour la date sélectionnée.
