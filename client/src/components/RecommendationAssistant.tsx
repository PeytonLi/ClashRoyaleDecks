'use client';

import { useMemo } from 'react';
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAssistantInstructions,
} from '@assistant-ui/react';
import { AssistantChatTransport, useChatRuntime } from '@assistant-ui/react-ai-sdk';
import { Bot, Send, Sparkles, UserRound } from 'lucide-react';

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-start">
      <div className="max-w-[88%] rounded-[8px] border border-border-subtle bg-surface-card px-3 py-2 text-sm leading-6 text-text-secondary">
        <div className="mb-1 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-brand-cyan">
          <Bot className="h-3.5 w-3.5" />
          Assistant
        </div>
        <MessagePrimitive.Content />
      </div>
    </MessagePrimitive.Root>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end">
      <div className="max-w-[88%] rounded-[8px] bg-brand-gold px-3 py-2 text-sm font-semibold leading-6 text-brand-ink">
        <div className="mb-1 flex items-center justify-end gap-1.5 text-xs font-bold uppercase tracking-wide text-brand-ink/70">
          You
          <UserRound className="h-3.5 w-3.5" />
        </div>
        <MessagePrimitive.Content />
      </div>
    </MessagePrimitive.Root>
  );
}

function RecommendationThread() {
  useAssistantInstructions(
    'Help users prepare a Clash Royale recommendation scan. If they want a deck with a specific card, direct them to the optional card field before scanning.',
  );

  return (
    <ThreadPrimitive.Root className="flex h-[28rem] flex-col overflow-hidden rounded-[8px] border border-border-subtle bg-surface-card/45">
      <ThreadPrimitive.Viewport className="flex min-h-0 grow flex-col gap-3 overflow-y-auto p-3">
        <ThreadPrimitive.Empty>
          <div className="grid grow place-items-center px-4 text-center">
            <div>
              <div className="mx-auto mb-3 grid h-10 w-10 place-items-center rounded-[8px] bg-gradient-card">
                <Sparkles className="h-5 w-5 text-brand-gold" />
              </div>
              <p className="font-display text-lg font-bold text-text-primary">Deck assistant</p>
              <p className="mt-2 text-sm leading-6 text-text-muted">
                Ask about archetypes, card picks, or what to enter before the scan.
              </p>
            </div>
          </div>
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages>
          {({ message }) => (
            message.role === 'user' ? <UserMessage /> : <AssistantMessage />
          )}
        </ThreadPrimitive.Messages>

        <ThreadPrimitive.ViewportFooter className="sticky bottom-0 mt-auto bg-surface-primary/80 pt-2 backdrop-blur">
          <ComposerPrimitive.Root className="flex min-h-12 items-end gap-2 rounded-[8px] border border-border-subtle bg-surface-card px-3 py-2 focus-within:border-brand-gold/70">
            <ComposerPrimitive.Input
              className="max-h-28 min-h-8 grow resize-none bg-transparent text-sm leading-6 text-text-primary outline-none placeholder:text-text-muted"
              placeholder="Ask about a deck idea"
            />
            <ComposerPrimitive.Send
              className="grid h-9 w-9 shrink-0 place-items-center rounded-[8px] bg-brand-gold text-brand-ink transition-opacity disabled:cursor-not-allowed disabled:opacity-45"
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </ComposerPrimitive.Send>
          </ComposerPrimitive.Root>
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
}

export default function RecommendationAssistant() {
  const transport = useMemo(() => new AssistantChatTransport({ api: '/api/chat' }), []);
  const runtime = useChatRuntime({ transport });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <RecommendationThread />
    </AssistantRuntimeProvider>
  );
}
