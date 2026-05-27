# Jarvis Frontend

Vite + React + TypeScript + Tailwind dashboard.

## Local development

```bash
cd frontend
npm install
cp ../.env.example ../.env       # only used by the backend, but VITE_API_BASE_URL is read from here too
npm run dev
```

Open <http://localhost:5173>. The dev server proxies `/api/*` to the backend at `http://localhost:8000` (override with `VITE_API_BASE_URL`).

## Scripts

- `npm run dev` — Vite dev server with hot module replacement
- `npm run build` — production build to `dist/`
- `npm run preview` — serve the production build locally
- `npm run lint` — ESLint
- `npm run typecheck` — TypeScript project references build

## Layout

```
src/
├── components/   # MicButton, ConversationView, StatusPanel, TaskList, etc.
├── hooks/        # useChat (WebSocket), useRecorder (MediaRecorder), useStatus, useTasks
├── lib/          # api client + shared types
├── styles/       # Tailwind + global CSS
├── App.tsx
└── main.tsx
```

## Browser support

Voice input relies on the MediaRecorder API (Chromium, Firefox, recent Safari). The backend's Whisper endpoint accepts WebM/Opus, MP4, OGG, WAV.
