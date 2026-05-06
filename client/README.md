# Client App (Next.js)

Frontend for the Clash Royale Deck Recommender.

## Local Development

```bash
pnpm install
pnpm dev
```

The app runs on `http://localhost:3000` and communicates with backend proxy routes under `src/app/api`.

## Useful Scripts

```bash
pnpm dev      # start dev server
pnpm build    # production build
pnpm start    # run production build
pnpm lint     # lint checks
```

## Key Paths

- `src/app/recommend/page.tsx`: recommendation input form
- `src/app/results/page.tsx`: recommendation results UI
- `src/app/api/player/[tag]/route.ts`: player proxy API route
- `src/app/api/recommend/route.ts`: recommendation proxy API route
- `src/app/api/chat/route.ts`: OpenAI-backed assistant-ui chat route
- `src/components/RecommendationAssistant.tsx`: recommendation-page chatbot

## Notes

- Keep frontend requests routed through Next.js API handlers instead of calling backend directly from browser code.
- Set `OPENAI_API_KEY` for the recommendation-page chatbot. Override `OPENAI_CHAT_MODEL` if needed.
- Tailwind class order and design tokens are lint-enforced.
