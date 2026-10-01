"""
API REST de scoring crédit
Contexte : Banque gabonaise - Conforme COBAC
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np
import sqlite3
import joblib
from pathlib import Path
from datetime import datetime

from api.schemas import (
    ClientInput, ScoringResult, BatchInput, BatchResult, KPIResponse
)


# =====================================================================
# ÉTAT GLOBAL (chargé au démarrage)
# =====================================================================
class AppState:
    model = None
    encoders = None
    features = None
    df_portefeuille = None
    version = "1.0.0"

state = AppState()


# =====================================================================
# CYCLE DE VIE DE L'APP
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Chargement du modèle et des données au démarrage"""
    print("🚀 Démarrage de l'API Scoring Crédit...")
    
    # Charger le modèle ML
    model_path = Path('models/scoring_model.pkl')
    if not model_path.exists():
        raise RuntimeError(
            f"❌ Modèle introuvable : {model_path}\n"
            f"Lance d'abord : python src/scoring_model.py"
        )
    
    data = joblib.load(model_path)
    state.model = data['model']
    state.encoders = data['encoders']
    state.features = data['features']
    print(f"✅ Modèle chargé ({type(state.model).__name__})")
    
    # Charger les données du portefeuille
    db_path = Path('database/credit_risk.db')
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        state.df_portefeuille = pd.read_sql_query("SELECT * FROM credits", conn)
        conn.close()
        print(f"✅ Portefeuille chargé : {len(state.df_portefeuille):,} crédits")
    
    print("✅ API prête !\n")
    yield
    print("\n👋 Arrêt de l'API")


# =====================================================================
# APPLICATION FASTAPI
# =====================================================================
app = FastAPI(
    title="🏦 API Scoring Crédit — Gabon",
    description=(
        "API REST pour le scoring du risque crédit bancaire. "
        "Modèle Random Forest entraîné sur un portefeuille de 32 084 crédits, "
        "adapté au contexte COBAC."
    ),
    version=state.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS (pour permettre les appels depuis n'importe quel front-end)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# FONCTIONS UTILITAIRES
# =====================================================================
def categoriser_score(score: int) -> str:
    """
    Catégorisation calibrée sur la distribution réelle du portefeuille.
    - A : score >= 800  → taux défaut réel 0.97%
    - B : score >= 700  → taux défaut réel 4.76%
    - C : score >= 587  → taux défaut réel ~10%
    - D : score >= 400  → taux défaut réel ~50%
    - E : score <  400  → taux défaut réel 78%
    """
    if score >= 800: return 'A - Excellent'
    if score >= 700: return 'B - Bon'
    if score >= 587: return 'C - Moyen'
    if score >= 400: return 'D - Risqué'
    return 'E - Très risqué'


def scorer_client(client_dict: dict) -> ScoringResult:
    """Score un client (dict) et retourne le ScoringResult"""
    df = pd.DataFrame([client_dict])
    
    # Calculer les features dérivées
    df['ratio_endettement'] = (
        df['montant_credit_fcfa'] / df['duree_mois'] / df['revenu_mensuel_fcfa']
    ).clip(0, 3)
    df['taux_effort'] = (
        df['montant_credit_fcfa'] / df['duree_mois'] / df['revenu_mensuel_fcfa'] * 100
    ).clip(0, 200)
    
    # Encoder les variables catégorielles
    for col, le in state.encoders.items():
        val = str(df[col].iloc[0])
        if val in le.classes_:
            df[f'{col}_enc'] = le.transform([val])[0]
        else:
            df[f'{col}_enc'] = -1  # valeur inconnue
    
    # Prédiction
    proba = state.model.predict_proba(df[state.features])[0, 1]
    score = int((1 - proba) * 1000)
    categorie = categoriser_score(score)
    
    # Décision — SEUILS CALIBRÉS sur la distribution réelle
    # ACCEPTÉ  : score >= 724 → taux défaut réel 2.74%
    # EXAMEN   : 587 <= score < 724 → taux défaut réel 9.70%
    # REFUSÉ   : score < 587 → taux défaut réel 58.79%
    if score >= 724:
        decision = 'ACCEPTÉ'
        reco = (
            "Client éligible. Taux de défaut observé sur ce segment : 2,7%. "
            "Procéder à l'octroi selon les conditions standards."
        )
    elif score >= 587:
        decision = 'À EXAMINER'
        reco = (
            "Dossier à examiner par le comité. Taux de défaut observé : 9,7%. "
            "Vérifier les garanties et l'historique relationnel."
        )
    else:
        decision = 'REFUSÉ'
        reco = (
            "Profil à risque élevé. Taux de défaut observé : 58,8%. "
            "Refus recommandé ou demande de garanties exceptionnelles."
        )
    
    return ScoringResult(
        probabilite_defaut=round(proba * 100, 2),
        score=score,
        categorie=categorie,
        decision=decision,
        recommandation=reco
    )


# =====================================================================
# ENDPOINTS
# =====================================================================

@app.get("/", tags=["Accueil"])
async def root():
    """Page d'accueil - liste des endpoints disponibles"""
    return {
        "api": "Scoring Crédit Bancaire — Gabon",
        "version": state.version,
        "status": "✅ opérationnelle",
        "documentation": "/docs",
        "endpoints": {
            "GET  /health": "Vérification de l'état de l'API",
            "POST /scorer": "Scorer un nouveau client",
            "POST /scorer/batch": "Scorer plusieurs clients",
            "GET  /kpis": "KPI globaux du portefeuille",
            "GET  /secteurs": "Analyse par secteur d'activité",
            "GET  /produits": "Analyse par type de produit",
            "GET  /modele/info": "Informations sur le modèle ML",
        }
    }


@app.get("/health", tags=["Monitoring"])
async def health():
    """Vérification de l'état de l'API et du modèle"""
    return {
        "status": "healthy",
        "modele_charge": state.model is not None,
        "portefeuille_charge": state.df_portefeuille is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/scorer", response_model=ScoringResult, tags=["Scoring"])
async def scorer(client: ClientInput):
    """
    Score un nouveau client.
    
    Retourne :
    - **probabilite_defaut** : probabilité de défaut (%)
    - **score** : score interne 0-1000 (1000 = excellent)
    - **categorie** : catégorie de risque (A-E)
    - **decision** : ACCEPTÉ / À EXAMINER / REFUSÉ
    - **recommandation** : conseil détaillé
    """
    try:
        result = scorer_client(client.model_dump())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du scoring : {str(e)}"
        )


@app.post("/scorer/batch", response_model=BatchResult, tags=["Scoring"])
async def scorer_batch(batch: BatchInput):
    """
    Score plusieurs clients en une seule requête (max 100).
    Utile pour les imports en masse depuis Excel ou un SI.
    """
    try:
        resultats = [
            scorer_client(c.model_dump()) for c in batch.clients
        ]
        return BatchResult(total=len(resultats), resultats=resultats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du scoring batch : {str(e)}"
        )


@app.get("/kpis", response_model=KPIResponse, tags=["Portefeuille"])
async def kpis():
    """KPI globaux du portefeuille"""
    if state.df_portefeuille is None:
        raise HTTPException(503, "Portefeuille non chargé")
    
    df = state.df_portefeuille
    return KPIResponse(
        total_prets=len(df),
        nb_defauts=int(df['defaut'].sum()),
        taux_defaut_pct=round(df['defaut'].mean() * 100, 2),
        encours_total_fcfa=float(df['montant_credit_fcfa'].sum()),
        encours_defaut_fcfa=float(df.loc[df['defaut'] == 1, 'montant_credit_fcfa'].sum()),
        montant_moyen_fcfa=float(df['montant_credit_fcfa'].mean()),
        taux_interet_moyen=float(df['taux_interet'].mean()),
    )


@app.get("/secteurs", tags=["Portefeuille"])
async def secteurs():
    """Analyse du risque par secteur d'activité"""
    if state.df_portefeuille is None:
        raise HTTPException(503, "Portefeuille non chargé")
    
    df = state.df_portefeuille
    result = (
        df.groupby('secteur_activite')['defaut']
        .agg(nb_prets='count', nb_defauts='sum', taux_defaut='mean')
        .reset_index()
    )
    result['taux_defaut_pct'] = (result['taux_defaut'] * 100).round(2)
    result = result.drop(columns='taux_defaut').sort_values(
        'taux_defaut_pct', ascending=False
    )
    return result.to_dict(orient='records')


@app.get("/produits", tags=["Portefeuille"])
async def produits():
    """Analyse du risque par type de produit"""
    if state.df_portefeuille is None:
        raise HTTPException(503, "Portefeuille non chargé")
    
    df = state.df_portefeuille
    result = (
        df.groupby('type_produit')['defaut']
        .agg(nb_prets='count', nb_defauts='sum', taux_defaut='mean')
        .reset_index()
    )
    result['taux_defaut_pct'] = (result['taux_defaut'] * 100).round(2)
    result = result.drop(columns='taux_defaut').sort_values(
        'taux_defaut_pct', ascending=False
    )
    return result.to_dict(orient='records')


@app.get("/modele/info", tags=["Modèle"])
async def modele_info():
    """Informations sur le modèle ML"""
    if state.model is None:
        raise HTTPException(503, "Modèle non chargé")
    
    # Importance des features
    if hasattr(state.model, 'feature_importances_'):
        importances = state.model.feature_importances_
    else:
        importances = np.zeros(len(state.features))
    
    feature_imp = sorted(
        zip(state.features, importances.tolist()),
        key=lambda x: x[1], reverse=True
    )[:10]
    
    return {
        "type_modele": type(state.model).__name__,
        "nb_features": len(state.features),
        "features": state.features,
        "top_10_importances": [
            {"feature": f, "importance_pct": round(i * 100, 2)}
            for f, i in feature_imp
        ]
    }


# =====================================================================
# LANCEMENT DIRECT
# =====================================================================
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )