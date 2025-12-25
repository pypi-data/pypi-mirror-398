# Research: LLMs in Terminal User Interfaces

This document surveys the current state of the art for LLM chat interfaces in terminal/TUI applications.

## Existing TUI LLM Applications

### Python/Textual-based

| Project | Framework | Key Features | Stars |
|---------|-----------|--------------|-------|
| [Elia](https://github.com/darrenburns/elia) | Textual | Keyboard-centric, SQLite history, multi-provider, themes | ~2k |
| [PAR LLAMA](https://github.com/paulrobello/parllama) | Textual + Rich | Model management, multi-tab, vision support, code execution | ~800 |
| [GPTUI](https://github.com/happyapplehorse/gptui) | Textual | Multi-AI group chat, AI-initiated care, voice, plugins | ~300 |

### Rust-based

| Project | Framework | Key Features |
|---------|-----------|--------------|
| [Oatmeal](https://github.com/dustinblackman/oatmeal) | Ratatui | Editor integrations (Neovim), slash commands, session persistence |
| [llm-tui](https://github.com/guilhermeprokisch/llm-tui) | Ratatui | Multiple conversations, multi-model support |

### CLI Tools (Non-TUI)

| Project | Description |
|---------|-------------|
| [llm](https://github.com/simonw/llm) | Swiss-army knife CLI for LLMs, SQLite logging, plugin system |
| [Aider](https://github.com/Aider-AI/aider) | AI pair programming, repo mapping, auto-commits |
| [Claude Code](https://github.com/anthropics/claude-code) | TypeScript/Ink, MCP support, hooks, minimal UI philosophy |

---

## Architecture Patterns

### 1. Claude Code's Minimal Approach

From [How Claude Code is Built](https://newsletter.pragmaticengineer.com/p/how-claude-code-is-built):

> "The team tries to make the UI as minimal as possible. Every time there's a new model release, they delete code."

**Key decisions:**
- TypeScript + React + Ink (terminal React renderer)
- No virtualization/sandboxing - runs locally
- 90% of code written by the model itself
- Modular tool system with permission controls
- Session history in `~/.claude/projects/`

### 2. Elia's SQLite-First Design

- All conversations persisted to local SQLite
- Supports conversation search and resume
- Multiple themes (nebula, cobalt, twilight, hacker, etc.)
- Environment-based provider configuration

### 3. PAR LLAMA's Feature-Rich Approach

- Multi-tab conversations with full history
- Custom prompt library + Fabric pattern import
- Code execution sandbox (Python, Node, Bash)
- Remote Ollama support (doesn't require local install)
- Vision model support for image-based chat

### 4. GPTUI's Plugin Architecture

- Decoupled TUI from underlying kernel
- Semantic Kernel for plugin management
- Jobs + Handlers pattern for extensibility
- AI-Care: proactive AI messaging

---

## Key UX Patterns

### Streaming Markdown Rendering

From [Textual's approach](https://willmcgugan.github.io/streaming-markdown/):

**The Challenge:**
> "Markdown rendering jank—syntax fragments being rendered as raw text until they form a complete Markdown element."

**Solutions:**

1. **Token Buffering** - Buffer between LLM producer and Markdown widget consumer
2. **Finite State Machine** - Stateful stream processor for ambiguous sequences
3. **Incremental Parsing** - No full re-parse on changes, append new nodes separately

**Textual Implementation:**
```python
@work(thread=True)
def send_prompt(self, prompt: str) -> None:
    response = self.chat.send(prompt, stream=True)
    for chunk in response:
        self.markdown.update(chunk)  # Streaming update
```

### Chat Input Placeholder Text

Common placeholder text patterns in AI chat interfaces:

| Application/Pattern | Placeholder Text |
|---------------------|------------------|
| ChatGPT | "Message ChatGPT" |
| Claude | "How can Claude help you today?" |
| Gemini | "Ask Gemini" |
| GitHub Copilot | "Ask Copilot" |
| Vercel AI SDK | "Say something..." |
| Gradio ChatInterface | "Type a message..." |
| Generic AI | "Ask anything..." |
| Generic chat | "Type a message..." |
| Generic search | "Search..." |

**Best Practices from UX Research:**

1. **Be action-oriented** - Use verbs like "Ask", "Type", "Message" rather than passive labels
2. **Keep it short** - 2-4 words is ideal ([TinyMCE best practices](https://www.tiny.cloud/blog/textarea-placeholder-usage-examples-and-best-practices/))
3. **Avoid generic text** - "Enter text here" is too vague ([NNGroup](https://www.nngroup.com/articles/form-design-placeholders/))
4. **Consider context** - Contextual examples can help (e.g., "e.g. How do I install Office")
5. **Don't rely on placeholder alone** - Placeholders disappear on focus, so critical info should be elsewhere

**Common patterns:**
- `Message [Name]...` - Personalized, used by ChatGPT
- `Ask [Name]...` - Action-oriented, used by Copilot/Gemini
- `Type a message...` - Generic but clear
- `How can I help?` - Conversational
- `Say something...` - Casual, used by AI SDK

**Our choice:** `Message...` - Short, action-oriented, and model-agnostic.

### Keyboard-Centric Navigation

Common patterns from [vim-keybindings-everywhere](https://github.com/erikw/vim-keybindings-everywhere-the-ultimate-list):

| Action | Common Binding |
|--------|----------------|
| New chat | `Ctrl+N` |
| Clear | `Ctrl+L` |
| History up/down | `Ctrl+P` / `Ctrl+N` or `j/k` |
| Submit | `Enter` |
| Multi-line input | `Shift+Enter` or `!multi` command |
| Cancel generation | `Ctrl+C` or `Escape` |
| Copy response | `/copy` or `Ctrl+Y` |
| Toggle sidebar | `Ctrl+B` |

### Conversation Persistence

From [LLM's logging](https://llm.datasette.io/en/stable/logging.html):

**SQLite Schema Pattern:**
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    name TEXT,
    model TEXT,
    created_at TEXT
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,  -- 'user', 'assistant', 'system'
    content TEXT,
    timestamp TEXT,
    tokens INTEGER,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

**History Management Strategies:**
1. Send last N messages only
2. Limit by token count
3. Summarize older messages
4. Sliding window with system prompt anchoring

---

## MCP Integration

### Current State

From [MCP documentation](https://modelcontextprotocol.io/clients):

**CLI Tools:**
- [mcptools](https://github.com/f/mcptools) - Universal MCP CLI (stdio + HTTP)
- [mcp-cli](https://github.com/chrishayuk/mcp-cli) - Chat mode, interactive mode, streaming

**Integration patterns:**
```python
# Tool discovery -> OpenAI format conversion
tools = mcp_client.list_tools()
openai_tools = [tool.to_openai_format() for tool in tools]
llm.set_tools(openai_tools)

# Tool execution loop
response = llm.complete(messages)
if response.tool_calls:
    for call in response.tool_calls:
        result = mcp_client.call_tool(call.name, call.args)
        messages.append({"role": "tool", "content": result})
    response = llm.complete(messages)  # Continue with results
```

**Supported transports:**
- Stdio (most common for local tools)
- HTTP/SSE (for remote servers)

---

## Provider Abstraction

### LiteLLM Pattern

Universal interface across providers:
```python
from litellm import completion

# Same API for all providers
completion(model="gpt-4o-mini", messages=[...])
completion(model="claude-3-sonnet", messages=[...])
completion(model="ollama/llama3", messages=[...])
```

### Provider-Specific Features

| Provider | Special Features |
|----------|-----------------|
| OpenAI | Function calling, JSON mode, vision |
| Anthropic | Extended thinking, computer use, caching |
| Ollama | Local models, custom modelfiles |
| Google | Grounding, code execution |

---

## Design Recommendations for textual-chat

### Must-Have Features

1. **Streaming responses** with proper Markdown buffering
2. **Message persistence** (SQLite recommended)
3. **Multi-provider support** via LiteLLM
4. **MCP tool integration** for extensibility
5. **Keyboard shortcuts** (Ctrl+L clear, Ctrl+C cancel, etc.)

### Should-Have Features

1. **Conversation history** sidebar/picker
2. **System prompt** configuration
3. **Theme support** (inherit from Textual)
4. **Token counting** display
5. **Copy/export** functionality

### Nice-to-Have Features

1. **Vision support** (image input)
2. **Voice input** integration
3. **Multi-tab** conversations
4. **Slash commands** (/clear, /model, /system)
5. **Code block** actions (copy, run)

### Anti-Patterns to Avoid

1. **Full re-render** on each streaming chunk
2. **Blocking UI** during API calls
3. **No cancellation** support for long generations
4. **Hardcoded providers** - always abstract
5. **No persistence** - users expect history

---

## Sources

- [Elia GitHub](https://github.com/darrenburns/elia)
- [PAR LLAMA GitHub](https://github.com/paulrobello/parllama)
- [GPTUI GitHub](https://github.com/happyapplehorse/gptui)
- [Oatmeal GitHub](https://github.com/dustinblackman/oatmeal)
- [llm by Simon Willison](https://github.com/simonw/llm)
- [Aider](https://github.com/Aider-AI/aider)
- [How Claude Code is Built](https://newsletter.pragmaticengineer.com/p/how-claude-code-is-built)
- [Textual Streaming Markdown](https://willmcgugan.github.io/streaming-markdown/)
- [Textual Blog - Anatomy of a TUI](https://textual.textualize.io/blog/2024/09/15/anatomy-of-a-textual-user-interface/)
- [MCP Tools CLI](https://github.com/f/mcptools)
- [LLM SQLite Logging](https://llm.datasette.io/en/stable/logging.html)
- [Chrome LLM Rendering Best Practices](https://developer.chrome.com/docs/ai/render-llm-responses)
