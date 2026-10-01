"""
Calibration des seuils de décision du scoring
Analyse la distribution des scores et propose des seuils optimaux.
"""
import pandas as pd
import numpy as np
import joblib


# Charger modèle + encoders
data = joblib.load('models/scoring_model.pkl')
model = data['model']
encoders = data['encoders']
features = data['features']
cat_cols = data['cat_cols']

# Charger portefeuille
df = pd.read_csv('data/processed/credits_clean.csv')

# Encoder
df_enc = df.copy()
for col in cat_cols:
    df_enc[f'{col}_enc'] = encoders[col].transform(df_enc[col].astype(str))

# Prédictions
probas = model.predict_proba(df_enc[features])[:, 1]
df['proba_defaut'] = probas
df['score'] = ((1 - probas) * 1000).round(0).astype(int)

# Distribution des scores
print("=" * 70)
print("📊 DISTRIBUTION DES SCORES")
print("=" * 70)
print(df['score'].describe().round(0).to_string())

print("\n📊 QUANTILES (déciles) :")
for q in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    val = df['score'].quantile(q)
    print(f"   {int(q*100):3d}% : score >= {int(val)}")

# Lien score / taux de défaut réel
print("\n📊 TAUX DE DÉFAUT RÉEL PAR TRANCHE DE SCORE :")
bins = [0, 400, 500, 600, 700, 800, 1000]
df['tranche'] = pd.cut(df['score'], bins=bins, include_lowest=True)
stats = df.groupby('tranche', observed=True)['defaut'].agg(
    ['count', 'sum', 'mean']
)
stats['taux_pct'] = (stats['mean'] * 100).round(2)
stats['part_pct'] = (stats['count'] / len(df) * 100).round(2)
print(stats[['count', 'sum', 'taux_pct', 'part_pct']].to_string())

# Proposition de seuils optimaux
print("\n" + "=" * 70)
print("🎯 PROPOSITION DE SEUILS OPTIMAUX")
print("=" * 70)

# Approche : seuils basés sur la distribution réelle
seuil_accept = int(df['score'].quantile(0.65))  # top 35% accepté
seuil_refus = int(df['score'].quantile(0.30))   # bottom 30% refusé

print(f"\n   Seuil ACCEPTÉ  : score >= {seuil_accept}")
print(f"      → {(df['score'] >= seuil_accept).sum():,} clients "
      f"({(df['score'] >= seuil_accept).mean()*100:.1f}%)")
print(f"      → Taux de défaut réel : "
      f"{df[df['score'] >= seuil_accept]['defaut'].mean()*100:.2f}%")

print(f"\n   Seuil REFUSÉ   : score < {seuil_refus}")
print(f"      → {(df['score'] < seuil_refus).sum():,} clients "
      f"({(df['score'] < seuil_refus).mean()*100:.1f}%)")
print(f"      → Taux de défaut réel : "
      f"{df[df['score'] < seuil_refus]['defaut'].mean()*100:.2f}%")

print(f"\n   Zone EXAMEN    : {seuil_refus} <= score < {seuil_accept}")
print(f"      → {((df['score'] >= seuil_refus) & (df['score'] < seuil_accept)).sum():,} clients")
print(f"      → Taux de défaut réel : "
      f"{df[(df['score'] >= seuil_refus) & (df['score'] < seuil_accept)]['defaut'].mean()*100:.2f}%")

print("\n💡 Copie ces seuils dans api/main.py et dashboard/app.py")