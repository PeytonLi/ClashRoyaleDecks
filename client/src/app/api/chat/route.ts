import { openai } from '@ai-sdk/openai';
import { convertToModelMessages, streamText, type UIMessage } from 'ai';

import { auth } from '@/auth';

export const maxDuration = 30;

const SYSTEM_PROMPT = [
  'You are CR Deck Lab assistant, a concise Clash Royale deck recommendation helper.',
  'Help users choose a player tag, archetype preference, and optional card preference for the recommendation scan.',
  'If a user says they want a deck with a specific card, tell them to enter that card in the optional card field before running the scan.',
  'Do not claim that you generated deck recommendations yourself. The scan endpoint produces recommendations after the user submits the form.',
  'Keep answers short and practical.',
].join(' ');

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return Response.json({ error: 'Authentication required.' }, { status: 401 });
  }

  if (!process.env.OPENAI_API_KEY) {
    return Response.json(
      { error: 'OPENAI_API_KEY is not configured.' },
      { status: 500 },
    );
  }

  let body: { messages?: UIMessage[]; system?: string };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: 'Invalid request body.' }, { status: 400 });
  }

  const messages = body.messages ?? [];
  const system = [SYSTEM_PROMPT, body.system].filter(Boolean).join('\n\n');
  const model = process.env.OPENAI_CHAT_MODEL || 'gpt-5.4-mini';

  const result = streamText({
    model: openai(model),
    system,
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
