"""
Schémas Pydantic pour l'API de scoring crédit
Validation automatique des données d'entrée/sortie
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


# =====================================================================
# CLIENT À SCORER
# =====================================================================
class ClientInput(BaseModel):
    """Données d'un client pour le scoring"""
    age: int = Field(..., ge=18, le=100, description="Âge du client")
    ville: str = Field(..., description="Ville de résidence")
    secteur_activite: str = Field(..., description="Secteur d'activité")
    type_emploi: str = Field(..., description="Type d'emploi")
    anciennete_client_mois: int = Field(..., ge=0, description="Ancienneté en mois")
    revenu_mensuel_fcfa: float = Field(..., gt=0, description="Revenu mensuel en FCFA")
    type_produit: str = Field(..., description="Type de produit crédit")
    montant_credit_fcfa: float = Field(..., gt=0, description="Montant en FCFA")
    duree_mois: int = Field(..., gt=0, description="Durée en mois")
    taux_interet: float = Field(..., gt=0, description="Taux d'intérêt en %")
    garantie: str = Field(..., description="Type de garantie")
    nb_incidents_24m: int = Field(0, ge=0, le=10, description="Incidents 24 mois")
    nb_credits_en_cours: int = Field(0, ge=0, le=20, description="Crédits en cours")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 35,
                "ville": "Libreville",
                "secteur_activite": "Commerce",
                "type_emploi": "Salarié privé",
                "anciennete_client_mois": 48,
                "revenu_mensuel_fcfa": 600000,
                "type_produit": "Crédit consommation",
                "montant_credit_fcfa": 2000000,
                "duree_mois": 36,
                "taux_interet": 11.5,
                "garantie": "Salaire",
                "nb_incidents_24m": 0,
                "nb_credits_en_cours": 1
            }
        }
    )


# =====================================================================
# RÉSULTAT DE SCORING
# =====================================================================
class ScoringResult(BaseModel):
    """Résultat du scoring d'un client"""
    probabilite_defaut: float = Field(..., description="Probabilité de défaut (%)")
    score: int = Field(..., description="Score interne 0-1000 (1000 = excellent)")
    categorie: str = Field(..., description="Catégorie de risque (A-E)")
    decision: Literal['ACCEPTÉ', 'À EXAMINER', 'REFUSÉ'] = Field(
        ..., description="Décision recommandée"
    )
    recommandation: str = Field(..., description="Recommandation détaillée")


# =====================================================================
# BATCH DE CLIENTS
# =====================================================================
class BatchInput(BaseModel):
    """Liste de clients à scorer en une seule requête"""
    clients: list[ClientInput] = Field(..., min_length=1, max_length=100)


class BatchResult(BaseModel):
    """Résultats du scoring batch"""
    total: int
    resultats: list[ScoringResult]


# =====================================================================
# KPI GLOBAUX
# =====================================================================
class KPIResponse(BaseModel):
    """KPI globaux du portefeuille"""
    total_prets: int
    nb_defauts: int
    taux_defaut_pct: float
    encours_total_fcfa: float
    encours_defaut_fcfa: float
    montant_moyen_fcfa: float
    taux_interet_moyen: float