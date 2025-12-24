# TestIO MCP Server - Agent Usability Tasks

**Version:** 1.3
**Last Updated:** 2025-12-03 (Added Tasks 10-12: Search, Bug Investigation, Quick Summary)
**Purpose:** Task prompts for AI agent usability testing (NO SOLUTION HINTS)

---

## 📖 Instructions for Test Administrator

**This file contains ONLY the task prompts to give to the agent.**

- Give agent these tasks ONE AT A TIME
- Do NOT show success criteria, metrics, or evaluator notes
- Do NOT hint at which tools to use
- Do NOT explain expected outputs
- Let agent explore and discover independently

**For evaluation criteria and scoring, see:** `AGENT_USABILITY_EVALUATION.md` (DO NOT share with agent)

---

## 🎯 Usability Test Tasks (12 Tasks)

### Task 1: Product Discovery

"Find all products for mobile apps and tell me how many there are."

---

### Task 2: Test Filtering

"Show me all locked tests for any product you find. I only need the first 20 results."

---

### Task 3: Pagination Challenge

"I need to see tests 50-99 (items 50 through 99) for product ID 18559. How would you fetch exactly that range?"

---

### Task 4: Error Recovery

"Get me details on test ID 999999."

---

### Task 5: Complex Workflow

"I want to see the second page of archived tests for any mobile app product. Show me items 101-200."

---

### Task 6: System Health

"How fresh is the data in the system? Are we up to date?"

---

### Task 7: Large Report Export

"I need a complete bug report for product 18559 covering July to October 2025. The product has over 200 tests, so I'm worried about getting all the data. Can you get me the full report in a way I can save and share with my team?"

---

### Task 8: Feature Discovery and Drill-Down

"I need to see all features for the Canva product (ID 18559) that have user stories. Then get the full details including the actual user story titles for the first feature you find. Finally, tell me who the top 5 most active testers are."

---

### Task 9: Analytics Discovery

"I want to find out which features have the most bugs. Show me the top 5 features ranked by total bug count, and also tell me the bugs-per-test ratio for each to understand how fragile they are."

---

### Task 10: Search Discovery

"I'm looking for any tests or bugs related to 'login authentication'. Can you search across all entities and show me what you find? I want to see the most relevant results."

---

### Task 11: Bug Investigation Workflow

"I found some tests that are producing rejected bugs. Can you show me all the rejected bugs for test ID 141290, and then get me the full details on the bug with the highest severity to understand why it was rejected?"

---

### Task 12: Quick Summary Lookup

"Give me a quick summary of product 18559 - I just need the basics like name, test count, and feature count, not the full list of everything."

---

## 📝 Notes for Test Administrator

- Start timing when task is presented
- Record agent's actions and tool calls
- Note any requests for help or clarification
- Stop timing when agent declares task complete
- Use AGENT_USABILITY_EVALUATION.md to score performance

**Do not interrupt or guide the agent unless:**
- Agent explicitly asks for help (mark as "external help needed")
- Agent is clearly stuck in an infinite loop (mark as failed attempt)
- Safety issue (API abuse, destructive actions)

---

**Document Version:** 1.3
**Last Updated:** 2025-12-03 (Added Tasks 10-12: Search, Bug Investigation, Quick Summary)
**Companion Document:** `AGENT_USABILITY_EVALUATION.md` (evaluator scoring guide)
