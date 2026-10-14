# Référence de l'API Flask

Cette API expose les données LCR et le cycle de vie des ajustements manuels.
Toutes les routes commencent par `/api` et échangent des représentations JSON
d'objets métier, sauf la réponse vide du `DELETE`.

Un « objet » désigne ici une structure JSON composée de propriétés. L'API ne
transmet pas directement des objets Python ou Pydantic : Pydantic valide le
contrat côté serveur, puis Flask le sérialise en JSON pour le transport HTTP.

## Démarrage et Swagger

```bash
cd flask_streamlit_app
source .venv/bin/activate
python -m api.app
```

- URL de base : `http://127.0.0.1:5000`
- Swagger UI : `http://127.0.0.1:5000/apidocs`
- Spécification OpenAPI JSON : `http://127.0.0.1:5000/apispec_1.json`

## Vue d'ensemble

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/api/health` | Vérifier que Flask répond |
| `GET` | `/api/asofdates` | Lister les dates d'arrêté |
| `GET` | `/api/asofdates/{asofdate}/versions` | Lister les versions d'une date |
| `GET` | `/api/asofdates/{asofdate}/latest-active-adjustment` | Trouver le dernier ajustement actif antérieur |
| `GET` | `/api/lcr-summary` | Agréger la situation LCR |
| `GET` | `/api/adjustments` | Consulter le registre |
| `POST` | `/api/adjustments` | Créer un bloc d'ajustement |
| `DELETE` | `/api/adjustments/{adjustment_id}` | Supprimer toutes les lignes d'un bloc |

## Objets JSON échangés

### Cardinalité par route

| Route | Requête | Réponse réussie |
|---|---|---|
| `GET /api/health` | aucun corps | un objet de statut |
| `GET /api/asofdates` | aucun corps | un tableau de chaînes `date` |
| `GET /api/asofdates/{asofdate}/versions` | aucun corps | un tableau de chaînes `date-time` |
| `GET /api/lcr-summary` | paramètres d'URL | un objet `LcrSummary` |
| `GET /api/asofdates/{asofdate}/latest-active-adjustment` | aucun corps | un objet `AdjustmentRegistryBlockResponse` ou `null` |
| `GET /api/adjustments` | aucun corps | un tableau d'objets `AdjustmentRegistryBlockResponse` |
| `POST /api/adjustments` | un objet `AdjustmentBatchRequest` | un objet `AdjustmentCreationResponse` |
| `DELETE /api/adjustments/{adjustment_id}` | aucun corps | aucun corps (`204`) |

### `AdjustmentAmounts`

Représente les montants d'une ligne d'ajustement. Les montants sont exprimés
en euros complets et doivent être des nombres finis.

| Propriété JSON | Type | Obligatoire | Valeur par défaut |
|---|---|---:|---:|
| `ldpImpactLcrReglementaire` | nombre | oui | — |
| `ldpImpactLcrGestion` | nombre | oui | — |
| `impactLcrInflow` | nombre | non | `0` |
| `impactLcrOutflow` | nombre | non | `0` |
| `impactLcrAsset` | nombre | non | `0` |
| `impactLcrAssetCash` | nombre | non | `0` |

### `AdjustmentBatchRequest`

Objet reçu par `POST /api/adjustments`.

| Propriété JSON | Type | Obligatoire | Règle |
|---|---|---:|---|
| `asofdate` | chaîne `date` | oui | format `YYYY-MM-DD` |
| `asofdateflowVersion` | chaîne `date-time` | oui | format ISO 8601 |
| `adjustments` | tableau d'`AdjustmentAmounts` | oui | entre 1 et 100 éléments |

### `AdjustmentCreationResponse`

Objet retourné après la création transactionnelle d'un bloc.

| Propriété JSON | Type | Description |
|---|---|---|
| `adjustmentId` | chaîne `UUID` | identifiant commun à toutes les lignes créées |
| `lineCount` | entier | nombre de lignes créées |
| `status` | chaîne | toujours `ACTIVE` à la création |

### `AdjustmentLineResponse`

Représente un deal fictif actif relu depuis `public.completude_table`.

| Propriété JSON | Type | Description |
|---|---|---|
| `biId` | chaîne | identifiant unique de la ligne |
| `tradeNo` | entier | numéro de trade fictif généré |
| `ldpImpactLcrReglementaire` | nombre | impact réglementaire en euros |
| `ldpImpactLcrGestion` | nombre | impact gestion en euros |
| `impactLcrInflow` | nombre | impact inflow en euros |
| `impactLcrOutflow` | nombre | impact outflow en euros |
| `impactLcrAsset` | nombre | impact asset en euros |
| `impactLcrAssetCash` | nombre | impact asset cash en euros |

### `AdjustmentRegistryBlockResponse`

Représente un bloc du registre et contient ses lignes actives.

| Propriété JSON | Type | Nullable | Description |
|---|---|---:|---|
| `adjustmentId` | chaîne `UUID` | non | identifiant du bloc |
| `asofdate` | chaîne `date` | non | date d'arrêté ajustée |
| `asofdateflowVersion` | chaîne `date-time` | non | version ajustée |
| `createdAt` | chaîne `date-time` | non | date de création |
| `createdBy` | chaîne | non | auteur de la création |
| `status` | chaîne | non | `ACTIVE` ou `DELETED` |
| `deletedAt` | chaîne `date-time` | oui | date de suppression |
| `deletedBy` | chaîne | oui | auteur de la suppression |
| `lastEventAt` | chaîne `date-time` | non | création ou suppression la plus récente |
| `lines` | tableau d'`AdjustmentLineResponse` | non | lignes actives, vide si le bloc est supprimé |

Un bloc `ACTIVE` possède des propriétés `deletedAt` et `deletedBy` à `null`.
Un bloc `DELETED` possède son audit de suppression et un tableau `lines` vide.

### `LcrSummary`

Objet retourné par `GET /api/lcr-summary`. `rows` contient les montants agrégés
par `productLine`; `total` contient la somme de toutes les lignes.

| Propriété JSON | Type | Description |
|---|---|---|
| `asofdate` | chaîne `date` | date interrogée |
| `asofdateflowVersion` | chaîne `date-time` | version interrogée |
| `rows` | tableau de `LcrSummaryRow` | agrégats par `productLine` |
| `total` | objet `LcrSummaryTotal` | somme de toutes les lignes |

Un objet `LcrSummaryRow` contient `productLine` (chaîne), puis les quatre
montants numériques `amount0d`, `amount30d`, `lcrReglementaire` et
`lcrGestion`. Un objet `LcrSummaryTotal` contient les quatre mêmes montants,
sans `productLine`.

### `ErrorResponse`

Toutes les réponses d'erreur JSON utilisent le même objet :

| Propriété JSON | Type | Description |
|---|---|---|
| `error` | chaîne | message lisible, sans détail PostgreSQL sensible |

## Format des erreurs

Les erreurs ont toujours une propriété `error` :

```json
{
  "error": "La date doit utiliser le format YYYY-MM-DD."
}
```

Les erreurs techniques psycopg2 ne sont jamais retournées au client. Une erreur
de base non prévue produit uniquement :

```json
{
  "error": "Une erreur PostgreSQL est survenue."
}
```

---

## GET `/api/health`

Vérifie uniquement que le processus Flask fonctionne. Cette route ne teste pas
la connexion PostgreSQL.

```bash
curl http://127.0.0.1:5000/api/health
```

Réponse `200 OK` :

```json
{
  "status": "ok"
}
```

---

## GET `/api/asofdates`

Retourne les dates distinctes présentes dans `public.completude_table`, de la
plus récente à la plus ancienne.

```bash
curl http://127.0.0.1:5000/api/asofdates
```

Réponse `200 OK` :

```json
[
  "2026-10-05",
  "2026-10-04"
]
```

Réponse `500 Internal Server Error` si PostgreSQL est indisponible :

```json
{
  "error": "Impossible de charger les dates d'arrêté."
}
```

---

## GET `/api/asofdates/{asofdate}/versions`

Retourne les versions disponibles pour une date. `asofdate` doit respecter le
format ISO `YYYY-MM-DD`.

```bash
curl http://127.0.0.1:5000/api/asofdates/2026-10-05/versions
```

Réponse `200 OK` :

```json
[
  "2026-10-06T15:30:00",
  "2026-10-06T09:00:00"
]
```

Réponse `400 Bad Request` pour `/api/asofdates/05-10-2026/versions` :

```json
{
  "error": "La date doit utiliser le format YYYY-MM-DD."
}
```

---

## GET `/api/lcr-summary`

Agrège les lignes de `public.completude_table` par `product_line` pour un
contexte précis. La réponse est un objet `LcrSummary`.

Paramètres de requête :

| Paramètre | Format | Obligatoire | Exemple |
|---|---|---:|---|
| `asofdate` | date ISO | oui | `2026-10-05` |
| `version` | date-heure ISO | oui | `2026-10-06T15:30:00` |

```bash
curl --get http://127.0.0.1:5000/api/lcr-summary \
  --data-urlencode "asofdate=2026-10-05" \
  --data-urlencode "version=2026-10-06T15:30:00"
```

Réponse `200 OK` :

```json
{
  "asofdate": "2026-10-05",
  "asofdateflowVersion": "2026-10-06T15:30:00",
  "rows": [
    {
      "productLine": "LOAN",
      "amount0d": 1000000.0,
      "amount30d": 750000.0,
      "lcrReglementaire": 250000.0,
      "lcrGestion": 200000.0
    }
  ],
  "total": {
    "amount0d": 1000000.0,
    "amount30d": 750000.0,
    "lcrReglementaire": 250000.0,
    "lcrGestion": 200000.0
  }
}
```

Réponse `400 Bad Request` si un paramètre manque ou n'est pas une valeur ISO.

---

## GET `/api/asofdates/{asofdate}/latest-active-adjustment`

Retourne le bloc d'ajustement `ACTIVE` dont l'`asofdate` est la plus récente
parmi les dates strictement antérieures à la date sélectionnée. Si plusieurs
blocs existent pour cette date, le dernier bloc créé est retenu. Ses lignes
sont relues depuis `public.completude_table` grâce aux `bi_id`. La réponse est
un objet `AdjustmentRegistryBlockResponse` ou la valeur JSON `null`.

```bash
curl http://127.0.0.1:5000/api/asofdates/2026-10-10/latest-active-adjustment
```

Réponse `200 OK` abrégée :

```json
{
  "adjustmentId": "a2432f6a-2142-41de-a34b-6ec75625a346",
  "asofdate": "2026-10-05",
  "asofdateflowVersion": "2026-10-06T15:30:00",
  "status": "ACTIVE",
  "lines": [
    {
      "biId": "824a1434-8a25-4588-a91c-406ea02b4aef",
      "tradeNo": 123456789,
      "ldpImpactLcrReglementaire": 5000000.0,
      "ldpImpactLcrGestion": 250000.0
    }
  ]
}
```

Si aucun ajustement actif et antérieur n'existe, la route retourne toujours
`200 OK`, avec le JSON suivant :

```json
null
```

Une date identique à la date sélectionnée n'est jamais retenue, car la règle
utilise volontairement une comparaison stricte `<`.

---

## GET `/api/adjustments`

Retourne les blocs actifs et supprimés, triés du dernier événement au plus
ancien. Pour un bloc actif, `lines` est relu depuis `completude_table` grâce aux
`bi_id`. Pour un bloc supprimé, `lines` est vide. La réponse est un tableau
d'objets `AdjustmentRegistryBlockResponse`, éventuellement vide.

```bash
curl http://127.0.0.1:5000/api/adjustments
```

Réponse `200 OK` abrégée :

```json
[
  {
    "adjustmentId": "a2432f6a-2142-41de-a34b-6ec75625a346",
    "asofdate": "2026-10-05",
    "asofdateflowVersion": "2026-10-06T15:30:00",
    "createdAt": "2026-10-09T09:15:00",
    "createdBy": "local_user",
    "status": "ACTIVE",
    "deletedAt": null,
    "deletedBy": null,
    "lastEventAt": "2026-10-09T09:15:00",
    "lines": [
      {
        "biId": "824a1434-8a25-4588-a91c-406ea02b4aef",
        "tradeNo": 123456789,
        "ldpImpactLcrReglementaire": 5000000.0,
        "ldpImpactLcrGestion": 250000.0,
        "impactLcrInflow": 0.0,
        "impactLcrOutflow": 0.0,
        "impactLcrAsset": 0.0,
        "impactLcrAssetCash": 0.0
      }
    ]
  }
]
```

---

## POST `/api/adjustments`

Crée de 1 à 100 deals fictifs dans une seule transaction PostgreSQL. Toutes les
lignes reçoivent le même `adjustment_id`, mais chacune reçoit son propre `bi_id`
et son propre `TradeNo`. La requête utilise l'objet `AdjustmentBatchRequest` et
la réponse l'objet `AdjustmentCreationResponse`.

### Corps JSON

Le tableau `adjustments` contient de 1 à 100 objets `AdjustmentAmounts`. Les
champs non déclarés dans ces objets sont refusés.

```bash
curl --request POST http://127.0.0.1:5000/api/adjustments \
  --header "Content-Type: application/json" \
  --data '{
    "asofdate": "2026-10-05",
    "asofdateflowVersion": "2026-10-06T15:30:00",
    "adjustments": [
      {
        "ldpImpactLcrReglementaire": 5000000,
        "ldpImpactLcrGestion": 250000,
        "impactLcrInflow": 100000
      },
      {
        "ldpImpactLcrReglementaire": -1000000,
        "ldpImpactLcrGestion": -500000,
        "impactLcrAsset": 200000
      }
    ]
  }'
```

Réponse `201 Created` :

```json
{
  "adjustmentId": "a2432f6a-2142-41de-a34b-6ec75625a346",
  "lineCount": 2,
  "status": "ACTIVE"
}
```

Si une seule insertion échoue, toute la transaction est annulée : aucun deal
du bloc et aucune entrée de registre ne sont conservés.

Réponse `400 Bad Request` typique :

```json
{
  "error": "Le champ 'adjustments.0.ldpImpactLcrGestion' est obligatoire."
}
```

---

## DELETE `/api/adjustments/{adjustment_id}`

Supprime toutes les lignes `completude_table` associées au bloc, puis marque
l'entrée du registre `DELETED`. Le registre conserve uniquement les métadonnées
d'audit ; la liste des `bi_id` est vidée.

```bash
curl --request DELETE \
  http://127.0.0.1:5000/api/adjustments/a2432f6a-2142-41de-a34b-6ec75625a346
```

Réponse réussie : `204 No Content`, sans corps JSON.

| Code | Signification |
|---:|---|
| `400` | `adjustment_id` n'est pas un UUID |
| `404` | aucun ajustement ne possède cet identifiant |
| `409` | ajustement déjà supprimé ou lignes actives incomplètes |
| `500` | erreur PostgreSQL masquée au client |

## Ordre d'appel recommandé

```text
GET /api/asofdates
    → GET /api/asofdates/{asofdate}/versions
        → GET /api/lcr-summary
            → POST /api/adjustments
                → GET /api/lcr-summary
                → GET /api/adjustments
                    → DELETE /api/adjustments/{adjustment_id}
```

Après un `POST` ou un `DELETE`, rechargez le résumé LCR et le registre afin
d'afficher les données actualisées.
