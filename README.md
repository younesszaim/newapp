# LCR Adjustment

Application interne simple permettant de créer et suivre des trades fictifs
d'ajustement LCR.

## Architecture

```text
Navigateur
   ↓
Composant Angular
   ↓
Service Angular (HttpClient)
   ↓ HTTP / JSON
Routeur FastAPI
   ↓
Service métier
   ↓
Repository (SQL explicite)
   ↓
Supabase PostgreSQL
```

Angular ne se connecte jamais directement à PostgreSQL. Le mot de passe de la
base reste uniquement dans `backend/.env`.

## État actuel : étape 15

- frontend Angular standalone avec routing ;
- Tailwind CSS configuré ;
- navigation vers Créer un ajustement et Registre ;
- backend FastAPI avec CORS ;
- configuration par variables d'environnement ;
- endpoint de contrôle `GET /api/health`.
- connexion PostgreSQL avec psycopg2 ;
- SQL explicite dans un repository ;
- endpoint `GET /api/asofdates`.
- endpoint `GET /api/asofdates/{asofdate}/versions`.
- service Angular utilisant `HttpClient` ;
- sélecteur Date d'arrêté / Version alimenté par l'API ;
- état local géré avec des signaux Angular.
- table `public.adjustment_registry` avec historique des suppressions ;
- endpoint `GET /api/lcr-summary` ;
- agrégation SQL unique avec `GROUP BY product_line` ;
- total et détection d'un ajustement actif.
- tableau Angular de la situation LCR par Product Line ;
- totaux affichés dans quatre cartes KPI au-dessus de la grille, sans ligne de
  données TOTAL ;
- formatage réutilisable en `K€`, `M€` et `Bn€` avec valeur exacte en
  infobulle.
- tableau implémenté avec AG Grid Community et thème Quartz personnalisé CACIB.
- AG Grid éditable pour saisir plusieurs deals fictifs ;
- colonnes obligatoires identifiées par `*` et contrôlées ligne par ligne ;
- colonnes optionnelles clairement indiquées et converties à zéro si vides ;
- endpoint batch transactionnel `POST /api/adjustments` ;
- insertion atomique de toutes les lignes dans `completude_table` et
  `adjustment_registry` ;
- plusieurs ajustements actifs autorisés pour une même date/version ;
- dialogue Angular présentant le nombre de lignes et les totaux avant validation ;
- appel POST du lot uniquement après confirmation ;
- rechargement du résumé depuis PostgreSQL après création.
- endpoint `GET /api/adjustments` incluant actifs et supprimés ;
- page Registre avec filtres, statuts et vue de détail ;
- snapshot des montants conservé dans le registre pour l'audit.
- endpoint transactionnel `DELETE /api/adjustments/{adjustment_id}` ;
- suppression du trade et passage du registre à `DELETED` avec date et auteur ;
- dialogue de confirmation dans le registre avant toute suppression.
- tests backend isolés couvrant création, doublon, suppression et audit.

Le test réel de PostgreSQL nécessite un `DATABASE_URL` valide dans
`backend/.env`.

## Lancer Angular

```bash
cd frontend
npm install
npm start
```

Puis ouvrir <http://localhost:4200>.

## Lancer FastAPI

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

L'API est sur <http://localhost:8000> et Swagger sur
<http://localhost:8000/docs>.

## Notions Angular introduites

- **Composant standalone** : une partie autonome de l'interface, sans `NgModule`.
- **Routing** : associe une URL à un composant. Par exemple `/ajustements`
  affiche la page du registre.
- **Injection de dépendances** : Angular fournira `HttpClient` aux services qui
  en ont besoin. `provideHttpClient()` l'enregistre une seule fois au démarrage.
- **Chargement différé** : `loadComponent` charge le code d'une page lorsqu'elle
  est visitée.

## Lancer les tests

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v

cd ../frontend
npm test -- --watch=false
```

## Prochaine étape

Valider la nouvelle saisie multi-lignes avec les utilisateurs métier.
