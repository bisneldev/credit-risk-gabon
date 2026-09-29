"""
Diagnostic complet du dataset crédit
"""
import pandas as pd
import numpy as np


def diagnostic_complet(df, target_col='defaut'):
    """
    Analyse exploratoire initiale du dataset.
    Retourne un dict avec toutes les métriques clés.
    """
    print("=" * 70)
    print("📊 DIAGNOSTIC INITIAL DU DATASET")
    print("=" * 70)
    
    rapport = {}
    
    # ---- 1. Dimensions ----
    print(f"\n1️⃣ DIMENSIONS")
    print(f"   • Lignes    : {df.shape[0]:,}")
    print(f"   • Colonnes  : {df.shape[1]}")
    rapport['n_lignes'] = df.shape[0]
    rapport['n_colonnes'] = df.shape[1]
    
    # ---- 2. Types de colonnes ----
    print(f"\n2️⃣ TYPES DE COLONNES")
    types = df.dtypes.value_counts()
    for t, nb in types.items():
        print(f"   • {str(t):15s} : {nb} colonnes")
    
    # ---- 3. Valeurs manquantes ----
    print(f"\n3️⃣ VALEURS MANQUANTES")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        'manquants': missing,
        'pourcentage': missing_pct
    }).query('manquants > 0').sort_values('pourcentage', ascending=False)
    
    if len(missing_df) == 0:
        print("   ✅ Aucune valeur manquante")
    else:
        print(f"   ⚠️  {len(missing_df)} colonne(s) concernée(s)")
        print(missing_df.to_string())
    rapport['missing'] = missing_df
    
    # ---- 4. Doublons ----
    n_dup = df.duplicated().sum()
    print(f"\n4️⃣ DOUBLONS")
    print(f"   • {n_dup:,} lignes dupliquées ({n_dup/len(df)*100:.2f}%)")
    rapport['doublons'] = n_dup
    
    # ---- 5. Variable cible ----
    if target_col in df.columns:
        print(f"\n5️⃣ VARIABLE CIBLE : '{target_col}'")
        counts = df[target_col].value_counts().sort_index()
        for val, nb in counts.items():
            label = "Sain" if val == 0 else "Défaut"
            pct = nb / len(df) * 100
            print(f"   • {label:8s} (={val}) : {nb:,} ({pct:.2f}%)")
        rapport['taux_defaut'] = df[target_col].mean() * 100
    
    # ---- 6. Statistiques numériques ----
    print(f"\n6️⃣ STATISTIQUES DES VARIABLES NUMÉRIQUES")
    num_df = df.select_dtypes(include=[np.number])
    stats = num_df.describe().T[['mean', 'std', 'min', '50%', 'max']].round(2)
    print(stats.to_string())
    
    # ---- 7. Colonnes catégorielles ----
    print(f"\n7️⃣ VARIABLES CATÉGORIELLES (cardinalité)")
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        n_unique = df[col].nunique()
        print(f"   • {col:25s} : {n_unique} valeurs uniques")
    
    # ---- 8. Colonnes constantes ----
    constantes = [c for c in df.columns if df[c].nunique() <= 1]
    print(f"\n8️⃣ COLONNES CONSTANTES")
    if constantes:
        print(f"   ⚠️  {constantes}")
    else:
        print("   ✅ Aucune colonne constante")
    
    print("\n" + "=" * 70)
    print("✅ Diagnostic terminé")
    print("=" * 70)
    
    return rapport


if __name__ == '__main__':
    df = pd.read_csv('data/raw/credits_gabon.csv')
    diagnostic_complet(df)