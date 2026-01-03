#!/bin/bash
# Skripti GitHub-repositorion pushaamiseen

echo "=========================================="
echo "GitHub Push -skripti"
echo "=========================================="
echo ""
echo "Tämä skripti lisää GitHub-remoten ja pushaa koodin."
echo ""
read -p "Anna GitHub-repositorion URL (esim. https://github.com/kayttajanimi/MJ_stats.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "Virhe: URL ei voi olla tyhjä!"
    exit 1
fi

echo ""
echo "Lisätään remote: $REPO_URL"
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

echo ""
echo "Tarkistetaan remote:"
git remote -v

echo ""
echo "Pushataan koodi GitHubiin..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Onnistui! Koodi on nyt GitHubissa."
    echo ""
    echo "Seuraava askel: Mene https://share.streamlit.io ja deployaa sovellus!"
else
    echo ""
    echo "❌ Push epäonnistui. Tarkista:"
    echo "   - Onko GitHub-repositorio luotu?"
    echo "   - Onko URL oikein?"
    echo "   - Onko sinulla oikeudet repositorioon?"
fi

