# Prompt Engineering Research: Evidence Validation in Analysis Workflows

**Date:** 2025-12-02
**Status:** Research Complete, Implementation Pending
**Context:** Improving `analyze-product-quality` prompt to prevent unvalidated claims

---

## Problem Statement

During real-world usage of the `analyze-product-quality` prompt, the model made speculative claims without evidence. Initial fix attempt used **prohibition lists** (banned words like "likely", "suggests", "possibly") with "ZERO TOLERANCE" warnings.

**Hypothesis:** Prohibition lists are poor prompt engineering. Research needed to find better patterns.

---

## Research Findings

### Key Insight: Positive Framing Beats Prohibition Lists

> "The most effective prompts use positive language and avoid negative language -- in other words, 'Do say do, and don't say don't.'"
> — [TechTarget Best Practices](https://www.techtarget.com/searchenterpriseai/tip/Prompt-engineering-tips-and-best-practices)

### What We Did (Anti-Pattern)

```markdown
## Prohibited Language

> [!CAUTION]
> **ZERO TOLERANCE:** If you catch yourself using ANY of these words, STOP immediately.

| Prohibited | Replace With |
|------------|--------------|
| "likely" | Cite evidence... |
| "suggests" | ... |
| [13 more words] | ... |
```

**Problems:**
- Creates cognitive load scanning for prohibited words
- Focuses attention on what NOT to do
- Ambiguous edge cases (when IS "likely" okay?)
- Defensive/restrictive tone

### What Research Recommends

| Approach | Description | Source |
|----------|-------------|--------|
| **Positive framing** | Tell model what TO do, not what to avoid | [DigitalOcean](https://www.digitalocean.com/resources/articles/prompt-engineering-best-practices) |
| **Few-shot examples** | Show 2-3 examples of desired behavior | [IBM Few-Shot Guide](https://www.ibm.com/think/topics/few-shot-prompting) |
| **Role/persona** | Define clear role that implies behavior | [Learn Prompting](https://learnprompting.org/docs/advanced/zero_shot/role_prompting) |
| **Structured output schemas** | Define output format, model follows it | [Claude Structured Outputs](https://www.claude.com/blog/structured-outputs-on-the-claude-developer-platform) |
| **Constitutional principles** | "Choose the response that is more X" | [Anthropic Constitutional AI](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback) |

---

## Recommended Pattern: Example-Driven Positive Framing

### Instead of Prohibition List:

```markdown
❌ PROHIBITED: "likely", "suggests", "possibly", "may indicate"...
   ZERO TOLERANCE - STOP immediately
```

### Use Role + Examples:

```markdown
## Your Role

You are an **evidence-based quality analyst**. Every claim you make is grounded in specific data you have examined.

## How You Present Findings

**Format for validated findings:**
```
**Finding:** [Specific statement] 🟢 HIGH confidence
**Evidence:** Examined [N] of [M] bugs. Pattern in [X]%.
**Bug IDs:** #123, #456, #789
```

**Format when you need user input:**
```
**Hypothesis (needs your input):** [Statement]
**What I found:** [Data points]
**What I need from you:** [Specific question]
```

## Examples of Good Analysis

### Example 1: Validated Finding
**Finding:** Authentication bugs dominate "not reproducible" rejections 🟢 HIGH
**Evidence:** Examined 7 of 133 "not reproducible" bugs. 5 of 7 (71%) were auth/login failures.
**Bug IDs:** #2779183, #2779438, #2706747, #2673525, #2673254

### Example 2: Asking for User Input
**Hypothesis (needs your input):** iOS test environment may have configuration issues.
**What I found:** 5 auth bugs rejected as "not reproducible", all marked "[Not New]" by testers.
**What I need from you:** Do testers use shared accounts? Is iOS test env identical to production?

### Example 3: What NOT to Do (Contrast)
❌ "This pattern suggests environment issues, which may indicate flaky test conditions."
✅ "5 of 7 bugs show auth failures. I cannot determine root cause without your input on test environment setup."
```

---

## Key Principles from Research

### 1. Anthropic's Approach (Constitutional AI)
- Uses principles framed as "Choose the response that is more X"
- Focuses on positive characteristics (helpful, honest, harmless)
- Avoids prohibition lists in favor of guiding principles

### 2. OpenAI's GPT-4.1 Guidance
> "A single clear sentence is almost always sufficient to steer behavior."
> — [OpenAI GPT-4.1 Prompting Guide](https://cookbook.openai.com/examples/gpt4-1_prompting_guide)

### 3. Few-Shot Effectiveness
- "Up to 76 accuracy points improvement" with proper formatting
- "Best bang for buck" for enhancing output quality
- Superior for structured outputs and specialized tasks

### 4. Role Prompting
- Creates more desirable outputs for open-ended tasks
- Most effective when personas align closely with task context
- Single clear role definition > list of behaviors

---

## Implementation Recommendations

### Phase 1: Simplify Current Prompt

**Remove:**
- 13-word prohibition table
- "ZERO TOLERANCE" warnings
- "STOP immediately" language
- Redundant validation checklists

**Keep:**
- Evidence Validation Protocol (Two-Pass pattern)
- Confidence Scoring system (🟢🟡🔴)
- PAUSE for user input behavior

### Phase 2: Add Few-Shot Examples

Add 3-4 concrete examples showing:
1. Good finding with evidence
2. Hypothesis that needs user input
3. Contrast example (before/after)
4. Strategy recommendation with evidence basis

### Phase 3: Strengthen Role Definition

Replace scattered rules with clear role:

```markdown
## Your Role

You are an **evidence-based quality analyst** for TestIO. Your core behaviors:

1. **Ground every claim in data** - Cite bug IDs, sample sizes, percentages
2. **Ask when uncertain** - If you can't cite evidence, ask the user for context
3. **Quantify recommendations** - "Prevents X bugs/year based on Y pattern"

You never speculate. You either have evidence or you ask.
```

---

## Open Questions for Further Research

### 1. Optimal Number of Examples
- Research suggests 2-5 few-shot examples
- How many is optimal for analysis workflows specifically?
- Does example diversity matter more than quantity?

### 2. Role Specificity
- "Evidence-based analyst" vs "CSM quality consultant"
- Does domain-specific role improve adherence?
- Can role definition replace behavioral rules entirely?

### 3. Structured Output Enforcement
- Claude supports native JSON schema enforcement
- Could we define a `Finding` schema that enforces evidence fields?
- Trade-off: Rigidity vs conversational flexibility

### 4. Meta-Prompting for Analysis
- Can we create a reusable "analysis template" pattern?
- Would a two-stage prompt (plan → execute) improve rigor?
- How do other MCP servers handle complex analysis prompts?

### 5. Constitutional Principles Approach
- Could we define 3-5 principles instead of rules?
- Example: "Always choose the response that cites specific evidence"
- How does this compare to few-shot examples?

---

## Next Steps

1. [ ] **Rewrite prompt** using positive framing + few-shot examples
2. [ ] **A/B test** new prompt vs current prohibition-heavy version
3. [ ] **Measure** speculation language usage, user corrections needed
4. [ ] **Iterate** based on real-world usage feedback

---

## Sources

**Official Documentation:**
- [Anthropic Prompt Engineering Overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Anthropic Constitutional AI](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback)
- [OpenAI Best Practices](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)
- [OpenAI GPT-4.1 Prompting Guide](https://cookbook.openai.com/examples/gpt4-1_prompting_guide)

**MCP Resources:**
- [MCP Prompts Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts)
- [Building MCP Servers (Medium)](https://medium.com/@cstroliadavis/building-mcp-servers-13570f347c74)

**Research & Best Practices:**
- [TechTarget: Prompt Engineering Best Practices](https://www.techtarget.com/searchenterpriseai/tip/Prompt-engineering-tips-and-best-practices)
- [DigitalOcean: Positive Framing](https://www.digitalocean.com/resources/articles/prompt-engineering-best-practices)
- [IBM: Few-Shot Prompting](https://www.ibm.com/think/topics/few-shot-prompting)
- [PromptHub: Few-Shot Guide](https://www.prompthub.us/blog/the-few-shot-prompting-guide)
- [Learn Prompting: Role Prompting](https://learnprompting.org/docs/advanced/zero_shot/role_prompting)
- [Prompt Engineering Guide: Meta-Prompting](https://www.promptingguide.ai/techniques/meta-prompting)
- [arXiv: Negative Prompts Research](https://arxiv.org/abs/2406.02965)

---

**Document Version:** 1.0
**Author:** Claude (Opus 4.5) with research-investigator agent
**Reviewer:** Ricardo Leon
