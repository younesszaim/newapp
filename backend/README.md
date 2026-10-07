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
- `sql/create_adjustment_registry.sql` crée le registre et ses index de manière
  idempotente : le script peut être rejoué sans recréer la table.
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

## Tests automatisés

Les tests métier utilisent des repositories simulés. Ils ne lisent ni ne
modifient la base Supabase et peuvent donc être lancés sans `DATABASE_URL` :

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v
```

Ils couvrent notamment la création, le refus d'un doublon actif, la suppression
et la conservation de la trace d'audit.

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

## Résumé LCR

```text
GET /api/lcr-summary?asofdate=2026-10-05&version=2026-10-06T15:30:00
        ↓
lcr_router.get_lcr_summary()
        ↓
lcr_service.build_lcr_summary()
        ↓
lcr_repository.get_lcr_summary_rows()
        ↓
GROUP BY product_line dans PostgreSQL
```

Le repository récupère les agrégats. Le service calcule ensuite la ligne
`total` et recherche l'ajustement actif dans `adjustment_registry`. Le router
renvoie finalement le contrat JSON validé par les schémas Pydantic de
`app/schemas/lcr.py`.

Exemple abrégé :

```json
{
  "rows": [{ "productLine": "LOAN", "amount0d": 45000 }],
  "total": { "amount0d": 57000 },
  "hasAdjustment": false,
  "adjustment": null
}
```

## Création transactionnelle

`POST /api/adjustments` reçoit le contexte commun et une liste de 1 à 100 deals
fictifs. Chaque ligne contient les six montants. Les champs techniques sont
appliqués par `ADJUSTMENT_DEFAULTS` dans `app/config.py`.

```text
POST /api/adjustments
        ↓
génération d'un adjustment_id commun
        ↓
pour chaque ligne : génération bi_id et TradeNo
        ↓
INSERT public.completude_table
        ↓ après toutes les lignes, même connexion / même transaction
INSERT d'un bloc dans public.adjustment_registry avec les bi_id
        ↓
COMMIT automatique à la fin de la requête
```

Si une insertion échoue, le context manager psycopg2 de `database.py` annule
le lot complet. Le registre contient un bloc `ACTIVE` par validation utilisateur,
et plusieurs blocs peuvent partager la même date et la même version. Le endpoint
GET relit les lignes actives directement depuis `completude_table`. Une suppression
efface toutes les lignes du bloc puis vide ses `bi_id` ; seuls le statut `DELETED`,
la date et l'auteur de suppression sont conservés.

## Pourquoi CORS ?

Angular tourne sur le port `4200` et FastAPI sur le port `8000`. Pour un
navigateur, ce sont deux origines distinctes. CORS autorise explicitement
`http://localhost:4200` à appeler l'API pendant le développement.
