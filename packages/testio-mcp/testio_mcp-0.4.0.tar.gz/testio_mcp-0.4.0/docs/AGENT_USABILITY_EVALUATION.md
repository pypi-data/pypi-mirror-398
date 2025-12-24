# TestIO MCP Server - Agent Usability Evaluation Guide

**Version:** 1.3
**Created:** 2025-11-19
**Last Updated:** 2025-12-03 (Added Tasks 10-12 evaluation, updated Task 8 workflow)
**Purpose:** Success criteria and scoring for usability testing (EVALUATOR ONLY - DO NOT SHARE WITH AGENT)

---

## 🚨 CRITICAL: Do Not Share This File With Test Agents

**This file contains success criteria and expected solutions.**

- Agent should ONLY see task prompts from `AGENT_USABILITY_TASKS.md`
- This file is for evaluators to assess agent performance
- Sharing this file defeats the purpose of usability testing

---

## 📖 Evaluation Philosophy

### What We're Testing

1. **Tool Discoverability**: Can agents find the right tool without being told which one to use?
2. **Parameter Clarity**: Are parameter names and descriptions sufficient for correct usage?
3. **Error Quality**: Do error messages guide agents to successful completion?
4. **Self-Service**: Can agents complete tasks without external documentation?

### What Success Looks Like

- ✅ Agent discovers correct tool from description
- ✅ Agent understands parameters from signatures
- ✅ Agent recovers from errors using error messages
- ✅ Agent completes task without asking user for help

### What Failure Looks Like

- ❌ Agent gives up: "I don't know which tool to use"
- ❌ Agent guesses wrong tool repeatedly
- ❌ Agent can't figure out parameter format
- ❌ Agent can't recover from error without external help

---

## 📋 Task Evaluation Criteria

### Task 1: Product Discovery (Basic)

**Task Given to Agent:**
> "Find all products for mobile apps and tell me how many there are."

**Success Criteria:**
- ✅ Agent discovers `list_products` tool
- ✅ Agent figures out `product_type` parameter
- ✅ Agent determines correct value (mobile_app_ios, mobile_app_android, or both)
- ✅ Agent successfully retrieves and counts products

**Metrics to Record:**
- Tool discovery attempts: _____
- Parameter errors: _____
- Time to completion: _____
- External help needed: Yes / No

**Evaluator Notes:**
- Did agent find tool on first try? _____
- Were parameter names clear? _____
- Were parameter values discoverable (enum)? _____

**Scoring Guidance:**
- **5 points**: Found `list_products` immediately, understood `product_type` parameter, got results on first try
- **4 points**: Found tool quickly, 1 parameter error before success
- **3 points**: Explored 2-3 tools before finding correct one
- **2 points**: Multiple tool attempts, several parameter errors
- **1 point**: Could not complete without help

---

### Task 2: Test Filtering (Intermediate)

**Task Given to Agent:**
> "Show me all locked tests for any product you find. I only need the first 20 results."

**Success Criteria:**
- ✅ Agent discovers `list_products` first (to get product ID)
- ✅ Agent extracts a product ID from results
- ✅ Agent discovers `list_tests` tool
- ✅ Agent figures out status filtering (statuses parameter)
- ✅ Agent applies pagination (per_page=20)
- ✅ Agent successfully retrieves results

**Metrics to Record:**
- Tool discovery attempts: _____
- Parameter errors: _____
- Pagination discovered: Yes / No
- Time to completion: _____

**Evaluator Notes:**
- Did agent understand multi-step workflow? _____
- Did agent discover pagination without prompting? _____
- Were status values discoverable? _____

**Scoring Guidance:**
- **5 points**: Discovered 2-step workflow naturally, applied both filtering and pagination correctly
- **4 points**: Completed workflow with 1-2 parameter errors
- **3 points**: Completed but missed pagination (returned all results) OR needed hint about workflow
- **2 points**: Struggled with parameter formats, multiple errors
- **1 point**: Could not complete multi-step workflow

---

### Task 3: Pagination Discovery (Advanced)

**Task Given to Agent:**
> "I need to see tests 50-99 (items 50 through 99) for product ID 25073. How would you fetch exactly that range?"

**Success Criteria:**
- ✅ Agent discovers `list_tests` pagination parameters
- ✅ Agent figures out offset mechanism (offset=50, per_page=50)
- ✅ OR agent figures out page mechanism (page=2, per_page=50 with offset=0)
- ✅ Agent explains the pagination approach
- ✅ Agent successfully retrieves the requested range

**Metrics to Record:**
- Pagination strategy discovered: offset / page / both / neither
- Correct range calculated: Yes / No
- Parameter errors: _____
- Time to completion: _____

**Evaluator Notes:**
- Did agent discover offset parameter? _____
- Did agent understand offset + page combination? _____
- Was start_index/end_index metadata helpful? _____

**Scoring Guidance:**
- **5 points**: Discovered offset parameter, calculated correct range (offset=50, per_page=50), verified with start_index/end_index
- **4 points**: Used page-based approach (page=2, offset=0, per_page=50) - works but less precise
- **3 points**: Attempted pagination but got range wrong (off-by-one errors)
- **2 points**: Retrieved data but couldn't figure out how to get specific range
- **1 point**: Could not figure out pagination at all

---

### Task 4: Error Recovery (Error Handling)

**Task Given to Agent:**
> "Get me details on test ID 999999."

**Success Criteria:**
- ✅ Agent discovers `get_test_summary` tool
- ✅ Agent attempts call with invalid test ID
- ✅ Agent receives error message
- ✅ Agent understands error (test not found)
- ✅ Agent suggests actionable next step (use list_tests to find valid ID)

**Metrics to Record:**
- Error message clarity rating: 1-5 (1=confusing, 5=crystal clear)
- Recovery action suggested: Yes / No
- External help needed: Yes / No

**Evaluator Notes:**
- Was error message format clear (❌ ℹ️  💡)? _____
- Did error explain what went wrong? _____
- Did error suggest how to fix it? _____
- Did agent recover independently? _____

**Scoring Guidance:**
- **5 points**: Read error, understood immediately, suggested using list_tests to find valid ID
- **4 points**: Understood error, recovered with minor exploration
- **3 points**: Understood error but needed external guidance for next steps
- **2 points**: Confused by error message, required explanation
- **1 point**: Could not interpret error or recover

---

### Task 5: Multi-Step Workflow (Complex)

**Task Given to Agent:**
> "I want to see the second page of archived tests for any mobile app product. Show me items 101-200."

**Success Criteria:**
- ✅ Agent discovers `list_products` tool
- ✅ Agent filters by mobile product type
- ✅ Agent extracts product ID
- ✅ Agent discovers `list_tests` tool
- ✅ Agent applies status filter (statuses=["archived"])
- ✅ Agent calculates pagination (page=2, per_page=100 OR offset=100, per_page=100)
- ✅ Agent successfully retrieves results
- ✅ Agent verifies item range matches request

**Metrics to Record:**
- Tool discovery attempts: _____
- Workflow steps completed: _____ / 8
- Parameter errors: _____
- Time to completion: _____
- Correct result: Yes / No

**Evaluator Notes:**
- Did agent chain tools correctly? _____
- Did agent understand filter + pagination combination? _____
- Did agent verify results met requirements? _____

**Scoring Guidance:**
- **5 points**: Completed full workflow, applied both filters and pagination correctly, verified range
- **4 points**: Completed workflow with 1-2 minor errors (corrected independently)
- **3 points**: Completed core workflow but missed either filtering OR pagination
- **2 points**: Struggled with multi-step coordination, required hints
- **1 point**: Could not complete workflow without significant help

---

### Task 6: Database Awareness (System Knowledge)

**Task Given to Agent:**
> "How fresh is the data in the system? Are we up to date?"

**Success Criteria:**
- ✅ Agent discovers `get_database_stats` tool (not obvious from task wording)
- ✅ Agent calls tool to check sync status
- ✅ Agent interprets results (last_synced timestamps, test counts)
- ✅ Agent provides meaningful assessment of data freshness

**Metrics to Record:**
- Tool discovery: Immediate / After exploration / Failed
- Correct tool selected: Yes / No
- Time to completion: _____

**Evaluator Notes:**
- Was tool name discoverable from task? _____
- Did agent understand database vs cache concept? _____
- Could agent interpret technical output? _____

**Scoring Guidance:**
- **5 points**: Found `get_database_stats` quickly, interpreted results correctly, gave meaningful assessment
- **4 points**: Found tool after exploring 2-3 options, interpreted correctly
- **3 points**: Found tool but struggled to interpret output (timestamp parsing, etc.)
- **2 points**: Guessed wrong tool initially, required guidance
- **1 point**: Could not discover correct tool

---

### Task 7: Large Report Export (Feature Discovery)

**Task Given to Agent:**
> "I need a complete bug report for product 18559 covering July to October 2025. The product has over 200 tests, so I'm worried about getting all the data. Can you get me the full report in a way I can save and share with my team?"

**Success Criteria:**
- ✅ Agent discovers `get_product_quality_report` tool
- ✅ Agent understands date filtering (start_date, end_date parameters)
- ✅ Agent recognizes concern about data size (>200 tests)
- ✅ Agent discovers `output_file` parameter (file export feature)
- ✅ Agent uses output_file to export to file
- ✅ Agent explains file location and how to share it
- ✅ Agent successfully retrieves file metadata response

**Metrics to Record:**
- Tool discovery: Immediate / After exploration / Failed
- File export feature discovered: Yes / No
- Parameter format correct: Yes / No
- Time to completion: _____
- External help needed: Yes / No

**Evaluator Notes:**
- Did agent recognize "worried about getting all the data" as hint for file export? _____
- Did agent discover output_file parameter without prompting? _____
- Did agent understand relative vs absolute path resolution? _____
- Did agent explain where file was saved? _____
- Did agent verify file was created successfully? _____

**Scoring Guidance:**
- **5 points**: Discovered file export feature naturally, used output_file parameter correctly, explained file location and sharing options
- **4 points**: Found file export after exploring parameters, minor path confusion but self-corrected
- **3 points**: Generated report but initially returned JSON response (missed file export), discovered feature after hint or second attempt
- **2 points**: Struggled to understand output_file parameter, required documentation or examples
- **1 point**: Could not discover file export feature, only returned JSON response

**Key Usability Indicators:**
- **Excellent (5)**: "I see there's an output_file parameter - I'll use that to export the report to a file you can share"
- **Good (4)**: "Let me check the parameters... there's an output_file option, I'll try that"
- **Acceptable (3)**: [Returns JSON first] "That's a lot of data, let me see if there's a way to export to file"
- **Poor (2)**: "I can get the report but I'm not sure how to save it"
- **Failed (1)**: [Returns JSON] "Here's the report" [doesn't address size concern or sharing]

**What This Tests:**
- **Feature Discoverability**: Can agents find optional features from parameter descriptions?
- **Context Awareness**: Do agents recognize user concerns and map them to features?
- **Parameter Documentation**: Is output_file parameter sufficiently documented?
- **Path Resolution**: Do agents understand relative vs absolute paths?

---

### Task 8: Feature Discovery and Drill-Down (Multi-Tool Workflow)

**Task Given to Agent:**
> "I need to see all features for the Canva product (ID 18559) that have user stories. Then get the full details including the actual user story titles for the first feature you find. Finally, tell me who the top 5 most active testers are."

**⚠️ CRITICAL WORKFLOW:** This task tests the list_features → get_feature_summary drill-down pattern. The `list_features` tool returns only `user_story_count` (integer), NOT the actual user story titles. To see story titles, agents MUST call `get_feature_summary(feature_id=X)`.

**Success Criteria:**
- ✅ Agent discovers `list_features` tool for first request
- ✅ Agent applies `has_user_stories=true` filter
- ✅ Agent calls list_features(product_id=18559, has_user_stories=true)
- ✅ Agent extracts feature_id from results
- ✅ Agent discovers `get_feature_summary` tool (NOT list_user_stories)
- ✅ Agent calls get_feature_summary(feature_id=X) to see actual user stories
- ✅ Agent discovers `list_users` tool for third request
- ✅ Agent understands "testers" maps to user_type="tester"
- ✅ Agent discovers pagination parameter (per_page=5)
- ✅ Agent successfully completes 3-step workflow

**Metrics to Record:**
- Tool discovery attempts: _____
- Workflow steps completed: _____ / 10
- Parameter errors: _____
- Drill-down success (list → get_summary pattern): Yes / No
- Time to completion: _____
- Correct result: Yes / No

**Evaluator Notes:**
- Did agent use `has_user_stories=true` filter? _____
- Did agent recognize list_features returns counts, not titles? _____
- Did agent discover get_feature_summary for drill-down? _____
- Did agent extract feature_id correctly? _____
- Did agent understand "testers" → user_type="tester"? _____
- Did agent discover pagination for limiting results? _____

**Scoring Guidance:**
- **5 points**: Perfect drill-down workflow (list → filter → extract ID → get_summary), mapped testers correctly, applied pagination
- **4 points**: Completed workflow with 1 minor error (e.g., missed has_user_stories filter but self-corrected)
- **3 points**: Found list_features but struggled with drill-down pattern - didn't know how to get actual story titles
- **2 points**: Couldn't figure out how to get actual user_stories - only saw counts
- **1 point**: Failed to complete multi-step workflow

**What This Tests:**
- **List vs Summary Pattern**: Can agents understand that list tools return counts, summary tools return details?
- **Drill-Down Discovery**: Can agents find the get_feature_summary tool to expand on list_features results?
- **Filter Discovery**: Can agents discover has_user_stories filter from parameter names?
- **Enum Parameter Discovery**: Can agents map "testers" to user_type="tester"?
- **Multi-Step Orchestration**: Can agents manage 3-step workflows without losing context?

**Expected Agent Behavior (Score 5):**
1. "I'll use list_features with has_user_stories=true to find features that have stories"
2. [Receives features with user_story_count] "I see feature X has 3 user stories. Let me get the actual titles"
3. "I'll use get_feature_summary to see the full details including story titles"
4. [Receives feature with embedded user_stories array] "Now I'll get the top 5 testers using list_users"
5. "I'll use list_users with user_type='tester' and per_page=5"

**Key Usability Indicator:**
- **Excellent (5):** "I'll use list_features to find features, then get_feature_summary to see the actual stories"
- **Good (4):** [Uses list_features] "I see user_story_count but need the actual stories - let me find another tool"
- **Poor (2):** "I found list_features but it only shows counts, not sure how to get stories"

**Common Failure Patterns:**
- **Failed (Score 1)**: "I don't see a tool for features. Should I use list_tests?"
- **Poor (Score 2)**: "list_features shows user_story_count: 3 but I can't find how to see the actual stories"
- **Acceptable (Score 3)**: [Completes features + summary] "I can't find how to get testers"
- **Good (Score 4)**: [Completes all 3 steps] "Here are all users. I'm not sure how to filter to just testers"

---

### Task 9: Analytics Discovery (Dynamic Query Building)

**Task Given to Agent:**
> "I want to find out which features have the most bugs. Show me the top 5 features ranked by total bug count, and also tell me the bugs-per-test ratio for each to understand how fragile they are."

**Success Criteria:**
- ✅ Agent discovers analytics capabilities (optional but helpful)
- ✅ Agent discovers `query_metrics` tool
- ✅ Agent understands `metrics` parameter (needs both bug_count and bugs_per_test)
- ✅ Agent understands `dimensions` parameter (needs ["feature"])
- ✅ Agent applies sorting (sort_by="bug_count", sort_order="desc")
- ✅ Agent constructs correct query_metrics call
- ✅ Agent interprets response and presents top 5 features with both metrics
- ✅ Agent successfully completes the workflow

**Metrics to Record:**
- Tool discovery attempts: _____
- Capabilities exploration (called get_analytics_capabilities): Yes / No
- Parameter errors: _____
- Query attempts before success: _____
- Time to completion: _____
- Correct result: Yes / No

**Evaluator Notes:**
- Did agent discover get_analytics_capabilities tool? _____
- Did agent use get_analytics_capabilities to discover dimensions/metrics? _____
- Did agent understand that two metrics are needed (bug_count + bugs_per_test)? _____
- Did agent discover query_metrics tool without prompting? _____
- Did agent understand metrics vs dimensions distinction? _____
- Did agent apply sorting correctly? _____
- Did agent handle validation errors gracefully (if any)? _____

**Scoring Guidance:**
- **5 points**: Discovered both tools, explored capabilities first, constructed perfect query (2 metrics, 1 dimension, correct sorting), interpreted results correctly
- **4 points**: Found query_metrics, constructed correct query with 1-2 parameter errors (self-corrected)
- **3 points**: Found query_metrics but struggled with parameters (missing bugs_per_test OR sorting), needed hints
- **2 points**: Found tool but couldn't construct valid query, required documentation or examples
- **1 point**: Could not discover analytics tools or complete workflow

**What This Tests:**
- **Tool Discovery**: Can agents find specialized analytics tools from task description?
- **Capabilities Exploration**: Do agents discover and use get_analytics_capabilities for guidance?
- **Parameter Understanding**: Can agents distinguish metrics (what to measure) from dimensions (how to group)?
- **Multi-Metric Queries**: Can agents request multiple metrics in one query?
- **Sorting Discovery**: Can agents discover sort_by and sort_order parameters?
- **Response Interpretation**: Can agents extract and present relevant data from analytics results?

**Expected Agent Behavior (Score 5):**
1. "Let me first check what analytics capabilities are available"
2. [Calls get_analytics_capabilities] "I see dimensions like 'feature' and metrics like 'bug_count' and 'bugs_per_test'"
3. "I'll use query_metrics to get bug counts and fragility ratios by feature"
4. [Calls query_metrics with metrics=["bug_count", "bugs_per_test"], dimensions=["feature"], sort_by="bug_count", sort_order="desc"]
5. [Receives results] "Here are the top 5 features: Feature A has 45 bugs (2.3 bugs/test), Feature B has 38 bugs (1.9 bugs/test)..."

**Common Failure Patterns:**
- **Failed (Score 1)**: "I don't see an analytics tool. Should I list all bugs and count manually?"
- **Poor (Score 2)**: "I found query_metrics but I'm not sure what parameters to use"
- **Acceptable (Score 3)**: [Only requests bug_count] "Here are features by bug count. I'm not sure how to get the bugs-per-test ratio"
- **Good (Score 4)**: [Correct query] "Here are the results sorted by bug count, showing both total bugs and the ratio"

**Key Usability Indicators:**
- **Excellent (5)**: "I see get_analytics_capabilities - let me check what's available first" [discovers both metrics naturally]
- **Good (4)**: "I'll use query_metrics with bug_count and bugs_per_test metrics" [understands multi-metric concept]
- **Acceptable (3)**: "I'll query by feature dimension" [gets dimensions right but misses one metric]
- **Poor (2)**: "What's the difference between metrics and dimensions?" [confusion about core concepts]
- **Failed (1)**: "I don't see any analytics tools" [cannot discover tools from task description]

---

### Task 10: Search Discovery

**Task Given to Agent:**
> "I'm looking for any tests or bugs related to 'login authentication'. Can you search across all entities and show me what you find? I want to see the most relevant results."

**Success Criteria:**
- ✅ Agent discovers `search` tool
- ✅ Agent understands `query` parameter
- ✅ Agent optionally filters by `entities` parameter
- ✅ Agent interprets BM25 ranking (score + rank)
- ✅ Agent presents results in relevance order

**Metrics to Record:**
- Tool discovery: Immediate / After exploration / Failed
- Correct parameters used: Yes / No
- Ranking interpretation: Yes / No
- Time to completion: _____

**Evaluator Notes:**
- Did agent discover search tool immediately from task? _____
- Did agent understand entity filtering is optional? _____
- Did agent explain ranking/relevance to user? _____

**Scoring Guidance:**
- **5 points**: Found search tool immediately, used query correctly, explained BM25 ranking to user
- **4 points**: Found tool quickly, used correctly with 1 minor error
- **3 points**: Found tool after trial-and-error, struggled with entity filter
- **2 points**: Tried other tools first (list_tests, list_bugs), eventually found search
- **1 point**: Could not discover search tool

**What This Tests:**
- **Tool Discovery**: Can agents find the search tool from natural language?
- **Parameter Understanding**: Can agents use query and optional entity filters?
- **Result Interpretation**: Can agents explain BM25 relevance ranking?

---

### Task 11: Bug Investigation Workflow

**Task Given to Agent:**
> "I found some tests that are producing rejected bugs. Can you show me all the rejected bugs for test ID 141290, and then get me the full details on the bug with the highest severity to understand why it was rejected?"

**⚠️ CRITICAL:** `list_bugs` requires `test_ids` parameter (mandatory). Agent must use list_bugs(test_ids=[141290]), NOT try to list all bugs globally.

**Success Criteria:**
- ✅ Agent discovers `list_bugs` tool
- ✅ Agent understands `test_ids` is REQUIRED (not optional)
- ✅ Agent applies `status=["rejected"]` filter
- ✅ Agent chains to `get_bug_summary` for details
- ✅ Agent finds rejection_reason field in bug details

**Metrics to Record:**
- Tool discovery attempts: _____
- Understood test_ids is required: Yes / No
- Filter applied correctly: Yes / No
- Drill-down to get_bug_summary: Yes / No
- Time to completion: _____

**Evaluator Notes:**
- Did agent try to list bugs globally first (fail)? _____
- Did agent understand test_ids scoping requirement? _____
- Did agent find rejection_reason in bug details? _____

**Scoring Guidance:**
- **5 points**: Perfect workflow - list_bugs with test_ids and status filter, get_bug_summary for details, found rejection_reason
- **4 points**: Completed workflow with 1 minor error (e.g., missed status filter initially)
- **3 points**: Found list_bugs but struggled with required test_ids parameter
- **2 points**: Tried to list all bugs globally, required error message guidance
- **1 point**: Could not figure out bug workflow

**What This Tests:**
- **Required Parameter Discovery**: Can agents recognize mandatory parameters?
- **Filter Chaining**: Can agents apply multiple filters (test_ids + status)?
- **Drill-Down Pattern**: Can agents chain list → get_summary for details?
- **Error Recovery**: Do agents learn from "test_ids required" error?

**Key Usability Indicator:**
- **Excellent (5):** "I'll use list_bugs with test_ids=[141290] and status=['rejected']"
- **Poor (2):** "Let me list all bugs... [error] Oh, I need test_ids"

---

### Task 12: Quick Summary Lookup

**Task Given to Agent:**
> "Give me a quick summary of product 18559 - I just need the basics like name, test count, and feature count, not the full list of everything."

**Success Criteria:**
- ✅ Agent chooses `get_product_summary` over `list_products`
- ✅ Agent understands cache-only operation (fast, no API)
- ✅ Agent recognizes lightweight vs. heavy operations
- ✅ Agent presents summary information clearly

**Metrics to Record:**
- Tool discovery: Immediate / After exploration / Failed
- Correct tool chosen (summary vs list): Yes / No
- Response time noted: Yes / No
- Time to completion: _____

**Evaluator Notes:**
- Did agent choose summary tool over list tool? _____
- Did agent mention this is a cache-only operation? _____
- Did agent note the response was fast? _____

**Scoring Guidance:**
- **5 points**: Found get_product_summary immediately, noted it's lightweight/cache-only
- **4 points**: Found summary tool after brief exploration, used correctly
- **3 points**: Used list_products then filtered/extracted (works but inefficient)
- **2 points**: Used list_products without realizing summary tool exists
- **1 point**: Could not get product information at all

**What This Tests:**
- **Efficiency Discovery**: Can agents choose appropriate tools for task scope?
- **Summary vs List Pattern**: Do agents understand when to use summary tools?
- **Performance Awareness**: Do agents recognize cache-only operations are faster?

**Key Usability Indicator:**
- **Excellent (5):** "I'll use get_product_summary - it's a quick cache lookup"
- **Acceptable (3):** "Let me use list_products and filter for ID 18559"

---

## 🎓 Usability Scoring System

### Individual Task Scoring (1-5 Scale)

**5 - Excellent**: Agent completed task efficiently with no errors
- Found correct tools immediately
- Understood all parameters
- No external help needed

**4 - Good**: Agent completed task with minor issues
- Found tools quickly (1-2 attempts)
- 1-2 parameter errors before success
- Self-corrected without help

**3 - Acceptable**: Agent completed task but struggled
- Multiple tool explorations needed
- Several parameter errors
- Minor external hints acceptable

**2 - Poor**: Agent struggled significantly
- Wrong tools attempted multiple times
- Required external documentation
- Needed step-by-step guidance

**1 - Failed**: Agent could not complete task
- Could not find correct tool
- Could not figure out parameters
- Required complete solution

### Overall Usability Score Calculation

**Formula:**
```
Overall Score = (Task1 + Task2 + Task3 + Task4 + (Task5 * 2) + Task6 + Task7 + Task8 + Task9 + Task10 + Task11 + Task12) / 13

(Task 5 weighted 2x due to complexity; 13 total weighted units)
```

**Grade Interpretation:**
- **A (4.5-5.0):** Excellent UX - Agents self-serve efficiently
- **B (3.5-4.4):** Good UX - Minor improvements needed
- **C (2.5-3.4):** Acceptable UX - Several usability issues
- **D (1.5-2.4):** Poor UX - Agents struggle significantly
- **F (<1.5):** Critical UX Issues - Major redesign needed

---

## 📊 Evaluation Template

### Test Execution Record

**Agent Name/ID:** ___________________
**Test Date:** ___________________
**Environment:** ___________________
**Evaluator:** ___________________

| Task | Score (1-5) | Tool Discovery | Parameter Errors | Time | External Help? | Notes |
|------|-------------|----------------|------------------|------|----------------|-------|
| 1. Product Discovery | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 2. Test Filtering | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 3. Pagination | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 4. Error Recovery | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 5. Multi-Step (2x) | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 6. System Health | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 7. File Export | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 8. Feature Drill-Down | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 9. Analytics | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 10. Search Discovery | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 11. Bug Investigation | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |
| 12. Quick Summary | ___ | ___ attempts | ___ | ___ | Yes / No | _____ |

**Raw Score:** _____ / 13 = _____

**Overall Usability Score:** _____ / 5.0

**Grade:** _____ (A/B/C/D/F)

---

## 🔍 Common Usability Issues to Watch For

### Tool Discovery Problems

**Symptoms:**
- Agent browses many tools before finding correct one
- Agent tries obviously wrong tools
- Agent gives up and asks which tool to use

**Root Causes:**
- ❌ Tool names too technical
- ❌ Tool descriptions too vague
- ❌ Similar-sounding tools (naming collision)

**Good Signs:**
- ✅ Tool names map naturally to user intent
- ✅ Descriptions clearly state when to use tool
- ✅ Agent finds correct tool in 1-2 attempts

---

### Parameter Clarity Problems

**Symptoms:**
- Multiple parameter type errors
- Agent asks "what format should this be?"
- Agent trial-and-errors parameter values

**Root Causes:**
- ❌ Parameter names unclear (e.g., `p_id` vs `product_id`)
- ❌ Parameter types not obvious (string vs int vs enum)
- ❌ Parameter relationships not documented (page + offset)
- ❌ Default values not discoverable

**Good Signs:**
- ✅ Parameter names self-documenting
- ✅ Type hints provide clear expectations
- ✅ Agent gets parameters right on first try

---

### Error Message Problems

**Symptoms:**
- Agent confused by error
- Agent asks "what does this mean?"
- Agent cannot determine next steps

**Root Causes:**
- ❌ Technical jargon without explanation
- ❌ No actionable guidance
- ❌ Missing context (what/why)

**Good Signs:**
- ✅ Three-part format visible (❌ ℹ️  💡)
- ✅ Agent understands error immediately
- ✅ Agent knows what to do next

---

## 📈 Using Results to Improve UX

### If Tool Discovery Scores Are Low (<3.0 average)

**Recommended Fixes:**
1. Review tool names - use user-centric language
2. Improve tool descriptions - lead with "Use this when..."
3. Add example use cases to descriptions
4. Consider renaming confusing tools

**Priority:** HIGH (agents can't even start tasks)

---

### If Parameter Clarity Scores Are Low (<3.0 average)

**Recommended Fixes:**
1. Add parameter examples in docstrings
2. Use clearer parameter names
3. Document parameter relationships
4. Provide enum values in descriptions
5. Add type hints if missing

**Priority:** MEDIUM (agents find tools but struggle to use them)

---

### If Error Recovery Scores Are Low (<3.0 average)

**Recommended Fixes:**
1. Audit all error messages for three-part format (❌ ℹ️  💡)
2. Add context: explain WHY error occurred
3. Add guidance: suggest HOW to fix it
4. Reference related tools when relevant

**Priority:** HIGH (poor error UX blocks agent progress)

---

### If Complex Workflow Scores Are Low (<3.0 on Task 5)

**Recommended Fixes:**
1. Add workflow examples to tool descriptions
2. Document common task patterns
3. Add hints about tool chaining
4. Consider adding a "workflows" guide

**Priority:** MEDIUM (advanced use cases suffer)

---

## 🎬 Post-Test Action Plan

### Immediate Actions (After Each Test)

1. **Record scores** in evaluation template
2. **Note patterns** - recurring issues across tasks
3. **Document surprises** - unexpected agent behaviors
4. **Capture quotes** - interesting agent statements

### Analysis Phase

1. **Calculate overall score** and assign grade
2. **Identify top 3 issues** by frequency and severity
3. **Prioritize fixes** - HIGH/MEDIUM/LOW
4. **Create improvement tickets** with specific examples

### Iteration Cycle

1. **Implement fixes** based on priority
2. **Re-test** same scenarios with same agent
3. **Measure improvement** - before/after scores
4. **Document learnings** in ADRs or architecture docs

### Trend Tracking

**Maintain a test history log:**
| Date | Agent | Overall Score | Grade | Top Issues | Fixes Applied |
|------|-------|---------------|-------|------------|---------------|
| 2025-11-19 | Agent-A | 3.2 | C | Tool discovery, pagination | Renamed tools, improved docs |
| 2025-11-26 | Agent-A | 4.1 | B | Pagination | Added examples |
| 2025-12-03 | Agent-B | 4.6 | A | (none) | (validation) |

**Goal:** Trend toward Grade A (4.5+) over 3-4 iterations

---

## 📝 Example Completed Evaluation

### Sample Agent Test Results

**Agent:** Claude Sonnet 4.5
**Date:** 2025-11-19
**Evaluator:** Quinn (Test Architect)

| Task | Score | Notes |
|------|-------|-------|
| 1. Product Discovery | 5 | Found `list_products` immediately, understood enum |
| 2. Test Filtering | 4 | Discovered workflow naturally, 1 parameter typo |
| 3. Pagination | 3 | Used page=2 approach, didn't discover offset parameter |
| 4. Error Recovery | 5 | Error message clear, suggested list_tests immediately |
| 5. Multi-Step (2x) | 4 | Completed workflow, minor confusion on item range |
| 6. Database Health | 4 | Found tool after exploring 2 options |
| 7. File Export | 5 | Discovered output_file parameter, explained file location |

**Overall Score:** (5+4+3+5+(4*2)+4+5)/8 = **4.25 / 5.0**

**Grade:** B (Good UX)

**Key Findings:**
- ✅ Tool discovery excellent (names are clear)
- ✅ Error messages effective (three-part format works)
- ⚠️  Offset parameter not discoverable (needs documentation)
- ⚠️  Item range calculation confusing (needs examples)

**Recommended Actions:**
1. Add offset parameter example to tool docstring
2. Add "fetch items X-Y" example showing offset calculation
3. Re-test pagination scenario after improvements

---

**Document Version:** 1.3
**Last Updated:** 2025-12-03 (Added Tasks 10-12 evaluation, updated Task 8 workflow)
**Companion Document:** `AGENT_USABILITY_TASKS.md` (task prompts for agents)
**Do Not Share With:** Test agents (evaluator use only)
