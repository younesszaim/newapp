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

La prochaine étape ajoutera la connexion PostgreSQL et l'endpoint des dates
d'arrêté, sans encore construire le reste des écrans.
