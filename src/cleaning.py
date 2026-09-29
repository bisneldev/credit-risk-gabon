"""
Nettoyage et préparation du dataset crédit
Contexte : Banque gabonaise
"""
import pandas as pd
import numpy as np
from pathlib import Path


def nettoyer_donnees(df, verbose=True):
    """
    Pipeline de nettoyage en 8 étapes.
    Retourne (df_clean, rapport)
    """
    df = df.copy()
    n_initial = len(df)
    rapport = {'etapes': [], 'n_initial': n_initial}
    
    if verbose:
        print("=" * 70)
        print("🧹 NETTOYAGE ET PRÉPARATION DES DONNÉES")
        print("=" * 70)
        print(f"\n📥 Point de départ : {n_initial:,} lignes\n")
    
    # ================================================================
    # ÉTAPE 1 : Suppression des colonnes non pertinentes pour le ML
    # ================================================================
    cols_a_supprimer = [
        'client_id',           # identifiant
        'date_octroi',         # date brute (on garde annee/mois plus tard)
        'jours_retard',        # cause du défaut (fuite de données !)
        'classification_cobac',# cause du défaut (fuite de données !)
        'provision_fcfa',      # conséquence du défaut (fuite !)
    ]
    cols_presentes = [c for c in cols_a_supprimer if c in df.columns]
    df = df.drop(columns=cols_presentes)
    
    rapport['etapes'].append(f"Colonnes supprimées : {len(cols_presentes)}")
    if verbose:
        print(f"1️⃣ Suppression colonnes fuite/non-pertinentes : {len(cols_presentes)}")
        for c in cols_presentes:
            print(f"   🗑️  {c}")
    
    # ================================================================
    # ÉTAPE 2 : Filtrage des valeurs aberrantes (âge)
    # ================================================================
    n_avant = len(df)
    df = df[(df['age'] >= 18) & (df['age'] <= 80)]
    supprimes = n_avant - len(df)
    rapport['etapes'].append(f"Filtrage âge : -{supprimes} lignes")
    if verbose:
        print(f"\n2️⃣ Filtrage âge (18-80 ans) : -{supprimes} lignes")
    
    # ================================================================
    # ÉTAPE 3 : Filtrage des revenus aberrants (outliers extrêmes)
    # ================================================================
    n_avant = len(df)
    # On supprime les revenus < 50 000 FCFA (SMIG gabonais ~150k mais on tolère)
    # et > 99e percentile (revenus exceptionnels qui biaisent)
    seuil_bas = 50000
    seuil_haut = df['revenu_mensuel_fcfa'].quantile(0.99)
    df = df[
        (df['revenu_mensuel_fcfa'] >= seuil_bas) & 
        (df['revenu_mensuel_fcfa'] <= seuil_haut)
    ]
    supprimes = n_avant - len(df)
    rapport['etapes'].append(f"Filtrage revenus : -{supprimes} lignes")
    if verbose:
        print(f"\n3️⃣ Filtrage revenus [{seuil_bas:,} - {seuil_haut:,.0f} FCFA] : -{supprimes} lignes")
    
    # ================================================================
    # ÉTAPE 4 : Filtrage des montants de crédit aberrants
    # ================================================================
    n_avant = len(df)
    seuil_montant_haut = df['montant_credit_fcfa'].quantile(0.995)
    df = df[
        (df['montant_credit_fcfa'] >= 100000) & 
        (df['montant_credit_fcfa'] <= seuil_montant_haut)
    ]
    supprimes = n_avant - len(df)
    rapport['etapes'].append(f"Filtrage montants crédit : -{supprimes} lignes")
    if verbose:
        print(f"\n4️⃣ Filtrage montants crédit [100k - {seuil_montant_haut:,.0f} FCFA] : -{supprimes} lignes")
    
    # ================================================================
    # ÉTAPE 5 : Filtrage des ratios d'endettement extrêmes
    # ================================================================
    n_avant = len(df)
    df = df[(df['ratio_endettement'] >= 0) & (df['ratio_endettement'] <= 1.5)]
    supprimes = n_avant - len(df)
    rapport['etapes'].append(f"Filtrage ratio endettement : -{supprimes} lignes")
    if verbose:
        print(f"\n5️⃣ Filtrage ratio endettement (0 - 1.5) : -{supprimes} lignes")
    
    # ================================================================
    # ÉTAPE 6 : Suppression des doublons
    # ================================================================
    n_avant = len(df)
    df = df.drop_duplicates()
    supprimes = n_avant - len(df)
    rapport['etapes'].append(f"Doublons supprimés : {supprimes}")
    if verbose:
        print(f"\n6️⃣ Suppression doublons : -{supprimes} lignes")
    
    # ================================================================
    # ÉTAPE 7 : Feature engineering
    # ================================================================
    if verbose:
        print(f"\n7️⃣ Feature engineering...")
    
    # Ratio d'endettement recalibré : mensualité / revenu mensuel en %
    mensualite = df['montant_credit_fcfa'] / df['duree_mois']
    df['ratio_endettement'] = (mensualite / df['revenu_mensuel_fcfa']).round(3)
    
    # Tranche d'âge
    df['tranche_age'] = pd.cut(
        df['age'],
        bins=[17, 30, 45, 60, 100],
        labels=['18-29', '30-44', '45-59', '60+']
    )
    
    # Tranche de revenu
    df['tranche_revenu'] = pd.cut(
        df['revenu_mensuel_fcfa'],
        bins=[0, 200000, 500000, 1000000, np.inf],
        labels=['<200k', '200-500k', '500k-1M', '>1M']
    )
    
    # Tranche de montant
    df['tranche_montant'] = pd.cut(
        df['montant_credit_fcfa'],
        bins=[0, 500000, 2000000, 10000000, np.inf],
        labels=['<500k', '500k-2M', '2M-10M', '>10M']
    )
    
    # Ratio mensualité sur revenu en % (plus lisible)
    df['taux_effort'] = (mensualite / df['revenu_mensuel_fcfa'] * 100).round(2)
    
    # Score de risque composite
    df['risque_produit'] = df['type_produit'].map({
        'Crédit consommation': 0.25, 'Crédit immobilier': 0.10,
        'Crédit PME': 0.30, 'Découvert': 0.20,
        'Crédit auto': 0.15, 'Crédit scolaire': 0.12, 'Microfinance': 0.35
    })
    
    # Revenu log (pour modèles linéaires)
    df['revenu_log'] = np.log1p(df['revenu_mensuel_fcfa']).round(3)
    df['montant_log'] = np.log1p(df['montant_credit_fcfa']).round(3)
    
    if verbose:
        print(f"   ✨ Nouvelles colonnes : tranche_age, tranche_revenu,")
        print(f"      tranche_montant, taux_effort, revenu_log, montant_log")
    
    # ================================================================
    # ÉTAPE 8 : Vérification finale
    # ================================================================
    # Vérifier qu'il n'y a plus de valeurs manquantes
    n_missing = df.isnull().sum().sum()
    if n_missing > 0:
        if verbose:
            print(f"\n⚠️  {n_missing} valeurs manquantes détectées — imputation...")
        # Numériques : médiane
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())
    
    # ================================================================
    # RAPPORT FINAL
    # ================================================================
    n_final = len(df)
    rapport['n_final'] = n_final
    rapport['lignes_supprimees'] = n_initial - n_final
    rapport['taux_conservation'] = round(n_final / n_initial * 100, 2)
    rapport['taux_defaut'] = round(df['defaut'].mean() * 100, 2)
    
    if verbose:
        print("\n" + "=" * 70)
        print("📊 RAPPORT DE NETTOYAGE")
        print("=" * 70)
        print(f"📥 Observations initiales : {n_initial:,}")
        print(f"📤 Observations finales   : {n_final:,}")
        print(f"🗑️  Lignes supprimées     : {n_initial - n_final:,} "
              f"({(n_initial-n_final)/n_initial*100:.2f}%)")
        print(f"✅ Taux de conservation   : {rapport['taux_conservation']}%")
        print(f"📉 Taux de défaut         : {rapport['taux_defaut']}%")
        print("=" * 70)
    
    return df, rapport


def sauvegarder_donnees_propres(df, chemin='data/processed/credits_clean.csv'):
    """Sauvegarde le dataset nettoyé"""
    Path(chemin).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(chemin, index=False, encoding='utf-8')
    print(f"\n💾 Données nettoyées sauvegardées : {chemin}")


if __name__ == '__main__':
    # Chargement
    df_raw = pd.read_csv('data/raw/credits_gabon.csv')
    
    # Nettoyage
    df_clean, rapport = nettoyer_donnees(df_raw)
    
    # Sauvegarde
    sauvegarder_donnees_propres(df_clean)
    
    # Aperçu
    print("\n📋 Aperçu des données nettoyées :")
    print(df_clean.head())
    
    print(f"\n📋 Colonnes finales ({len(df_clean.columns)}) :")
    for i, col in enumerate(df_clean.columns, 1):
        print(f"   {i:2d}. {col}")