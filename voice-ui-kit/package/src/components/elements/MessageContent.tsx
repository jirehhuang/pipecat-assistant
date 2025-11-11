import { cn } from "@/lib/utils";
import {
  ConversationMessage,
  ConversationMessagePart,
} from "@/types/conversation";
import { Fragment } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Thinking from "./Thinking";

interface Props {
  /**
   * Custom CSS classes for the component
   */
  classNames?: {
    /**
     * Custom CSS classes for the message content
     */
    messageContent?: string;
    /**
     * Custom CSS classes for the thinking
     */
    thinking?: string;
    /**
     * Custom CSS classes for the time
     */
    time?: string;
  };
  /**
   * The message to display
   */
  message: ConversationMessage;
  /**
   * Enable markdown rendering in message content.
   * @default false
   */
  enableMarkdown?: boolean;
}

export const MessageContent = ({ classNames = {}, message, enableMarkdown = false }: Props) => {
  const parts = Array.isArray(message.parts) ? message.parts : [];
  return (
    <div className={cn("flex flex-col gap-2", classNames.messageContent)}>
      {parts.map((part: ConversationMessagePart, idx: number) => {
        const nextPart = parts?.[idx + 1] ?? null;
        const isText = typeof part.text === "string";
        const nextIsText = nextPart && typeof nextPart.text === "string";
        return (
          <Fragment key={idx}>
            {isText ? (
              enableMarkdown ? (
                <div className="markdown-content">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // Prevent paragraph wrapping for single-line content and add spacing
                      p: ({ children, ...props }) => <div {...props} className="mb-2 last:mb-0">{children}</div>,
                      // Style headings
                      h1: ({ children, ...props }) => <h1 {...props} className="text-xl font-bold mb-2">{children}</h1>,
                      h2: ({ children, ...props }) => <h2 {...props} className="text-lg font-semibold mb-2">{children}</h2>,
                      h3: ({ children, ...props }) => <h3 {...props} className="text-base font-medium mb-1">{children}</h3>,
                      // Style code blocks
                      pre: ({ children, ...props }) => (
                        <pre {...props} className="bg-muted p-3 rounded text-sm overflow-x-auto mb-2 last:mb-0">
                          {children}
                        </pre>
                      ),
                      // Style inline code
                      code: ({ children, ...props }) => (
                        <code {...props} className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">
                          {children}
                        </code>
                      ),
                      // Style lists
                      ul: ({ children, ...props }) => <ul {...props} className="list-disc list-inside mb-2 last:mb-0 space-y-1">{children}</ul>,
                      ol: ({ children, ...props }) => <ol {...props} className="list-decimal list-inside mb-2 last:mb-0 space-y-1">{children}</ol>,
                      li: ({ children, ...props }) => <li {...props} className="ml-2">{children}</li>,
                      // Style links
                      a: ({ children, ...props }) => <a {...props} className="text-primary underline hover:no-underline">{children}</a>,
                      // Style blockquotes
                      blockquote: ({ children, ...props }) => (
                        <blockquote {...props} className="border-l-4 border-muted pl-4 italic mb-2 last:mb-0">
                          {children}
                        </blockquote>
                      ),
                      // Style tables
                      table: ({ children, ...props }) => (
                        <div className="overflow-x-auto mb-2 last:mb-0">
                          <table {...props} className="min-w-full border-collapse border border-muted">
                            {children}
                          </table>
                        </div>
                      ),
                      th: ({ children, ...props }) => (
                        <th {...props} className="border border-muted bg-muted/50 px-3 py-2 text-left font-semibold">
                          {children}
                        </th>
                      ),
                      td: ({ children, ...props }) => (
                        <td {...props} className="border border-muted px-3 py-2">
                          {children}
                        </td>
                      ),
                    }}
                  >
                    {typeof part.text === "string" ? part.text : String(part.text)}
                  </ReactMarkdown>
                </div>
              ) : (
                part.text
              )
            ) : (
              part.text
            )}
            {isText && nextIsText ? " " : null}
          </Fragment>
        );
      })}
      {parts.length === 0 ||
      parts.every(
        (part) => typeof part.text === "string" && part.text.trim() === "",
      ) ? (
        <Thinking className={classNames.thinking} />
      ) : null}
      <div
        className={cn("self-end text-xs text-gray-500 mb-1", classNames.time)}
      >
        {new Date(message.createdAt).toLocaleTimeString()}
      </div>
    </div>
  );
};
