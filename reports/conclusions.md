# 📌 Synthèse analytique — Analyse du Risque Crédit

## 1. Périmètre de l'étude

- **32 581** crédits initialement chargés
- **32 084** crédits après nettoyage (taux de conservation : **98,47 %**)
- Période couverte : portefeuille représentatif de 7 villes du Gabon

## 2. Taux de défaut global

| Métrique | Valeur |
|----------|--------|
| Taux de défaut | **21,89 %** |
| Nombre de défauts | **7 023** |
| Encours total | 18,95 Mds FCFA |
| Encours en défaut | 4,52 Mds FCFA |
| Perte potentielle (LGD 60 %) | 2,71 Mds FCFA |

## 3. Facteurs de risque identifiés

### 3.1 🚨 Incidents de paiement (facteur n°1)
- **Sans incidents** : 14,78 % de défaut
- **Avec incidents (24 mois)** : 73,66 % de défaut
- **→ Multiplication du risque par 5**

### 3.2 💳 Type de produit

| Produit | Taux de défaut |
|---------|---------------|
| Microfinance | 35,34 % 🔴 |
| Crédit PME | 31,06 % 🔴 |
| Crédit consommation | 24,54 % |
| Découvert | 18,38 % |
| Crédit auto | 15,30 % |
| Crédit immobilier | 12,10 % 🟢 |
| Crédit scolaire | 12,08 % 🟢 |

### 3.3 🏭 Secteur d'activité

- **Agriculture** : 29,80 % (le plus risqué)
- **BTP** : 27,17 %
- **Fonction publique** : 16,91 % (le plus sûr)

### 3.4 📊 Ratio d'effort

- Corrélation avec le défaut : **+0,14** (modérée mais significative)
- Les clients à taux d'effort > 40 % concentrent la majorité des défauts

### 3.5 🗺️ Concentration géographique

- **Libreville** concentre **45,36 %** de l'encours
- **Tchibanga** affiche le taux de défaut le plus élevé : **24,16 %**

## 4. Classification COBAC

| Catégorie | % portefeuille | Taux défaut observé | Encours (Mds FCFA) |
|-----------|---------------|---------------------|---------------------|
| Saine | 86,16 % | 14,10 % | 15,85 |
| Observation | 0,77 % | 35,48 % | 0,30 |
| Douteuse | 12,45 % | 72,62 % | 2,45 |
| Litigieuse | 0,62 % | 68,84 % | 0,35 |

**Lecture** : la classification COBAC **discrimine correctement** les profils à risque. Les clients classés "Saine" ont un taux de défaut **5 fois inférieur** à celui des "Douteuses".

## 5. Recommandations opérationnelles

### Priorité 1 — Gestion du risque immédiat
- 🎯 **Renforcer le scoring d'entrée** sur les produits Microfinance et Crédit PME
- 🔍 **Contrôle renforcé** sur les secteurs Agriculture et BTP
- ⚠️ **Exclure systématiquement** les clients avec incidents de paiement < 24 mois

### Priorité 2 — Pilotage
- 📊 **Dashboard mensuel** à destination du comité des risques
- 📈 **Suivi trimestriel** de la classification COBAC
- 💼 **Reporting réglementaire** automatisé

### Priorité 3 — Transformation digitale
- 🤖 **Industrialiser le scoring** avec un modèle ML (RF/XGBoost)
- 🔗 **Connecter au SI bancaire** via API
- 📱 **Application mobile** pour les agents de crédit

## 6. Pistes de suivi

1. **Modélisation prédictive** : Random Forest / XGBoost avec validation croisée
2. **Backtesting** : validation sur données historiques réelles
3. **Stress tests** : simulation de scénarios macro-économiques (baisse du PIB, hausse du chômage)
4. **Détection de dérive** : monitoring mensuel du modèle

---

*Rapport généré dans le cadre d'un projet de démonstration — les données sont synthétiques et ne reflètent pas la situation réelle d'une banque gabonaise.*