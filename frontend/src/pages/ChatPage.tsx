import { useParams } from "react-router-dom";
import { useRef, useState, useEffect } from "react";
import { Bot, RotateCcw, Send, User } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/common/EmptyState";
import { MarkdownMessage } from "@/components/chat/MarkdownMessage";
import { useDatasetInsights } from "@/hooks/useDataset";
import { cn } from "@/lib/utils";
import { ApiError } from "@/services/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  isError?: boolean;
}

export default function ChatPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const insights = useDatasetInsights(datasetId);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (regenerateOf?: string) => {
    const question = regenerateOf ?? input.trim();
    if (!question || insights.isPending) return;

    if (!regenerateOf) {
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", content: question }]);
      setInput("");
    }

    try {
      const result = await insights.mutateAsync({ question });
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "assistant", content: result.insights }]);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong generating insights.";
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "assistant", content: message, isError: true }]);
    }
  };

  const lastUserMessage = [...messages].reverse().find((m) => m.role === "user")?.content;

  return (
    <div className="mx-auto flex h-[calc(100vh-8.5rem)] max-w-3xl flex-col">
      <PageHeader title="AI Chat" description="Ask questions about this dataset in plain English." />

      <div className="flex-1 overflow-y-auto rounded-xl border border-border bg-card/40 p-4">
        {messages.length === 0 ? (
          <EmptyState
            icon={Bot}
            title="Ask anything about your data"
            description='Try "What are the key trends in this dataset?" or "Summarize the missing values."'
          />
        ) : (
          <div className="space-y-5">
            {messages.map((m) => (
              <div key={m.id} className={cn("flex gap-3", m.role === "user" && "flex-row-reverse")}>
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                    m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                  )}
                >
                  {m.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                <div
                  className={cn(
                    "max-w-[85%] rounded-xl px-4 py-2.5 text-sm",
                    m.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : m.isError
                      ? "border border-destructive/30 bg-destructive/5 text-destructive"
                      : "bg-muted"
                  )}
                >
                  {m.role === "assistant" ? <MarkdownMessage content={m.content} /> : m.content}
                </div>
              </div>
            ))}
            {insights.isPending && (
              <div className="flex items-center gap-2 pl-11 text-sm text-muted-foreground">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground" />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:0.15s]" />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:0.3s]" />
              </div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center gap-2">
        {lastUserMessage && (
          <Button variant="outline" size="icon" onClick={() => handleSend(lastUserMessage)} aria-label="Regenerate response" disabled={insights.isPending}>
            <RotateCcw className="h-4 w-4" />
          </Button>
        )}
        <Input
          placeholder="Ask a question about this dataset…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={insights.isPending}
        />
        <Button onClick={() => handleSend()} disabled={insights.isPending || !input.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Each question calls the backend's insights endpoint independently — conversation memory isn't supported server-side yet.
      </p>
    </div>
  );
}
