# 🚀 Streamlit Cloud -deployment ohjeet

## Vaihe 1: GitHub-repositorio

1. **Luo uusi repositorio GitHubissa:**
   - Mene [github.com/new](https://github.com/new)
   - Anna nimi esim. `MJ_stats` tai `mailajoket-tilastoselain`
   - Valitse **Public** tai **Private** (suositus: Private jos data on arkaluontoista)
   - **Älä** valitse "Add a README file", "Add .gitignore" tai "Choose a license" (ne on jo projektissa)
   - Klikkaa "Create repository"

2. **Kopioi repositorion URL** (esim. `https://github.com/kayttajanimi/MJ_stats.git`)

## Vaihe 2: Yhdistä paikallinen repositorio GitHubiin

### Komentorivillä:

```bash
cd /Users/juhorissanen/Desktop/MJ_stats

# Lisää GitHub-repositorio remoteksi
git remote add origin <GITHUB_REPO_URL>

# Tarkista että remote on lisätty
git remote -v

# Pushaa koodi GitHubiin
git push -u origin main
```

### Työpöytäsovelluksella:

1. Avaa GitHub Desktop (tai muu git-sovellus)
2. Valitse "Add" → "Add Existing Repository"
3. Valitse kansio: `/Users/juhorissanen/Desktop/MJ_stats`
4. Klikkaa "Publish repository" tai "Push origin"
5. Valitse GitHub-repositorio ja klikkaa "Push"

## Vaihe 3: Streamlit Cloud -deployment

1. **Mene Streamlit Cloudiin:**
   - [share.streamlit.io](https://share.streamlit.io)
   - Kirjaudu sisään GitHub-tililläsi

2. **Luo uusi sovellus:**
   - Klikkaa "New app"
   - Valitse:
     - **Repository:** Valitse juuri luomasi repositorio
     - **Branch:** `main` (tai `master`)
     - **Main file path:** `app.py`
     - **Python version:** `3.11`
   - Klikkaa "Deploy!"

3. **Odota deploymentin valmistumista:**
   - Streamlit Cloud asentaa automaattisesti `requirements.txt`:n riippuvuudet
   - Jos deployment epäonnistuu, tarkista:
     - Onko `requirements.txt` oikein?
     - Onko `app.py` olemassa?
     - Onko Excel-tiedosto repositoriossa?

4. **Sovellus on valmis!**
   - Saat URL:n muodossa: `https://mj-stats-xxxxx.streamlit.app`
   - Voit jakaa tämän URL:n muille käyttäjille

## Tärkeät tiedostot

- ✅ `app.py` - Pääsovellus
- ✅ `requirements.txt` - Python-riippuvuudet
- ✅ `mailajoket_2014_2026_dataworkbook.xlsx` - Data-tiedosto
- ✅ `.streamlit/config.toml` - Streamlit-asetukset
- ✅ `.gitignore` - Git-ignorointi

## Ongelmatilanteet

### Deployment epäonnistuu
- Tarkista että kaikki tiedostot on pushattu GitHubiin
- Tarkista `requirements.txt` -vaihtoehdot
- Tarkista Streamlit Cloud -logit virheilmoituksista

### Excel-tiedosto ei löydy
- Varmista että `mailajoket_2014_2026_dataworkbook.xlsx` on repositoriossa
- Tarkista että se ei ole `.gitignore`:ssa

### Sovellus on hidas
- Streamlit Cloud käyttää ilmaista tieriä, joka voi olla hitaampi
- Tarkista että `st.cache_data` on käytössä datan latauksessa

## Päivitykset

Kun teet muutoksia:

```bash
git add .
git commit -m "Kuvaus muutoksista"
git push origin main
```

Streamlit Cloud päivittyy automaattisesti!

