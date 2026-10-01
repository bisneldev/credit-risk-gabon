"""
Modèle prédictif de scoring crédit
Contexte : Banque gabonaise - Conforme COBAC
Modèles : Random Forest + XGBoost
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, roc_auc_score, roc_curve,
    confusion_matrix, precision_recall_curve, average_precision_score
)

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("⚠️  XGBoost non installé - utilisation Random Forest uniquement")


# =====================================================================
# FEATURES & ENCODAGE
# =====================================================================
CAT_COLS = ['ville', 'secteur_activite', 'type_emploi',
            'type_produit', 'garantie']

NUM_COLS = [
    'age', 'anciennete_client_mois', 'revenu_mensuel_fcfa',
    'montant_credit_fcfa', 'duree_mois', 'taux_interet',
    'ratio_endettement', 'nb_incidents_24m', 'nb_credits_en_cours',
    'taux_effort'
]


def preparer_features(df, encoders=None, fit=True):
    """
    Encode les variables catégorielles + sélectionne les features.
    Retourne (X, y, encoders).
    """
    df = df.copy()
    
    if fit or encoders is None:
        encoders = {}
        for col in CAT_COLS:
            le = LabelEncoder()
            df[f'{col}_enc'] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
    else:
        for col in CAT_COLS:
            le = encoders[col]
            # Gérer les valeurs inconnues
            df[f'{col}_enc'] = df[col].astype(str).apply(
                lambda x: le.transform([x])[0] 
                if x in le.classes_ else -1
            )
    
    features = NUM_COLS + [f'{c}_enc' for c in CAT_COLS]
    X = df[features]
    y = df['defaut'] if 'defaut' in df.columns else None
    
    return X, y, encoders, features


# =====================================================================
# ENTRAÎNEMENT
# =====================================================================
def entrainer_modeles(df, test_size=0.25, random_state=42):
    """
    Entraîne et compare plusieurs modèles.
    Retourne un dict avec tous les résultats.
    """
    print("=" * 70)
    print("🤖 ENTRAÎNEMENT DES MODÈLES DE SCORING CRÉDIT")
    print("=" * 70)
    
    # ---- Préparation ----
    X, y, encoders, features = preparer_features(df, fit=True)
    
    print(f"\n📊 Dataset : {len(X):,} lignes × {len(features)} features")
    print(f"📉 Taux de défaut : {y.mean()*100:.2f}%")
    print(f"\n🔀 Split : {(1-test_size)*100:.0f}% train / {test_size*100:.0f}% test")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"   • Train : {len(X_train):,} lignes")
    print(f"   • Test  : {len(X_test):,} lignes")
    
    # ---- Modèles à comparer ----
    modeles = {
        'Logistic Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(
                max_iter=2000, class_weight='balanced', 
                random_state=random_state
            ))
        ]),
        'Random Forest': RandomForestClassifier(
            n_estimators=200, max_depth=12, 
            class_weight='balanced', random_state=random_state, n_jobs=-1
        ),
    }
    
    if HAS_XGBOOST:
        # Calcul du ratio pour XGBoost
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
        modeles['XGBoost'] = XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            scale_pos_weight=scale_pos_weight,
            random_state=random_state, eval_metric='logloss'
        )
    
    # ---- Entraînement & évaluation ----
    resultats = {}
    
    for nom, modele in modeles.items():
        print(f"\n{'─' * 70}")
        print(f"🎯 {nom}")
        print(f"{'─' * 70}")
        
        # Entraînement
        modele.fit(X_train, y_train)
        
        # Prédictions
        y_pred = modele.predict(X_test)
        y_proba = modele.predict_proba(X_test)[:, 1]
        
        # Métriques
        auc = roc_auc_score(y_test, y_proba)
        ap = average_precision_score(y_test, y_proba)
        report = classification_report(y_test, y_pred, output_dict=True)
        cm = confusion_matrix(y_test, y_pred)
        
        print(f"   🎯 AUC-ROC        : {auc:.4f}")
        print(f"   🎯 Avg Precision  : {ap:.4f}")
        print(f"   🎯 Precision défaut : {report['1']['precision']:.4f}")
        print(f"   🎯 Recall défaut    : {report['1']['recall']:.4f}")
        print(f"   🎯 F1-score défaut  : {report['1']['f1-score']:.4f}")
        print(f"\n   Matrice de confusion :")
        print(f"      Vrais négatifs  : {cm[0,0]:,}")
        print(f"      Faux positifs   : {cm[0,1]:,}")
        print(f"      Faux négatifs   : {cm[1,0]:,}")
        print(f"      Vrais positifs  : {cm[1,1]:,}")
        
        resultats[nom] = {
            'modele': modele,
            'auc': auc,
            'avg_precision': ap,
            'report': report,
            'confusion_matrix': cm,
            'y_pred': y_pred,
            'y_proba': y_proba,
        }
    
    # ---- Sélection du meilleur modèle ----
    meilleur_nom = max(resultats, key=lambda k: resultats[k]['auc'])
    meilleur = resultats[meilleur_nom]
    
    print(f"\n{'=' * 70}")
    print(f"🏆 MEILLEUR MODÈLE : {meilleur_nom}")
    print(f"   AUC-ROC = {meilleur['auc']:.4f}")
    print(f"{'=' * 70}")
    
    return {
        'resultats': resultats,
        'meilleur_nom': meilleur_nom,
        'meilleur_modele': meilleur['modele'],
        'encoders': encoders,
        'features': features,
        'X_test': X_test,
        'y_test': y_test,
    }


# =====================================================================
# FEATURE IMPORTANCE
# =====================================================================
def calculer_importance(meilleur_modele, features):
    """Calcule l'importance des features"""
    # Pipeline : prendre le classifieur final
    if hasattr(meilleur_modele, 'named_steps'):
        modele_final = list(meilleur_modele.named_steps.values())[-1]
    else:
        modele_final = meilleur_modele
    
    if hasattr(modele_final, 'feature_importances_'):
        imp = modele_final.feature_importances_
    elif hasattr(modele_final, 'coef_'):
        imp = np.abs(modele_final.coef_[0])
    else:
        return None
    
    df_imp = pd.DataFrame({
        'feature': features,
        'importance': imp
    }).sort_values('importance', ascending=False)
    
    # Normaliser en %
    df_imp['importance_pct'] = (
        df_imp['importance'] / df_imp['importance'].sum() * 100
    ).round(2)
    
    return df_imp


# =====================================================================
# SCORING 0-1000
# =====================================================================
def convertir_en_score(proba, method='linear'):
    """
    Convertit une probabilité de défaut en score 0-1000.
    1000 = très bon client (faible risque)
    0 = très risqué
    """
    if method == 'linear':
        score = ((1 - proba) * 1000).round(0).astype(int)
    return score


def categoriser_score(score):
    """Catégorise un score en niveau de risque"""
    if score >= 800: return 'A - Excellent'
    if score >= 650: return 'B - Bon'
    if score >= 500: return 'C - Moyen'
    if score >= 350: return 'D - Risqué'
    return 'E - Très risqué'


# =====================================================================
# SAUVEGARDE
# =====================================================================
def sauvegarder_modele(meilleur_modele, encoders, features, 
                       path='models/scoring_model.pkl'):
    """Sauvegarde le modèle entraîné"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        'model': meilleur_modele,
        'encoders': encoders,
        'features': features,
        'cat_cols': CAT_COLS,
        'num_cols': NUM_COLS,
    }, path)
    print(f"\n💾 Modèle sauvegardé : {path}")


def charger_modele(path='models/scoring_model.pkl'):
    """Charge un modèle sauvegardé"""
    data = joblib.load(path)
    return data['model'], data['encoders'], data['features']


def scorer_nouveau_client(client_dict, modele, encoders, features):
    """
    Score un nouveau client (dict) et retourne le score 0-1000
    + la catégorie de risque + la probabilité de défaut.
    """
    df = pd.DataFrame([client_dict])
    
    # Encodage
    for col in CAT_COLS:
        df[f'{col}_enc'] = encoders[col].transform(df[col].astype(str))
    
    # Prédiction
    proba = modele.predict_proba(df[features])[0, 1]
    score = int((1 - proba) * 1000)
    categorie = categoriser_score(score)
    
    return {
        'probabilite_defaut': round(proba * 100, 2),
        'score': score,
        'categorie': categorie,
        'decision': (
            'ACCEPTÉ' if score >= 650 
            else 'À EXAMINER' if score >= 500 
            else 'REFUSÉ'
        )
    }


# =====================================================================
# SCRIPT PRINCIPAL
# =====================================================================
if __name__ == '__main__':
    # Chargement
    print("🔄 Chargement des données nettoyées...")
    df = pd.read_csv('data/processed/credits_clean.csv')
    
    # Entraînement
    resultats = entrainer_modeles(df)
    
    # Importance des features
    print("\n" + "=" * 70)
    print("📊 IMPORTANCE DES FEATURES (meilleur modèle)")
    print("=" * 70)
    imp = calculer_importance(
        resultats['meilleur_modele'],
        resultats['features']
    )
    print(imp.to_string(index=False))
    
    # Test sur 3 clients fictifs
    print("\n" + "=" * 70)
    print("🧪 TEST SUR CLIENTS FICTIFS")
    print("=" * 70)
    
    # Client 1 : profil risqué
    client_risque = {
        'age': 28, 'ville': 'Libreville', 'secteur_activite': 'Agriculture',
        'type_emploi': 'Indépendant', 'anciennete_client_mois': 6,
        'revenu_mensuel_fcfa': 200000, 'type_produit': 'Microfinance',
        'montant_credit_fcfa': 500000, 'duree_mois': 12, 'taux_interet': 12,
        'garantie': 'Aucune', 'nb_incidents_24m': 1, 'nb_credits_en_cours': 2,
        'ratio_endettement': 0.21, 'taux_effort': 21,
    }
    
    # Client 2 : profil moyen
    client_moyen = {
        'age': 40, 'ville': 'Libreville', 'secteur_activite': 'Commerce',
        'type_emploi': 'Salarié privé', 'anciennete_client_mois': 60,
        'revenu_mensuel_fcfa': 600000, 'type_produit': 'Crédit consommation',
        'montant_credit_fcfa': 2000000, 'duree_mois': 36, 'taux_interet': 11,
        'garantie': 'Salaire', 'nb_incidents_24m': 0, 'nb_credits_en_cours': 1,
        'ratio_endettement': 0.09, 'taux_effort': 9,
    }
    
    # Client 3 : profil excellent
    client_excellent = {
        'age': 45, 'ville': 'Libreville', 'secteur_activite': 'Fonction publique',
        'type_emploi': 'Fonctionnaire', 'anciennete_client_mois': 120,
        'revenu_mensuel_fcfa': 1500000, 'type_produit': 'Crédit immobilier',
        'montant_credit_fcfa': 3000000, 'duree_mois': 120, 'taux_interet': 8,
        'garantie': 'Hypothèque', 'nb_incidents_24m': 0, 'nb_credits_en_cours': 0,
        'ratio_endettement': 0.02, 'taux_effort': 2,
    }
    
    for nom, client in [
        ('🔴 Profil RISQUÉ', client_risque),
        ('🟡 Profil MOYEN', client_moyen),
        ('🟢 Profil EXCELLENT', client_excellent),
    ]:
        resultat = scorer_nouveau_client(
            client,
            resultats['meilleur_modele'],
            resultats['encoders'],
            resultats['features']
        )
        print(f"\n{nom}")
        print(f"   Probabilité de défaut : {resultat['probabilite_defaut']}%")
        print(f"   Score                 : {resultat['score']}/1000")
        print(f"   Catégorie             : {resultat['categorie']}")
        print(f"   Décision              : {resultat['decision']}")
    
    # Sauvegarde
    sauvegarder_modele(
        resultats['meilleur_modele'],
        resultats['encoders'],
        resultats['features']
    )
    
    print("\n" + "=" * 70)
    print("✅ MODÈLE DE SCORING ENTRAÎNÉ ET SAUVEGARDÉ")
    print("=" * 70)