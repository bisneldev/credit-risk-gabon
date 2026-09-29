"""
Générateur de données synthétiques pour l'analyse du risque crédit
Contexte : Banque gabonaise - Conforme classification COBAC
"""
import pandas as pd
import numpy as np
from pathlib import Path


def generer_donnees_gabon(n=32581, seed=42):
    """
    Génère un dataset synthétique réaliste (32 581 crédits).
    Colonnes alignées sur les pratiques KYC + classification COBAC.
    """
    np.random.seed(seed)
    
    print(f"🔄 Génération de {n:,} crédits...")
    
    # ---- Référentiels ----
    villes = ['Libreville', 'Port-Gentil', 'Franceville', 
              'Oyem', 'Moanda', 'Lambaréné', 'Tchibanga']
    poids_villes = [0.45, 0.20, 0.10, 0.07, 0.06, 0.07, 0.05]
    
    secteurs = ['Commerce', 'BTP', 'Services', 'Agriculture', 
                'Transport', 'Industrie', 'Pétrole & Gaz', 
                'Fonction publique', 'Santé', 'Éducation']
    
    types_emploi = ['Salarié privé', 'Fonctionnaire', 
                    'Indépendant', 'Commerçant', 'Retraité']
    poids_emploi = [0.40, 0.25, 0.15, 0.15, 0.05]
    
    produits = ['Crédit consommation', 'Crédit immobilier', 
                'Crédit PME', 'Découvert', 'Crédit auto',
                'Crédit scolaire', 'Microfinance']
    poids_produits = [0.30, 0.15, 0.20, 0.10, 0.15, 0.05, 0.05]
    
    garanties = ['Aucune', 'Salaire', 'Caution solidaire', 
                 'Hypothèque', 'Nantissement']
    poids_garanties = [0.20, 0.40, 0.20, 0.10, 0.10]
    
    # ---- Construction du DataFrame ----
    df = pd.DataFrame({
        'client_id': [f'GAB{str(i).zfill(6)}' for i in range(1, n + 1)],
        'age': np.random.randint(21, 70, n),
        'ville': np.random.choice(villes, n, p=poids_villes),
        'secteur_activite': np.random.choice(secteurs, n),
        'type_emploi': np.random.choice(types_emploi, n, p=poids_emploi),
        'anciennete_client_mois': np.random.randint(1, 240, n),
        'revenu_mensuel_fcfa': np.random.lognormal(13.5, 0.6, n).clip(80000, 5000000).round(0),
        'type_produit': np.random.choice(produits, n, p=poids_produits),
        'montant_credit_fcfa': np.random.lognormal(13, 0.8, n).clip(100000, 100000000).round(0),
        'duree_mois': np.random.choice([6, 12, 24, 36, 60, 84, 120, 180], n),
        'taux_interet': np.random.uniform(7, 15, n).round(2),
        'garantie': np.random.choice(garanties, n, p=poids_garanties),
        'nb_incidents_24m': np.random.binomial(1, 0.12, n),
        'nb_credits_en_cours': np.random.randint(0, 4, n),
    })
    
    # Date d'octroi répartie sur 3 ans
    df['date_octroi'] = pd.date_range('2022-01-01', periods=n, freq='3h')[:n]
    
    # ---- Ratio d'endettement ----
    mensualite = df['montant_credit_fcfa'] / df['duree_mois']
    df['ratio_endettement'] = (mensualite / df['revenu_mensuel_fcfa']).clip(0, 3).round(3)
    
    # ---- Score de risque (logique métier gabonaise) ----
    risque_produit = df['type_produit'].map({
        'Crédit consommation': 0.25, 'Crédit immobilier': 0.10,
        'Crédit PME': 0.30, 'Découvert': 0.20,
        'Crédit auto': 0.15, 'Crédit scolaire': 0.12, 'Microfinance': 0.35
    })
    
    risque_secteur = df['secteur_activite'].map({
        'Commerce': 0.20, 'BTP': 0.28, 'Services': 0.15,
        'Agriculture': 0.30, 'Transport': 0.22, 'Industrie': 0.14,
        'Pétrole & Gaz': 0.10, 'Fonction publique': 0.05,
        'Santé': 0.12, 'Éducation': 0.08
    })
    
    score_risque = (
        risque_produit * 0.35
        + risque_secteur * 0.20
        + df['ratio_endettement'] * 0.20
        + df['nb_incidents_24m'] * 0.15
        + (df['anciennete_client_mois'] < 12).astype(int) * 0.10
        + np.random.normal(0, 0.08, n)
    )
    
    # ~22% de défaut (réaliste pour le Gabon)
    df['defaut'] = (score_risque > np.percentile(score_risque, 78)).astype(int)
    
    # Jours de retard
    df['jours_retard'] = np.where(
        df['defaut'] == 1,
        np.random.randint(30, 500, n),
        0
    )
    
    # ---- Classification COBAC ----
    def classifier_cobac(jours):
        if jours == 0: return 'Saine'
        if jours < 90: return 'Observation'
        if jours < 180: return 'Douteuse'
        if jours < 360: return 'Litigieuse'
        return 'Irrecouvrable'
    
    df['classification_cobac'] = df['jours_retard'].apply(classifier_cobac)
    
    # ---- Provisionnement COBAC ----
    provision_map = {
        'Saine': 0, 'Observation': 0.05,
        'Douteuse': 0.30, 'Litigieuse': 0.50, 'Irrecouvrable': 1.0
    }
    df['provision_fcfa'] = (
        df['montant_credit_fcfa'] 
        * df['classification_cobac'].map(provision_map)
    ).round(0)
    
    print(f"✅ {len(df):,} crédits générés")
    print(f"📉 Taux de défaut : {df['defaut'].mean()*100:.2f}%")
    
    return df


def sauvegarder_donnees(df, chemin='data/raw/credits_gabon.csv'):
    """Sauvegarde le dataset en CSV"""
    Path(chemin).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(chemin, index=False, encoding='utf-8')
    print(f"💾 Données sauvegardées : {chemin}")


if __name__ == '__main__':
    df = generer_donnees_gabon(n=32581)
    sauvegarder_donnees(df)
    print("\n📋 Aperçu :")
    print(df.head())