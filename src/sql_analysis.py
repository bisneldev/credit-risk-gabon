"""
Analyse SQL du risque crédit - SQLite
Reproduit les analyses EDA en SQL + ajoute reporting réglementaire COBAC
"""
import sqlite3
import pandas as pd
from pathlib import Path


class SQLAnalyzer:
    """Gestionnaire de base de données SQLite pour l'analyse crédit"""
    
    def __init__(self, db_path='database/credit_risk.db'):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        print(f"🔗 Connexion à : {db_path}")
    
    # ==============================================================
    # CHARGEMENT DES DONNÉES
    # ==============================================================
    def charger_dataframe(self, df, table='credits'):
        """Charge un DataFrame dans une table SQLite"""
        df.to_sql(table, self.conn, if_exists='replace', index=False)
        n = self.query(f"SELECT COUNT(*) as n FROM {table}").iloc[0]['n']
        print(f"✅ {n:,} lignes chargées dans la table '{table}'")
    
    def query(self, sql):
        """Exécute une requête SQL et retourne un DataFrame"""
        return pd.read_sql_query(sql, self.conn)
    
    def tables(self):
        """Liste les tables existantes"""
        return self.query(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    
    # ==============================================================
    # REQUÊTE 1 : KPI GLOBAUX
    # ==============================================================
    def kpi_globaux(self):
        return self.query("""
            SELECT 
                COUNT(*) AS total_prets,
                SUM(defaut) AS nb_defauts,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_pct,
                ROUND(SUM(montant_credit_fcfa) / 1e9, 3) AS encours_milliards_fcfa,
                ROUND(SUM(CASE WHEN defaut = 1 
                    THEN montant_credit_fcfa ELSE 0 END) / 1e9, 3) 
                    AS encours_defaut_milliards_fcfa,
                ROUND(AVG(montant_credit_fcfa), 0) AS montant_moyen_fcfa,
                ROUND(AVG(taux_interet), 2) AS taux_interet_moyen,
                ROUND(AVG(taux_effort), 2) AS taux_effort_moyen
            FROM credits
        """)
    
    # ==============================================================
    # REQUÊTE 2 : TAUX DE DÉFAUT PAR SECTEUR
    # ==============================================================
    def defaut_par_secteur(self):
        return self.query("""
            SELECT 
                secteur_activite,
                COUNT(*) AS nb_prets,
                SUM(defaut) AS nb_defauts,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_pct,
                ROUND(AVG(montant_credit_fcfa), 0) AS montant_moyen,
                ROUND(SUM(montant_credit_fcfa) / 1e6, 1) AS exposition_millions_fcfa,
                ROUND(SUM(CASE WHEN defaut = 1 
                    THEN montant_credit_fcfa ELSE 0 END) / 1e6, 1) 
                    AS perte_potentielle_millions
            FROM credits
            GROUP BY secteur_activite
            HAVING COUNT(*) >= 30
            ORDER BY taux_defaut_pct DESC
        """)
    
    # ==============================================================
    # REQUÊTE 3 : TAUX DE DÉFAUT PAR TYPE DE PRODUIT
    # ==============================================================
    def defaut_par_produit(self):
        return self.query("""
            SELECT 
                type_produit,
                COUNT(*) AS nb_prets,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_pct,
                ROUND(AVG(montant_credit_fcfa), 0) AS montant_moyen,
                ROUND(AVG(duree_mois), 0) AS duree_moyenne_mois,
                ROUND(AVG(taux_interet), 2) AS taux_moyen
            FROM credits
            GROUP BY type_produit
            ORDER BY taux_defaut_pct DESC
        """)
    
    # ==============================================================
    # REQUÊTE 4 : TAUX DE DÉFAUT PAR TRANCHE DE REVENU
    # ==============================================================
    def defaut_par_revenu(self):
        return self.query("""
            SELECT 
                tranche_revenu,
                COUNT(*) AS nb_prets,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_pct,
                ROUND(AVG(revenu_mensuel_fcfa), 0) AS revenu_moyen,
                ROUND(AVG(montant_credit_fcfa), 0) AS montant_moyen,
                ROUND(SUM(CASE WHEN defaut = 1 
                    THEN montant_credit_fcfa ELSE 0 END) / 1e6, 1) 
                    AS perte_potentielle_millions
            FROM credits
            GROUP BY tranche_revenu
            ORDER BY 
                CASE tranche_revenu
                    WHEN '<200k' THEN 1
                    WHEN '200-500k' THEN 2
                    WHEN '500k-1M' THEN 3
                    WHEN '>1M' THEN 4
                END
        """)
    
    # ==============================================================
    # REQUÊTE 5 : IMPACT DES INCIDENTS DE PAIEMENT
    # ==============================================================
    def impact_incidents(self):
        return self.query("""
            SELECT 
                CASE 
                    WHEN nb_incidents_24m = 0 THEN 'Sans incidents (24m)'
                    ELSE 'Avec incidents (24m)'
                END AS categorie,
                COUNT(*) AS nb_prets,
                SUM(defaut) AS nb_defauts,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_pct,
                ROUND(AVG(montant_credit_fcfa), 0) AS montant_moyen
            FROM credits
            GROUP BY categorie
            ORDER BY taux_defaut_pct DESC
        """)
    
    # ==============================================================
    # REQUÊTE 6 : CONCENTRATION GÉOGRAPHIQUE (risque pays)
    # ==============================================================
    def analyse_geographique(self):
        return self.query("""
            WITH total AS (
                SELECT SUM(montant_credit_fcfa) AS total_encours FROM credits
            )
            SELECT 
                ville,
                COUNT(*) AS nb_clients,
                ROUND(SUM(montant_credit_fcfa) / 1e6, 1) AS encours_millions,
                ROUND(100.0 * SUM(montant_credit_fcfa) / 
                      (SELECT total_encours FROM total), 2) AS concentration_pct,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_pct
            FROM credits
            GROUP BY ville
            ORDER BY encours_millions DESC
        """)
    
    # ==============================================================
    # REQUÊTE 7 : CROISEMENT SECTEUR × GARANTIE (segments critiques)
    # ==============================================================
    def segments_critiques(self, seuil_n=50):
        return self.query(f"""
            SELECT 
                secteur_activite,
                garantie,
                COUNT(*) AS nb_prets,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_pct,
                ROUND(SUM(montant_credit_fcfa) / 1e6, 1) AS exposition_millions
            FROM credits
            GROUP BY secteur_activite, garantie
            HAVING COUNT(*) >= {seuil_n}
            ORDER BY taux_defaut_pct DESC
            LIMIT 15
        """)
    
    # ==============================================================
    # REQUÊTE 8 : MATRICE DE RISQUE COBAC (classification provisoire)
    # ==============================================================
    def matrice_cobac(self):
        """
        Classification COBAC simulée à partir du taux d'effort + incidents :
        - Saine        : taux_effort < 30% ET pas d'incidents
        - Observation  : taux_effort < 40% ET pas d'incidents
        - Douteuse     : taux_effort < 50% OU 1 incident
        - Litigieuse   : taux_effort > 50% OU incidents multiples
        """
        return self.query("""
            WITH classified AS (
                SELECT 
                    *,
                    CASE 
                        WHEN taux_effort < 30 AND nb_incidents_24m = 0 
                            THEN '1. Saine'
                        WHEN taux_effort < 40 AND nb_incidents_24m = 0 
                            THEN '2. Observation'
                        WHEN taux_effort < 50 OR nb_incidents_24m = 1 
                            THEN '3. Douteuse'
                        ELSE '4. Litigieuse'
                    END AS categorie_cobac
                FROM credits
            )
            SELECT 
                categorie_cobac,
                COUNT(*) AS nb_credits,
                ROUND(SUM(montant_credit_fcfa) / 1e9, 3) AS encours_milliards,
                ROUND(100.0 * COUNT(*) / 
                      (SELECT COUNT(*) FROM classified), 2) AS part_pct,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_observe
            FROM classified
            GROUP BY categorie_cobac
            ORDER BY categorie_cobac
        """)
    
    # ==============================================================
    # REQUÊTE 9 : TOP 10 DES SEGMENTS LES PLUS RISQUÉS
    # ==============================================================
    def top_segments_risque(self):
        return self.query("""
            SELECT 
                secteur_activite,
                type_produit,
                COUNT(*) AS nb_prets,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS taux_defaut_pct,
                ROUND(SUM(CASE WHEN defaut = 1 
                    THEN montant_credit_fcfa ELSE 0 END) / 1e6, 1) 
                    AS perte_potentielle_millions
            FROM credits
            GROUP BY secteur_activite, type_produit
            HAVING COUNT(*) >= 30
            ORDER BY perte_potentielle_millions DESC
            LIMIT 10
        """)
    
    # ==============================================================
    # REQUÊTE 10 : TABLEAU DE BORD SYNTHÉTIQUE
    # ==============================================================
    def dashboard_synthetique(self):
        """Construit le tableau de bord en Python (plus robuste que UNION ALL)"""
        indicateurs = []
        
        # 1. Taux de défaut global
        r = self.query("""
            SELECT ROUND(100.0 * SUM(defaut) / COUNT(*), 2) AS v
            FROM credits
        """)
        indicateurs.append({
            'indicateur': 'Taux de défaut global',
            'valeur': f"{r.iloc[0]['v']} %"
        })
        
        # 2. Encours total
        r = self.query("""
            SELECT ROUND(SUM(montant_credit_fcfa) / 1e9, 2) AS v
            FROM credits
        """)
        indicateurs.append({
            'indicateur': 'Encours total',
            'valeur': f"{r.iloc[0]['v']} milliards FCFA"
        })
        
        # 3. Encours en défaut
        r = self.query("""
            SELECT ROUND(SUM(CASE WHEN defaut = 1 
                THEN montant_credit_fcfa ELSE 0 END) / 1e9, 2) AS v
            FROM credits
        """)
        indicateurs.append({
            'indicateur': 'Encours en défaut',
            'valeur': f"{r.iloc[0]['v']} milliards FCFA"
        })
        
        # 4. Perte potentielle (LGD 60%)
        r = self.query("""
            SELECT ROUND(SUM(CASE WHEN defaut = 1 
                THEN montant_credit_fcfa ELSE 0 END) * 0.6 / 1e9, 2) AS v
            FROM credits
        """)
        indicateurs.append({
            'indicateur': 'Perte potentielle estimée (LGD 60%)',
            'valeur': f"{r.iloc[0]['v']} milliards FCFA"
        })
        
        # 5. Part clients avec incidents
        r = self.query("""
            SELECT ROUND(100.0 * SUM(nb_incidents_24m) / COUNT(*), 2) AS v
            FROM credits
        """)
        indicateurs.append({
            'indicateur': 'Clients avec incidents (24m)',
            'valeur': f"{r.iloc[0]['v']} %"
        })
        
        # 6. Secteur le plus risqué (requête isolée, sans UNION)
        r = self.query("""
            SELECT 
                secteur_activite,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 1) AS taux
            FROM credits
            GROUP BY secteur_activite
            ORDER BY taux DESC
            LIMIT 1
        """)
        indicateurs.append({
            'indicateur': 'Secteur le plus risqué',
            'valeur': f"{r.iloc[0]['secteur_activite']} ({r.iloc[0]['taux']} %)"
        })
        
        # 7. Produit le plus risqué
        r = self.query("""
            SELECT 
                type_produit,
                ROUND(100.0 * SUM(defaut) / COUNT(*), 1) AS taux
            FROM credits
            GROUP BY type_produit
            ORDER BY taux DESC
            LIMIT 1
        """)
        indicateurs.append({
            'indicateur': 'Produit le plus risqué',
            'valeur': f"{r.iloc[0]['type_produit']} ({r.iloc[0]['taux']} %)"
        })
        
        return pd.DataFrame(indicateurs)
    
    # ==============================================================
    # SAUVEGARDE EN CSV
    # ==============================================================
    def exporter_csv(self, output_dir='reports/sql'):
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        requetes = {
            'kpi_globaux': self.kpi_globaux(),
            'defaut_par_secteur': self.defaut_par_secteur(),
            'defaut_par_produit': self.defaut_par_produit(),
            'defaut_par_revenu': self.defaut_par_revenu(),
            'impact_incidents': self.impact_incidents(),
            'analyse_geographique': self.analyse_geographique(),
            'segments_critiques': self.segments_critiques(),
            'matrice_cobac': self.matrice_cobac(),
            'top_segments_risque': self.top_segments_risque(),
            'dashboard_synthetique': self.dashboard_synthetique(),
        }
        for nom, df in requetes.items():
            df.to_csv(f"{output_dir}/{nom}.csv", index=False, encoding='utf-8')
        print(f"💾 {len(requetes)} fichiers CSV exportés dans {output_dir}/")
        return requetes
    
    def close(self):
        self.conn.close()


# ==================================================================
# SCRIPT PRINCIPAL
# ==================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("🗄️  ANALYSE SQL DU RISQUE CRÉDIT")
    print("=" * 70)
    
    # 1. Chargement
    df = pd.read_csv('data/processed/credits_clean.csv')
    print(f"\n📥 {len(df):,} lignes chargées depuis le CSV")
    
    # 2. Création base
    db = SQLAnalyzer('database/credit_risk.db')
    db.charger_dataframe(df, table='credits')
    
    # 3. KPI globaux
    print("\n" + "=" * 70)
    print("📊 KPI GLOBAUX")
    print("=" * 70)
    print(db.kpi_globaux().T.to_string())
    
    # 4. Analyse par secteur
    print("\n" + "=" * 70)
    print("🏭 TAUX DE DÉFAUT PAR SECTEUR")
    print("=" * 70)
    print(db.defaut_par_secteur().to_string(index=False))
    
    # 5. Analyse par produit
    print("\n" + "=" * 70)
    print("💳 TAUX DE DÉFAUT PAR PRODUIT")
    print("=" * 70)
    print(db.defaut_par_produit().to_string(index=False))
    
    # 6. Impact des incidents
    print("\n" + "=" * 70)
    print("⚠️  IMPACT DES INCIDENTS DE PAIEMENT")
    print("=" * 70)
    print(db.impact_incidents().to_string(index=False))
    
    # 7. Concentration géographique
    print("\n" + "=" * 70)
    print("🗺️  CONCENTRATION GÉOGRAPHIQUE")
    print("=" * 70)
    print(db.analyse_geographique().to_string(index=False))
    
    # 8. Matrice COBAC
    print("\n" + "=" * 70)
    print("🏛️  MATRICE DE RISQUE COBAC (simulation)")
    print("=" * 70)
    print(db.matrice_cobac().to_string(index=False))
    
    # 9. Top segments risqués
    print("\n" + "=" * 70)
    print("🔴 TOP 10 SEGMENTS LES PLUS RISQUÉS (par perte potentielle)")
    print("=" * 70)
    print(db.top_segments_risque().to_string(index=False))
    
    # 10. Dashboard synthétique
    print("\n" + "=" * 70)
    print("📋 SYNTHÈSE POUR LA DIRECTION")
    print("=" * 70)
    print(db.dashboard_synthetique().to_string(index=False))
    
    # 11. Export CSV
    print("\n")
    db.exporter_csv()
    
    # 12. Fermeture
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ ANALYSE SQL TERMINÉE")
    print("=" * 70)
    print("📁 Base SQLite : database/credit_risk.db")
    print("📁 Exports CSV : reports/sql/*.csv")