# Étapes de développement — Flask + Streamlit

Ce document retrace la construction de l'application. Chaque étape correspond
à un commit autonome afin de pouvoir lire, tester ou restaurer progressivement
le projet.

## 1. Squelette Flask et Streamlit

Commit : `8e952a9`

- création du dossier `flask_streamlit_app` ;
- endpoint Flask `GET /api/health` ;
- première page Streamlit ;
- configuration locale avec `.env` ;
- séparation des dépendances dans `requirements.txt`.

Validation : démarrer Flask et Streamlit, puis vérifier que l'interface affiche
« API Flask connectée ».

## 2. Documentation Swagger

Commit : `938a252`

- intégration de Flasgger ;
- Swagger UI sur `http://127.0.0.1:5000/apidocs` ;
- documentation et test interactif du health check.

## 3. Connexion PostgreSQL et dates d'arrêté

Commit : `a832e08`

- connexion `psycopg2` alimentée par `DATABASE_URL` ;
- curseur `RealDictCursor` ;
- endpoint `GET /api/asofdates` ;
- premier sélecteur Streamlit ;
- tests sans modifier la base réelle.

## 4. Versions dépendantes de la date

Commit : `473fb56`

- endpoint `GET /api/asofdates/{asofdate}/versions` ;
- requête SQL paramétrée ;
- validation du format `YYYY-MM-DD` ;
- second sélecteur Streamlit dépendant du premier.

## 5. Résumé LCR

Commit : `8685b34`

- endpoint `GET /api/lcr-summary` ;
- agrégation SQL par `product_line` ;
- quatre totaux LCR ;
- cartes KPI et tableau Streamlit.

## 6. Saisie multi-lignes

Commit : `572a5bc`

- grille éditable avec `st.data_editor` ;
- LCR réglementaire et LCR gestion obligatoires ;
- Inflow, Outflow, Asset et Asset Cash optionnels, avec zéro par défaut ;
- limite de 100 lignes ;
- endpoint transactionnel `POST /api/adjustments` ;
- un `adjustment_id` commun, un `bi_id` et un `TradeNo` par ligne.

## 7. Registre et suppression groupée

Commit : `f20a03b`

- endpoint `GET /api/adjustments` ;
- lecture des lignes actives depuis `completude_table` par leurs `bi_id` ;
- endpoint `DELETE /api/adjustments/{adjustment_id}` ;
- suppression physique de toutes les lignes du bloc ;
- conservation du statut `DELETED`, de la date et de l'auteur uniquement.

## 8. Visualisation simplifiée du registre

Commit : `b04bbb2`

- filtres Date d'arrêté et Version ;
- compteurs de blocs et de lignes ;
- séparation Actifs / Supprimés ;
- détails repliés pour éviter un écran rempli de lignes ;
- tri par dernier événement.

## 9. Contrats Pydantic pour les ajustements

- `AdjustmentAmounts` valide chaque ligne et conserve les montants en
  `Decimal` ;
- `AdjustmentBatchRequest` valide le contexte et la limite de 1 à 100 lignes ;
- `AdjustmentCreationResponse` garantit la structure de la réponse `201` ;
- les alias Pydantic conservent le contrat JSON camelCase existant ;
- les champs inconnus sont refusés afin de détecter immédiatement une faute de
  frappe côté client.

Pydantic est utilisé à la frontière HTTP, car les données JSON doivent être
analysées et validées. Une `dataclass` serait préférable pour un objet métier
interne déjà fiable, mais elle ne remplace pas cette validation d'entrée.

## 10. Configuration et erreurs centralisées

- `Settings` charge et valide `DATABASE_URL`, `CREATED_BY` et le délai de
  connexion depuis `.env` ;
- `get_settings()` met la configuration en cache ;
- les services utilisent des exceptions métier explicites pour les erreurs
  `404`, `409` et `500` ;
- Flask transforme ces exceptions dans un format JSON commun ;
- un gestionnaire PostgreSQL masque les détails techniques au client ;
- les routes ne répètent plus les mêmes blocs `try/except`.

## 11. Modèles Pydantic du registre

- `AdjustmentLineResponse` représente une ligne active issue de
  `completude_table` ;
- `AdjustmentRegistryBlockResponse` représente un bloc actif ou supprimé ;
- les `UUID`, dates, statuts et montants sont typés ;
- les montants restent en `Decimal` dans Python et sont sérialisés comme nombres
  JSON ;
- un validateur garantit qu'un bloc supprimé possède son audit et ne conserve
  aucune ligne.

## 12. Dataclasses pour les résultats PostgreSQL

- `AdjustmentTradeRecord` représente une ligne SQL active ;
- `RegistryBlockRecord` représente un bloc SQL et ses lignes ;
- `RegistryBlockLockRecord` contient uniquement les données nécessaires à une
  suppression verrouillée ;
- les objets utilisent `frozen=True` et `slots=True` pour être immuables et
  légers ;
- le repository transforme les résultats `RealDictCursor` en dataclasses ;
- le service transforme ensuite ces objets internes en modèles Pydantic HTTP.

La séparation est volontaire : les dataclasses représentent des données déjà
issues de PostgreSQL, tandis que Pydantic valide les données externes et le
contrat JSON.

## 13. Dernier ajustement actif antérieur

- ajout de `GET /api/asofdates/{asofdate}/latest-active-adjustment` ;
- recherche uniquement des blocs `ACTIVE` avec `asofdate < date sélectionnée` ;
- tri par `asofdate DESC`, puis `created_at DESC`, avec un seul résultat ;
- relecture des lignes actives dans `completude_table` à partir des `bi_id` ;
- réponse `200 OK` avec le bloc Pydantic existant, ou `null` sans résultat ;
- mutualisation de la requête qui charge les trades par `bi_id` ;
- tests d'exemple pour le repository, le service et la route Flask.

## Préparer la base

Exécuter [create_adjustment_registry.sql](../sql/create_adjustment_registry.sql)
une seule fois dans l'éditeur SQL Supabase. Le script utilise `IF NOT EXISTS`,
il peut donc être rejoué sans recréer la table ou les index.

La table métier `public.completude_table` doit déjà exister. Le projet ne la
crée pas et ne modifie pas sa structure.

## Lancer le projet

```bash
cd flask_streamlit_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Renseigner `DATABASE_URL` dans `.env`, puis ouvrir deux terminaux :

```bash
# Terminal 1
python -m api.app

# Terminal 2
streamlit run streamlit_app.py
```

Adresses utiles :

- Streamlit : `http://localhost:8501` ;
- Swagger : `http://127.0.0.1:5000/apidocs` ;
- health check : `http://127.0.0.1:5000/api/health`.

## Exécuter les tests

```bash
python -m unittest discover -s tests -v
```

Les tests simulent les repositories PostgreSQL. Ils vérifient les règles métier
sans injecter ni supprimer de données dans Supabase.
