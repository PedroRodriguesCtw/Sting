# STING public microsite

Public-safe landing page for the STING team and its project overview.

This repository intentionally avoids internal department references and keeps only public-facing project context.

## Included
- Team overview
- VideoAR summary
- Shud summary
- Local JSON-powered assistant knowledge base

## Local knowledge
- `docs/knowledge-base.json` contains the source data used by the assistant.
- The backend reads that JSON directly and answers questions without extracting text from SharePoint PDFs.

## Publish with GitHub Pages
1. Push this repository to GitHub.
2. In the repository settings, open Pages.
3. Choose the branch and root folder.
4. Save and wait for the site to publish.

## Run locally with backend
1. Start the local server from `C:\IDC\Sting`:
   `C:\Users\ctw00288\AppData\Local\Programs\Python\Python314\python.exe server.py`
2. Open `http://127.0.0.1:8000`.
3. The assistant will use the local knowledge API exposed by `server.py`.
4. The API answers from `docs/knowledge-base.json` without any SharePoint PDF extraction.
