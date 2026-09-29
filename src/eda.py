"""
Analyse Exploratoire des Données (EDA) - Risque Crédit Gabon
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path


# Palette cohérente
COLORS = {
    'sain': '#2a9d8f',
    'defaut': '#e63946',
    'primaire': '#1f3a5f',
    'accent': '#f4a261',
}
COLOR_MAP = {0: COLORS['sain'], 1: COLORS['defaut']}


def analyse_globale(df):
    """KPI globaux + stats clés"""
    print("=" * 70)
    print("📊 ANALYSE GLOBALE DU PORTEFEUILLE")
    print("=" * 70)
    
    stats = {
        'total_prets': len(df),
        'taux_defaut_global': round(df['defaut'].mean() * 100, 2),
        'montant_total_fcfa': df['montant_credit_fcfa'].sum(),
        'montant_moyen_fcfa': df['montant_credit_fcfa'].mean(),
        'encours_defaut_fcfa': df.loc[df['defaut'] == 1, 'montant_credit_fcfa'].sum(),
        'taux_interet_moyen': round(df['taux_interet'].mean(), 2),
        'revenu_median': df['revenu_mensuel_fcfa'].median(),
        'ratio_effort_moyen': round(df['taux_effort'].mean(), 2),
    }
    
    print(f"\n📈 Indicateurs clés :")
    print(f"   • Total prêts          : {stats['total_prets']:,}")
    print(f"   • Taux de défaut       : {stats['taux_defaut_global']}%")
    print(f"   • Encours total        : {stats['montant_total_fcfa']/1e9:.2f} milliards FCFA")
    print(f"   • Montant moyen        : {stats['montant_moyen_fcfa']/1e6:.2f} M FCFA")
    print(f"   • Encours en défaut    : {stats['encours_defaut_fcfa']/1e9:.2f} milliards FCFA")
    print(f"   • Taux d'intérêt moyen : {stats['taux_interet_moyen']}%")
    print(f"   • Revenu médian        : {stats['revenu_median']:,.0f} FCFA")
    
    return stats


def graphique_taux_defaut_par_segment(df, segment_col, titre=None, ordre=None):
    """Génère un bar chart du taux de défaut par segment"""
    data = (
        df.groupby(segment_col, observed=True)['defaut']
        .agg(['count', 'mean'])
        .reset_index()
    )
    data['taux_defaut'] = (data['mean'] * 100).round(2)
    data = data.rename(columns={'count': 'nb_prets'})
    
    if ordre:
        data[segment_col] = pd.Categorical(
            data[segment_col], categories=ordre, ordered=True
        )
        data = data.sort_values(segment_col)
    
    fig = px.bar(
        data, x=segment_col, y='taux_defaut',
        color='taux_defaut',
        color_continuous_scale='Reds',
        text='taux_defaut',
        title=titre or f"Taux de défaut par {segment_col}",
        hover_data={'nb_prets': True, 'mean': False}
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        template='plotly_white',
        coloraxis_showscale=False,
        height=400,
        yaxis_title="Taux de défaut (%)",
        xaxis_title=""
    )
    return fig, data


def graphique_distribution(df, col, titre=None, log_x=False):
    """Distribution d'une variable selon le défaut"""
    fig = px.histogram(
        df, x=col, color='defaut',
        nbins=50,
        barmode='overlay',
        color_discrete_map=COLOR_MAP,
        title=titre or f"Distribution de {col}",
        log_y=log_x,
        labels={'defaut': 'Statut'}
    )
    fig.update_layout(
        template='plotly_white',
        height=400,
        legend_title="Statut"
    )
    return fig


def graphique_correlation(df):
    """Matrice de corrélation avec la target"""
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Retirer les colonnes redondantes
    cols_exclure = ['revenu_log', 'montant_log', 'risque_produit']
    num_cols = [c for c in num_cols if c not in cols_exclure]
    
    corr = df[num_cols].corr()[['defaut']].drop('defaut')
    corr = corr.sort_values('defaut')
    
    fig = px.bar(
        corr.reset_index(),
        x='defaut', y='index',
        orientation='h',
        color='defaut',
        color_continuous_scale='RdBu_r',
        title="Corrélation des variables avec le défaut",
        labels={'defaut': 'Corrélation', 'index': ''}
    )
    fig.update_layout(
        template='plotly_white',
        height=500,
        coloraxis_showscale=False
    )
    return fig, corr


def graphique_double_critere(df, col1, col2, titre=None):
    """Croisement de 2 variables catégorielles"""
    pivot = (
        df.groupby([col1, col2], observed=True)['defaut']
        .mean()
        .reset_index()
    )
    pivot['taux_defaut'] = (pivot['defaut'] * 100).round(2)
    
    fig = px.density_heatmap(
        pivot, x=col1, y=col2, z='taux_defaut',
        color_continuous_scale='Reds',
        text_auto='.1f',
        title=titre or f"Taux de défaut : {col1} × {col2}"
    )
    fig.update_layout(template='plotly_white', height=450)
    return fig, pivot


def graphique_evolution_temporelle(df):
    """Évolution du taux de défaut dans le temps (approximatif)"""
    # On utilise l'index comme proxy temporel
    df_temp = df.copy()
    df_temp['bucket'] = pd.qcut(df_temp.index, q=10, labels=False)
    evolution = (
        df_temp.groupby('bucket')['defaut']
        .agg(['count', 'mean'])
        .reset_index()
    )
    evolution['taux_defaut'] = (evolution['mean'] * 100).round(2)
    
    fig = px.line(
        evolution, x='bucket', y='taux_defaut',
        markers=True,
        title="Évolution du taux de défaut (par décile)",
        labels={'bucket': 'Période (décile)', 'taux_defaut': 'Taux de défaut (%)'}
    )
    fig.update_traces(line_color=COLORS['defaut'], line_width=3)
    fig.update_layout(template='plotly_white', height=400)
    return fig, evolution


def generer_rapport_eda(df, output_dir='reports/eda'):
    """Génère tous les graphiques et les sauvegarde en HTML"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("📈 GÉNÉRATION DES GRAPHIQUES EDA")
    print("=" * 70)
    
    graphiques = {}
    
    # 1. Taux de défaut par tranche d'âge
    fig, data = graphique_taux_defaut_par_segment(
        df, 'tranche_age', 
        "Taux de défaut par tranche d'âge",
        ordre=['18-29', '30-44', '45-59', '60+']
    )
    graphiques['defaut_par_age'] = fig
    print(f"\n✅ defaut_par_age — {len(data)} segments")
    print(data.to_string(index=False))
    
    # 2. Taux de défaut par secteur d'activité
    fig, data = graphique_taux_defaut_par_segment(
        df, 'secteur_activite',
        "Taux de défaut par secteur d'activité"
    )
    graphiques['defaut_par_secteur'] = fig
    print(f"\n✅ defaut_par_secteur — {len(data)} segments")
    print(data.sort_values('taux_defaut', ascending=False).to_string(index=False))
    
    # 3. Taux de défaut par type de produit
    fig, data = graphique_taux_defaut_par_segment(
        df, 'type_produit',
        "Taux de défaut par type de produit"
    )
    graphiques['defaut_par_produit'] = fig
    print(f"\n✅ defaut_par_produit — {len(data)} segments")
    print(data.sort_values('taux_defaut', ascending=False).to_string(index=False))
    
    # 4. Taux de défaut par tranche de revenu
    fig, data = graphique_taux_defaut_par_segment(
        df, 'tranche_revenu',
        "Taux de défaut par tranche de revenu",
        ordre=['<200k', '200-500k', '500k-1M', '>1M']
    )
    graphiques['defaut_par_revenu'] = fig
    print(f"\n✅ defaut_par_revenu")
    print(data.to_string(index=False))
    
    # 5. Taux de défaut par ville
    fig, data = graphique_taux_defaut_par_segment(
        df, 'ville',
        "Taux de défaut par ville"
    )
    graphiques['defaut_par_ville'] = fig
    print(f"\n✅ defaut_par_ville")
    print(data.sort_values('taux_defaut', ascending=False).to_string(index=False))
    
    # 6. Taux de défaut selon incidents
    df['incidents_label'] = df['nb_incidents_24m'].map({
        0: 'Sans incidents (24m)', 1: 'Avec incidents (24m)'
    })
    fig, data = graphique_taux_defaut_par_segment(
        df, 'incidents_label',
        "Impact des incidents de paiement (24 mois)"
    )
    graphiques['defaut_par_incidents'] = fig
    print(f"\n✅ defaut_par_incidents")
    print(data.to_string(index=False))
    
    # 7. Taux de défaut par garantie
    fig, data = graphique_taux_defaut_par_segment(
        df, 'garantie',
        "Taux de défaut selon le type de garantie"
    )
    graphiques['defaut_par_garantie'] = fig
    print(f"\n✅ defaut_par_garantie")
    print(data.sort_values('taux_defaut').to_string(index=False))
    
    # 8. Corrélations
    fig, corr = graphique_correlation(df)
    graphiques['correlations'] = fig
    print(f"\n✅ correlations")
    print(corr.round(3).to_string())
    
    # 9. Croisement secteur × garantie
    fig, pivot = graphique_double_critere(
        df, 'secteur_activite', 'garantie',
        "Taux de défaut : Secteur × Garantie"
    )
    graphiques['heatmap_secteur_garantie'] = fig
    print(f"\n✅ heatmap_secteur_garantie")
    
    # 10. Distribution des montants
    fig = graphique_distribution(
        df[df['montant_credit_fcfa'] < df['montant_credit_fcfa'].quantile(0.95)],
        'montant_credit_fcfa',
        "Distribution des montants de crédit selon le défaut"
    )
    graphiques['distribution_montants'] = fig
    print(f"\n✅ distribution_montants")
    
    # Sauvegarde HTML
    print(f"\n💾 Sauvegarde des graphiques dans {output_dir}/")
    for nom, fig in graphiques.items():
        chemin = f"{output_dir}/{nom}.html"
        fig.write_html(chemin)
        print(f"   ✅ {nom}.html")
    
    return graphiques


if __name__ == '__main__':
    # Chargement
    print("🔄 Chargement des données nettoyées...")
    df = pd.read_csv('data/processed/credits_clean.csv')
    
    # Analyse globale
    stats = analyse_globale(df)
    
    # Génération des graphiques
    graphiques = generer_rapport_eda(df)
    
    print("\n" + "=" * 70)
    print("✅ EDA TERMINÉE")
    print("=" * 70)
    print(f"\n📁 {len(graphiques)} graphiques générés dans reports/eda/")
    print("👉 Ouvre-les dans ton navigateur pour les visualiser")