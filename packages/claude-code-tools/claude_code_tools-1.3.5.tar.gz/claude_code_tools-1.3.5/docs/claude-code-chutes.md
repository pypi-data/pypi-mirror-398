Here’s what I found (forums + docs) and the cleanest ways to run **Claude Code** against **Chutes (OpenAI-compatible) instead of Anthropic models**—including whether you need an extra router.

---

## TL;DR

* **You can’t point Claude Code directly at Chutes** because Claude Code speaks the **Anthropic `/v1/messages`** format, while Chutes exposes an **OpenAI-compatible `/v1/chat/completions`** API. You need a **translator/gateway** in the middle. ([Anthropic][1])
* Two working choices seen in the community and in Anthropic’s docs:

  1. **Claude Code Router (CCR)** — purpose-built local proxy that converts Claude Code → OpenAI format; works with OpenRouter, DeepSeek, Groq, etc., and also with custom OpenAI-compatible bases like **Chutes**. ([GitHub][2], [npm][3])
  2. **LiteLLM “Anthropic unified endpoint”** — run LiteLLM as a gateway that **exposes an Anthropic-style endpoint** to Claude Code, while LiteLLM calls Chutes behind the scenes using its **OpenAI-compatible** route. ([Anthropic][1], [LiteLLM][4], [LiteLLM][5])

Reddit users repeatedly report running **Claude Code + Chutes** successfully (often with GLM-4.5, DeepSeek, or Kimi K2) by using a router/gateway. ([Reddit][6], [Reddit][7], [Reddit][8])

---

## Option A — Claude Code Router (simplest)

**When to choose:** quick setup focused on Claude Code; easy model switching with `/model`.

1. **Install**

```bash
npm i -g @anthropic-ai/claude-code @musistudio/claude-code-router
```

CCR runs a local server and translates requests for you. ([GitHub][2])

2. **Configure CCR for Chutes**
   Create `~/.claude-code-router/config.json` like:

```json
{
  "Providers": [
    {
      "name": "chutes",
      "api_base_url": "https://llm.chutes.ai/v1/chat/completions",
      "api_keys": ["YOUR_CHUTES_API_KEY"],
      "models": ["deepseek-ai/DeepSeek-V3-0324"],
      "transformer": { "use": ["openrouter"] }
    }
  ],
  "Router": { "default": "chutes,deepseek-ai/DeepSeek-V3-0324" }
}
```

Notes:

* Chutes’ **base URL** is OpenAI-style: `https://llm.chutes.ai/v1/chat/completions`. ([Reddit][9])
* Model IDs vary (e.g., `deepseek-ai/DeepSeek-V3-0324`, `Qwen/Qwen3-235B-A22B`, `ZhipuAI/glm-4.5`)—grab the exact string from Chutes’ model page. ([Reddit][9])

3. **Start CCR and point Claude Code at it**

```bash
ccr start
export ANTHROPIC_BASE_URL=http://127.0.0.1:3456
claude
```

CCR exposes an Anthropic-compatible endpoint; setting `ANTHROPIC_BASE_URL` makes Claude Code use it. In the Claude Code REPL you can switch models with `/model provider,model`. ([npm][3])

**Community confirmation:** multiple Reddit threads mention using Claude Code with GLM-4.5/DeepSeek **via Chutes** (often preferring CCR). ([Reddit][6], [Reddit][7])
**Video walkthroughs:** several YouTube explainers demo **Claude Code Router**, setup, and model routing. ([YouTube][10], [YouTube][11])

---

## Option B — LiteLLM “Anthropic unified endpoint” (more general)

**When to choose:** you want observability, spend controls, or to route many providers with one gateway.

1. **Define a LiteLLM model that points to Chutes**
   Create `litellm_config.yaml`:

```yaml
model_list:
  - model_name: chutes-deepseek-v3
    litellm_params:
      model: openai/deepseek-ai/DeepSeek-V3-0324   # tell LiteLLM it's OpenAI-compatible
      api_base: https://llm.chutes.ai/v1           # base should include /v1
      api_key: YOUR_CHUTES_API_KEY
```

LiteLLM’s OpenAI-compatible docs show the `openai/` prefix and the need for `/v1` in `api_base`. ([LiteLLM][5])

2. **Run LiteLLM and expose an Anthropic-style endpoint**

```bash
litellm --config /path/to/litellm_config.yaml
export ANTHROPIC_BASE_URL=http://127.0.0.1:4000
claude
```

Anthropic’s **LLM Gateway** guide explicitly supports setting `ANTHROPIC_BASE_URL` to a LiteLLM endpoint that speaks the **Anthropic messages** format. ([Anthropic][1], [LiteLLM][4])

**Working example calling Chutes through LiteLLM (code snippet/gist):** shows `api_base="https://llm.chutes.ai/v1"` and an `openai/...` model. ([Gist][12])

---

## Do you need “Claude Code Router”?

* **You need some router/gateway.** Claude Code won’t talk directly to Chutes’ OpenAI endpoint. You can use **CCR** (purpose-built) **or** **LiteLLM** (general gateway). Anthropic’s own docs describe the LiteLLM route with `ANTHROPIC_BASE_URL`, which is often the most “officially documented” path. ([Anthropic][1])
* If you already run LiteLLM for other projects, use **Option B**. If you just want the fastest path specifically for Claude Code, **Option A (CCR)** is very popular on Reddit/YouTube. ([Reddit][7], [YouTube][10])

---

## Model tips & quirks from forums

* **GLM-4.5** and **DeepSeek** models are frequently called out as working well with Claude Code via Chutes (router required). ([Reddit][6])
* Some users report **tool-call robustness varies by model** (e.g., mixed results for Qwen Coder vs GLM-4.5). Test your target model for tool use. ([Reddit][13])
* Chutes availability/rate-limit errors happen occasionally; regenerating keys or retrial often resolves. Base URL must be exact. ([Reddit][9])

---

### Sources

* Anthropic docs — **LLM Gateway configuration** (LiteLLM, `ANTHROPIC_BASE_URL`, Anthropic-format endpoint). ([Anthropic][1])
* LiteLLM docs — **Anthropic unified endpoint** and **OpenAI-compatible** config (`openai/` model prefix, `/v1` base). ([LiteLLM][4], [LiteLLM][5])
* **Claude Code Router** repo/features and usage, plus fork with added key rotation & commands. ([GitHub][2], [npm][3])
* Reddit confirmations & how-tos (Chutes base URL, examples, and user reports running Claude Code + Chutes): ([Reddit][9], [Reddit][6], [Reddit][7])
* YouTube demos of **Claude Code Router** setup/routing. ([YouTube][10], [YouTube][11])

---

If you’d like, tell me your target model on Chutes (e.g., DeepSeek V3, GLM-4.5, Kimi K2), and I’ll hand you an exact `config.json` (CCR) or `litellm_config.yaml` that you can paste in and run.

[1]: https://docs.anthropic.com/en/docs/claude-code/llm-gateway "LLM gateway configuration - Anthropic"
[2]: https://github.com/musistudio/claude-code-router "GitHub - musistudio/claude-code-router: Use Claude Code as the foundation for coding infrastructure, allowing you to decide how to interact with the model while enjoying updates from Anthropic."
[3]: https://www.npmjs.com/package/%40tellerlin/claude-code-router?activeTab=code "@tellerlin/claude-code-router - npm"
[4]: https://docs.litellm.ai/docs/anthropic_unified?utm_source=chatgpt.com "v1/messages"
[5]: https://docs.litellm.ai/docs/providers/openai_compatible?utm_source=chatgpt.com "OpenAI-Compatible Endpoints"
[6]: https://www.reddit.com/r/ChatGPTCoding/comments/1mcgm9s/psa_zaiglm45_is_absolutely_crushing_it_for_coding/?utm_source=chatgpt.com "zai/glm-4.5 is absolutely crushing it for coding - way better ..."
[7]: https://www.reddit.com/r/LocalLLaMA/comments/1mchsyd/tutorial_use_glm_45_or_any_llm_with_claude_code/?utm_source=chatgpt.com "[tutorial] Use GLM 4.5 (or any LLM) with Claude Code"
[8]: https://www.reddit.com/r/ClaudeAI/comments/1m3nyrn/who_is_using_claude_code_with_kimi_k2_thoughts/?utm_source=chatgpt.com "Who is using Claude Code with kimi k2? Thoughts? Tips?"
[9]: https://www.reddit.com/r/JanitorAI_Official/comments/1ju5vih/visual_guide_for_deepseek_users_via_chutesai_full/ "Visual Guide for DeepSeek Users (via Chutes.ai) – Full Credit to u/r3dux1337! : r/JanitorAI_Official"
[10]: https://www.youtube.com/watch?pp=0gcJCfwAo7VqN5tD&v=sAuCUAZnXAE&utm_source=chatgpt.com "Claude Code Router + Gemini 2.5 Pro FREE API: RIP Gemini ..."
[11]: https://www.youtube.com/watch?v=df-Fu2n7SLM&utm_source=chatgpt.com "The Claude Code HACK Anthropic Does Not Want You To Use"
[12]: https://gist.github.com/aquan9/58f4a77414a74703157bf79ea1bf009f?utm_source=chatgpt.com "Using litellm with chutes.ai from the bit-tensor chutes subnet."
[13]: https://www.reddit.com/r/LocalLLaMA/comments/1mf8la7/qwen3coder_is_bad_at_tool_call_while_glm45_is/?utm_source=chatgpt.com "Qwen3-Coder is bad at tool call while glm-4.5 is ..."
