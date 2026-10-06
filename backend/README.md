# Backend FastAPI

Ce dossier contient l'API de **LCR Adjustment**.

## Rôle des fichiers de l'étape 1

- `app/main.py` crée FastAPI, configure CORS et expose `/api/health`.
- `app/config.py` lit la configuration depuis l'environnement et `.env`.
- `.env.example` documente les variables attendues sans contenir de secret.
- `requirements.txt` liste les bibliothèques Python.

## Démarrage

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Vérification :

```bash
curl http://localhost:8000/api/health
```

Réponse attendue :

```json
{"status":"ok","application":"LCR Adjustment API"}
```

La documentation interactive est disponible sur <http://localhost:8000/docs>.

## Pourquoi CORS ?

Angular tourne sur le port `4200` et FastAPI sur le port `8000`. Pour un
navigateur, ce sont deux origines distinctes. CORS autorise explicitement
`http://localhost:4200` à appeler l'API pendant le développement.
