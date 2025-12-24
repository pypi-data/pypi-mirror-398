def to_html(specs: dict) -> str:
    """Exporte en HTML formaté"""
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Specifications</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .content {
            padding: 40px;
        }
        .section {
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            border-left: 5px solid #667eea;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section h2::before {
            content: '▸';
            font-size: 0.8em;
        }
        .param {
            margin-bottom: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 15px;
            align-items: start;
        }
        .param-label {
            font-weight: bold;
            color: #495057;
            text-transform: capitalize;
        }
        .param-value {
            color: #212529;
        }
        .character {
            margin-bottom: 20px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            border: 2px solid #e9ecef;
        }
        .character h3 {
            color: #764ba2;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .metadata {
            background: #e9ecef;
            padding: 15px 20px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }
        @media (max-width: 768px) {
            .param {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 Video Specifications</h1>
            <p>Complete technical and creative details</p>
        </div>
        <div class="content">
"""

    # Technical
    html += """
        <div class="section">
            <h2>📹 Technical Specifications</h2>
"""
    for key, value in specs["technical"].items():
        html += f"""
            <div class="param">
                <div class="param-label">{key.replace('_', ' ')}</div>
                <div class="param-value">{value}</div>
            </div>
"""
    html += "            </div>\n"

    # Setting & Atmosphere
    html += """
        <div class="section">
            <h2>🌅 Setting & Atmosphere</h2>
"""
    for key, value in specs["setting_atmosphere"].items():
        html += f"""
            <div class="param">
                <div class="param-label">{key.replace('_', ' ')}</div>
                <div class="param-value">{value}</div>
            </div>
"""
    html += "            </div>\n"

    # Camera & Visuals
    html += """
        <div class="section">
            <h2>🎥 Camera & Visuals</h2>
"""
    for key, value in specs["camera_visuals"].items():
        html += f"""
            <div class="param">
                <div class="param-label">{key.replace('_', ' ')}</div>
                <div class="param-value">{value}</div>
            </div>
"""
    html += "            </div>\n"

    # Scene Content
    html += """
        <div class="section">
            <h2>🎬 Scene Content</h2>
"""
    for key, value in specs["scene_content"].items():
        html += f"""
            <div class="param">
                <div class="param-label">{key.replace('_', ' ')}</div>
                <div class="param-value">{value}</div>
            </div>
"""
    html += "            </div>\n"

    # Characters
    if specs["characters"]:
        html += """
        <div class="section">
            <h2>👥 Characters</h2>
"""
        for idx, char in enumerate(specs["characters"], 1):
            html += f"""
            <div class="character">
                <h3>Character #{idx}: {char['name']}</h3>
"""
            for key, value in char.items():
                if key != "name":
                    html += f"""
                <div class="param">
                    <div class="param-label">{key.replace('_', ' ')}</div>
                    <div class="param-value">{value}</div>
                </div>
"""
            html += "                </div>\n"
        html += "            </div>\n"

    # Footer with metadata
    html += f"""
    </div>
    <div class="metadata">
        Created on {specs['metadata']['created_at']} | Tool v{specs['metadata']['tool_version']}
    </div>
</div>
</body>
</html>
"""
    return html