# Validation client — LCR Adjustment

Ce document sert de fil conducteur pour la revue du prototype Figma, puis de
l'application de démonstration. Toutes les valeurs présentées au client doivent
être fictives.

## Objectif de la session

Valider que les utilisateurs comprennent le parcours sans explication
technique : sélectionner un contexte, lire la situation LCR, créer un
ajustement, puis le retrouver ou le supprimer dans le registre.

## Écrans à présenter dans Figma

1. **Création — aucun contexte sélectionné**
   - date d'arrêté disponible ;
   - version désactivée tant que la date n'est pas choisie.
2. **Création — situation LCR chargée**
   - quatre cartes KPI ;
   - tableau AG Grid par Product Line ;
   - formulaire avec deux montants principaux.
3. **Champs avancés**
   - Inflow, Outflow, Asset et Asset Cash ;
   - valeurs initialisées à zéro.
4. **Aperçu avant création**
   - contexte sélectionné ;
   - valeurs actuelles et projetées ;
   - aucune écriture en base à cette étape.
5. **Confirmation de création**
   - action explicite ;
   - possibilité d'annuler.
6. **Registre**
   - filtres date/version ;
   - statuts Actif et Supprimé ;
   - détail d'un ajustement.
7. **Confirmation de suppression**
   - rappel du contexte ;
   - explication de la conservation de la trace d'audit.
8. **États transverses**
   - chargement, liste vide, erreur API et confirmation de succès.

## Prototype cliquable attendu

```text
Création vide
    → choix de la date
    → choix de la version
    → situation LCR + formulaire
    → aperçu
    → confirmation
    → succès
    → registre
    → détail
    → confirmation de suppression
```

Le bouton de confirmation finale doit être volontairement distinct du bouton
de prévisualisation. La suppression ne doit jamais être déclenchée par un seul
clic depuis le tableau.

## Questions à poser aux clients

1. Comprenez-vous immédiatement quelle date et quelle version sont ajustées ?
2. Les quatre KPI suffisent-ils pour prendre la décision ?
3. Les termes « réglementaire », « gestion », « inflow » et « outflow » sont-ils
   assez explicites ?
4. Quelles informations doivent absolument apparaître dans l'aperçu ?
5. Le registre contient-il les bons critères de recherche ?
6. La différence entre un ajustement Actif et Supprimé est-elle claire ?
7. Qui doit être autorisé à créer et à supprimer un ajustement ?

## Critères de validation

- le parcours principal est réalisable sans aide ;
- les montants sont compris comme des euros complets ;
- aucune action irréversible n'est ambiguë ;
- les libellés métier sont approuvés ;
- les informations d'audit répondent au besoin de contrôle ;
- les retours sont classés en **bloquant**, **important** ou **confort**.

## Déroulé conseillé

- 5 minutes de contexte et objectifs ;
- 10 minutes de test silencieux par le client ;
- 10 minutes de questions et commentaires Figma ;
- 5 minutes pour confirmer les décisions et les priorités.

Éviter de guider l'utilisateur pendant les dix premières minutes : les hésitations
observées sont précisément les informations utiles pour améliorer l'interface.
