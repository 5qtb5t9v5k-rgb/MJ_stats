# 🚀 GitHub Push -ohjeet

## Nopea tapa (skripti)

Aja komento:
```bash
./push_to_github.sh
```

Skripti kysyy GitHub-repositorion URL:n ja tekee loput automaattisesti.

## Manuaalinen tapa

### 1. Luo GitHub-repositorio (jos ei ole vielä)
- Mene: https://github.com/new
- Anna nimi (esim. `MJ_stats`)
- **Älä** valitse README/.gitignore/license
- Klikkaa "Create repository"
- Kopioi URL (esim. `https://github.com/kayttajanimi/MJ_stats.git`)

### 2. Lisää remote ja pushaa

```bash
# Lisää GitHub-repositorio remoteksi
git remote add origin <GITHUB_REPO_URL>

# Tarkista että remote on lisätty
git remote -v

# Pushaa koodi GitHubiin
git push -u origin main
```

### 3. Jos remote on jo olemassa ja haluat vaihtaa sen

```bash
# Poista vanha remote
git remote remove origin

# Lisää uusi remote
git remote add origin <UUSI_GITHUB_REPO_URL>

# Pushaa
git push -u origin main
```

## Tarkista onnistuminen

Kun push onnistuu, näet:
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
...
To https://github.com/kayttajanimi/MJ_stats.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

## Seuraava askel

Kun koodi on GitHubissa:
1. Mene https://share.streamlit.io
2. Kirjaudu GitHub-tililläsi
3. Valitse "New app"
4. Valitse repositorio ja branch `main`
5. Main file: `app.py`
6. Python version: `3.11`
7. Klikkaa "Deploy!"

