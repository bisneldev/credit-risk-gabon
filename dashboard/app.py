"""
Dashboard interactif - Analyse du Risque Crédit Bancaire
Contexte : Banque gabonaise - Conforme COBAC
"""
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3

# =====================================================================
# CHARGEMENT DES DONNÉES
# =====================================================================
DB_PATH = 'database/credit_risk.db'
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM credits", conn)
conn.close()

print(f"✅ {len(df):,} lignes chargées depuis la base SQLite")

# =====================================================================
# PALETTE & CONSTANTES
# =====================================================================
COLORS = {
    'primaire': '#1f3a5f',
    'accent': '#e63946',
    'success': '#2a9d8f',
    'warning': '#f4a261',
    'light': '#f5f7fa',
    'white': '#ffffff',
}
DEFECT_COLORS = {0: COLORS['success'], 1: COLORS['accent']}


# =====================================================================
# FONCTION KPI CARD
# =====================================================================
def kpi_card(titre, valeur, sous_titre="", couleur=None):
    couleur = couleur or COLORS['primaire']
    return html.Div([
        html.P(titre, style={
            'margin': 0, 'color': '#7a8899', 'fontSize': '13px',
            'fontWeight': '600', 'letterSpacing': '0.5px',
            'textTransform': 'uppercase'
        }),
        html.H2(valeur, style={
            'margin': '8px 0 4px 0', 'color': couleur,
            'fontSize': '28px', 'fontWeight': '700'
        }),
        html.P(sous_titre, style={
            'margin': 0, 'color': '#a0aec0', 'fontSize': '12px'
        }),
    ], style={
        'background': COLORS['white'],
        'padding': '20px 22px',
        'borderRadius': '12px',
        'boxShadow': '0 2px 12px rgba(0,0,0,0.06)',
        'borderLeft': f'4px solid {couleur}',
        'flex': 1,
        'minWidth': '200px'
    })


# =====================================================================
# APPLICATION
# =====================================================================
app = dash.Dash(__name__, title="Risque Crédit - Gabon")
server = app.server

# ---------- LAYOUT ----------
app.layout = html.Div([

    # HEADER
    html.Div([
        html.Div([
            html.H1("🏦 Analyse du Risque Crédit",
                    style={'margin': 0, 'color': 'white',
                           'fontSize': '28px', 'fontWeight': '700'}),
            html.P("Portefeuille bancaire — Contexte Gabon / COBAC",
                   style={'margin': '5px 0 0 0', 'color': '#b8c5d6',
                          'fontSize': '14px'}),
        ], style={'flex': 1}),
        html.Div([
            html.P(f"📊 {len(df):,} prêts analysés",
                   style={'color': 'white', 'margin': 0,
                          'fontSize': '14px', 'fontWeight': '600'}),
            html.P(f"💰 {df['montant_credit_fcfa'].sum()/1e9:.2f} Mds FCFA",
                   style={'color': '#b8c5d6', 'margin': '4px 0 0 0',
                          'fontSize': '13px'}),
        ], style={'textAlign': 'right'})
    ], style={
        'background': f'linear-gradient(90deg, {COLORS["primaire"]}, #2c5282)',
        'padding': '25px 40px',
        'display': 'flex',
        'alignItems': 'center'
    }),

    # KPIs
    html.Div(id='kpi-container', style={
        'display': 'flex',
        'gap': '20px',
        'padding': '25px 40px',
        'flexWrap': 'wrap'
    }),

    # FILTRES
    html.Div([
        html.Div([
            html.Label("🏭 Secteur d'activité",
                       style={'fontWeight': '600', 'fontSize': '13px',
                              'color': '#4a5568', 'marginBottom': '6px',
                              'display': 'block'}),
            dcc.Dropdown(
                id='filtre-secteur',
                options=[{'label': 'Tous les secteurs', 'value': 'ALL'}] +
                        [{'label': s, 'value': s}
                         for s in sorted(df['secteur_activite'].unique())],
                value='ALL', clearable=False,
                style={'fontSize': '14px'}
            )
        ], style={'flex': 1, 'minWidth': '220px'}),

        html.Div([
            html.Label("💳 Type de produit",
                       style={'fontWeight': '600', 'fontSize': '13px',
                              'color': '#4a5568', 'marginBottom': '6px',
                              'display': 'block'}),
            dcc.Dropdown(
                id='filtre-produit',
                options=[{'label': 'Tous les produits', 'value': 'ALL'}] +
                        [{'label': p, 'value': p}
                         for p in sorted(df['type_produit'].unique())],
                value='ALL', clearable=False,
                style={'fontSize': '14px'}
            )
        ], style={'flex': 1, 'minWidth': '220px'}),

        html.Div([
            html.Label("📊 Taux de défaut",
                       style={'fontWeight': '600', 'fontSize': '13px',
                              'color': '#4a5568', 'marginBottom': '6px',
                              'display': 'block'}),
            dcc.Dropdown(
                id='filtre-defaut',
                options=[
                    {'label': 'Tous les crédits', 'value': 'ALL'},
                    {'label': 'Sains uniquement', 'value': 0},
                    {'label': 'En défaut uniquement', 'value': 1},
                ],
                value='ALL', clearable=False,
                style={'fontSize': '14px'}
            )
        ], style={'flex': 1, 'minWidth': '220px'}),
    ], style={
        'display': 'flex',
        'gap': '20px',
        'padding': '0 40px 25px 40px',
        'flexWrap': 'wrap'
    }),

    # GRAPHIQUES LIGNE 1
    html.Div([
        html.Div(dcc.Graph(id='graph-secteur'),
                 style={'flex': 1, 'minWidth': '450px'}),
        html.Div(dcc.Graph(id='graph-produit'),
                 style={'flex': 1, 'minWidth': '450px'}),
    ], style={
        'display': 'flex', 'gap': '20px',
        'padding': '0 40px 20px 40px', 'flexWrap': 'wrap'
    }),

    # GRAPHIQUES LIGNE 2
    html.Div([
        html.Div(dcc.Graph(id='graph-incidents'),
                 style={'flex': 1, 'minWidth': '450px'}),
        html.Div(dcc.Graph(id='graph-revenu'),
                 style={'flex': 1, 'minWidth': '450px'}),
    ], style={
        'display': 'flex', 'gap': '20px',
        'padding': '0 40px 20px 40px', 'flexWrap': 'wrap'
    }),

    # MATRICE COBAC
    html.Div([
        html.H3("🏛️ Matrice de risque COBAC (simulation)",
                style={'color': COLORS['primaire'], 'padding': '0 40px',
                       'margin': '20px 0 10px 0'}),
        html.Div(dcc.Graph(id='graph-cobac'),
                 style={'padding': '0 40px'})
    ]),

    # TABLEAU TOP SEGMENTS
    html.Div([
        html.H3("🔴 Top 10 segments les plus risqués",
                style={'color': COLORS['primaire'], 'padding': '0 40px',
                       'margin': '20px 0 10px 0'}),
        html.Div(id='tableau-risque',
                 style={'padding': '0 40px 40px 40px'})
    ]),

    # FOOTER
    html.Div([
        html.P("📌 Projet d'analyse du risque crédit — Python, SQL, Plotly Dash",
               style={'color': '#718096', 'fontSize': '12px',
                      'textAlign': 'center', 'margin': 0}),
    ], style={'padding': '20px', 'background': '#e2e8f0'})

], style={
    'fontFamily': "'Segoe UI', Arial, sans-serif",
    'background': COLORS['light'],
    'minHeight': '100vh',
    'margin': 0
})


# =====================================================================
# CALLBACK PRINCIPAL
# =====================================================================
@app.callback(
    [Output('kpi-container', 'children'),
     Output('graph-secteur', 'figure'),
     Output('graph-produit', 'figure'),
     Output('graph-incidents', 'figure'),
     Output('graph-revenu', 'figure'),
     Output('graph-cobac', 'figure'),
     Output('tableau-risque', 'children')],
    [Input('filtre-secteur', 'value'),
     Input('filtre-produit', 'value'),
     Input('filtre-defaut', 'value')]
)
def update_dashboard(secteur, produit, defaut):
    # ---- Filtrage ----
    dff = df.copy()
    if secteur != 'ALL':
        dff = dff[dff['secteur_activite'] == secteur]
    if produit != 'ALL':
        dff = dff[dff['type_produit'] == produit]
    if defaut != 'ALL':
        dff = dff[dff['defaut'] == defaut]
    
    if len(dff) == 0:
        empty = go.Figure().update_layout(
            title="Aucune donnée pour ces filtres",
            template='plotly_white'
        )
        return [], empty, empty, empty, empty, empty, html.P("Aucune donnée")
    
    # ---- KPIs ----
    taux = dff['defaut'].mean() * 100
    perte_pot = dff.loc[dff['defaut'] == 1, 'montant_credit_fcfa'].sum() * 0.6
    
    kpis = [
        kpi_card("📊 Total prêts", f"{len(dff):,}",
                 f"{len(dff)/len(df)*100:.1f} % du portefeuille",
                 COLORS['primaire']),
        kpi_card("⚠️ Taux de défaut", f"{taux:.2f} %",
                 f"{dff['defaut'].sum():,} prêts en défaut",
                 COLORS['accent']),
        kpi_card("💰 Encours", f"{dff['montant_credit_fcfa'].sum()/1e9:.2f} Mds",
                 "FCFA", COLORS['success']),
        kpi_card("🔻 Perte potentielle", f"{perte_pot/1e9:.2f} Mds",
                 "FCFA (LGD 60%)", COLORS['warning']),
    ]
    
    # ---- Graph 1 : Taux de défaut par secteur ----
    g1 = (dff.groupby('secteur_activite')['defaut']
          .agg(['count', 'mean']).reset_index())
    g1['taux'] = (g1['mean'] * 100).round(2)
    g1 = g1.sort_values('taux', ascending=True)
    
    fig1 = px.bar(
        g1, x='taux', y='secteur_activite', orientation='h',
        color='taux', color_continuous_scale='Reds',
        text='taux',
        title="Taux de défaut par secteur",
        labels={'taux': 'Taux (%)', 'secteur_activite': ''}
    )
    fig1.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig1.update_layout(
        template='plotly_white', height=400,
        coloraxis_showscale=False,
        margin=dict(l=10, r=40, t=50, b=10)
    )
    
    # ---- Graph 2 : Taux de défaut par produit ----
    g2 = (dff.groupby('type_produit')['defaut']
          .agg(['count', 'mean']).reset_index())
    g2['taux'] = (g2['mean'] * 100).round(2)
    g2 = g2.sort_values('taux', ascending=True)
    
    fig2 = px.bar(
        g2, x='taux', y='type_produit', orientation='h',
        color='taux', color_continuous_scale='OrRd',
        text='taux',
        title="Taux de défaut par type de produit",
        labels={'taux': 'Taux (%)', 'type_produit': ''}
    )
    fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig2.update_layout(
        template='plotly_white', height=400,
        coloraxis_showscale=False,
        margin=dict(l=10, r=40, t=50, b=10)
    )
    
    # ---- Graph 3 : Impact des incidents ----
    dff_inc = dff.copy()
    dff_inc['incidents'] = dff_inc['nb_incidents_24m'].map({
        0: 'Sans incidents', 1: 'Avec incidents'
    })
    g3 = (dff_inc.groupby('incidents')['defaut']
          .agg(['count', 'mean']).reset_index())
    g3['taux'] = (g3['mean'] * 100).round(2)
    
    fig3 = px.bar(
        g3, x='incidents', y='taux',
        color='incidents',
        color_discrete_map={
            'Sans incidents': COLORS['success'],
            'Avec incidents': COLORS['accent']
        },
        text='taux',
        title="Impact des incidents de paiement (24 mois)",
        labels={'taux': 'Taux de défaut (%)', 'incidents': ''}
    )
    fig3.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig3.update_layout(
        template='plotly_white', height=400,
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    # ---- Graph 4 : Taux de défaut par tranche de revenu ----
    g4 = (dff.groupby('tranche_revenu', observed=True)['defaut']
          .agg(['count', 'mean']).reset_index())
    g4['taux'] = (g4['mean'] * 100).round(2)
    g4['tranche_revenu'] = pd.Categorical(
        g4['tranche_revenu'],
        categories=['<200k', '200-500k', '500k-1M', '>1M'],
        ordered=True
    )
    g4 = g4.sort_values('tranche_revenu')
    
    fig4 = px.bar(
        g4, x='tranche_revenu', y='taux',
        color='taux', color_continuous_scale='Blues',
        text='taux',
        title="Taux de défaut par tranche de revenu",
        labels={'taux': 'Taux (%)', 'tranche_revenu': 'Revenu mensuel (FCFA)'}
    )
    fig4.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig4.update_layout(
        template='plotly_white', height=400,
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    # ---- Graph 5 : Matrice COBAC (recalculée sur sous-ensemble) ----
    cobac = dff.copy()
    cobac['categorie_cobac'] = 'Saine'
    cobac.loc[
        (cobac['taux_effort'] >= 30) & (cobac['nb_incidents_24m'] == 0),
        'categorie_cobac'] = 'Observation'
    cobac.loc[
        (cobac['taux_effort'] >= 40) | (cobac['nb_incidents_24m'] == 1),
        'categorie_cobac'] = 'Douteuse'
    cobac.loc[
        (cobac['taux_effort'] >= 50) & (cobac['nb_incidents_24m'] == 1),
        'categorie_cobac'] = 'Litigieuse'
    
    g5 = (cobac.groupby('categorie_cobac')
          .agg(nb=('defaut', 'count'), taux=('defaut', 'mean'))
          .reset_index())
    g5['taux'] = (g5['taux'] * 100).round(2)
    
    ordre_cobac = ['Saine', 'Observation', 'Douteuse', 'Litigieuse']
    # Ne garder que les catégories réellement présentes dans les données filtrées
    ordre_present = [c for c in ordre_cobac if c in g5['categorie_cobac'].values]
    g5['categorie_cobac'] = pd.Categorical(
        g5['categorie_cobac'], categories=ordre_present, ordered=True
    )
    g5 = g5.sort_values('categorie_cobac')
    
    colors_cobac = {
        'Saine': COLORS['success'],
        'Observation': '#8ecae6',
        'Douteuse': COLORS['warning'],
        'Litigieuse': COLORS['accent']
    }
    
    fig5 = px.bar(
        g5, x='categorie_cobac', y='taux',
        color='categorie_cobac',
        color_discrete_map=colors_cobac,
        text='taux',
        title="Classification COBAC — Taux de défaut observé",
        labels={'taux': 'Taux observé (%)', 'categorie_cobac': 'Catégorie'}
    )
    fig5.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig5.update_layout(
        template='plotly_white', height=380,
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    # ---- Tableau top segments ----
    top = (dff.groupby(['secteur_activite', 'type_produit'])['defaut']
           .agg(['count', 'mean']).reset_index())
    top = top[top['count'] >= 20].nlargest(10, 'mean')
    top['Taux défaut'] = (top['mean'] * 100).round(2).astype(str) + ' %'
    top['Nb prêts'] = top['count'].apply(lambda x: f"{x:,}")
    top = top.rename(columns={
        'secteur_activite': 'Secteur',
        'type_produit': 'Produit'
    })
    
    tableau = dash_table.DataTable(
        data=top[['Secteur', 'Produit', 'Nb prêts', 'Taux défaut']].to_dict('records'),
        columns=[
            {'name': c, 'id': c}
            for c in ['Secteur', 'Produit', 'Nb prêts', 'Taux défaut']
        ],
        style_cell={
            'textAlign': 'left',
            'padding': '12px 15px',
            'fontFamily': "'Segoe UI', Arial, sans-serif",
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': COLORS['primaire'],
            'color': 'white',
            'fontWeight': 'bold',
            'fontSize': '13px',
            'textTransform': 'uppercase'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'},
             'backgroundColor': '#f8f9fa'},
            {'if': {'column_id': 'Taux défaut'},
             'fontWeight': 'bold', 'color': COLORS['accent']},
        ],
        style_as_list_view=True,
    )
    
    return kpis, fig1, fig2, fig3, fig4, fig5, tableau


# =====================================================================
# LANCEMENT
# =====================================================================
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 Dashboard démarré")
    print("=" * 70)
    print("👉 Ouvre ton navigateur : http://127.0.0.1:8050")
    print("⛔ Pour arrêter : Ctrl + C")
    print("=" * 70 + "\n")
    app.run(debug=True, port=8050)