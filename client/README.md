# Client App (Next.js)

Frontend for the Clash Royale Deck Recommender.

## Local Development

```bash
npm install
npm run dev
```

The app runs on `http://localhost:3000` and communicates with backend proxy routes under `src/app/api`.

## Useful Scripts

```bash
npm run dev      # start dev server
npm run build    # production build
npm run start    # run production build
npm run lint     # lint checks
```

## Key Paths

- `src/app/recommend/page.tsx`: recommendation input form
- `src/app/results/page.tsx`: recommendation results UI
- `src/app/api/player/[tag]/route.ts`: player proxy API route
- `src/app/api/recommend/route.ts`: recommendation proxy API route

## Notes

- Keep frontend requests routed through Next.js API handlers instead of calling backend directly from browser code.
- Tailwind class order and design tokens are lint-enforced.
