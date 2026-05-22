# Finance Dashboard

Interactive web app — monthly reviews, category & merchant filters.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Docker
```bash
docker build -t finance-dashboard .
docker run -p 8501:8501 finance-dashboard
```

## Deploy to GitHub
1. Push this repo to GitHub (branch: `main`).
2. GitHub Actions auto-builds and pushes a Docker image to `ghcr.io/<you>/<repo>:latest`.
3. Pull and run that image on any host.
