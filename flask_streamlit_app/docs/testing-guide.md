# Guide pédagogique des tests

La suite utilise uniquement `unittest`, fourni avec Python. Les appels HTTP,
PostgreSQL et Streamlit sont simulés : les exemples sont rapides et ne peuvent
pas modifier la base réelle.

## Exécuter tous les tests

```bash
cd flask_streamlit_app
source .venv/bin/activate
python -m unittest discover -s tests -v
```

L'option `-v` affiche le nom de chaque exemple. Les avertissements Streamlit
« No runtime found » sont normaux : l'interface est volontairement testée sans
serveur ni navigateur.

## Lire un test : Arrange, Act, Assert

Chaque exemple suit trois petites étapes :

```python
# Arrange : préparer un faux curseur PostgreSQL.
cursor = FakeCursor([{"asofdate": date(2026, 10, 5)}])

# Act : appeler la vraie fonction.
result = list_asofdates(FakeConnection(cursor))

# Assert : vérifier le résultat et la requête.
self.assertEqual(result, ["2026-10-05"])
self.assertIn("DISTINCT asofdate", cursor.query)
```

`FakeCursor` et `FakeConnection` sont définis dans `tests/fakes.py`. Ils ne
reproduisent que les quelques méthodes psycopg2 utilisées par le projet. Cela
rend les exemples plus lisibles qu'un mock générique.

## Correspondance entre le code et les exemples

| Module testé | Fonctions couvertes | Fichier d'exemples |
|---|---|---|
| `api.app` | `create_app`, health check | `tests/test_database_and_app.py` |
| `api.database` | `database_connection` avec et sans URL | `tests/test_database_and_app.py` |
| `api.context_repository` | `list_asofdates`, `list_versions` | `tests/test_context_repository.py` |
| `api.context_routes` | succès, date invalide, erreur de configuration | `tests/test_context_routes.py` |
| `api.lcr_repository` | `get_lcr_summary_rows` et paramètres SQL | `tests/test_lcr_repository.py` |
| `api.lcr_service` | `build_lcr_summary` et calcul des totaux | `tests/test_lcr.py` |
| `api.lcr_routes` | succès et paramètres manquants | `tests/test_lcr.py` |
| `api.adjustment_repository` | toutes les lectures, insertions, mises à jour et suppressions | `tests/test_adjustment_repository.py` |
| `api.adjustment_service` | validation, nombres, TradeNo, création, registre et suppression | `tests/test_adjustments.py` |
| `api.adjustment_routes` | GET, POST, DELETE et entrées invalides | `tests/test_adjustments.py` |
| `streamlit_app` | HTTP, cache, formatage, pages, grille, registre et navigation | `tests/test_streamlit_app.py` |

## Exécuter un seul fichier

Pour apprendre une partie à la fois :

```bash
python -m unittest tests.test_context_repository -v
python -m unittest tests.test_lcr -v
python -m unittest tests.test_adjustment_repository -v
python -m unittest tests.test_adjustments -v
python -m unittest tests.test_streamlit_app -v
```

## Exécuter un seul exemple

Le nom complet cible une seule méthode :

```bash
python -m unittest \
  tests.test_adjustments.AdjustmentTest.test_lines_share_one_registry_block \
  -v
```

Cet exemple montre que deux lignes sont insérées séparément dans
`completude_table`, mais qu'une seule insertion est faite dans
`adjustment_registry`.

## Comprendre les mocks

Exemple d'un appel HTTP Streamlit simulé :

```python
@patch("streamlit_app.requests.post")
def test_save_adjustments_posts_one_batch(self, post):
    post.return_value.json.return_value = {"adjustmentId": "id-1"}

    result = save_adjustments("2026-10-05", "version-1", [{"amount": 100}])

    self.assertEqual(result["adjustmentId"], "id-1")
```

`patch` remplace temporairement `requests.post`. Le test vérifie donc la
construction de la requête sans démarrer Flask et sans envoyer de données.

## Ajouter un nouvel exemple

Lorsqu'une fonction est ajoutée :

1. choisir le fichier correspondant à sa couche ;
2. tester un cas nominal avec une valeur concrète ;
3. tester au moins une entrée invalide si la fonction valide des données ;
4. vérifier les paramètres SQL ou HTTP, pas seulement la valeur retournée ;
5. relancer toute la suite avant le commit.
