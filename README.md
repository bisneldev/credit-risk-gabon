# 🏦 Analyse du Risque Crédit Bancaire — Contexte Gabon

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.1-150458.svg)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18-3F4F75.svg)](https://plotly.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Système d'aide à la décision pour l'analyse du risque crédit, adapté au contexte bancaire gabonais et conforme aux principes de classification **COBAC**.

---

## 🎯 Objectif

Analyser un portefeuille de **32 084 crédits bancaires** pour :
- **Mesurer** le taux de défaut global et par segment
- **Identifier** les caractéristiques associées au risque
- **Fournir** un outil d'aide à la décision (dashboard interactif + reporting)
- **Simuler** une classification COBAC des créances

---

## 📊 Résultats clés

| Indicateur | Valeur |
|-----------|--------|
| 📥 Observations initiales | **32 581** |
| ✨ Observations après nettoyage | **32 084** |
| 📉 Taux de défaut global | **21,89 %** |
| 💰 Encours total | **18,95 Mds FCFA** |
| 🔻 Perte potentielle (LGD 60 %) | **2,71 Mds FCFA** |

### 🔍 Facteurs de risque identifiés

| Facteur | Impact observé |
|---------|----------------|
| ⚠️ **Incidents de paiement (24 mois)** | **× 5** de risque (73,66 % vs 14,78 %) |
| 💳 **Microfinance / Crédit PME** | 35,3 % / 31,1 % de défaut |
| 🏭 **Secteur Agriculture / BTP** | 29,8 % / 27,2 % de défaut |
| 📊 **Ratio d'effort élevé** | Corrélation +0,14 |

---

## 🏛️ Matrice COBAC (simulation)

| Catégorie | Part portefeuille | Taux de défaut observé |
|-----------|-------------------|------------------------|
| 1. Saine | 86,16 % | **14,10 %** ✅ |
| 2. Observation | 0,77 % | 35,48 % ⚠️ |
| 3. Douteuse | 12,45 % | **72,62 %** 🔴 |
| 4. Litigieuse | 0,62 % | 68,84 % 🔴 |

> Le système **sépare efficacement** les bons clients (Saine : 14 %) des mauvais (Douteuse : 73 %) — **écart de 5×**.

---

## 🛠️ Architecture du projet

```
credit-risk-gabon/
├── data/
│   ├── raw/                    # Données brutes
│   └── processed/              # Données nettoyées
├── database/
│   └── credit_risk.db          # Base SQLite
├── src/
│   ├── data_loader_gabon.py    # Génération des données
│   ├── diagnostic.py           # Étape 1 : Diagnostic
│   ├── cleaning.py             # Étape 2 : Nettoyage
│   ├── eda.py                  # Étape 3 : Analyse exploratoire
│   └── sql_analysis.py         # Étape 4 : Analyse SQL
├── dashboard/
│   └── app.py                  # Étape 5 : Dashboard Dash
├── reports/
│   ├── eda/                    # 10 graphiques HTML
│   ├── sql/                    # 10 exports CSV
│   └── screenshots/            # Captures du dashboard
├── requirements.txt
└── README.md
```

---

## 🚀 Installation & Lancement

### 1. Cloner le projet
```bash
git clone https://github.com/TON_USERNAME/credit-risk-gabon.git
cd credit-risk-gabon
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Générer les données et exécuter le pipeline

```bash
# Étape 1 : Génération des données
python src/data_loader_gabon.py

# Étape 2 : Diagnostic
python src/diagnostic.py

# Étape 3 : Nettoyage
python src/cleaning.py

# Étape 4 : Analyse exploratoire (génère 10 graphiques HTML)
python src/eda.py

# Étape 5 : Analyse SQL (crée la base + 10 CSV)
python src/sql_analysis.py

# Étape 6 : Lancer le dashboard interactif
python dashboard/app.py
```

### 5. Ouvrir le dashboard

Dans ton navigateur : **http://127.0.0.1:8050**

---

## 📸 Aperçu du dashboard

### Vue globale
![Dashboard global](reports/screenshots/dashboard_global.png)

### Focus secteur Agriculture (le plus risqué)
![Dashboard Agriculture](reports/screenshots/dashboard_agriculture.png)

---

## 🔬 Stack technique

| Domaine | Outils |
|---------|--------|
| **Langage** | Python 3.10+ |
| **Data** | Pandas, NumPy |
| **Base de données** | SQLite, SQLAlchemy |
| **Visualisation** | Plotly Express, Plotly Graph Objects |
| **Dashboard** | Dash |
| **Modélisation** | Scikit-learn (à venir) |

---

## 💡 Perspectives d'évolution

- 🤖 **Modèle prédictif** de scoring crédit (Random Forest, XGBoost)
- 📡 **API REST** (FastAPI) pour intégration au SI bancaire
- 📈 **Reporting automatique** PDF/Excel conforme COBAC
- 🔔 **Alertes** en temps réel sur dégradation de segments
- 🌍 **Extension** : scoring multi-pays CEMAC

---

## 👤 Auteur

**Bisneldev**
- 🎓 Ingénierie Financière — Sciences et Techniques Comptables et Financières
- 💼 Finance, Audit, Contrôle de gestion + Développement d'applications
- 📧 bisneldev@gmail.com
- 💼 [LinkedIn](https://www.linkedin.com/in/bisnel-n-078ba5197/)

---

## 📄 Licence

Ce projet est sous licence MIT — voir le fichier [LICENSE](LICENSE) pour plus de détails.