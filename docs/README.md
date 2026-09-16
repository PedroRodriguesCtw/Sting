# STING public microsite

Public-safe landing page for the STING team and its project overview.

This repository intentionally avoids internal department references and keeps only public-facing project context.

## Included
- Team overview
- VideoAR summary
- Shud summary
- Internal resource links hosted on SharePoint

## Internal references
- VideoAR reference: https://criticaltechworks-my.sharepoint.com/:b:/r/personal/ctw00288_criticaltechworks_com/Documents/Sting/Team%26Project%20presentation/VAR@DE-310.pdf?d=w43c4cd72ba67408f99a8056a5be3d48d&csf=1&web=1&e=lv1LBd
- Shud onboarding: https://criticaltechworks-my.sharepoint.com/:b:/r/personal/ctw00288_criticaltechworks_com/Documents/Sting/Team%26Project%20presentation/2026-05-21_SlopeHUD_OnboardingCTW.pdf?d=wca2cb38ff8e8463c9d5ec1a4bf880b9b&csf=1&web=1&e=xu9f0r

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
4. On startup, the backend tries to parse the SharePoint PDFs when they are already accessible in your session; if not, it silently falls back to the normal local knowledge base.
