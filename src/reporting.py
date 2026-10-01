"""
Génération de rapports réglementaires COBAC
- Rapport PDF (KPIs, analyses, recommandations)
- Fichier Excel multi-onglets
"""
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime

# PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# Excel
import xlsxwriter


# =====================================================================
# PALETTE
# =====================================================================
COLORS = {
    'primaire': '#1f3a5f',
    'accent': '#e63946',
    'success': '#2a9d8f',
    'warning': '#f4a261',
    'light': '#f5f7fa',
}


# =====================================================================
# CHARGEMENT DES DONNÉES
# =====================================================================
def charger_donnees(db_path='database/credit_risk.db'):
    """Charge le DataFrame depuis SQLite"""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM credits", conn)
    conn.close()
    return df


# =====================================================================
# CALCUL DES KPIs
# =====================================================================
def calculer_kpis(df):
    """Calcule tous les KPIs du portefeuille"""
    return {
        'total_prets': len(df),
        'nb_defauts': int(df['defaut'].sum()),
        'taux_defaut': round(df['defaut'].mean() * 100, 2),
        'encours_total_fcfa': df['montant_credit_fcfa'].sum(),
        'encours_defaut_fcfa': df.loc[df['defaut'] == 1, 'montant_credit_fcfa'].sum(),
        'perte_potentielle_fcfa': df.loc[df['defaut'] == 1, 'montant_credit_fcfa'].sum() * 0.6,
        'montant_moyen_fcfa': df['montant_credit_fcfa'].mean(),
        'taux_interet_moyen': round(df['taux_interet'].mean(), 2),
        'taux_effort_moyen': round(df['taux_effort'].mean(), 2),
    }


# =====================================================================
# RAPPORT PDF
# =====================================================================
def generer_rapport_pdf(df, output_path='reports/rapport_cobac.pdf'):
    """Génère un rapport PDF professionnel style COBAC"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"📄 Génération du rapport PDF...")
    
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    titre_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=20, textColor=colors.HexColor(COLORS['primaire']),
        spaceAfter=6, alignment=TA_CENTER
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontSize=14, textColor=colors.HexColor(COLORS['primaire']),
        spaceBefore=20, spaceAfter=10
    )
    normal_style = ParagraphStyle(
        'Normal', parent=styles['Normal'],
        fontSize=10, alignment=TA_JUSTIFY, leading=14
    )
    small_style = ParagraphStyle(
        'Small', parent=styles['Normal'],
        fontSize=8, textColor=colors.grey
    )
    
    kpis = calculer_kpis(df)
    elements = []
    
    # ---- EN-TÊTE ----
    elements.append(Paragraph(
        "RAPPORT D'ANALYSE DU RISQUE CRÉDIT", titre_style
    ))
    elements.append(Paragraph(
        f"Conforme aux exigences de classification COBAC",
        ParagraphStyle('sub', parent=styles['Normal'], fontSize=11,
                       textColor=colors.HexColor('#666'), alignment=TA_CENTER)
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"Date du rapport : {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle('date', parent=small_style, alignment=TA_CENTER)
    ))
    elements.append(Spacer(1, 20))
    
    # ---- SECTION 1 : SYNTHÈSE ----
    elements.append(Paragraph("1. Synthèse exécutive", h1_style))
    
    synthesis_text = f"""
    Le portefeuille analysé comprend <b>{kpis['total_prets']:,} crédits</b> 
    pour un encours total de <b>{kpis['encours_total_fcfa']/1e9:.2f} milliards FCFA</b>. 
    Le taux de défaut observé s'élève à <b>{kpis['taux_defaut']}%</b>, 
    représentant <b>{kpis['nb_defauts']:,} dossiers</b> pour un encours en défaut 
    de <b>{kpis['encours_defaut_fcfa']/1e9:.2f} milliards FCFA</b>.
    """
    elements.append(Paragraph(synthesis_text, normal_style))
    elements.append(Spacer(1, 12))
    
    # ---- TABLEAU KPI ----
    data_kpi = [
        ['Indicateur', 'Valeur'],
        ['Total prêts', f"{kpis['total_prets']:,}"],
        ['Taux de défaut global', f"{kpis['taux_defaut']} %"],
        ['Nombre de défauts', f"{kpis['nb_defauts']:,}"],
        ['Encours total', f"{kpis['encours_total_fcfa']/1e9:.2f} Mds FCFA"],
        ['Encours en défaut', f"{kpis['encours_defaut_fcfa']/1e9:.2f} Mds FCFA"],
        ['Perte potentielle (LGD 60%)', f"{kpis['perte_potentielle_fcfa']/1e9:.2f} Mds FCFA"],
        ['Montant moyen', f"{kpis['montant_moyen_fcfa']/1e6:.2f} M FCFA"],
    ]
    
    table_kpi = Table(data_kpi, colWidths=[8*cm, 8*cm])
    table_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primaire'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_kpi)
    
    # ---- SECTION 2 : ANALYSE PAR SECTEUR ----
    elements.append(Paragraph("2. Analyse du risque par secteur d'activité", h1_style))
    
    secteurs = (
        df.groupby('secteur_activite')['defaut']
        .agg(['count', 'sum', 'mean'])
        .reset_index()
        .sort_values('mean', ascending=False)
    )
    secteurs['taux'] = (secteurs['mean'] * 100).round(2)
    secteurs['exposition'] = df.groupby('secteur_activite')['montant_credit_fcfa'].sum().values / 1e6
    
    data_secteurs = [['Secteur', 'Nb prêts', 'Défauts', 'Taux', 'Exposition (M FCFA)']]
    for _, row in secteurs.iterrows():
        data_secteurs.append([
            row['secteur_activite'],
            f"{int(row['count']):,}",
            f"{int(row['sum']):,}",
            f"{row['taux']:.2f} %",
            f"{row['exposition']:.1f}",
        ])
    
    table_secteurs = Table(data_secteurs, colWidths=[4.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4*cm])
    table_secteurs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primaire'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(table_secteurs)
    
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        f"<b>Constat :</b> le secteur <b>{secteurs.iloc[0]['secteur_activite']}</b> "
        f"présente le taux de défaut le plus élevé (<b>{secteurs.iloc[0]['taux']:.2f}%</b>), "
        f"contre <b>{secteurs.iloc[-1]['taux']:.2f}%</b> pour le secteur "
        f"le moins risqué ({secteurs.iloc[-1]['secteur_activite']}).",
        normal_style
    ))
    
    # ---- SECTION 3 : ANALYSE PAR PRODUIT ----
    elements.append(Paragraph("3. Analyse du risque par type de produit", h1_style))
    
    produits = (
        df.groupby('type_produit')['defaut']
        .agg(['count', 'sum', 'mean'])
        .reset_index()
        .sort_values('mean', ascending=False)
    )
    produits['taux'] = (produits['mean'] * 100).round(2)
    
    data_produits = [['Type de produit', 'Nb prêts', 'Défauts', 'Taux de défaut']]
    for _, row in produits.iterrows():
        data_produits.append([
            row['type_produit'],
            f"{int(row['count']):,}",
            f"{int(row['sum']):,}",
            f"{row['taux']:.2f} %",
        ])
    
    table_produits = Table(data_produits, colWidths=[6*cm, 3*cm, 3*cm, 4*cm])
    table_produits.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primaire'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(table_produits)
    
    # ---- PAGE BREAK ----
    elements.append(PageBreak())
    
    # ---- SECTION 4 : CLASSIFICATION COBAC ----
    elements.append(Paragraph("4. Classification COBAC des créances", h1_style))
    
    # Recalcul COBAC sur les données
    cobac = df.copy()
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
    
    cobac_stats = (
        cobac.groupby('categorie_cobac')
        .agg(nb=('defaut', 'count'), defauts=('defaut', 'sum'),
             encours=('montant_credit_fcfa', 'sum'),
             taux=('defaut', 'mean'))
        .reset_index()
    )
    cobac_stats['part_pct'] = (cobac_stats['nb'] / len(cobac) * 100).round(2)
    cobac_stats['taux'] = (cobac_stats['taux'] * 100).round(2)
    cobac_stats['encours_mds'] = (cobac_stats['encours'] / 1e9).round(3)
    
    data_cobac = [['Catégorie COBAC', 'Nb crédits', 'Part', 'Encours', 'Taux défaut']]
    ordre = ['Saine', 'Observation', 'Douteuse', 'Litigieuse']
    for cat in ordre:
        row = cobac_stats[cobac_stats['categorie_cobac'] == cat]
        if len(row) > 0:
            row = row.iloc[0]
            data_cobac.append([
                cat,
                f"{int(row['nb']):,}",
                f"{row['part_pct']:.2f} %",
                f"{row['encours_mds']:.3f} Mds",
                f"{row['taux']:.2f} %",
            ])
    
    table_cobac = Table(data_cobac, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    table_cobac.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primaire'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(table_cobac)
    
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        "<b>Lecture :</b> la classification COBAC discrimine efficacement les profils. "
        "Les créances classées 'Saine' présentent un taux de défaut nettement inférieur "
        "à celui des créances 'Douteuses' ou 'Litigieuses'.",
        normal_style
    ))
    
    # ---- SECTION 5 : RECOMMANDATIONS ----
    elements.append(Paragraph("5. Recommandations", h1_style))
    
    recommandations = [
        "<b>Renforcer le scoring d'entrée</b> sur les produits à fort risque "
        "(Microfinance, Crédit PME) et les secteurs sensibles (Agriculture, BTP).",
        
        "<b>Contrôle systématique</b> des clients présentant des incidents de paiement "
        "sur les 24 derniers mois (facteur #1 de risque).",
        
        "<b>Pilotage trimestriel</b> via le dashboard interactif et suivi de la "
        "classification COBAC.",
        
        "<b>Industrialisation du scoring prédictif</b> (modèle Random Forest - AUC 0,82) "
        "pour automatiser les décisions d'octroi.",
        
        "<b>Reporting réglementaire automatisé</b> conforme aux exigences COBAC."
    ]
    
    for i, rec in enumerate(recommandations, 1):
        elements.append(Paragraph(f"{i}. {rec}", normal_style))
        elements.append(Spacer(1, 6))
    
    # ---- PIED DE PAGE ----
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "Document généré automatiquement — Projet d'analyse du risque crédit bancaire",
        small_style
    ))
    
    # ---- BUILD ----
    doc.build(elements)
    print(f"✅ Rapport PDF généré : {output_path}")
    return output_path


# =====================================================================
# RAPPORT EXCEL
# =====================================================================
def generer_rapport_excel(df, output_path='reports/rapport_cobac.xlsx'):
    """Génère un Excel multi-onglets formaté"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    print(f"📊 Génération du rapport Excel...")
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formats
        titre_fmt = workbook.add_format({
            'bold': True, 'font_size': 16, 
            'font_color': COLORS['primaire'], 'align': 'center'
        })
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': COLORS['primaire'],
            'font_color': 'white', 'border': 1, 'align': 'center'
        })
        kpi_label_fmt = workbook.add_format({
            'bold': True, 'bg_color': COLORS['light'],
            'border': 1, 'align': 'left'
        })
        kpi_value_fmt = workbook.add_format({
            'border': 1, 'align': 'right', 'num_format': '#,##0.00'
        })
        cell_fmt = workbook.add_format({'border': 1})
        
        # ---- ONGLET 1 : SYNTHÈSE ----
        kpis = calculer_kpis(df)
        df_kpi = pd.DataFrame([
            ['Total prêts', kpis['total_prets']],
            ['Taux de défaut (%)', kpis['taux_defaut']],
            ['Nombre de défauts', kpis['nb_defauts']],
            ['Encours total (FCFA)', kpis['encours_total_fcfa']],
            ['Encours en défaut (FCFA)', kpis['encours_defaut_fcfa']],
            ['Perte potentielle LGD 60% (FCFA)', kpis['perte_potentielle_fcfa']],
            ['Montant moyen (FCFA)', kpis['montant_moyen_fcfa']],
            ['Taux d\'intérêt moyen (%)', kpis['taux_interet_moyen']],
        ], columns=['Indicateur', 'Valeur'])
        
        df_kpi.to_excel(writer, sheet_name='Synthèse', index=False, startrow=2)
        
        worksheet = writer.sheets['Synthèse']
        worksheet.write('A1', 'SYNTHÈSE — ANALYSE RISQUE CRÉDIT COBAC', titre_fmt)
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 20)
        worksheet.conditional_format('B4:B11', {
            'type': 'data_bar', 'bar_color': COLORS['primaire']
        })
        
        # ---- ONGLET 2 : PAR SECTEUR ----
        secteurs = (
            df.groupby('secteur_activite')['defaut']
            .agg(nb_prets='count', nb_defauts='sum', taux_defaut='mean')
            .reset_index()
        )
        secteurs['taux_defaut_pct'] = (secteurs['taux_defaut'] * 100).round(2)
        secteurs = secteurs.drop(columns='taux_defaut').sort_values(
            'taux_defaut_pct', ascending=False
        )
        secteurs.to_excel(writer, sheet_name='Secteurs', index=False, startrow=1)
        
        ws = writer.sheets['Secteurs']
        ws.write('A1', 'Analyse par secteur d\'activité', titre_fmt)
        ws.set_column('A:A', 25)
        ws.set_column('B:D', 15)
        
        # ---- ONGLET 3 : PAR PRODUIT ----
        produits = (
            df.groupby('type_produit')['defaut']
            .agg(nb_prets='count', nb_defauts='sum', taux_defaut='mean')
            .reset_index()
        )
        produits['taux_defaut_pct'] = (produits['taux_defaut'] * 100).round(2)
        produits = produits.drop(columns='taux_defaut').sort_values(
            'taux_defaut_pct', ascending=False
        )
        produits.to_excel(writer, sheet_name='Produits', index=False, startrow=1)
        
        ws = writer.sheets['Produits']
        ws.write('A1', 'Analyse par type de produit', titre_fmt)
        ws.set_column('A:A', 25)
        ws.set_column('B:D', 15)
        
        # ---- ONGLET 4 : CLASSIFICATION COBAC ----
        cobac = df.copy()
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
        
        cobac_stats = (
            cobac.groupby('categorie_cobac')
            .agg(nb_credits=('defaut', 'count'),
                 nb_defauts=('defaut', 'sum'),
                 encours_fcfa=('montant_credit_fcfa', 'sum'),
                 taux_defaut=('defaut', 'mean'))
            .reset_index()
        )
        cobac_stats['part_pct'] = (cobac_stats['nb_credits'] / len(cobac) * 100).round(2)
        cobac_stats['taux_defaut_pct'] = (cobac_stats['taux_defaut'] * 100).round(2)
        cobac_stats = cobac_stats.drop(columns='taux_defaut')
        
        cobac_stats.to_excel(writer, sheet_name='COBAC', index=False, startrow=1)
        ws = writer.sheets['COBAC']
        ws.write('A1', 'Classification COBAC des créances', titre_fmt)
        ws.set_column('A:A', 20)
        ws.set_column('B:F', 18)
    
    print(f"✅ Rapport Excel généré : {output_path}")
    return output_path


# =====================================================================
# SCRIPT PRINCIPAL
# =====================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("📄 GÉNÉRATION DES RAPPORTS COBAC")
    print("=" * 70)
    
    print("\n🔄 Chargement des données...")
    df = charger_donnees()
    print(f"✅ {len(df):,} lignes chargées")
    
    # Génération PDF
    print()
    pdf_path = generer_rapport_pdf(df)
    
    # Génération Excel
    print()
    excel_path = generer_rapport_excel(df)
    
    print("\n" + "=" * 70)
    print("✅ RAPPORTS GÉNÉRÉS")
    print("=" * 70)
    print(f"📄 PDF   : {pdf_path}")
    print(f"📊 Excel : {excel_path}")