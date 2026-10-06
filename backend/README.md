# Backend FastAPI

Ce dossier contient l'API de **LCR Adjustment**.

## Rôle des fichiers

- `app/main.py` crée FastAPI, configure CORS et expose `/api/health`.
- `app/config.py` lit la configuration depuis l'environnement et `.env`.
- `app/database.py` charge `DATABASE_URL`, puis ouvre et ferme une connexion
  psycopg2 par requête.
- `app/routers/context_router.py` reçoit les requêtes HTTP de contexte.
- `app/repositories/lcr_repository.py` contient le SQL lisible exécuté sur
  `public.completude_table`.
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

## Premier flux PostgreSQL

Lorsque Angular appellera `GET /api/asofdates`, le trajet sera :

```text
GET /api/asofdates
        ↓
context_router.list_asofdates()
        ↓
lcr_repository.get_asofdates()
        ↓
SELECT DISTINCT asofdate FROM public.completude_table
        ↓
["2026-10-05", "2026-10-04"]
```

FastAPI convertit automatiquement les objets Python `date` en chaînes JSON au
format ISO `YYYY-MM-DD`.

La liste des versions utilise la date sélectionnée :

```text
GET /api/asofdates/2026-10-05/versions
        ↓
SELECT DISTINCT asofdateflow_version
FROM public.completude_table
WHERE asofdate = 2026-10-05
        ↓
["2026-10-06T11:45:00"]
```

Dans le code SQL, la date est transmise avec `%s`. Ce paramétrage empêche
l'injection SQL et laisse psycopg2 convertir correctement la date Python.

## Pourquoi CORS ?

Angular tourne sur le port `4200` et FastAPI sur le port `8000`. Pour un
navigateur, ce sont deux origines distinctes. CORS autorise explicitement
`http://localhost:4200` à appeler l'API pendant le développement.
