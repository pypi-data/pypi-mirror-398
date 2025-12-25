from IPython.display import display, HTML

def exploration_dataframe(df, titre="Analyse DataFrame"):
    """
    Analyse rapide et claire d'un DataFrame avec focus sur le contenu des colonnes
    """

    # CSS moderne et épuré
    css = """
    <style>
    .df-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #fafafa;
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        border: 1px solid #e1e5e9;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .df-title {
        font-size: 24px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 20px;
        text-align: center;
    }

    .df-summary {
        display: flex;
        justify-content: space-around;
        background: white;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 24px;
        border: 1px solid #e8eaed;
    }

    .summary-item {
        text-align: center;
    }

    .summary-value {
        font-size: 20px;
        font-weight: 600;
        color: #1976d2;
        display: block;
    }

    .summary-label {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .columns-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
    }

    .column-card {
        background: white;
        border-radius: 8px;
        padding: 20px;
        border: 1px solid #e8eaed;
        transition: all 0.2s ease;
    }

    .column-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }

    .column-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .column-name {
        font-size: 16px;
        font-weight: 600;
        color: #1a1a1a;
    }

    .type-badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .type-numeric { background: #e8f5e8; color: #2e7d32; }
    .type-text { background: #fff3e0; color: #f57c00; }
    .type-datetime { background: #e3f2fd; color: #1565c0; }

    .column-stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 16px;
    }

    .stat-item {
        text-align: center;
        padding: 8px;
        background: #f8f9fa;
        border-radius: 6px;
    }

    .stat-value {
        font-size: 16px;
        font-weight: 600;
        color: #1a1a1a;
        display: block;
    }

    .stat-label {
        font-size: 11px;
        color: #666;
        text-transform: uppercase;
    }

    .examples-section {
        border-top: 1px solid #f0f0f0;
        padding-top: 16px;
    }

    .examples-title {
        font-size: 12px;
        font-weight: 600;
        color: #666;
        margin-bottom: 8px;
        text-transform: uppercase;
    }

    .examples-list {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .example-tag {
        background: #f1f3f4;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 13px;
        color: #444;
        border: 1px solid #e0e0e0;
    }

    .missing-warning {
        background: #fef7f0;
        border: 1px solid #fdd835;
        color: #e65100;
        padding: 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-bottom: 12px;
    }
    </style>
    """

    # Informations générales
    nb_lignes, nb_colonnes = df.shape

    # Types de données
    types_map = {
        'number': ('Numérique', 'type-numeric'),
        'object': ('Texte', 'type-text'),
        'datetime': ('Date', 'type-datetime')
    }

    # Construction du HTML
    html = f"""
    {css}
    <div class="df-container">
        <div class="df-title">{titre}</div>

        <div class="df-summary">
            <div class="summary-item">
                <span class="summary-value">{nb_lignes:,}</span>
                <span class="summary-label">Lignes</span>
            </div>
            <div class="summary-item">
                <span class="summary-value">{nb_colonnes}</span>
                <span class="summary-label">Colonnes</span>
            </div>
            <div class="summary-item">
                <span class="summary-value">{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB</span>
                <span class="summary-label">Mémoire</span>
            </div>
        </div>

        <div class="columns-grid">
    """

    # Analyse de chaque colonne
    for col in df.columns:
        # Déterminer le type
        if pd.api.types.is_numeric_dtype(df[col]):
            type_name, type_class = 'Numérique', 'type-numeric'
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            type_name, type_class = 'Date', 'type-datetime'
        else:
            type_name, type_class = 'Texte', 'type-text'

        # Statistiques de base
        nb_manquantes = df[col].isna().sum()
        nb_distinctes = df[col].nunique()
        pct_manquantes = (nb_manquantes / len(df)) * 100

        # Début de la carte
        html += f"""
        <div class="column-card">
            <div class="column-header">
                <span class="column-name">{col}</span>
                <span class="type-badge {type_class}">{type_name}</span>
            </div>
        """

        # Alerte valeurs manquantes
        if nb_manquantes > 0:
            html += f"""
            <div class="missing-warning">
                ⚠️ {nb_manquantes:,} valeurs manquantes ({pct_manquantes:.1f}%)
            </div>
            """

        # Statistiques
        html += f"""
        <div class="column-stats">
            <div class="stat-item">
                <span class="stat-value">{nb_distinctes:,}</span>
                <span class="stat-label">Distinctes</span>
            </div>
        """

        # Statistiques numériques
        if pd.api.types.is_numeric_dtype(df[col]) and not df[col].isna().all():
            html += f"""
            <div class="stat-item">
                <span class="stat-value">{df[col].mean():.2f}</span>
                <span class="stat-label">Moyenne</span>
            </div>
            """
        else:
            html += f"""
            <div class="stat-item">
                <span class="stat-value">{len(df[col].dropna())}</span>
                <span class="stat-label">Remplies</span>
            </div>
            """

        html += "</div>"

        # Exemples de valeurs
        if nb_distinctes > 0:
            # Prendre un échantillon représentatif
            valeurs_sample = df[col].dropna().unique()
            if len(valeurs_sample) > 8:
                valeurs_sample = valeurs_sample[:8]

            html += f"""
            <div class="examples-section">
                <div class="examples-title">Exemples de valeurs</div>
                <div class="examples-list">
            """

            for val in valeurs_sample:
                val_str = str(val)
                if len(val_str) > 25:
                    val_str = val_str[:25] + "..."
                html += f'<span class="example-tag">{val_str}</span>'

            if len(df[col].dropna().unique()) > 8:
                html += f'<span class="example-tag">+{len(df[col].dropna().unique()) - 8} autres...</span>'

            html += "</div></div>"

        html += "</div>"

    html += """
        </div>
    </div>
    """

    display(HTML(html))

# Fonction d'usage rapide
def explorer(df, titre="Analyse DataFrame"):
    """Version ultra-simple"""
    exploration_dataframe(df, titre)