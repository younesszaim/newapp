# LCR Adjustments — Flask + Streamlit

Cette version reconstruit progressivement l'application LCR existante avec :

- Flask pour l'API HTTP ;
- Streamlit pour l'interface utilisateur ;
- PostgreSQL avec `psycopg2` pour conserver la même base de données.

Documentation complémentaire :

- [étapes détaillées de développement](docs/development-steps.md) ;
- [référence complète des routes API](docs/api-reference.md) ;
- [guide pédagogique des tests](docs/testing-guide.md) ;
- [création SQL du registre des ajustements](sql/create_adjustment_registry.sql).

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

## Étape 3 — versions dépendantes de la date

`GET /api/asofdates/{asofdate}/versions` retourne les versions PostgreSQL de
la date choisie. Streamlit affiche automatiquement le second sélecteur après
la sélection d'une date.

## Étape 4 — résumé LCR

`GET /api/lcr-summary?asofdate=...&version=...` agrège les données par
`product_line`. Streamlit affiche les quatre totaux dans des cartes, puis les
lignes dans un tableau interactif.

## Étape 5 — saisie multi-lignes

Streamlit utilise `st.data_editor` pour ajouter ou supprimer des lignes. Les
colonnes LCR réglementaire et LCR gestion sont obligatoires ; les quatre autres
valent zéro lorsqu'elles sont vides. `POST /api/adjustments` enregistre le lot
dans une seule transaction et crée un seul `adjustment_id` dans le registre.

## Étape 6 — registre et suppression groupée

Le menu Streamlit sépare maintenant la création et le registre. Chaque bloc du
registre affiche son `adjustment_id`, son contexte, son statut et ses lignes
actives relues depuis `completude_table`. La suppression efface toutes les
lignes du bloc et conserve uniquement le statut `DELETED`, la date et l'auteur.

La prochaine étape appliquera le thème visuel CACIB et finalisera l'expérience
utilisateur.

### Visualisation du registre

Le registre propose des filtres Date d'arrêté et Version, trois indicateurs de
synthèse et deux onglets séparant les blocs actifs des blocs supprimés. Tous les
résultats sont triés par dernier événement : création pour un bloc actif,
suppression pour un bloc supprimé.
