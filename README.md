# Frontend (React + Vite + Tailwind)

This folder contains a minimal React frontend that uses Tailwind CSS and Vite.
It expects your Flask backend to run locally at http://127.0.0.1:5000 (the dev server proxies `/search` and `/song` to that address).

Quick start (beginner-friendly):

1. Open a terminal in this folder:
   cd frontend

2. Install dependencies:
   npm install

3. Start the dev server:
   npm run dev

4. Confirm your Flask backend is running (`python app.py` in the root project).

5. Open the URL shown by Vite (usually http://localhost:5173) and try searches.

Notes:
- The dev server proxies `/search` and `/song` to the Flask backend so the UI code does not need any changes.
- If you need HTTPS or other proxy rules, edit `vite.config.js`.
