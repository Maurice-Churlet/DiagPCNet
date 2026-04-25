texts = ["🌐 Réseau", "💾 Stockage", "🔌 Périphériques", "🐙 Projets Git", "🧹 Maintenance", "⚙️ Gestion", "🔐 Coffre", "📜 Scripts"]
for t in texts:
    try:
        clean = t.split(" ", 1)[-1].strip()
        print(f"CLEAN: {clean}")
    except:
        pass
