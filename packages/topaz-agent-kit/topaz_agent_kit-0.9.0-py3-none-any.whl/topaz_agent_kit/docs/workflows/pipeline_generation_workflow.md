# Pipeline Generation Workflow

This document defines the step-by-step workflow for generating a complete, production-ready pipeline configuration from a use case description. 

## How to Use This Workflow

**For AI Assistant**: When the user requests to create a new pipeline or says "follow the pipeline generation workflow", execute this workflow step-by-step. Work interactively with the user through each phase.

**For Users**: Reference this document when working with the AI assistant to create new pipelines. The AI will guide you through each step.

## Table of Contents

> **Navigation**: Use the links below to quickly jump to any section. All sections are in this single document for complete context and easy reference.

### Quick Navigation
- [User Review Checkpoints](#user-review-checkpoints)
- [Overview](#overview)
- [Prerequisites](#prerequisites)

### Step 1: Comprehensive Requirements Gathering
- [1.1 Basic Use Case Information](#11-basic-use-case-information)
  - [1.1.1 Handle Incomplete Information](#111-handle-incomplete-information)
  - [1.1.2 Generate Pipeline ID](#112-generate-pipeline-id)
  - [1.1.3 Agent Naming Convention & Prefix Confirmation](#113-agent-naming-convention--prefix-confirmation)
- [1.2 Workflow Pattern Preferences](#12-workflow-pattern-preferences)
- [1.3 Agent Identification & Responsibilities](#13-agent-identification--responsibilities)
  - [1.3.1 Agent ID Conflict Check](#131-agent-id-conflict-check)
- [1.4 Conditional Logic & Decision Points](#14-conditional-logic--decision-points)
- [1.5 Human-in-the-Loop (HITL) Requirements](#15-human-in-the-loop-hitl-requirements)
- [1.6 MCP Tools & External Dependencies](#16-mcp-tools--external-dependencies)
  - [1.6.1 Local Tools (Pipeline-Specific Tools)](#161-local-tools-pipeline-specific-tools)
- [1.7 Output Requirements](#17-output-requirements)
- [1.8 Icon & Visual Preferences](#18-icon--visual-preferences)
- [1.9 Protocol & Remote Execution Preferences](#19-protocol--remote-execution-preferences)
- [1.10 Additional Requirements](#110-additional-requirements)
- [1.11 Requirements Summary & Review](#111-requirements-summary--review)
- [1.12 Mock Data Requirements & Script Generation](#112-mock-data-requirements--script-generation)
  - [1.12.1 Identify Data Requirements](#1121-identify-data-requirements)
  - [1.12.2 Reference Example Scripts](#1122-reference-example-scripts)
  - [1.12.3 Generate Mock Data Script](#1123-generate-mock-data-script)
  - [1.12.4 Register Script in scripts.yml](#1124-register-script-in-scriptsyml)
  - [1.12.5 User Testing & Validation](#1125-user-testing--validation)

### Step 2: Workflow Design & Proposal
- [2.1 Agent Identification & Finalization](#21-agent-identification--finalization)
  - [2.1.1 Protocol Selection (A2A)](#211-protocol-selection-a2a)
  - [2.1.2 MCP Tool Requirements Analysis](#212-mcp-tool-requirements-analysis)
- [2.2 Workflow Pattern Design](#22-workflow-pattern-design)
  - [2.2.0 Review Available Patterns (If Needed)](#220-review-available-patterns-if-needed)
  - [2.2.1 Design Execution Pattern](#221-design-execution-pattern)
  - [2.2.2 Dependency Validation](#222-dependency-validation)
  - [2.2.3 Complex Workflow Considerations](#223-complex-workflow-considerations)
- [2.3 HITL Gates Design](#23-hitl-gates-design)
  - [2.3.0 HITL Gate Types and Usage Patterns](#230-hitl-gate-types-and-usage-patterns)
    - [2.3.0.1 Approval Gates](#2301-approval-gates)
    - [2.3.0.2 Input Gates](#2302-input-gates)
    - [2.3.0.3 Selection Gates](#2303-selection-gates)
    - [2.3.0.4 HITL Gate Placement Strategies](#2304-hitl-gate-placement-strategies)
    - [2.3.0.5 HITL Gates in Different Pattern Types](#2305-hitl-gates-in-different-pattern-types)
  - [2.3.1 Gate Configuration Validation](#231-gate-configuration-validation)
  - [2.3.2 Retry Logic Configuration](#232-retry-logic-configuration)
- [2.4 Output Structure Design](#24-output-structure-design)
  - [2.4.1 Output Schema Design Guidelines](#241-output-schema-design-guidelines)
  - [2.4.2 Intermediate Outputs](#242-intermediate-outputs)
  - [2.4.3 Output Transformations](#243-output-transformations)
- [2.5 Present Workflow Proposal](#25-present-workflow-proposal)
  - [2.5.1 Create Design Document](#251-create-design-document)
  - [2.5.2 Present Workflow Proposal](#252-present-workflow-proposal)
- [2.6 User Review: Workflow Proposal](#26-user-review-workflow-proposal)

### Step 3: Interactive Refinement
- [3.1 Review & Feedback Loop](#31-review--feedback-loop)
- [3.2 Final Confirmation](#32-final-confirmation)

### Step 4: File Generation
- [4.0 Pre-Generation Checks](#40-pre-generation-checks)
- [4.1 Generate Pipeline Config](#41-generate-pipeline-config)
- [4.2 Generate Agent Configs](#42-generate-agent-configs)
  - [4.2.1 Model Configuration](#421-model-configuration)
  - [4.2.2 Remote Configuration](#422-remote-configuration)
- [4.3 Generate Prompt Templates](#43-generate-prompt-templates)
  - [4.3.0 Context Variable Access Rules](#430-context-variable-access-rules)
  - [4.3.1 Prompt Quality Validation](#431-prompt-quality-validation)
- [4.4 Generate UI Manifest](#44-generate-ui-manifest)
- [4.5 Icon Suggestions](#45-icon-suggestions)
- [4.6 Update Main Config Files](#46-update-main-config-files)
  - [4.6.3 Update Assistant Classification Prompt](#463-update-assistant-classification-prompt)
- [4.7 User Review: Generated Files](#47-user-review-generated-files)

### Step 5: Validation & Summary
- [5.1 Validate Generated Files](#51-validate-generated-files)
  - [5.1.2 Context Variable Validation](#512-context-variable-validation)
  - [5.1.1 User Review: Validation Results](#511-user-review-validation-results)
- [5.2 Generate Summary](#52-generate-summary)
  - [5.2.1 Summary Template](#521-summary-template)
- [5.3 User Review: Final Summary](#53-user-review-final-summary)
- [5.4 Post-Generation Notes](#54-post-generation-notes)
  - [5.4.1 Testing Pipeline](#541-testing-pipeline)

### Reference Sections
- [Common Patterns & Examples](#common-patterns--examples)
- [Jinja2 Filters Reference](#jinja2-filters-reference)
- [Important Reminders](#important-reminders)
- [Troubleshooting](#troubleshooting)
- [Workflow Completion](#workflow-completion)

## User Review Checkpoints

This workflow includes **6 explicit user review checkpoints** (marked with 🔍) where the AI must pause and wait for user approval before proceeding:

1. **After Requirements Gathering** (Step 1.11) - Review all collected requirements before mock data generation
2. **After Mock Data Script** (Step 1.12.5) - Test mock data script before workflow design
3. **After Workflow Proposal** (Step 2.6) - Review proposal before refinement
3. **Before File Generation** (Step 3.2) - Final confirmation before generating files
4. **After File Generation** (Step 4.7) - Review generated files before validation
5. **After Validation** (Step 5.1.1) - Review validation results before final summary
6. **Final Summary Review** (Step 5.3) - Review final summary and confirm completion

**Important**: The AI must NOT proceed past any review checkpoint without explicit user approval.

## Overview

When the user provides a use case, follow these steps to:
1. Analyze the use case and design the complete workflow through interactive discussion
2. Generate production-ready config files that can be run immediately
3. Create well-crafted, use-case-specific prompts for each agent
4. Generate all supporting files (UI manifests, assets)
5. Validate and provide summary

## Prerequisites

Before starting, ensure you understand:
- The project structure (check `src/topaz_agent_kit/templates/starters/ensemble/` for templates)
- Pipeline configuration format (see `src/topaz_agent_kit/templates/starters/ensemble/config/pipelines/`)
- Agent configuration format (see `src/topaz_agent_kit/templates/starters/ensemble/config/agents/`)
- Prompt template format (see `src/topaz_agent_kit/templates/starters/ensemble/config/prompts/`)
- UI manifest format (see `src/topaz_agent_kit/templates/starters/ensemble/config/ui_manifests/`)

## Base Path Selection

**🔍 CRITICAL**: Before starting pipeline generation, establish the base path where files will be generated.

**Action**: Ask the user for the base path:

**Question**: "Where should I generate the pipeline files?"

**Default**: If user doesn't specify, use: `src/topaz_agent_kit/templates/starters/ensemble/`

**Options**:
- User can provide a custom base path
- User can accept the default

**Important Notes**:
- All file paths in this workflow are **relative to the base path**
- When communicating with users, show format: "Base: `{base_path}` → `config/pipelines/{pipeline_id}.yml`"
- Store the base path and use it consistently throughout the workflow

**Example Communication**:
- "I'll use the default base path: `src/topaz_agent_kit/templates/starters/ensemble/`"
- "Files will be generated at: Base: `src/topaz_agent_kit/templates/starters/ensemble/` → `config/pipelines/{pipeline_id}.yml`"

## Interactive Conversation Best Practices

**🔍 IMPORTANT**: This workflow requires natural, interactive conversation with users. Follow these principles to create a smooth, intuitive experience.

### When to Batch Questions

**Batch related questions together** to avoid overwhelming users:
- ✅ **Good**: "Let me understand your workflow needs. What pattern should agents follow - sequential, parallel, or mixed? And which agents will run remotely initially?"
- ❌ **Bad**: Ask about pattern, wait for answer, then ask about remote execution separately

**Examples of good batching**:
- Basic use case info (name, description, purpose) - ask together
- Agent identification (roles, inputs, outputs) - ask for all agents at once
- HITL requirements (gates, placement, types) - group by gate type

### When to Ask One at a Time

**Ask complex questions individually** to allow thoughtful responses:
- ✅ **Good**: "What should we call this pipeline?" → wait → "What's the detailed purpose?" → wait
- ❌ **Bad**: "What's the name, description, purpose, pattern, agents, gates, and outputs?" (too much at once)

**Examples of one-at-a-time**:
- Pipeline naming (important decision)
- Complex pattern choices (needs explanation)
- Agent role definitions (each needs careful thought)
- Gate placement decisions (affects workflow structure)

### Handling User Uncertainty

**When users are unsure**, provide guidance rather than waiting:
- ✅ **Good**: "I see you're not sure about the pattern. Based on your use case, I'd suggest sequential flow because [reason]. Does that work, or would you prefer parallel execution?"
- ❌ **Bad**: "What pattern do you want?" → user says "I don't know" → "OK, let me know when you decide"

**Strategies for uncertainty**:
- **Provide examples**: Show 2-3 similar pipelines and explain why each might work
- **Make recommendations**: Analyze the use case and suggest the best option with reasoning
- **Offer to defer**: Allow users to skip optional sections and return later
- **Use progressive disclosure**: Start high-level, then drill down based on user responses

### Handling Interruptions

**When users interrupt or change direction**, adapt gracefully:
- ✅ **Good**: "I understand you want to change the agent list. Let me update what we have so far: [summary]. Now, what agents would you like instead?"
- ❌ **Bad**: "But we already discussed agents. Let's finish the current step first."

**Strategies for interruptions**:
- **Acknowledge the change**: "I see you want to modify [X]. Let me update our plan."
- **Summarize current state**: Briefly recap what's been decided so far
- **Resume from new point**: Continue from where the user wants to go
- **Save context**: Remember previous decisions that still apply

### Natural vs Robotic Patterns

**Natural conversation patterns**:
- ✅ "Based on your use case, I think we'll need about 3-4 agents. Let's start by identifying the main tasks..."
- ✅ "That makes sense! For a sequential flow like this, we typically need [X]. Does that align with what you're thinking?"
- ✅ "Great question! Let me explain how that works: [explanation]. Does that help clarify?"

**Robotic patterns to avoid**:
- ❌ "Step 1.3: Agent Identification. Please provide agent roles, inputs, and outputs."
- ❌ "According to the workflow, I need to ask about agents now."
- ❌ "You must provide all agent information before proceeding."

### Progressive Disclosure

**Start high-level, then drill down**:
1. **First**: "What problem does this pipeline solve?" (high-level)
2. **Then**: "What are the main steps to solve it?" (medium-level)
3. **Finally**: "For each step, what specific inputs and outputs are needed?" (detailed)

**Use examples to guide**:
- When user is unsure, reference similar existing pipelines
- Show patterns that worked for similar use cases
- Explain why certain patterns fit their needs

**Allow flexibility**:
- Users can skip optional sections and return later
- Users can change their minds and revise earlier decisions
- Don't force completion of every sub-step if user wants to move forward

## Step 1: Comprehensive Requirements Gathering

**🔍 CRITICAL**: This step collects ALL information needed before designing the workflow. Ask ALL questions in this section systematically before proceeding to design. Do NOT start designing until all requirements are collected and confirmed.

**Important Notes**:
- **Step 1 = COLLECT**: You are gathering information from the user
- **Step 2 = USE**: You will use the collected information to design the workflow
- If user doesn't know an answer, provide suggestions based on use case analysis
- If user gives partial information, ask follow-up questions to complete the picture
- If user provides conflicting information, ask for clarification before proceeding

**Progressive Disclosure Approach**:
- **Start high-level**: Begin with broad questions about the use case and overall goal
- **Drill down gradually**: Move from general to specific as you understand the use case better
- **Use examples**: When user is unsure, reference similar existing pipelines and explain why they might work
- **Offer to show patterns**: If user is uncertain about workflow patterns, offer to show examples from existing pipelines
- **Allow flexibility**: Users can skip optional sections (like icons) and return later if needed
- **Adapt to user knowledge**: If user is experienced, you can ask more technical questions. If new, provide more guidance

### 1.1 Basic Use Case Information

**Action**: Ask the user for basic information:

**Questions**:
1. **Use Case Description**: What problem does this pipeline solve? (Detailed description)
2. **Pipeline Name**: What should we call this pipeline? (Human-readable name)
3. **Pipeline Description**: What is the detailed purpose statement? (1-2 sentences)

**Additional Clarifying Questions** (if use case is vague):
- What is the primary goal of this pipeline?
- What inputs does the pipeline receive from users?
- What is the expected final output?
- Are there any specific requirements or constraints?
- Are there any existing agents or patterns we should reference?

### 1.1.1 Handle Incomplete Information

**If use case is vague or incomplete**:
- Ask clarifying questions before proceeding
- Don't make assumptions - ask user for clarification
- Provide examples of good use case descriptions:
  - Good: "A pipeline that analyzes customer support tickets, classifies them by priority, and generates response drafts"
  - Vague: "Something for customer support"
- Offer to pause and let user refine requirements if needed

### 1.1.2 Generate Pipeline ID

**Action**: Convert pipeline name to snake_case ID:
- Use slugify function: lowercase, replace spaces with underscores
- Remove special characters, keep only alphanumeric and underscores
- Example: "Email Summarizer" → "email_summarizer"
- Example: "Customer Support Analyzer" → "customer_support_analyzer"
- Verify ID doesn't conflict with existing pipelines in templates folder
- If conflict exists: Ask user for alternative name or append number (e.g., `email_summarizer_v2`)

**Naming Conventions**:
- **Pipeline ID**: snake_case, lowercase (e.g., `email_summarizer`)
- **Agent ID**: snake_case, lowercase, prefixed with pipeline ID (e.g., `email_summarizer_analyzer`)
- **Gate ID**: snake_case, lowercase, prefixed with pipeline ID (e.g., `email_summarizer_review`)
- **File Names**: Match IDs exactly (e.g., `email_summarizer_analyzer.yml`)
- **Icon Names**: Match IDs exactly (e.g., `email_summarizer_analyzer.svg`)

### 1.1.3 Agent Naming Convention & Prefix Confirmation

**🔍 CRITICAL**: All agents MUST be prefixed with the pipeline ID to avoid conflicts and ensure clarity.

**Action**: After generating pipeline ID, suggest and confirm the prefix with user:

1. **Suggest Prefix**: Based on pipeline ID, propose the prefix to use
   - Prefix is typically the same as pipeline ID
   - Example: Pipeline ID `contract_analyzer` → Prefix `contract_analyzer`
   - Example: Pipeline ID `email_summarizer` → Prefix `email_summarizer`

2. **Present to User**:
   - "Based on the pipeline ID `{pipeline_id}`, I suggest using `{pipeline_id}` as the prefix for all agents."
   - "This means all agent IDs will follow the pattern: `{pipeline_id}_{agent_role}`"
   - "For example: `{pipeline_id}_extractor`, `{pipeline_id}_analyzer`, etc."
   - "Does this prefix work for you, or would you prefer a different prefix?"

3. **Handle User Response**:
   - If user approves: Proceed with suggested prefix
   - If user suggests alternative: Use user's preferred prefix (but ensure it's still descriptive)
   - If user wants shorter prefix: Suggest shortened version (e.g., `contract` instead of `contract_analyzer`), but warn about potential conflicts

4. **Confirm Final Prefix**:
   - Document the confirmed prefix
   - Use this prefix consistently for all agents and gates in the pipeline
   - Note: Prefix should be snake_case, lowercase, and descriptive

**Pattern Analysis from Existing Pipelines**:
- ✅ **Consistent Prefixing**:
  - `article_smith` → `article_research_analyst`, `article_content_author`, `article_chief_editor`
  - `trip_planner` → `trip_requester`, `trip_flights_expert`, `trip_aggregator`
  - `appeal_grievance_processor` → `appeal_grievance_classifier`, `appeal_grievance_recommender`
  - `claim_processor` → `claim_document_extractor`, `claim_policy_validator`, `claim_email_drafter`
  - `math_compass` → `math_strategist`, `math_calculator`, `math_auditor`
  - `haiku_writers_room` → `haiku_form_expert`, `haiku_imagery_specialist`, `haiku_editor`
  - `stock_analysis` → `stock_research_analyst`, `stock_financial_analyst`, `stock_investment_advisor`
  - `reply_wizard` → `reply_context_wizard`, `reply_draft_wizard`, `reply_critique_wizard`

- ❌ **Inconsistent (Missing Prefix)**:
  - `legal_contract_analyzer` → `contract_classifier`, `key_terms_extractor` (should be `legal_contract_analyzer_classifier`, etc.)

**Naming Rules**:
1. **Agent ID Format**: `{pipeline_id}_{agent_role}`
   - Pipeline ID: `contract_analyzer`
   - Agent roles: `extractor`, `risk_analyzer`, `obligation_mapper`
   - Result: `contract_analyzer_extractor`, `contract_analyzer_risk_analyzer`, `contract_analyzer_obligation_mapper`

2. **Gate ID Format**: `{pipeline_id}_{gate_purpose}`
   - Pipeline ID: `contract_analyzer`
   - Gate purposes: `upload_contract`, `review_extraction`, `approve_risks`
   - Result: `contract_analyzer_upload_contract`, `contract_analyzer_review_extraction`, `contract_analyzer_approve_risks`

3. **Benefits of Prefixing**:
   - **Avoids conflicts**: Multiple pipelines can have agents with similar roles (e.g., `extractor` in different pipelines)
   - **Clear ownership**: Immediately identifies which pipeline an agent belongs to
   - **Namespace organization**: Groups related agents together
   - **Easier debugging**: Clear agent identification in logs and UI

4. **Agent Role Naming**:
   - Use descriptive, role-based names (e.g., `extractor`, `analyzer`, `validator`, `generator`)
   - Keep role names concise but clear
   - Avoid generic names like `agent1`, `processor`, `handler`
   - Use domain-specific terms when appropriate (e.g., `risk_analyzer` not just `analyzer`)

**Examples**:
- Pipeline: `contract_analyzer`
  - ✅ Good: `contract_analyzer_extractor`, `contract_analyzer_risk_analyzer`, `contract_analyzer_report_generator`
  - ❌ Bad: `extractor`, `risk_analyzer`, `contract_extractor` (missing or incomplete prefix)

- Pipeline: `email_summarizer`
  - ✅ Good: `email_summarizer_reader`, `email_summarizer_summarizer`, `email_summarizer_formatter`
  - ❌ Bad: `email_reader`, `summarizer`, `formatter` (missing or incomplete prefix)

**Action**: When generating agent IDs (after prefix confirmation):
1. Use the confirmed prefix (from Step 1.1.3)
2. Add underscore separator
3. Add agent role name
4. Verify full agent ID is unique and descriptive
5. Ensure all agents in the pipeline follow this pattern consistently

**Example Flow**:
- Pipeline ID: `contract_analyzer`
- Suggested Prefix: `contract_analyzer`
- User confirms: "Yes, that works"
- Agent IDs: `contract_analyzer_extractor`, `contract_analyzer_risk_analyzer`, etc.

**Alternative Flow**:
- Pipeline ID: `contract_analyzer`
- Suggested Prefix: `contract_analyzer`
- User suggests: "Can we use just `contract`?"
- AI response: "I can use `contract` as the prefix, but note that this might cause conflicts if you have multiple contract-related pipelines. Are you okay with that?"
- User confirms: "Yes, use `contract`"
- Agent IDs: `contract_extractor`, `contract_risk_analyzer`, etc.

### 1.2 Workflow Pattern Preferences

**Action**: Ask user about workflow pattern preferences BEFORE designing:

**If user is unsure**: First analyze the use case and suggest appropriate patterns, then ask for confirmation.

**Questions**:
1. **Execution Flow**: How should agents execute?
   - Sequential (one after another) - Default for dependent steps
   - Parallel (simultaneously) - For independent tasks
   - Repeat (same agent multiple times in parallel) - For processing multiple items
   - Enhanced Repeat (sequence of agents multiple times in parallel) - For processing multiple items through a pipeline
   - Mixed (some sequential, some parallel)
   - Conditional (branching based on conditions)
   - Group Chat (collaborative conversation)
   - Handoff (dynamic routing to specialists)
   - Loop (iterative refinement)

2. **Pattern Complexity**: What level of complexity?
   - Simple sequential flow
   - Sequential with some parallel steps
   - Complex nested patterns (sequential → parallel → conditional)
   - Special patterns (group chat, handoff)

3. **Reference Examples**: Would you like to see examples of similar patterns?
   - Show 2-3 relevant pipeline examples from templates
   - Explain why each pattern might work for this use case
   - Let user choose preferred pattern style

**Handling User Responses**:
- **If user knows**: Document their preferences directly
- **If user is unsure**: Analyze use case, suggest 2-3 appropriate patterns with explanations, then ask user to choose
- **If user says "you decide"**: Make recommendation based on use case analysis, explain reasoning, get confirmation
- **If user provides conflicting info**: Ask for clarification (e.g., "You mentioned sequential flow, but also mentioned parallel agents. Can you clarify?")

**Action**: After user responds:
- Document pattern preferences clearly
- Note any specific pattern requirements
- Reference similar pipelines if user wants examples
- If user is unsure, suggest patterns based on use case and show examples
- Resolve any conflicts before proceeding

### 1.3 Agent Identification & Responsibilities

**Action**: Ask user to identify agents needed:

**Questions**:
1. **Agent Roles**: What agents are needed? (List all)
   - For each agent: What is its specific role/responsibility?
   - What tasks will each agent perform?
   - What inputs does each agent need?
   - What outputs will each agent produce?

2. **Agent Dependencies**: Which agents depend on others?
   - Which agents can run independently (parallel)?
   - Which agents must wait for others (sequential)?
   - Are there any circular dependencies?

3. **Agent Count**: How many agents total?
   - If 5+ agents: Should we consider breaking into sub-pipelines?

**Handling User Responses**:
- **If user lists agents**: Document each with role, inputs, outputs
- **If user describes workflow steps**: Help identify agents from steps (e.g., "extract data" → extractor agent)
- **If user is unsure**: Suggest agent breakdown based on use case, then confirm
- **If dependencies unclear**: Ask clarifying questions about data flow between steps

**Action**: After collecting agent information:
- List all agents with roles, inputs, and outputs
- Document dependencies clearly
- Note which agents can run in parallel vs sequential (aligns with Step 1.2 pattern preferences)
- Use confirmed prefix from Step 1.1.3 for agent IDs (format: `{prefix}_{agent_role}`)
- If conflicts with Step 1.2 pattern preferences, ask for clarification

### 1.3.1 Agent ID Conflict Check

**🔍 CRITICAL**: After identifying all agents and applying the prefix, check for conflicts with existing agent files.

**Action**: For each agent ID (with prefix applied), check if agent config file already exists:

**Check Process**:
1. **Generate full agent IDs**: For each agent role, create full ID: `{confirmed_prefix}_{agent_role}`
2. **Check file existence**: For each agent ID, check if file exists:
   - Base: `{base_path}` → `config/agents/{agent_id}.yml`
3. **Identify conflicts**: List any agent IDs that conflict with existing files

**If conflicts found**:
- **Present conflicts to user**:
  - "I found that the following agent IDs conflict with existing agent files:"
  - List each conflicting agent ID and the existing file path
- **Ask user for resolution**:
  - "Would you like to:"
    - Option 1: "Use different agent role names to avoid conflicts?"
    - Option 2: "Use a different prefix to avoid conflicts?"
    - Option 3: "Overwrite existing files? (Not recommended unless intentional)"
- **Wait for user decision** before proceeding
- **If user chooses different names/prefix**: Update agent IDs, re-check for conflicts
- **If user chooses to overwrite**: Warn about overwriting, get explicit confirmation

**If no conflicts**:
- Document that all agent IDs are unique
- Proceed to next step

**Example Conflict Resolution**:
- Conflict: `contract_analyzer_extractor` already exists
- User chooses: "Use different role name"
- New ID: `contract_analyzer_document_extractor` (if available)
- Re-check: Verify new ID doesn't conflict

**Action**: After resolving conflicts (if any):
- Document final agent IDs
- Verify all agent IDs are unique and don't conflict
- Note in requirements summary that conflict check passed

### 1.4 Conditional Logic & Decision Points

**Action**: Ask about conditional logic needs:

**Questions**:
1. **Decision Points**: Are there any decision points in the workflow?
   - Does the workflow need to branch based on conditions?
   - Are there different paths based on input type/complexity?
   - Examples: Simple vs complex processing, different document types, user preferences

2. **Conditional Types**: What kind of conditionals?
   - Switch pattern (if/then/else based on agent output)
   - Conditional nodes/branches (run only if conditions met)
   - Conditional parallel (run some agents only if conditions met)
   - User-driven routing (selection gates determine path)
   - If-else pattern (`on_false` with alternative steps)
   - Stop action (`on_false: stop` to end pipeline gracefully)

3. **Conditional Variables**: What variables determine branching?
   - Agent output fields (e.g., `complexity_score > threshold`)
   - User selections (e.g., document type)
   - Input characteristics (e.g., file size, content type)
   - **Variable Syntax**: Conditions use the same variable syntax as agent inputs:
     - Explicit: `{{agent_id.field}}` (preferred, e.g., `coordinator.flights_ready == true`)
     - Simple: `{{field}}` (when field name is unique)
     - Supports expressions and filters (e.g., `contains(last_message, 'APPROVED')`)
   - **`on_false` Actions**: What should happen when condition is false?
     - Skip and continue (default)
     - Stop pipeline execution (`on_false: stop`)
     - Execute alternative steps (`on_false: [steps]` - if-else pattern)
     - Examples:
       - Stop if prerequisite not met: `on_false: stop`
       - Error handling branch: `on_false: [error_handler, cleanup, notify]`
       - Full alternative workflow: `on_false: { type: sequential, steps: [...] }`

**Action**: Document all conditional requirements before designing, including `on_false` behavior.

### 1.5 Human-in-the-Loop (HITL) Requirements

**Action**: Ask about HITL gate needs:

**Questions**:
1. **Approval Gates**: Where do you need human approval?
   - After which agent outputs?
   - Before which critical actions?
   - Quality checkpoints?

2. **Input Gates**: Where do you need user input?
   - File uploads (which stages?)
   - Form inputs (what information?)
   - Feedback collection (when?)

3. **Selection Gates**: Where do you need user selections?
   - Choosing between options (which decisions?)
   - Selecting from lists (what options?)
   - Editorial direction (what choices?)

4. **HITL Placement**: Where in the workflow?
   - At the start (file uploads)
   - Between agents (approvals)
   - After parallel agents (selection)
   - Before final output (review)

**Action**: Document all HITL requirements with:
- Gate type (approval/input/selection)
- Placement (after which agent)
- Purpose (what decision/input)
- Configuration details (fields, options, etc.)

### 1.6 MCP Tools & External Dependencies

**Action**: Ask about external tool needs:

**Questions**:
1. **File Processing**: Do any agents need to process files?
   - Which agent extracts files first? (Only ONE should extract)
   - Which agents use extracted data? (Should NOT re-extract)
   - File types expected? (PDF, DOCX, images, etc.)

2. **External Tools**: Do any agents need external tools?
   - Web search capabilities?
   - Database access?
   - Browser automation?
   - Document RAG queries?
   - Other MCP tools?

3. **Tool Justification**: For each tool request:
   - Why is this tool needed?
   - Can we use upstream agent output instead?
   - Is this the first agent extracting this file?

**Action**: Document tool requirements and ensure:
- Only first agent extracts each file
- Downstream agents reuse extracted data
- All tools are justified

**🔍 CRITICAL - Path Resolution for File/Database Operations**:
- **Agents using file/database MCP tools** (e.g., `sqlite_query`, `sqlite_execute`, `fs_listdir`, `fs_move_file`) **must** use `project_dir` to resolve absolute paths
- **Relative paths will fail** - MCP tools require absolute paths
- **Action**: When identifying agents that need file/database operations, note that they will need `project_dir` in their inputs (see Section 4.3.2 for details)

### 1.6.1 Local Tools (Pipeline-Specific Tools)

**Action**: Identify operations that should be implemented as pipeline-specific local tools.

**When to Use Local Tools** (Strongest Case):

✅ **Pipeline-specific business logic** that is:
- Tightly coupled to your data model (e.g., database schema, file formats)
- Deterministic and reproducible (e.g., calculations, validations, simulations)
- Requires strong correctness guarantees (e.g., billing calculations, data aggregations)
- Needs to be testable in isolation

✅ **Database operations** specific to your pipeline:
- Schema-aware queries (not generic SQL)
- Data validation against your schema
- Complex joins and aggregations specific to your domain
- Write operations that must follow your business rules

✅ **Domain-specific computations**:
- Billing calculations (e.g., tiered rates, time-of-use pricing)
- Statistical aggregations (e.g., customer segments, equity metrics)
- Data transformations specific to your use case

**When NOT to Use Local Tools**:

❌ Generic operations (use MCP tools instead):
- Generic SQL queries → Use `sqlite_query` MCP tool
- Generic file operations → Use `fs_*` MCP tools
- External API calls → Use MCP tools or external services

❌ Simple prompt-only logic:
- Text generation, summarization → Let LLM handle it
- Simple data formatting → Use prompt engineering

**Questions to Ask**:

1. **Database Operations**: Do agents need to read/write to a pipeline-specific database?
   - What tables/schema?
   - What operations? (queries, validations, aggregations, writes)
   - Are these operations schema-aware and domain-specific?

2. **Business Logic**: Are there deterministic computations needed?
   - Billing calculations?
   - Statistical aggregations?
   - Data validations?
   - Simulations?

3. **Tool Design**: For each identified need:
   - What should the tool be named? (e.g., `rate_case_validate_and_summarize`)
   - What parameters does it need? (e.g., `db_file`, `target_state`)
   - What does it return? (structured data)
   - Which agents will use it?

**Action**: Document local tool requirements:
- List of tools needed
- Toolkit name (e.g., `rate_case`, `claims`, `invoice`)
- Module path (e.g., `tools.rate_case_filing_navigator.rate_case_tools`)
- Which agents will use each tool

**Example from Rate Case Pipeline**:

```python
# File: tools/rate_case_filing_navigator/rate_case_tools.py

from topaz_agent_kit.local_tools.registry import pipeline_tool
from typing import Dict, Any, Optional

@pipeline_tool(toolkit="rate_case", name="rate_case_validate_and_summarize")
def rate_case_validate_and_summarize(
    db_file: str,
    target_state: str
) -> Dict[str, Any]:
    """Validate database schema and summarize data for a target state.
    
    Args:
        db_file: Absolute path to SQLite database file
        target_state: Full state name (e.g., "California")
    
    Returns:
        Dictionary with validation results and data summary
    """
    # Implementation: schema validation, data aggregation, etc.
    ...
```

**Agent Configuration** (will be generated in Step 4.2):

```yaml
# config/agents/rate_case_data_summarizer.yml
local_tools:
  modules:
    - tools.rate_case_filing_navigator.rate_case_tools
  toolkits: ["rate_case"]
  tools: ["rate_case.*"]  # Pattern matching all rate_case tools
```

**Key Points**:
- Local tools are **automatically adapted** for all frameworks (CrewAI, LangGraph, SK, OAK, ADK, MAF) via `FrameworkToolAdapter`
- Tools are **discovered** from modules at runtime
- Tools are **filtered** by toolkit and pattern matching
- Same tools work across **all agent frameworks** without modification

**Action**: After identifying local tool needs, propose:
1. Toolkit name (e.g., `rate_case`, `claims`, `invoice`)
2. Module path structure (e.g., `tools/{pipeline_id}/{module_name}.py`)
3. List of tool functions with signatures
4. Which agents will use which tools

**Reference**: See `projects/ensemble/tools/rate_case_filing_navigator/rate_case_tools.py` for a complete example.

### 1.7 Output Requirements

**Action**: Ask about output structure:

**Questions**:
1. **Final Output**: What is the final output?
   - Which agent produces the final output?
   - What fields should be included?
   - What format? (JSON, markdown, text)

2. **Intermediate Outputs**: Do you need intermediate outputs?
   - Which agent outputs should be captured?
   - For debugging, review, or downstream use?
   - What fields from each output?

3. **Output Transformations**: Do outputs need transformation?
   - Format conversions?
   - Data restructuring?
   - Value transformations?

**Action**: Document output requirements:
- Final output structure
- Intermediate outputs needed
- Transformations required

### 1.8 Icon & Visual Preferences

**Action**: Ask about icon preferences:

**Note**: Icons can be deferred to Step 4.5 (after agents are finalized) if user prefers. Ask if they want to handle icons now or later.

**Questions**:
1. **Icon Style**: Do you have icon preferences?
   - Lucide icons (default, recommended)
   - Specific icon names you prefer?
   - Visual style preferences? (minimal, detailed, etc.)
   - **Option**: "Would you like to select icons now, or defer to after we finalize the agent list?"

2. **Pipeline Icon**: What icon represents the overall pipeline?
   - Suggest 2-3 options from Lucide
   - Show links to icons on lucide.dev
   - Get user preference
   - **If deferred**: Note that icons will be selected in Step 4.5

3. **Agent Icons**: For each agent role identified:
   - Suggest 2-3 icon options per agent
   - Show links and explanations
   - Get user preferences
   - **If deferred**: Note that icons will be selected in Step 4.5 after agents are finalized

**Handling User Responses**:
- **If user wants to select now**: Collect all icon preferences, document them
- **If user wants to defer**: Note "Icons deferred to Step 4.5" and proceed
- **If user is unsure**: Suggest deferring to Step 4.5 when agent roles are finalized

**Action**: After user responds:
- If icons selected: Document all icon selections, note Lucide icon names, provide links
- If deferred: Note "Icons will be selected in Step 4.5" in requirements summary

### 1.9 Protocol & Remote Execution Preferences

**Action**: Ask about protocol preferences:

**Questions**:
1. **Protocol Selection**: All remote agents use A2A protocol
   - Default: A2A for all remote agents
   - Local agents automatically use IN-PROC

2. **Remote Execution**: Will any agents run remotely initially?
   - Which agents will run remotely? (If any)
   - What protocols? (A2A for remote, IN-PROC for local)
   - **Note**: Remote configuration will be added to ALL agents regardless, so they can be switched from local to remote later without code changes.

**Action**: Document protocol and remote preferences.

**Important**: Even if agents run locally initially, remote configuration will be included for all agents to allow easy switching between local and remote execution later.

### 1.10 Additional Requirements

**Action**: Ask about any other requirements:

**Questions**:
1. **Special Requirements**: Any other requirements?
   - Retry logic needed?
   - Error handling preferences?
   - Performance considerations?
   - Security requirements?

2. **Existing References**: Any existing pipelines/agents to reference?
   - Similar use cases?
   - Patterns to follow?
   - Code examples?

**Action**: Document any additional requirements.

### 1.11 Requirements Summary & Review

**🔍 REVIEW CHECKPOINT**: Present complete requirements summary:

**Action**: Before presenting summary, validate completeness using this checklist:

**Requirements Completeness Checklist**:
- [ ] Pipeline name, ID, and description collected
- [ ] Agent prefix confirmed
- [ ] Workflow pattern preferences documented (or user confirmed AI suggestion)
- [ ] All agents identified with roles, inputs, outputs
- [ ] Agent IDs generated with prefix (format: `{prefix}_{agent_role}`)
- [ ] **Agent ID conflict check passed** (no conflicts with existing agent files)
- [ ] Agent dependencies documented (parallel vs sequential)
- [ ] Conditional logic requirements documented (if any)
- [ ] HITL gate requirements documented (if any)
- [ ] MCP tool requirements documented (if any)
- [ ] Output requirements documented
- [ ] Icon preferences collected (or deferred to Step 4.5)
- [ ] Protocol preferences documented (if any)
- [ ] Additional requirements documented (if any)

**If any item is missing**:
- Ask user for missing information before proceeding
- If user wants to defer (e.g., icons), note it and proceed
- If critical item missing (e.g., agents), don't proceed until collected

**Action**: Compile and present all collected information using this structured template:

**Requirements Summary Template**:

1. **Use Case Summary**:
   - **Pipeline Name**: {name}
   - **Pipeline ID**: {id}
   - **Pipeline Description**: {description}
   - **Confirmed Prefix**: {prefix}

2. **Workflow Preferences**:
   - **Pattern Type**: {sequential/parallel/conditional/etc.}
   - **Pattern Complexity**: {simple/complex/nested}
   - **Execution Flow**: {description}

3. **Agents Summary**:
   - **Total Agents**: {count}
   - For each agent:
     - **Role**: {role}
     - **Inputs**: {inputs}
     - **Outputs**: {outputs}
     - **Dependencies**: {upstream agents}
     - **Can Run in Parallel**: {yes/no}

4. **Conditional Logic** (if any):
   - **Decision Points**: {list}
   - **Conditional Types**: {types}
   - **Variables**: {variables}

5. **HITL Gates** (if any):
   - For each gate:
     - **Type**: {approval/input/selection}
     - **Placement**: {after which agent}
     - **Purpose**: {description}

6. **MCP Tools**:
   - **File Processing**: {which agent extracts first}
   - **External Tools**: {list by agent}
   - **Tool Justification**: {brief notes}

7. **Outputs**:
   - **Final Output**: {agent, fields, format}
   - **Intermediate Outputs**: {list if any}
   - **Transformations**: {if any}

8. **Icons**:
   - **Pipeline Icon**: {selected or deferred}
   - **Agent Icons**: {selected or deferred}

9. **Protocols**:
   - **Protocol Preferences**: A2A for remote agents
   - **Remote Execution**: {if any}

10. **Additional Requirements**:
    - {any special requirements}

**Action**: Present summary using the template above, then ask user:
- "Does this requirements summary look complete and correct?"
- "Are there any missing requirements or changes needed?"
- "Should we proceed to workflow design with these requirements?"

**Handling User Responses**:
- **If user approves**: Proceed to Step 2
- **If user wants changes**: Make changes, update summary, ask for approval again
- **If user identifies missing info**: Collect missing information, update summary, ask for approval again
- **If user wants major changes**: Note that major changes can also be made in Step 3 (refinement), but it's better to fix now

**Wait for user approval before proceeding to Step 1.12.**

### 1.12 Mock Data Requirements & Script Generation

**🔍 CRITICAL CHECKPOINT**: Before designing the workflow, determine what mock data is needed. This ensures:
- Agents are designed with knowledge of actual data structure
- Database schema is defined before agent prompts are written
- Data fields are known when designing agent inputs/outputs
- Pipeline can be tested immediately after generation

**Action**: After requirements are finalized, check with user about mock data needs:

**Questions to Ask**:
1. "Does this pipeline require mock data for testing and development?"
2. "What type of data does the pipeline need to process?"
   - Database records (SQLite, PostgreSQL, etc.)
   - Document files (PDFs, text files, images, etc.)
   - API response data
   - Structured data files (JSON, CSV, etc.)
   - Other data types
3. "What data structure/schema is needed?"
   - Database tables and relationships
   - Document formats and fields
   - Data relationships and dependencies

**If user confirms mock data is needed**:

#### 1.12.1 Identify Data Requirements

**Action**: Work with user to finalize mock data requirements:

1. **Database Schema** (if applicable):
   - What tables are needed?
   - What are the table relationships?
   - What fields does each table have?
   - What indexes are needed?
   - What are realistic sample values?

2. **Document Files** (if applicable):
   - What document types are needed? (PDFs, text files, images, etc.)
   - What content should documents contain?
   - What fields/data should be extractable from documents?
   - How many sample documents are needed?

3. **Data Relationships**:
   - How do different data types relate?
   - What foreign key relationships exist?
   - What data dependencies need to be maintained?

4. **Data Volume**:
   - How many records/documents should be generated?
   - What are reasonable default counts?
   - Should counts be configurable?

5. **Data Paths**:
   - Where should database be stored? (default: `projects/ensemble/data/{pipeline_id}/`)
   - Where should documents be stored? (default: `projects/ensemble/data/{pipeline_id}/documents/`)
   - Are there subdirectories needed?

**Action**: Document all requirements clearly:
- Create a data requirements summary
- Show user the proposed data structure
- Get user approval on data requirements before generating script

#### 1.12.2 Reference Example Scripts

**Action**: Show user example scripts to understand the pattern:

**Example Scripts Available**:
1. **ECI Claims Database** (`src/topaz_agent_kit/scripts/setup_eci_database.py`):
   - Creates SQLite database with multiple related tables
   - Generates mock claims, voyages, buyers with relationships
   - Creates PDF documents (claim forms, invoices, bills of lading)
   - Uses `resolve_script_path()` for path resolution
   - Includes `--reset` flag for database recreation
   - Configurable counts for different claim types

2. **AG Database** (`src/topaz_agent_kit/scripts/setup_ag_database.py`):
   - Creates database with schema
   - Generates mock members and emails
   - Handles optional email sending
   - Includes reset and count parameters

3. **Invoice Match Database** (`src/topaz_agent_kit/scripts/setup_invoice_match_db.py`):
   - Creates database with POs, SOWs, invoices
   - Generates PDF invoices
   - Handles file output directories

**Action**: Explain to user:
- "I'll create a similar script for your pipeline based on these examples"
- "The script will follow the same patterns and conventions"
- "You can test the script before we proceed with pipeline generation"

#### 1.12.3 Generate Mock Data Script

**Action**: Create the mock data setup script:

**File Location**: `src/topaz_agent_kit/scripts/setup_{pipeline_id}_database.py` (or appropriate name)

**Template Structure**:
```python
#!/usr/bin/env python3
"""Setup script for {Pipeline Name} pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- {List of data types}
- {List of tables/documents}

Usage:
    python scripts/setup_{pipeline_id}_database.py [--db-path <path>] [--output-dir <dir>] [--reset] [--count <n>]
    uv run -m scripts.setup_{pipeline_id}_database --db-path projects/ensemble/data/{pipeline_id}/{pipeline_id}_database.db --reset
"""

import sqlite3
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name

def create_database_schema(db_path: str) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables based on requirements
    # ... schema creation code ...
    
    conn.commit()
    conn.close()
    print("✓ Database schema created")

def generate_mock_data(cursor, count: int) -> List[Dict[str, Any]]:
    """Generate mock data."""
    # ... data generation code ...
    pass

def main():
    parser = argparse.ArgumentParser(description="Setup {Pipeline Name} database and mock data")
    parser.add_argument(
        "--db-path",
        type=str,
        default="projects/ensemble/data/{pipeline_id}/{pipeline_id}_database.db",
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/ensemble/data/{pipeline_id}/documents",
        help="Output directory for generated files"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and recreate (WARNING: deletes all data)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of mock records to generate"
    )
    
    args = parser.parse_args()
    
    # Detect project name for path resolution
    project_name = detect_project_name(Path.cwd())
    
    # Resolve paths intelligently (works from repo root or project_dir)
    db_path = resolve_script_path(args.db_path, project_name=project_name)
    output_dir = resolve_script_path(args.output_dir, project_name=project_name)
    
    # Create directories
    db_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ... rest of script logic ...
    
    print("✓ Setup complete!")

if __name__ == "__main__":
    main()
```

**Key Requirements**:
- ✅ Use `resolve_script_path()` and `detect_project_name()` from `topaz_agent_kit.utils.path_resolver`
- ✅ Default paths relative to repository root (e.g., `projects/ensemble/data/{pipeline_id}/...`)
- ✅ Include `--reset` flag to drop and recreate tables
- ✅ Include `--db-path` and `--output-dir` arguments with sensible defaults
- ✅ Include count/quantity arguments for mock data generation
- ✅ Create database schema with proper tables, relationships, and indexes
- ✅ Generate realistic mock data that matches use case requirements
- ✅ Handle optional dependencies gracefully (e.g., reportlab for PDFs)
- ✅ Provide clear progress output during execution

#### 1.12.4 Register Script in scripts.yml

**Action**: Add script entry to registry:

**File**: `src/topaz_agent_kit/scripts/scripts.yml`

**Add entry**:
```yaml
- filename: "setup_{pipeline_id}_database.py"
  name: "Setup {Pipeline Name} Database"
  description: "Initializes the {Pipeline Name} database and generates mock data"
  category: "Setup"
  parameters:
    - name: "db-path"
      description: "Path to SQLite database file"
      type: "string"
      default: "projects/ensemble/data/{pipeline_id}/{pipeline_id}_database.db"
      required: false
    - name: "output-dir"
      description: "Directory for generated documents/files"
      type: "string"
      default: "projects/ensemble/data/{pipeline_id}/documents"
      required: false
    - name: "reset"
      description: "Reset database (drop existing tables)"
      type: "flag"
      default: "false"
      required: false
    - name: "count"
      description: "Number of mock records to generate"
      type: "integer"
      default: "10"
      required: false
```

**Action**: Show user:
- The script file that was created
- The scripts.yml entry that was added
- Explain that the script will be available in the Scripts tab in the UI

#### 1.12.5 User Testing & Validation

**🔍 CRITICAL CHECKPOINT**: User must test the script before proceeding.

**Action**: Ask user to test the script:
1. "I've created the mock data setup script. Please test it:"
   - "You can run it from the Scripts tab in the UI, or"
   - "Run it directly: `python src/topaz_agent_kit/scripts/setup_{pipeline_id}_database.py --reset`"
2. "After running the script, please verify:"
   - "Database was created with correct schema"
   - "Mock data was generated as expected"
   - "All required files/documents were created"
   - "Data structure matches your requirements"
3. "Does the generated data look correct?"
4. "Are there any changes needed to the data structure or script?"

**If user reports issues**:
- Fix the script based on feedback
- Update data structure if needed
- Re-test until user confirms it works correctly

**If user confirms script works**:
- Note: "Mock data script tested and validated"
- Proceed to Step 2 (Workflow Design)

**If user doesn't need mock data**:
- Note: "Mock data script generation skipped - no mock data needed for this pipeline"
- Proceed directly to Step 2 (Workflow Design)

**⚠️ IMPORTANT**: Do NOT proceed to Step 2 (Workflow Design) until:
- Mock data script is created (if needed)
- Script has been tested by user
- User confirms data structure is correct
- OR user confirms no mock data is needed

**Action**: After mock data is finalized:
- Document the data structure in requirements summary
- Note data fields that agents will need to access
- Proceed to Step 2 with complete data structure knowledge

## Step 2: Workflow Design & Proposal

**Action**: Now that ALL requirements are collected (from Step 1), design the complete workflow using the gathered information.

**🔍 CRITICAL**: Step 2 USES the information collected in Step 1. You are NOT collecting new information here - you are designing based on what was already collected.

### 2.1 Agent Identification & Finalization

**Action**: Use the agent information collected in Step 1.3 to finalize agent list:

**Important**: 
- **USE** the confirmed prefix from Step 1.1.3 when generating agent IDs
- **USE** agent roles, inputs, outputs from Step 1.3
- **USE** dependencies and parallel/sequential preferences from Step 1.3
- **REFERENCE** MCP tool requirements from Step 1.6
- **REFERENCE** protocol preferences from Step 1.9

**What to do here**:
- Finalize agent IDs using format: `{confirmed_prefix}_{agent_role}` (from Step 1.1.3)
- Use agent roles already collected in Step 1.3
- Use inputs/outputs already documented in Step 1.3
- Apply MCP tool requirements from Step 1.6
- Apply protocol preferences from Step 1.9

**What NOT to do**:
- Don't ask user for agent information again (already collected in Step 1.3)
- Don't ask user for MCP tools again (already collected in Step 1.6)
- Don't ask user for protocol preferences again (already collected in Step 1.9)

**Finalize for each agent**:
- **Agent ID**: snake_case identifier with confirmed prefix (e.g., `contract_analyzer_extractor` not just `extractor`)
- **Agent Role**: Use role from Step 1.3
- **Inputs**: Use inputs from Step 1.3
- **Outputs**: Use outputs from Step 1.3 (define JSON structure)
- **MCP Tools**: Use requirements from Step 1.6
- **Remote Configuration**: Add remote config to ALL agents (use Step 1.9 preferences for run_mode and protocols)

**Guidelines**:
- Each agent should have a single, clear responsibility
- Agent IDs MUST use the confirmed prefix: `{confirmed_prefix}_{agent_role}`
- Agent names should be descriptive and follow naming conventions
- Consider if agents can run in parallel (independent tasks)
- Consider if agents need sequential execution (dependencies)

**Example** (with confirmed prefix `contract_analyzer`):
- ✅ Good: `contract_analyzer_extractor`, `contract_analyzer_risk_analyzer`, `contract_analyzer_report_generator`
- ❌ Bad: `extractor`, `risk_analyzer`, `contract_extractor` (missing or incomplete prefix)

### 2.1.1 Protocol Selection (A2A)

**Guidelines for protocol selection**:
- **A2A (Agent-to-Agent)**: Use for standard agent communication (default and only remote protocol)
- **IN-PROC**: Use for local in-process execution (automatic for local agents)
- **Default**: All remote agents use `a2a` protocol
- **Consistency**: All remote agents in a workflow use `a2a` protocol

**Decision Criteria**:
- Remote agents → Always use `a2a`
- Local agents → Automatically use `in-proc` (no protocol suffix needed)

### 2.1.2 MCP Tool Requirements Analysis

**Action**: Use the MCP tool requirements collected in Step 1.6 to configure tools for each agent:

**Important**: This section USES the information from Step 1.6. Don't ask user again - apply what was already collected.

**🔍 CRITICAL**: Avoid duplicate file extraction - only ONE agent should extract each file.

**Common MCP Tool Needs**:
- **Web Search**: Agent needs to search the web → `search.*` toolkit
- **File Operations**: Agent needs to read/write files → `filesystem.*` toolkit
- **Database Access**: Agent needs database queries → `database.*` toolkit
- **Browser Automation**: Agent needs web scraping → `browser.*` toolkit
- **Document Extraction**: Agent needs to extract structured data from documents → `doc_extract.*` toolkit
- **Document RAG**: Agent needs to query document content → `doc_rag.*` toolkit
- **No External Tools**: Agent only uses LLM → No MCP config needed

**File Extraction Pattern** (CRITICAL):
- **First agent** (document extractor) should use `doc_extract.*` tools to extract file content
- **Downstream agents** should NOT re-extract the same file
- **Downstream agents** should use extracted data from upstream agent output (top-level variables)
- **Example**: 
  - `claim_document_extractor` uses `doc_extract.*` to extract claim details
  - `claim_policy_validator` uses `{{claim_details}}` (from upstream) and `doc_rag.*` for policy queries
  - `claim_policy_validator` does NOT use `doc_extract.*` on the same file

**MCP Tool Justification Checklist**:
- [ ] Does this agent need external tools? (If no, skip MCP config)
- [ ] If file extraction needed: Is this the FIRST agent that extracts this file?
- [ ] If not first: Can this agent use extracted data from upstream agent instead?
- [ ] Are the tools actually necessary for the agent's role?
- [ ] Will using these tools improve the agent's output quality?

**Process**:
1. Review agent's role and responsibilities
2. Determine if agent needs external capabilities
3. **For file/document processing**: Check if file was already extracted by upstream agent
4. **If file already extracted**: Use extracted data from upstream, don't re-extract
5. Reference available MCP servers in project configuration
6. Only add MCP config if tools are actually needed and justified
7. Document which tools each agent will use and why

**Examples**:
- **Document Extractor** (first agent) → Needs `doc_extract.*` tools ✅
- **Document Analyzer** (downstream) → Uses extracted data from upstream, may need `doc_rag.*` for queries ✅
- **Document Analyzer** (downstream) → Re-extracts same file with `doc_extract.*` ❌ WRONG
- **Research agent** → Needs `search.*` tools ✅
- **Content writer** → No external tools needed ✅

**Best Practices**:
- **Single extraction**: Extract each file/document only once (first agent)
- **Reuse data**: Downstream agents use extracted structured data
- **Justify tools**: Every MCP tool must have a clear purpose
- **Avoid redundancy**: Don't give multiple agents the same extraction tools for the same file

### 2.2 Workflow Pattern Design

**Action**: Design workflow pattern using preferences collected in Step 1.2.

**Important**: 
- **USE** the pattern preferences from Step 1.2
- **USE** the conditional logic requirements from Step 1.4
- **USE** the agent dependencies from Step 1.3
- If user provided specific pattern preference, use that as the base
- If user asked for suggestions, review patterns and recommend

### 2.2.0 Review Available Patterns (If Needed)

**When to review patterns**:
- If user asked for examples in Step 1.2
- If user was unsure about pattern choice in Step 1.2
- If pattern from Step 1.2 needs refinement or examples

**If user already chose pattern in Step 1.2**: Skip detailed review, but reference similar patterns for implementation details.

**🔍 CRITICAL STEP**: If reviewing patterns, review available pipeline patterns in the templates folder to understand what patterns work well for different use cases.

**Action**: Review all pipeline patterns in: Base: `{base_path}` → `config/pipelines/`

**Available Pipeline Patterns to Review**:

1. **Sequential Patterns**:
   - `reply_wizard.yml` - Simple sequential flow: context → draft → critique → polish
   - `math_compass.yml` - Sequential with conditional switch based on complexity
   - `stock_analysis.yml` - Sequential research flow with multiple analysis steps

2. **Parallel Patterns**:
   - `article_smith.yml` - Sequential base with nested parallel critique agents (content + format critiques run simultaneously)
   - `haiku_writers_room.yml` - Group chat pattern with collaborative specialist agents

3. **Repeat Patterns**:
   - **Single Agent Repeat**: Run the same agent multiple times in parallel
     - Each instance processes a different item from a list (e.g., multiple problems)
     - Use `node:` field to specify the agent to repeat
   - **Enhanced Repeat (Nested Sequential)**: Run a sequence of agents multiple times in parallel
     - Each instance processes one item through the complete sequence
     - Use `type: sequential` with `steps:` inside `repeat:` block
     - Enables true parallelization: instances don't wait for each other
     - Can nest single-agent repeat patterns inside the sequence
   - Instance count can be static or dynamic (evaluated from upstream agent output)
   - Each instance gets unique ID for proper result storage and MCP cleanup

3. **Conditional/Switch Patterns**:
   - `trip_planner.yml` - Conditional parallel execution based on flags (flights/hotels/activities based on readiness)
   - `math_compass.yml` - Switch pattern based on problem complexity (simple vs complex routing)
   - `translator.yml` - Handoff pattern with conditional routing to language-specific agents

4. **Complex Nested Patterns**:
   - `trip_planner.yml` - Sequential → Conditional → Parallel → Sequential (coordinator → conditional parallel experts → aggregator)
   - `article_smith.yml` - Sequential → Gate → Sequential → Parallel → Gate → Sequential (research → approval → draft → parallel critiques → selection → editor)

5. **Special Patterns**:
   - `haiku_writers_room.yml` - Group chat pattern (collaborative conversation with round-robin or LLM selection)
   - `translator.yml` - Handoff pattern (LLM-driven routing to specialists)

**Pattern Analysis Process**:
1. **Read each pipeline config** to understand:
   - What use case it solves
   - What pattern structure it uses
   - How gates are integrated
   - How conditionals are used
   - How parallel execution is structured
   - What makes the pattern effective for that use case

2. **Identify similar use cases**:
   - Find pipelines with similar domain or flow characteristics
   - Note which patterns work well for similar problems
   - Understand why certain patterns were chosen over alternatives

3. **Extract pattern insights**:
   - **When is sequential appropriate?** (dependent steps, linear flow, simple workflows)
   - **When does parallel make sense?** (independent tasks, performance optimization, concurrent analysis)
   - **When are conditionals needed?** (routing decisions, complexity-based branching, feature flags)
   - **How are gates integrated effectively?** (approval points, input collection, selection decisions)
   - **When to use group chat?** (collaborative tasks, iterative refinement, multi-agent discussion)
   - **When to use handoff?** (dynamic routing, specialist selection, LLM-driven decisions)

4. **Compare with current use case**:
   - Which patterns match the current use case characteristics?
   - What can be learned from similar pipelines?
   - What pattern variations might work?
   - Are there unique requirements that need custom pattern?

**Action**: After reviewing patterns, document findings:
- List 2-3 most relevant patterns for the current use case
- Explain why each pattern is relevant
- Note specific pattern elements that could be applied
- Identify any unique requirements that need custom approach

**Present pattern analysis to user**:
- "I've reviewed all available pipeline patterns. Here are the most relevant ones for your use case:"
- For each relevant pattern:
  - Pipeline name and use case
  - Pattern structure description
  - Why it's relevant
  - What can be learned from it
- Propose recommended pattern structure based on analysis
- Ask: "Does this pattern analysis make sense? Should we use a similar pattern or adapt it?"

**Wait for user feedback** before finalizing pattern design.

### 2.2.1 Design Execution Pattern

**Action**: Design the execution pattern using:
- Pattern preferences from Step 1.2
- Agent dependencies from Step 1.3
- Conditional logic requirements from Step 1.4
- Pattern examples reviewed (if Step 2.2.0 was executed)

**Pattern Types Available**:
- **Sequential**: Agents run one after another (default for dependent steps)
- **Parallel**: Agents run concurrently (use when agents are independent)
- **Repeat**: Same agent runs multiple times in parallel with different inputs (use for processing multiple items)
- **Loop**: Repeat a step until condition met (use for iterative refinement)
  - **Numeric Loop**: Use `max_iterations` with optional `termination.condition` for traditional loops
  - **List Iteration**: Use `iterate_over` to iterate over a list/array from a previous agent (e.g., `"scanner.pending_items"`)
- **Conditional/Switch**: Branch based on conditions (use for decision points)
- **Group Chat**: Collaborative conversation pattern (use for iterative collaboration)
- **Handoff**: LLM-driven routing to specialists (use for dynamic specialist selection)

**Pattern Structure**:
- Start with sequential pattern as base (most common)
- Identify parallel opportunities (agents that can run simultaneously)
- Identify conditional branches (if/then scenarios, routing decisions)
- Identify loops (iterative refinement needs):
  - **List-based iteration**: If an agent produces a list/array, use `iterate_over` pattern
  - **Condition-based iteration**: If iteration depends on runtime conditions, use numeric loop with `max_iterations`
- Consider switch patterns for routing decisions
- Consider group chat for collaborative tasks
- Consider handoff for dynamic specialist routing

**List Iteration Pattern (iterate_over) - When to Use**:
- An agent produces a list/array of items to process (e.g., `scanner.pending_claims_list`)
- You want to process each item through the same sequence of steps
- You want automatic termination when the list is exhausted
- Example: Processing pending claims, files, emails, orders from a queue

**List Iteration Example**:
```yaml
- type: loop
  condition: "scanner.total_count > 0"  # Optional: skip if list is empty
  iterate_over: "scanner.items_list"    # Path to the list
  loop_item_key: "current_item"         # Context key (default: "loop_item")
  termination:
    max_iterations: 100  # Optional: safety limit
  body:
    type: sequential
    steps:
      - node: processor  # Accesses current_item.field_name
```

### 2.2.2 Dependency Validation

**Action**: Before finalizing workflow, validate dependencies:

**Validation Checks**:
1. **Circular Dependencies**: Check for cycles (Agent A → Agent B → Agent A)
   - If found: Redesign workflow to break the cycle
   - Solution: Add intermediate agent or restructure flow

2. **Missing Dependencies**: Verify all referenced agents exist
   - Check `retry_target` points to valid agent
   - Check upstream agents referenced in prompts exist
   - Check gate actions reference valid agents

3. **Orphaned Agents**: Ensure all agents are used
   - All agents in nodes registry must appear in pattern
   - If agent not used: Ask user if it should be removed or added to pattern

4. **Dependency Chain**: Verify data flow makes sense
   - Each agent's inputs should be available from upstream agents or user
   - Check that context variables match actual agent outputs

**Action**: Present dependency analysis to user:
- Show agent dependency graph
- Highlight any issues found
- Get user confirmation before proceeding

### 2.2.3 Complex Workflow Considerations

**For workflows with 5+ agents**:
- Consider breaking into sub-pipelines if logical separation exists
- Use clear agent naming to avoid confusion
- Document agent dependencies clearly in proposal
- Consider using intermediate outputs for debugging
- Simplify pattern structure when possible (avoid deep nesting)
- Ask user if workflow complexity is necessary or can be simplified

**Sequential with Nested Parallel** (from `article_smith.yml`):
```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - gate: approval_gate
    - node: agent2
    - type: parallel  # Nested parallel pattern
      steps:
        - node: agent3
        - node: agent4
    - node: agent5
```

**Conditional Parallel** (from `trip_planner.yml`):
```yaml
pattern:
  type: sequential
  steps:
    - node: coordinator
    - type: parallel
      steps:
        - type: sequential
          condition: "coordinator.flights_ready == true"
          steps:
            - node: flights_expert
            - gate: select_flights
        - type: sequential
          condition: "coordinator.hotels_ready == true"
          steps:
            - node: hotels_expert
            - gate: select_hotels
```

**Switch Pattern** (from `math_compass.yml`):
```yaml
pattern:
  type: sequential
  steps:
    - node: strategist
    - type: switch(len(strategist.steps) > 2)
      cases:
        false:  # Simple path
          - node: calculator
        true:   # Complex path
          - node: calculator
          - node: auditor
```

**Group Chat Pattern** (from `haiku_writers_room.yml`):
```yaml
pattern:
  type: group_chat
  participants:
    - node: expert1
    - node: expert2
    - node: editor
  selection_strategy: round_robin
  termination:
    max_rounds: 9
    condition: "contains(last_message, 'APPROVED')"
```

**Handoff Pattern** (from `translator.yml`):
```yaml
pattern:
  type: handoff
  handoffs:
    - node: specialist_a
    - node: specialist_b
    - node: specialist_c
```

### 2.3 HITL Gates Design

**Action**: Use HITL requirements collected in Step 1.5 to place gates:

**Important**: 
- **USE** the HITL gate requirements from Step 1.5
- **USE** gate types, placement, and configuration already documented
- Don't ask user for HITL information again - apply what was collected

**Gate Types**:
- **Approval**: Simple approve/reject (e.g., review research before proceeding)
- **Input**: Collect structured input from user (e.g., feedback form, file uploads)
- **Selection**: User selects from predefined options (e.g., editorial direction)

### 2.3.0 HITL Gate Types and Usage Patterns

**🔍 CRITICAL**: Review existing pipelines to understand HITL gate patterns before designing gates.

**Reference Examples**:
- `article_smith.yml` - Approval gates after research, input gate for feedback, selection gate for edit type
- `appeal_grievance_processor.yml` - Input gates for file uploads at multiple stages
- `claim_processor.yml` - Approval gate before final email generation
- `trip_planner.yml` - Selection gates for choosing flights/hotels/activities

### 2.3.0.1 Approval Gates

**When to Use**:
- **After critical agent outputs** that need human verification before proceeding
- **Before irreversible actions** (e.g., sending emails, making decisions)
- **Quality checkpoints** where human review improves accuracy
- **Risk mitigation** points where errors would be costly

**Common Patterns**:
- After research/analysis agents (verify findings)
- After content generation (review before publishing)
- Before final output generation (approve draft)

**Placement in Patterns**:
- **Sequential**: After agent completes → Gate → Next agent
- **Parallel**: After parallel agents complete → Gate → Next step
- **Conditional**: After decision point → Gate → Branch

**Dynamic Descriptions**:
- Gate descriptions can use Jinja2 templates to dynamically display content from upstream agents
- **Available Jinja2 Filters**: The system provides a comprehensive set of filters for formatting numbers, colors, dates, and more. See [Jinja2 Filters Reference](#jinja2-filters-reference) for details.
- Use `{{ agent_id.field }}` syntax for explicit access to upstream agent outputs
- Example: `description: "{{ root_cause_identifier.explanation | default('Review the identified root cause.') }}"`
- This makes gates more informative by showing actual analysis results instead of static text

**When to Use Separate Jinja Files vs Inline Descriptions**:
- **Use separate Jinja files** (`config/hitl/gate_name.jinja`) for:
  - Complex descriptions with multiple sections (e.g., details, summaries, validation tables)
  - Extensive markdown tables and formatting
  - Long descriptions (50+ lines)
  - Descriptions with complex nested conditionals and loops
  - Templates that benefit from better syntax highlighting and editing
  - Reference in YAML: `description: jinja: "hitl/gate_name.jinja"`
- **Use inline descriptions** for:
  - Simple, short descriptions (1-10 lines)
  - Single-line dynamic content
  - Quick prototypes or simple approval gates
  - Format: `description: "{{ agent_id.field | default('Default text') }}"`
- **Examples**:
  - `eci_decision_gate.jinja` - Complex gate with multiple sections, tables, and validation summaries
  - `tci_recommendation_review_gate.jinja` - Extensive risk assessment display with multiple tables
  - Simple inline: `description: "{{ agent_id.summary | default('Review the results.') }}"`

**Configuration**:
```yaml
- gate: approve_research_report
  on_approve: continue  # Proceed to next step
  on_reject: stop       # Stop pipeline execution
```

**Example from `article_smith.yml`**:
```yaml
- node: article_research_analyst
- gate: approve_research_report
  on_approve: continue
  on_reject: stop
- node: article_content_author
```

**Best Practices**:
- Use clear, descriptive titles: "Review Research Report" not "Gate 1"
- Provide context in description: Show what's being reviewed
- Set reasonable timeouts: 30000ms (30 seconds) for quick reviews, 300000ms (5 minutes) for complex reviews
- Consider `on_timeout: approve` for non-critical approvals
- **Markdown Table Formatting**: When using tables in gate descriptions, follow strict whitespace control rules (see [Markdown Table Formatting in HITL Gates](#markdown-table-formatting-in-hitl-gates) section)

### 2.3.0.2 Input Gates

**When to Use**:
- **Document/file uploads** at pipeline start or specific stages
- **Collecting user feedback** to improve agent outputs
- **Gathering additional context** needed for downstream agents
- **Staged input collection** (collect different inputs at different stages)

**Common Patterns**:
- **Pipeline start**: Upload initial documents/files
- **Mid-pipeline**: Collect feedback or additional documents
- **Before specific agents**: Gather required inputs for next agent

**Placement in Patterns**:
- **Pipeline start**: First step before any agents (like `appeal_grievance_processor`)
- **Between agents**: After agent A → Gate → Agent B (Agent B uses input)
- **Before parallel branches**: Gate → Parallel agents (all agents use input)

**Configuration**:
```yaml
- gate: upload_contract_document
  on_submit: continue      # Proceed after file upload
  on_cancel: stop          # Stop if user cancels
  context_key: "uploaded_contract"  # Store file path in context
```

**Example from `appeal_grievance_processor.yml`**:
```yaml
pattern:
  steps:
    - gate: appeal_grievance_letter_upload  # First step - upload document
      on_submit: continue
      on_cancel: stop
    - node: appeal_grievance_classifier  # Agent uses uploaded file
    - gate: claim_history_file_upload        # Mid-pipeline upload
      on_submit: continue
      on_cancel: stop
    - node: appeal_grievance_recommender
```

**Field Types for Input Gates**:
- **file**: File upload (PDF, DOCX, TXT, etc.)
- **text**: Single-line text input
- **textarea**: Multi-line text input
- **number**: Numeric input
- **date**: Date picker
- **checkbox**: Boolean checkbox
- **select**: Dropdown selection

**File Upload Configuration**:
```yaml
gates:
  - id: upload_contract
    type: input
    title: "Upload Contract Document"
    description: "Please upload the contract document for analysis."
    fields:
      - name: contract_file
        label: "Contract Document"
        type: file
        required: true
        validation:
          file_types: ["pdf", "docx", "txt"]
          max_size_mb: 10
    context_key: "uploaded_contract_file"
    timeout_ms: 300000
    on_timeout: default
    default: stop
```

**Best Practices**:
- Use descriptive field names and labels
- Set appropriate file type restrictions
- Set reasonable file size limits
- Use clear `context_key` names (agents access via `{{uploaded_contract_file}}`)
- Consider timeout behavior: `default: stop` for required inputs

### 2.3.0.3 Selection Gates

**When to Use**:
- **Routing decisions** where user chooses workflow path
- **Option selection** from agent-generated alternatives
- **Preference selection** that affects downstream processing
- **Multi-option approval** with different actions per option

**Common Patterns**:
- After agent generates options → User selects → Different paths
- After parallel analysis → User selects preferred approach
- Before final generation → User selects style/format

**Placement in Patterns**:
- **After agent output**: Agent generates options → Gate → Route based on selection
- **After parallel agents**: Multiple agents → Gate → Route based on selection
- **Before conditional branches**: Gate → Switch/conditional based on selection

**Configuration**:
```yaml
- gate: select_edit_type
  on_conservative_edit: continue  # Action for option 1
  on_moderate_edit: continue      # Action for option 2
  on_comprehensive_edit: continue  # Action for option 3
```

**Example from `article_smith.yml`**:
```yaml
- type: parallel
  steps:
    - node: article_content_critique
    - node: article_format_critique
- gate: approve_critiques
  on_conservative_edit: continue
  on_moderate_edit: continue
  on_comprehensive_edit: continue
- node: article_chief_editor
```

**Selection Gate Configuration**:
```yaml
gates:
  - id: select_edit_type
    type: selection
    title: "Select Edit Approach"
    description: "Choose how comprehensive the edits should be."
    options:
      - value: "conservative_edit"
        label: "Conservative Edit"
        description: "Minor corrections only"
      - value: "moderate_edit"
        label: "Moderate Edit"
        description: "Improve clarity and structure"
      - value: "comprehensive_edit"
        label: "Comprehensive Edit"
        description: "Full rewrite if needed"
    context_key: "selected_edit_type"
    timeout_ms: 60000
    on_timeout: default
    default: "moderate_edit"
```

**Best Practices**:
- Provide clear option labels and descriptions
- Ensure actions match option values (`on_<option_value>`)
- Set default option for timeout scenarios
- Use descriptive `context_key` names
- Consider routing to different agents based on selection

### 2.3.0.4 HITL Gate Placement Strategies

**Strategy 1: Document Collection at Start**
- **Pattern**: Input gate → Agents
- **Use Case**: When documents are required before any processing
- **Example**: `appeal_grievance_processor` - upload letter first

**Strategy 2: Staged Document Collection**
- **Pattern**: Agent → Input gate → Agent → Input gate → Agent
- **Use Case**: When different documents are needed at different stages
- **Example**: `appeal_grievance_processor` - upload letter, then claim history, then research doc

**Strategy 3: Quality Checkpoints**
- **Pattern**: Agent → Approval gate → Next agent
- **Use Case**: Verify quality before proceeding
- **Example**: `article_smith` - approve research before authoring

**Strategy 4: Feedback Loops**
- **Pattern**: Agent → Input gate (feedback) → Retry agent
- **Use Case**: Iterative improvement with user feedback
- **Example**: `article_smith` - collect feedback, retry research

**Strategy 5: Parallel Review**
- **Pattern**: Parallel agents → Selection/Approval gate → Next step
- **Use Case**: Review multiple analyses and choose path
- **Example**: `article_smith` - parallel critiques → selection gate

**Strategy 6: Conditional Routing**
- **Pattern**: Agent → Selection gate → Conditional branches
- **Use Case**: User chooses workflow path
- **Example**: Custom pipelines with user-driven routing

### 2.3.0.5 HITL Gates in Different Pattern Types

**Sequential Patterns**:
- Gates naturally fit between sequential steps
- Common: Agent → Gate → Agent → Gate → Agent
- Example: `article_smith`, `claim_processor`

**Parallel Patterns**:
- Gates typically after parallel agents complete
- Can also gate individual parallel branches
- Example: `article_smith` - parallel critiques → selection gate

**Conditional/Switch Patterns**:
- Gates can be before switch (user chooses path)
- Gates can be after switch (review conditional output)
- Example: `trip_planner` - selection gates within conditional branches

**Group Chat Patterns**:
- Less common, but can gate before/after group chat
- Example: Approval gate before starting group chat

**Handoff Patterns**:
- Gates can collect input before handoff
- Gates can review handoff results
- Example: Input gate → Handoff → Approval gate

**Gate Configuration**:
- Determine gate ID (snake_case)
- Determine gate type (approval/input/selection)
- Define title and description for UI
- For input gates: define fields (name, type, label, required)
- For selection gates: define options (value, label, description)
- Set context_key for storing user input
- Set timeout_ms and on_timeout behavior
- Configure flow control actions (on_approve, on_reject, on_submit, on_cancel, etc.)

### 2.3.1 Gate Configuration Validation

**Action**: Validate gate configurations before finalizing:

**Validation Rules**:
- **Approval gates**: Must have `on_approve` and `on_reject` actions
- **Input gates**: Must have `on_continue` action, may have `on_retry` with `retry_target`
- **Selection gates**: Must have actions matching option values (e.g., `on_option_a`, `on_option_b`)
- **Retry logic**: If `retry_target` is specified, verify it points to valid agent
- **Context keys**: Ensure `context_key` names are unique and descriptive
- **Timeouts**: Set reasonable timeout values (default: 30000ms for approval, 60000ms for input)

**Checklist**:
- [ ] All gate actions reference valid next steps
- [ ] Selection gate actions match option values
- [ ] Retry targets point to valid agents
- [ ] Context keys are unique and descriptive
- [ ] Timeout values are reasonable

### 2.3.2 Retry Logic Configuration

**When to use retry logic**:
- When agent might fail due to transient errors
- When user feedback can improve results
- When iterative refinement is needed
- When quality check fails and rework is possible

**Configuration**:
- Set `retry_target` to agent to retry (usually the agent before the gate)
- Use `on_retry: retry_node` in gate configuration
- Consider `max_retries` if supported (to prevent infinite loops)
- Ensure retry makes sense (e.g., retrying research with user feedback)

**Example**:
```yaml
- gate: review_draft
  on_continue: continue
  on_retry: retry_node
  retry_target: content_author  # Retry the author with user feedback
```

### 2.4 Output Structure Design

**Action**: Use output requirements collected in Step 1.7 to design output structure:

**Important**: 
- **USE** the output requirements from Step 1.7
- **USE** the final output agent and fields already specified
- **USE** intermediate output requirements already documented
- **USE** transformation requirements already specified

### 2.4.1 Output Schema Design Guidelines

**Best Practices**:
- **Keep schemas flat when possible**: Avoid deep nesting (max 2-3 levels)
- **Use consistent field naming**: snake_case throughout (e.g., `summary_text`, `key_points`)
- **Always include error field**: Every output should have `error` field for error handling
- **Make fields self-descriptive**: Clear names that explain purpose (e.g., `final_article_md` not `result`)
- **Consider downstream needs**: Design schema thinking about what next agent needs
- **Document data types**: Note expected types (string, array, object, boolean)
- **Use arrays for lists**: Use arrays for multiple items (e.g., `key_points: ["point1", "point2"]`)

**Schema Examples**:
```json
// Good: Flat, clear, includes error
{
  "summary_text": "string",
  "key_points": ["string"],
  "sentiment": "string",
  "error": "string"
}

// Avoid: Too nested, unclear
{
  "data": {
    "result": {
      "content": {
        "text": "string"
      }
    }
  }
}
```

### 2.4.2 Intermediate Outputs

**When to use intermediate outputs**:
- When multiple agents need the same upstream output
- When debugging/troubleshooting pipeline execution
- When user wants to see progress at specific steps
- When output needs transformation before final use
- When intermediate results are valuable for review

**Configuration**:
```yaml
outputs:
  intermediate:
    - node: research_analyst
      selectors:
        - research_report
  final:
    node: final_editor
    selectors:
      - final_output
```

**🔍 CRITICAL**: Intermediate outputs do NOT use `id` fields. The schema only allows:
- `node` (required): Which node's output to capture
- `selectors` (required): JSON keys/paths to extract
- `transform` (optional): Jinja2 expression for transformation

**Incorrect** (DO NOT USE):
```yaml
intermediate:
  - id: research_summary  # ❌ WRONG - 'id' is not allowed
    node: research_analyst
    selectors:
      - research_report
```

### 2.4.3 Output Transformations

**Common transformations** (using Jinja2):
- **Extract nested field**: `{{ value.field_name }}`
- **Format text**: `{{ value | upper }}` or `{{ value | lower }}`
- **Combine fields**: `{{ value.field1 }} - {{ value.field2 }}`
- **Default values**: `{{ value or "default" }}`
- **Conditional**: `{% if value %}{{ value }}{% else %}N/A{% endif %}`

**When to use transformations**:
- When you need to extract specific fields from complex output
- When you need to format output for display
- When you need to provide defaults for missing values
- When you need to combine multiple fields

**Example**:
```yaml
outputs:
  final:
    node: summary_generator
    selectors:
      - summary_text
      - error
    transform: "{{ summary_text if summary_text else 'No summary available' }}"
```

### 2.5 Present Workflow Proposal

**Action**: Create a comprehensive design document and present complete workflow proposal to user:

**🔍 CRITICAL**: Before presenting the proposal, create a design document in `docs/designs/{pipeline_id}_design.md` following the standardized design format.

#### 2.5.1 Create Design Document

**Action**: Create a design document that serves as the single source of truth for the pipeline design.

**Design Document Format** (based on `appeal_grievance_processor_automated_design.md`):

```markdown
# {Pipeline Name} - Pipeline Design

## Overview

Brief description of the pipeline's purpose and what it accomplishes.

## Pipeline Flow

```
1. Agent1 (description)
   ↓
2. Agent2 (description)
   ├─ 3. Agent3 (description)
   └─ 4. Agent4 (description)
   ↓
5. Final Agent (description)
```

## Agent List & Goals

### 1. **Agent Name** (`agent_id`)
**Type:** OAK/ADK/SK (framework type)  
**Goal:** Clear, single-sentence goal statement  
**MCP Tools:** `toolkit.*` (specific tools used)  
**Input:** 
- `upstream_agent.field1`
- `upstream_agent.field2`

**Output:**
- `output_field1`: Description
- `output_field2`: Description

**Key Logic:**
- Step-by-step logic the agent follows
- Important decisions or calculations
- Error handling approach

---

### 2. **Next Agent** (`next_agent_id`)
[Same format as above]

## Pipeline Configuration

### Pattern Structure

```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - type: parallel
      steps:
        - node: agent2
        - node: agent3
    - node: agent4
```

### HITL Gates

#### 1. Gate Name (`gate_id`)
**Type:** Approval/Input/Selection  
**Location:** After `agent_name`  
**Purpose:** Why this gate is needed

**Configuration:**
- **Title:** "Human-readable title"
- **Description:** What the user sees
- **Options/Fields:** (for selection/input gates)
- **Default:** Default value if applicable
- **Context Key:** Where data is stored

**Gate Actions:**
- `on_approve`: Action taken
- `on_reject`: Action taken
- `on_cancel`: Action taken

**Output:**
- `output_field`: What gets stored

---

### Error Handling

- How errors are handled
- What happens on failure
- Retry logic (if any)

### Key Design Decisions

1. **Decision 1**: Rationale
2. **Decision 2**: Rationale
3. **Decision 3**: Rationale
```

**Design Document Requirements**:
- ✅ **Complete**: All agents documented with goals, inputs, outputs, MCP tools
- ✅ **Clear**: Each agent has a single, clear responsibility
- ✅ **Detailed**: Key logic section explains how each agent works
- ✅ **Structured**: Follows the exact format above for consistency
- ✅ **Comprehensive**: Includes pattern structure, gates, error handling, design decisions

**Benefits of Design Document**:
- Serves as single source of truth for pipeline design
- Makes it easy to review and understand the complete workflow
- Helps identify issues before implementation
- Provides clear documentation for future reference
- Enables easy comparison with other pipeline designs

**After creating design document**, reference it when presenting the proposal to the user.

#### 2.5.2 Present Workflow Proposal

**Action**: Present complete workflow proposal to user, referencing the design document:

**Format**:
1. **Reference Design Document**:
   - "I've created a comprehensive design document at `docs/designs/{pipeline_id}_design.md`"
   - "The design document includes all agents, their goals, inputs/outputs, and the complete pipeline structure"

2. **Workflow Diagram** (text-based):
   ```
   User Input
     ↓
   Agent1 (Research)
     ↓
   [Gate: Approval]
     ↓
   Agent2 (Draft)
     ↓
   [Parallel]
     ├─ Agent3 (Content Critique)
     └─ Agent4 (Format Critique)
     ↓
   [Gate: Selection]
     ↓
   Agent5 (Final Editor)
     ↓
   Final Output
   ```

3. **Agent Summary** (detailed info in design document):
   - For each agent: ID, role, type (OAK/ADK/SK), MCP tools
   - Reference design document for full details

4. **Pattern Structure**:
   - Show nested pattern structure
   - Explain execution flow
   - Reference design document for full YAML

5. **HITL Gates**:
   - List all gates with placement and configuration
   - Reference design document for full gate details

6. **Output Structure**:
   - Final output node and selectors
   - Intermediate outputs (if any)
   - Reference design document for full output schema

### 2.6 User Review: Workflow Proposal

**🔍 REVIEW CHECKPOINT**: After presenting the workflow proposal, explicitly ask:
- "Please review this workflow proposal. Does it meet your requirements?"
- "Are the agents correctly identified with appropriate roles?"
- "Is the workflow pattern (sequential/parallel/conditional) appropriate?"
- "Are the HITL gates placed correctly?"
- "Is the output structure what you expect?"

**Wait for user feedback before proceeding to refinement.**

## Step 3: Interactive Refinement

### 3.1 Review & Feedback Loop

**Action**: Allow user to review and request changes:

**Common Modifications**:
- Add/remove agents
- Modify agent roles or responsibilities
- Change workflow pattern (sequential → parallel, add conditionals)
- Add/modify/remove HITL gates
- Adjust execution order
- Modify output structure

**Process**:
1. Present proposal
2. Ask: "Does this workflow look correct? Any changes needed?"
3. If changes requested:
   - Make modifications
   - Re-present updated proposal
   - Repeat until approved
4. Once approved, proceed to generation

### 3.2 Final Confirmation

**🔍 REVIEW CHECKPOINT**: Before generating files, explicitly confirm with user:
- "Are all agents correctly defined with their roles?"
- "Is the workflow pattern correct?"
- "Are the HITL gates properly configured?"
- "Is the output structure correct?"
- "Are you ready to proceed with file generation?"

**Action**: Get explicit approval:
- "Please confirm: Should I proceed with generating all the configuration files?"
- Wait for explicit "yes" or approval before proceeding

**⚠️ IMPORTANT**: Do NOT proceed to file generation without explicit user approval.

## Step 4: File Generation

**Important**: All generated files should be placed relative to the base path established at the beginning: Base: `{base_path}`

### 4.0 Pre-Generation Checks

**Action**: Before generating files, perform these checks:

**File Conflict Check** (all paths relative to base path):
1. Check if pipeline config already exists: Base: `{base_path}` → `config/pipelines/{pipeline_id}.yml`
2. **Re-check agent config conflicts**: Base: `{base_path}` → `config/agents/{agent_id}.yml` (should have been checked in Step 1.3.1, but verify again)
3. Check if any prompt files already exist: Base: `{base_path}` → `config/prompts/{agent_id}.jinja`
4. Check if UI manifest exists: Base: `{base_path}` → `config/ui_manifests/{pipeline_id}.yml`

**Note**: Agent ID conflicts should have been checked and resolved in Step 1.3.1. This is a final safety check before file generation.

**If files exist**:
- Ask user: "Some files already exist. Do you want to:"
  - Overwrite existing files
  - Create new versions (with different names)
  - Cancel and modify pipeline ID
- Offer to backup existing files before overwriting
- Show diff preview if possible (list what will change)
- Get explicit user approval before overwriting

**Progress Indication**: Throughout file generation, inform user:
- "Generating pipeline config..."
- "Generating agent configs (1/3)..."
- "Generating prompt templates (2/3)..."
- "Generating UI manifest..."
- "Updating main config files..."

### 4.1 Generate Pipeline Config

**File**: Base: `{base_path}` → `config/pipelines/{pipeline_id}.yml`

**Structure**:
```yaml
name: "{Pipeline Name}"
description: "{Detailed description}"

# Optional: Pipelines registry for reusing existing pipelines as nodes
pipelines:
  - id: {sub_pipeline_id}
    pipeline_file: "pipelines/{sub_pipeline_id}.yml"

nodes:
  - id: {agent_id}
    config_file: "agents/{agent_id}.yml"
  # ... all agents

pattern:
  type: sequential  # or parallel, loop
  steps:
    - node: {agent_id}  # A2A for remote, IN-PROC for local (automatic)
    - pipeline: {sub_pipeline_id}  # Use existing pipeline as a node
      input_mapping:
        user_text: "{{parent_agent.field}}"  # Map parent context to sub-pipeline inputs
    - gate: {gate_id}
      on_approve: continue
      on_reject: stop
    - type: parallel  # nested pattern if needed
      steps:
        - node: {agent_id}:{protocol}
    # ... complete pattern

gates:
  - id: {gate_id}
    type: approval  # or input, selection
    title: "{UI Title}"
    description: "{UI Description}"
    timeout_ms: 30000
    on_timeout: approve
    # ... gate-specific config

outputs:
  final:
    node: {final_agent_id}
    selectors:
      - {output_field}
      - error
    transform: "{{ value }}"
```

**Checklist**:
- [ ] All agents listed in nodes section
- [ ] Pattern structure matches design
- [ ] All gates defined with proper configuration
- [ ] Output selectors match agent output schema
- [ ] Protocol: A2A for remote agents (no suffix needed in pattern)
- [ ] Gate actions (on_approve, on_reject, etc.) properly configured

**Reference**: See Base: `{base_path}` → `config/pipelines/article_smith.yml` for complete example.

### 4.2 Generate Agent Configs

**File**: Base: `{base_path}` → `config/agents/{agent_id}.yml` (one per agent)

### 4.2.1 Model Configuration

**Default**: Use `azure_openai` for all agents

**Alternative Models**: If user specifies different model:
- Update `model` field in agent config
- Ensure model is available in project configuration
- Note model choice in summary
- Common alternatives: `ollama_qwen2.5:14b`, `openai_gpt4`, etc.

**Structure**:
```yaml
id: {agent_id}
type: oak
model: "azure_openai"  # Default, can be changed if user specifies
run_mode: "local"

remote:  # Required for ALL agents (allows switching between local/remote later)
  url: http://127.0.0.1:{calculated_port}  # Calculate from existing agents (see 4.2.2)
  timeout: 30000  # Default timeout in milliseconds
  retry_attempts: 3  # Default retry attempts

agent_card:
  name: "{Human-readable Name}"
  description: "{Agent purpose}"
  skills:
    - id: "{skill_id}"
      name: "{Skill Name}"
      description: "{Skill description}"
      tags: ["tag1", "tag2"]
      examples:
        - "{Example input 1}"
  capabilities:
    streaming: true
    push_notifications: false
    state_transition_history: true
  tags: ["tag1", "tag2"]

mcp:  # ⚠️ ONLY add if agent truly needs external tools
  # When to add: Agent needs web search, external APIs, real-time data
  # When NOT to add: Agent only processes upstream data, generates content from context, analyzes mock data
  servers:
    - url: "http://127.0.0.1:8050/mcp"
      toolkits: ["search"]
      tools: ["search.*"]

prompt:
  instruction:
    jinja: prompts/{agent_id}.jinja
  inputs:
    inline: |
      - User Request: {{user_text}}
      {% if contract_type %}- Contract Type: {{contract_type}}{% endif %}
      {% if key_terms %}- Key Terms: {{key_terms}}{% endif %}
```

**Note**: Use top-level variables (e.g., `{{contract_type}}`) not `{{context.upstream.agent_id.field}}` syntax.

**🔍 CRITICAL - Agent YML File Formatting**:

1. **Preserve Section Comments**: When generating agent YML files, include proper section comments matching the reference format:
   ```yaml
   # =============================================================================
   # PARSER AGENT CONFIGURATION
   # =============================================================================
   #
   # This agent parses user input to extract structured information...
   #
   # =============================================================================
   ```

2. **Input Variables Syntax**: Variables in `inputs.inline` can use either syntax:
   - **Explicit syntax** (preferred): `{{agent_id.field}}` - More explicit, recommended
   - **Simple syntax**: `{{field}}` - Works when field name is unique across all upstream agents
   ```yaml
   # ✅ CORRECT - Explicit syntax (preferred)
   inputs:
     inline: |
       Complaint Type: {{complaint_wizard_parser.complaint_type}}
       Billing Issues: {{complaint_wizard_parser.billing_issues}}
   ```
   ```yaml
   # ✅ CORRECT - Simple syntax (when field names are unique)
   inputs:
     inline: |
       Complaint Type: {{complaint_type}}
       Billing Issues: {{billing_issues}}
   ```
   Both syntaxes work. Use explicit syntax (`{{agent_id.field}}`) when you want to be clear about the source, or simple syntax (`{{field}}`) when field names are unique across all upstream agents.

3. **Optional Variables Must Use Proper Jinja2 Conditionals**: For optional variables that may be null or empty, use proper Jinja2 conditional blocks (`{% if %}...{% endif %}`), NOT Python-style conditionals:
   ```yaml
   # ✅ CORRECT - Proper Jinja2 conditional syntax
   inputs:
     inline: |
       Complaint Type: {{complaint_type}}
       Billing Issues: {{billing_issues}}
       {% if amount_mentioned %}Amount Mentioned: {{amount_mentioned}}{% endif %}
       {% if timeframe %}Timeframe: {{timeframe}}{% endif %}
       {% if editorial_direction %}- Editorial Direction: {{editorial_direction}}{% endif %}
   
   # ❌ WRONG - Python-style conditionals cause JSON parsing errors
   inputs:
     inline: |
       Amount Mentioned: {{amount_mentioned if amount_mentioned is not none else "not mentioned"}}  # ❌ WRONG
       Timeframe: {{timeframe if timeframe is not none else "not specified"}}  # ❌ WRONG
   ```
   **Why**: Python-style conditionals in Jinja2 templates can cause JSON parsing errors during variable extraction. Use Jinja2 conditionals to conditionally include entire lines only when variables have values.

3. **All Required Sections**: Ensure each agent YML includes:
   - Section comments (properly formatted)
   - `id`, `type`, `model`, `run_mode`
   - `remote` section (with protocol_support and urls)
   - `agent_card` section (with name, description, skills, capabilities, tags)
   - `prompt` section (with instruction.jinja and inputs.inline)
   - `mcp` section (if agent needs external tools)

**Checklist**:
- [ ] Agent ID matches pipeline reference
- [ ] **Section comments included and properly formatted** (matching reference format)
- [ ] Agent card has descriptive name and description
- [ ] Skills defined with examples (if applicable)
- [ ] MCP configuration included if agent needs tools
- [ ] **Remote configuration included for ALL agents** (required for all agents)
- [ ] **run_mode set correctly** ("local" or "remote" based on Step 1.9)
- [ ] **Port assigned correctly** (default: 8100, or user-selected port not in reserved list)
- [ ] **Port assigned to ALL agents** (even if running locally initially)
- [ ] **Reserved ports avoided** (8090, 8050, 3000)
- [ ] **Input variables use correct syntax** (prefer `{{agent_id.field}}` for explicit access, or `{{field}}` when unique)
- [ ] **Optional variables use proper Jinja2 conditionals** (`{% if variable %}...{% endif %}` NOT Python-style conditionals)
- [ ] **`project_dir` included in inputs** if agent uses file/database operations (see Section 4.3.2)
- [ ] Prompt inputs reference correct context variables
- [ ] Input template uses Jinja2 syntax correctly

**Reference**: See Base: `{base_path}` → `config/agents/article_research_analyst.yml` for complete example.

### 4.2.2 Remote Configuration

**🔍 CRITICAL**: Add remote configuration to ALL agents, regardless of whether they run locally or remotely initially. This allows users to switch agents between local and remote execution later without code changes.

**Action**: For EACH agent (all agents need remote config):

1. **Remote config is required for all agents**:
   - Add `remote` section to every agent config
   - Set `run_mode: "local"` for agents that run locally initially
   - Set `run_mode: "remote"` for agents that run remotely initially (from Step 1.9)
   - Remote config enables switching between local/remote later

2. **Port Selection**:
   - **Default port**: 8100 (A2A standard, supports path-based routing)
   - **Ask user**: "What port should agents use? (Default: 8100)"
   - **Reserved ports to avoid**: 
     - 8090 (FastAPI server)
     - 8050 (MCP server)
     - 3000 (UI dev mode)
   - **Note**: All agents can use the same port (8100) since A2A supports path-based URLs like `http://127.0.0.1:8100/{agent_id}`
   - **If user chooses different port**: Verify it's not in the reserved list above
   - **No port scanning needed**: Since A2A supports path-based routing, all agents can share the same port

3. **Assign port to all agents** (ALL agents get the same port, even if running locally):
   - Use the port selected by user (default: 8100)
   - All agents use the same port with different paths: `http://127.0.0.1:{port}/{agent_id}`
   - Example: If port is 8100, all agents use:
     - `http://127.0.0.1:8100/{agent_id_1}`
     - `http://127.0.0.1:8100/{agent_id_2}`
     - `http://127.0.0.1:8100/{agent_id_3}`

**Configuration Structure**:

```yaml
remote:
  url: http://127.0.0.1:{port}/{agent_id}  # Port from user selection (default: 8100)
  timeout: 30000  # Default timeout in milliseconds
  retry_attempts: 3  # Default retry attempts
```

**Configuration Guidelines**:
- **Include `remote` section for ALL agents** (required for all agents)
- **Set `run_mode`**: `"local"` for agents running locally, `"remote"` for agents running remotely (from Step 1.9)
- **Port assignment**: Use user-selected port (default: 8100) for all agents
- **All agents share the same port**: A2A supports path-based routing, so each agent gets a unique path on the same port
- **Assign remote config to ALL agents** (even if running locally initially)
- **Document port assignment** in summary for user reference

**Examples**:

- **All agents** (using default port 8100):
  - Agent 1: run_mode: `"local"`, url: `http://127.0.0.1:8100/agent_1_id`
  - Agent 2: run_mode: `"local"`, url: `http://127.0.0.1:8100/agent_2_id`
  - Agent 3: run_mode: `"remote"`, url: `http://127.0.0.1:8100/agent_3_id`
  - All agents use the same port (8100) with different paths

**Important Notes**:
- **Remote config is required for ALL agents** (not just remote ones)
- **No port scanning needed**: A2A supports path-based routing, so all agents can use the same port
- **Default port is 8100**: This is the A2A standard port
- **Reserved ports**: Avoid 8090 (FastAPI), 8050 (MCP), 3000 (UI dev mode)
- **Users can switch run_mode** between "local" and "remote" later without changing ports
- **Document assigned port** in the summary for user reference

### 4.3 Generate Prompt Templates

**File**: Base: `{base_path}` → `config/prompts/{agent_id}.jinja` (one per agent)

> **Canonical Rule (matches `.cursor/rules/generic_agent_flow.mdc`)**  
> All new prompts **must** be schema-first and follow a consistent section order:
> - Role & Purpose  
> - Tasks  
> - (Optional) Notes / Constraints  
> - Instructions (including strict output format rules)  
> - Output Format (STRICT JSON ONLY…)  
> - Examples (at least one success; error example when applicable)

**🔍 CRITICAL - Prompt File Structure**:

1. **Prompts Must NOT Contain Variables**: Prompt files (`.jinja`) should contain ONLY instruction text. Variables are provided in the agent YML `inputs.inline` section, NOT in the prompt file itself.

   ```jinja
   # ✅ CORRECT - Prompt file contains only instructions
   You are a **Complaint Parser**, specializing in extracting structured information from customer complaints.
   
   Tasks:
   1. Extract complaint type (billing, service, technical, etc.)
   2. Identify billing issues mentioned
   3. Identify service issues mentioned
   ...
   ```

   ```yaml
   # ✅ CORRECT - Variables are in agent YML inputs.inline
   prompt:
     instruction:
       jinja: prompts/complaint_wizard_parser.jinja
     inputs:
       inline: |
         User Complaint: {{user_text}}
   ```

   ```jinja
   # ❌ WRONG - Do NOT put variables in prompt files
   You are a **Complaint Parser**.
   
   User Complaint: {{user_text}}  # ❌ WRONG - Variables belong in agent YML
   ```

2. **Variables Are Provided in Agent YML**: All input variables must be specified in the agent YML file's `prompt.inputs.inline` section, not in the prompt template file.

3. **Prompt File Contains Only Instructions**: The prompt file should contain:
- Role definition (Role & Purpose)
- Task descriptions (Tasks)
- Optional Notes / Constraints for edge cases
- Instructions (including strict JSON / error-handling rules)
- Output format specifications as a **literal JSON schema**
- Examples (✅ success and ❌ error) that strictly match the schema
- NO variable references (those go in agent YML)

### 4.3.0 Context Variable Access Rules

**🔍 CRITICAL**: Understand how context variables work before generating prompt inputs.

**Context Variable Access Pattern**:
- **Upstream agent outputs** are automatically extracted and made available as **top-level variables**
- Variables can be accessed using two syntaxes:
  - **Explicit syntax** (preferred): `{{agent_id.field}}` - More explicit, recommended when field names might conflict
  - **Simple syntax**: `{{field}}` - Works when field name is unique across all upstream agents
- The system automatically searches upstream agents for variables and makes them available
- **Never use**: `{{context.upstream.agent_id.field}}` - This syntax is not supported

**Correct Usage** (both syntaxes work):

**Explicit Syntax** (preferred):
```yaml
inputs:
  inline: |
    Contract Document: {{uploaded_contract_file}}
    Contract Type: {{legal_classifier.contract_type}}
    Key Terms: {{legal_key_terms_extractor.key_terms}}
    Risk Analysis: {{risk_analyzer.risk_analysis}}
```

**Simple Syntax** (when field names are unique):
```yaml
inputs:
  inline: |
    Contract Document: {{uploaded_contract_file}}
    Contract Type: {{contract_type}}
    Key Terms: {{key_terms}}
    Risk Analysis: {{risk_analysis}}
```

**Incorrect Usage** (DO NOT USE):
```yaml
inputs:
  inline: |
    Contract Type: {{context.upstream.legal_classifier.contract_type}}  # ❌ WRONG - Not supported
    Key Terms: {{context.upstream.legal_key_terms_extractor}}            # ❌ WRONG - Not supported
```

**How It Works**:
1. Upstream agent outputs JSON with fields (e.g., `contract_type`, `key_terms`)
2. System automatically extracts these fields from upstream agent's parsed output
3. Fields become top-level variables available to downstream agents
4. Downstream agents can reference them as:
   - `{{agent_id.field}}` (explicit, preferred)
   - `{{field}}` (simple, works when unique)

**Variable Sources**:
- `{{user_text}}` - Always available (user input)
- `{{uploaded_contract_file}}` - From input gate with `context_key: "uploaded_contract_file"`
- `{{contract_type}}` or `{{legal_classifier.contract_type}}` - From upstream agent output
- `{{key_terms}}` or `{{legal_key_terms_extractor.key_terms}}` - From upstream agent output
- `{{user_feedback}}` - From input gate with `context_key: "user_feedback"`

**Expressions Support**:
- Variables support Jinja2 expressions and filters
- Examples:
  - `{{agent_id.field | default('default_value')}}` - Default value if field is empty
  - `{{agent_id.field + 1}}` - Mathematical operations
  - `{{agent_id.field | upper}}` - String transformations
  - `{{agent_id.field if agent_id.field else 'N/A'}}` - Conditional expressions

**Action**: When generating prompt inputs:
1. Identify which variables the agent needs
2. Determine source: user input, upstream agent output, or HITL gate
3. **Prefer explicit syntax**: Use `{{agent_id.field}}` for clarity and to avoid conflicts
4. **Use simple syntax**: Use `{{field}}` only when field name is unique across all upstream agents
5. Never use `{{context.upstream.agent_id.field}}` syntax (not supported)
6. **Put variables in agent YML `inputs.inline`, NOT in prompt file**
7. **For optional variables**: Use Jinja2 conditionals `{% if variable %}...{% endif %}` to conditionally include lines, NOT Python-style conditionals like `{{var if var is not none else "default"}}`
8. **For expressions**: Use Jinja2 filters and expressions as needed (e.g., `{{field | default('value')}}`)

**Variable Placement Summary**:
- ✅ **Prompt file (`.jinja`)**: Contains ONLY instruction text, role definition, tasks, output format
- ✅ **Agent YML `inputs.inline`**: Contains ALL variable references (e.g., `{{user_text}}`, `{{complaint_type}}`)
- ❌ **Prompt file**: Should NEVER contain variables like `{{user_text}}` or `{{complaint_type}}`

### 4.3.1 Prompt Quality Validation

**Check before finalizing prompts**:
- [ ] Role definition is clear and specific to use case
- [ ] Tasks are actionable and measurable
- [ ] JSON schema matches agent's actual output needs
- [ ] Examples are realistic and relevant to use case
- [ ] Error handling is clearly defined
- [ ] Instructions reference available inputs correctly
- [ ] Prompt length is reasonable (not too verbose, not too brief)
- [ ] Output format instructions are clear and unambiguous
- [ ] Examples show both success and error cases

**Quality Guidelines**:
- **Be specific**: "Analyze email content" not "Process data"
- **Be actionable**: Break down into numbered tasks
- **Be clear**: Use simple language, avoid jargon
- **Be complete**: Include all necessary information
- **Be consistent**: Use same format across all prompts

**Structure**:
```
You are a **{Agent Role Name}**, specializing in {specific responsibility}.

---

Tasks:
1. {Task 1 description}
2. {Task 2 description}
...

Instructions:
- Always return output in **strict JSON format** (no additional text outside the JSON)
- Use only the output schema provided below
- Ensure valid JSON output (no trailing commas, no comments)
- If an error occurs, {output_object} must be empty, and only "error" should be populated

---

Output Format (STRICT JSON ONLY, no trailing commas, no comments)
{
  "{field1}": "<description>",
  "{field2}": {
    "{nested_field}": "<description>"
  },
  "error": "<error explanation if any, otherwise empty string>"
}

---

✅ Example of Successful Output
{
  "{field1}": "{example value}",
  "{field2}": {
    "{nested_field}": "{example value}"
  },
  "error": ""
}

---

❌ Example of Error Output
{
  "{field1}": "",
  "{field2}": {},
  "error": "{error message}"
}
```

**Guidelines**:
- Make prompts specific to the use case, not generic
- Include clear role definition
- Break down tasks clearly
- Define exact JSON output schema
- Provide examples of successful and error outputs
- Reference inputs from context (user_text, upstream agents)

**Checklist**:
- [ ] **Prompt file contains NO variables** (variables are in agent YML `inputs.inline`)
- [ ] Prompt is use-case-specific
- [ ] JSON schema matches agent's expected output
- [ ] Examples are relevant to the use case
- [ ] Error handling is defined
- [ ] Instructions reference available inputs (but don't include variable syntax)
- [ ] **All variables are in agent YML `inputs.inline` section**

**Reference**: See Base: `{base_path}` → `config/prompts/article_research_analyst.jinja` for example.

### 4.3.2 Path Resolution for File and Database Operations

**🔍 CRITICAL**: When agents need to access files or databases using relative paths, they **must** use `project_dir` to resolve absolute paths.

**Why This Is Required**:
- MCP tools (e.g., `sqlite_query`, `sqlite_execute`, `fs_listdir`, `fs_move_file`) require **absolute paths**
- Relative paths like `"data/ag/ag_database.db"` or `"projects/ensemble/data/ag/ag_database.db"` will fail with "file not found" errors
- The `project_dir` variable is automatically available as a top-level context variable and contains the absolute path to the project root

**Required Pattern**:

1. **Always pass `project_dir` in agent YML inputs**:
   ```yaml
   prompt:
     inputs:
       inline: |
         - User Request: {{user_text}}
         - Project Directory: {{project_dir}}
   ```

2. **Instruct agents to resolve paths in the prompt**:
   ```jinja
   Notes:
   - **Database Path Resolution**: The database path should be resolved as `"<project_dir>/data/ag/ag_database.db"` where `project_dir` is the absolute path to the project root provided in the input.
   - **Always use absolute paths** when calling `sqlite_query` - resolve the path relative to the project directory.
   ```

3. **Include path resolution in Instructions section**:
   ```jinja
   Instructions:
   - Always respond in **strict JSON format only** (no explanation text before or after the JSON).
   - **Path Resolution**: 
     - Read the **Project Directory** from the provided input (absolute path to project root).
     - Resolve the database path as `"<Project Directory>/data/ag/ag_database.db"` (absolute path).
     - **Always use absolute paths** when calling `sqlite_query`.
   ```

**When to Apply This Pattern**:
- ✅ **Database operations**: Any agent using `sqlite_query`, `sqlite_execute`, or `sqlite_schema`
- ✅ **File operations**: Any agent using `fs_listdir`, `fs_move_file`, `fs_makedirs`, or `fs_delete`
- ✅ **Document operations**: Any agent that needs to reference file paths for document processing
- ❌ **Not needed**: Agents that only process text/data without file system or database access

**Examples**:

**Example 1: Database Path Resolution**
```jinja
Tasks:
1. Read the **project directory path** from the provided input (this is the absolute path to the project root).
2. Resolve the **database path** as `"<project_dir>/data/ag/ag_database.db"` (absolute path).
3. Use `sqlite_query` to query the `ag_requests` table using the resolved absolute database path.
```

**Example 2: File Path Resolution**
```jinja
Tasks:
1. Read the **project directory path** from the provided input.
2. Resolve the **base folder path** as `"<project_dir>/data/invoices"` (absolute path).
3. Use `fs_listdir` to list files in the resolved absolute path.
```

**Common Mistakes to Avoid**:
- ❌ **Wrong**: `"The database path should be: projects/ensemble/data/ag/ag_database.db (relative to project root)"`
- ✅ **Correct**: `"Resolve the database path as '<project_dir>/data/ag/ag_database.db' (absolute path)"`
- ❌ **Wrong**: Not passing `project_dir` in agent YML inputs
- ✅ **Correct**: Always include `- Project Directory: {{project_dir}}` in `inputs.inline`
- ❌ **Wrong**: Telling agents to use relative paths
- ✅ **Correct**: Explicitly instruct agents to resolve absolute paths using `project_dir`

**Checklist**:
- [ ] Agent YML includes `- Project Directory: {{project_dir}}` in `inputs.inline`
- [ ] Prompt includes path resolution instructions in Notes section
- [ ] Prompt includes path resolution instructions in Instructions section
- [ ] Prompt explicitly states to use absolute paths in tool calls
- [ ] Examples (if any) show absolute paths, not relative paths

### 4.4 Generate UI Manifest

**File**: Base: `{base_path}` → `config/ui_manifests/{pipeline_id}.yml`

**Structure**:
```yaml
title: "{Pipeline Name}"
subtitle: "{Pipeline description}"

agents:
  - id: "{agent_id}"
    title: "{Agent Display Name}"
    subtitle: "{Agent description}"
    icon: "assets/{agent_id}.svg"
  # ... all agents

interaction_diagram: "assets/{pipeline_id}_workflow.svg"
```

**Checklist**:
- [ ] Title and subtitle match pipeline config
- [ ] All agents listed with correct IDs
- [ ] Agent titles are human-readable **WITHOUT pipeline prefix** (e.g., "Research Analyst" not "Article Research Analyst")
- [ ] Agent subtitles describe their purpose
- [ ] Icon paths follow naming convention
- [ ] Interaction diagram path is correct

**Agent Title Format**:
- **Agent ID**: Includes pipeline prefix (e.g., `article_research_analyst`)
- **Agent Title**: Human-readable name WITHOUT prefix (e.g., "Research Analyst")
- **Example**: 
  - ID: `article_research_analyst` → Title: "Research Analyst"
  - ID: `invoice_match_pro_folder_scanner` → Title: "Folder Scanner"

**Reference**: See Base: `{base_path}` → `config/ui_manifests/article_smith.yml` for example.

### 4.5 Icon Suggestions

**🔍 IMPORTANT**: 
- **Icons**: Only provide suggestions with Lucide icon names and links. Do NOT create placeholder SVG files.
- **Workflow Diagrams**: Workflow diagrams are auto-generated by the system. Do NOT create workflow diagram files.

**Action**: Suggest appropriate icons from [Lucide Icons](https://lucide.dev/) for each agent and pipeline:

**Icon Selection Process**:
1. **For each agent**: Based on the agent's role and responsibility, suggest 2-3 appropriate Lucide icons
2. **For pipeline**: Suggest 1-2 icons that represent the overall pipeline purpose
3. **Present suggestions** to user with:
   - Icon name from Lucide
   - Link to icon on lucide.dev
   - Brief explanation of why this icon fits
4. **Get user approval** for icon selections before proceeding

**Common Icon Mappings** (examples):
- **Research/Analysis agents**: `Search`, `FileSearch`, `Brain`, `Microscope`, `BarChart`
- **Writing/Content agents**: `PenTool`, `FileText`, `Edit`, `Type`, `BookOpen`
- **Review/Critique agents**: `Eye`, `CheckCircle`, `AlertCircle`, `MessageSquare`, `Star`
- **Editor/Refinement agents**: `Wand2`, `Sparkles`, `Zap`, `Scissors`, `Filter`
- **Classification agents**: `Tags`, `Layers`, `FolderTree`, `Hash`, `List`
- **Translation agents**: `Languages`, `Globe`, `MessageSquare`, `Repeat`
- **Email/Messaging agents**: `Mail`, `MessageSquare`, `Send`, `Inbox`
- **Data extraction agents**: `Download`, `FileDown`, `Database`, `Package`
- **Summary/Summarization**: `FileText`, `List`, `FileCheck`, `Clipboard`

**Pipeline Icon Suggestions**:
- **Content creation**: `FileText`, `PenTool`, `BookOpen`
- **Analysis workflows**: `BarChart`, `TrendingUp`, `Brain`
- **Communication**: `MessageSquare`, `Mail`, `Users`
- **Processing workflows**: `Settings`, `Workflow`, `Zap`

**Action**: For each suggested icon:
1. Provide icon name and link: `[Icon Name](https://lucide.dev/icons/{icon-name})`
2. Show a brief description: "This icon represents [agent role] because..."
3. Ask user: "Does this icon work, or would you prefer a different one?"

**After User Approval**:
- Note the selected Lucide icon names in the workflow summary
- User will download icons from lucide.dev and save them as SVG files manually
- Reference the icon names in the summary for user reference

**Workflow Diagram**:
- **⚠️ DO NOT CREATE**: Workflow diagrams are automatically generated by the system
- The `interaction_diagram` field in the UI manifest references the diagram path, but the actual diagram file is auto-generated
- No manual creation of workflow diagram files is needed

### 4.6 Update Main Config Files

**File**: Base: `{base_path}` → `config/pipeline.yml`

**Action**: Add pipeline entry:
```yaml
pipelines:
  # ... existing pipelines
  - id: {pipeline_id}
    config_file: "pipelines/{pipeline_id}.yml"
```

**File**: Base: `{base_path}` → `config/ui_manifest.yml`

**Action**: Add pipeline entry:
```yaml
pipelines:
  # ... existing pipelines
  - id: "{pipeline_id}"
    title: "{Pipeline Name}"
    subtitle: "{Pipeline description}"
    ui_manifest: "ui_manifests/{pipeline_id}.yml"
    icon: "assets/{pipeline_id}.svg"
```

**Checklist**:
- [ ] Pipeline ID matches filename
- [ ] Config file path is correct
- [ ] UI manifest path is correct
- [ ] Icon path is correct
- [ ] Entry added in correct location (alphabetical or logical order)

### 4.6.3 Update Assistant Classification Prompt

**🔍 CRITICAL**: The assistant uses a classification prompt to route user requests to the correct pipeline. This must be updated for the new pipeline to be discoverable.

**File**: Base: `{base_path}` → `config/prompts/assistant_intent_classifier.jinja`

**Action**: Add new pipeline entry to the "Pipelines:" section:

1. **Locate the Pipelines section** (around line 36-45)
2. **Add new pipeline entry** in alphabetical order (or logical grouping):
   ```jinja
   - `{pipeline_id}`: {Brief description of what the pipeline does}
   ```

**Format Guidelines**:
- Use backticks around pipeline_id: `` `pipeline_id` ``
- Description should be concise (one sentence, max 2 lines)
- Description should clearly indicate what the pipeline does and when to use it
- Match the description style of existing entries
- Place in alphabetical order by pipeline_id (or logical grouping if more appropriate)

**Example**:
```jinja
**Pipelines:**
use `execute_pipeline` tool to execute a pipeline. pass `pipeline_id` and `user_text` as arguments. 
if there are uploaded files, upload intent will be "session" and you can use the uploaded files in the pipeline.
`pipeline_id` is one of the following:
- `appeal_grievance_processor`: Process appeal and grievance requests by analyzing the appeal and grievance letter, researching the appeal and grievance, and writing a decision letter for the appeal and grievance.
- `article_smith`: Professional articles, reports, whitepapers
- `claim_processor`: Process insurance claims by analyzing the claim documents, validating against policy documents, presenting the case to the claim adjuster and generating an email draft for the claim adjuster
- `contract_analyzer`: Analyze legal contracts to extract key terms, identify risks, summarize obligations, and generate recommendations
- `math_compass`: Mathematical problems and calculations
- `stock_analysis`: Stock market analysis
- `reply_wizard`: Email and message drafting
- `translator`: Multi-language translation with intelligent specialist routing
- `trip_planner`: Trip planning including flights, hotels, and activities. Users can request trip planning for specific destinations, dates, and preferences. The pipeline will search for flights, hotels, and activities, present options for user selection, and generate a comprehensive trip plan.
```

**Description Best Practices**:
- **Be specific**: "Analyze legal contracts" not "Process documents"
- **Include key capabilities**: Mention what the pipeline does (extract, analyze, generate, etc.)
- **Indicate use case**: When should users use this pipeline?
- **Match existing style**: Keep descriptions consistent with other pipelines
- **Keep it concise**: One sentence, max 2 lines

**Checklist**:
- [ ] Pipeline ID matches the actual pipeline ID (from Step 1.1.1)
- [ ] Description accurately describes the pipeline's purpose
- [ ] Description is concise and clear
- [ ] Entry is placed in alphabetical order (or logical grouping)
- [ ] Format matches existing entries (backticks, colon, description)
- [ ] Description helps users understand when to use this pipeline

**Note**: This update ensures that the assistant can correctly route user requests to the new pipeline. Without this update, the pipeline won't be discoverable through the assistant interface.

### 4.7 User Review: Generated Files

**🔍 REVIEW CHECKPOINT**: After generating all files, present a summary to user:

**Action**: Show user:
1. **List of all generated files** with their paths:
   - Pipeline config: `config/pipelines/{pipeline_id}.yml`
   - Agent configs: `config/agents/{agent_id}.yml` (one per agent)
   - Prompt templates: `config/prompts/{agent_id}.jinja` (one per agent)
   - UI manifest: `config/ui_manifests/{pipeline_id}.yml`
   - **Assistant classification prompt**: `config/prompts/assistant_intent_classifier.jinja` (updated)
   - Main config files: `config/pipeline.yml`, `config/ui_manifest.yml` (updated)
2. **Key content preview** for each file type:
   - Pipeline config: Show pattern structure
   - Agent configs: Show agent names and roles
   - Prompt templates: Show first few lines of each prompt
   - UI manifest: Show agent list
   - Assistant classification prompt: Show the new pipeline entry added
3. **Icon suggestions** (if not already approved in Step 4.5):
   - Show suggested Lucide icons for pipeline and each agent
   - Provide links to icons on lucide.dev
   - Note: Icons are suggestions only - user will download and add them manually
   - Note selected icons for final summary
4. **Ask for review**:
   - "I've generated all the configuration files, including updating the assistant classification prompt. Would you like to review any specific files before we validate?"
   - "Are there any changes you'd like me to make to the generated files?"

**Action**: If user requests changes:
- Make the requested modifications
- Show what was changed
- Ask for confirmation again

**Wait for user approval before proceeding to validation.**

## Step 5: Validation & Summary

### 5.1 Validate Generated Files

**Action**: Validate all generated files:

**Validation Checks**:
1. **YAML Syntax**: All YAML files are valid
   - Check for syntax errors
   - Verify proper indentation
   - Check for missing required fields

2. **File References**: All referenced files exist
   - Agent config files referenced in pipeline exist
   - Prompt files referenced in agent configs exist
   - Icon file paths referenced in UI manifest are correct (icons will be added by user)
   - Assistant classification prompt file exists and contains new pipeline entry

3. **Schema Compliance**: Configs match expected schema
   - Pipeline config structure matches schema
   - Agent config structure matches schema
   - UI manifest structure matches schema

4. **Context Variables**: Prompt inputs reference valid context variables
   - Check `{{user_text}}` is used correctly (always available)
   - **CRITICAL**: Verify variables use top-level syntax: `{{variable_name}}` NOT `{{context.upstream.agent_id.field}}`
   - Check that referenced variables exist in upstream agent outputs or HITL gates
   - Verify conditional variables (e.g., `{% if user_feedback %}`) are used correctly
   - List all context variables used vs available
   - Ensure variables match field names from upstream agent JSON outputs

5. **Output Selectors**: Output selectors match agent output schemas
   - Verify selectors match JSON schema defined in prompts
   - Check that all selectors are valid JSON paths
   - Ensure `error` selector is included

6. **Dependency Validation**: Re-check dependencies
   - Verify no circular dependencies
   - Verify all agent references are valid
   - Verify gate actions reference valid next steps

**Tools**: Use `ConfigurationEngine` if available, or manually validate:
- Check file paths
- Validate YAML syntax
- Verify references
- Run schema validation if available

### 5.1.2 Context Variable Validation

**Action**: Verify all context variables in prompts are valid:

**Validation Process**:
1. **Extract all context variables** from prompt templates:
   - `{{user_text}}` - Always available
   - **CRITICAL**: Check for incorrect syntax - should be `{{variable_name}}` NOT `{{context.upstream.agent_id.field}}`
   - Top-level variables (e.g., `{{contract_type}}`) - Must exist in upstream agent output
   - `{{user_feedback}}` - Must come from input gate with context_key
   - Conditional variables: `{% if variable %}` - Must be defined

2. **Check availability**:
   - For each top-level variable (e.g., `{{contract_type}}`), verify it exists in upstream agent output
   - Verify upstream agent outputs this field in its JSON schema
   - For each gate-provided variable, verify gate exists and has matching context_key
   - For conditional variables, verify they're defined before use
   - **CRITICAL**: Ensure no variables use `{{context.upstream.agent_id.field}}` syntax (should be `{{field}}`)

3. **Present validation results**:
   - List all context variables found
   - Mark each as valid or invalid
   - Show which variables are available vs used
   - Fix any invalid references before proceeding

### 5.1.1 User Review: Validation Results

**🔍 REVIEW CHECKPOINT**: Present validation results to user:

**Action**: Show validation results:
- "Validation complete. Here are the results:"
- List any errors or warnings found
- If errors found: "I found some issues. Should I fix them now?"
- If no errors: "All files validated successfully!"

**Action**: If errors found:
- Fix the issues
- Re-validate
- Show updated results
- Get user confirmation that issues are resolved

**Wait for user acknowledgment before proceeding to summary.**

### 5.2 Generate Summary

**Action**: Present summary to user using this structured template:

### 5.2.1 Summary Template

**Use this structure for summary**:

1. **Pipeline Overview**:
   - **Name**: {Pipeline Name}
   - **ID**: {pipeline_id}
   - **Description**: {Detailed description}
   - **Number of Agents**: {count}
   - **Workflow Pattern**: {type} with {description}
   - **HITL Gates**: {count} gates ({types})
   - **Final Output**: From {agent_id} with fields {selectors}

2. **Agents Summary**:
   For each agent:
   - **ID**: {agent_id}
   - **Role**: {role description}
   - **Protocol**: A2A (for remote agents)
   - **MCP Tools**: {tools or "None"}
   - **Run Mode**: {local/remote} (from Step 1.9)
   - **Remote Config**: URL assigned (url: http://127.0.0.1:8100/{agent_id}) - All agents have remote config

3. **Workflow Pattern**:
   - **Type**: {sequential/parallel/loop/conditional}
   - **Structure**: {text description or diagram}
   - **Execution Flow**: {step-by-step flow}

4. **HITL Gates**:
   For each gate:
   - **ID**: {gate_id}
   - **Type**: {approval/input/selection}
   - **Placement**: After {agent_id}
   - **Purpose**: {description}

5. **Files Generated** (all relative to base path: `{base_path}`):
   - Pipeline config: Base: `{base_path}` → `config/pipelines/{pipeline_id}.yml`
   - Agent configs: Base: `{base_path}` → `config/agents/{agent_id}.yml` (list all)
   - Prompt templates: Base: `{base_path}` → `config/prompts/{agent_id}.jinja` (list all)
   - UI manifest: Base: `{base_path}` → `config/ui_manifests/{pipeline_id}.yml`
   - Icon Suggestions: List suggested Lucide icons for pipeline and agents (user will download and add them)
   - Updated files: 
     - Base: `{base_path}` → `config/pipeline.yml`
     - Base: `{base_path}` → `config/ui_manifest.yml`
     - Base: `{base_path}` → `config/prompts/assistant_intent_classifier.jinja` (added pipeline entry)

6. **Icon Suggestions** (for user to implement):
   - **Pipeline Icon**: [Icon Name](https://lucide.dev/icons/{icon-name}) - {description}
   - For each agent: [Icon Name](https://lucide.dev/icons/{icon-name}) - {description}
   - **Note**: User should download icons from Lucide and save as SVG files in Base: `{base_path}` → `ui/static/assets/`
   - **Note**: Workflow diagram is auto-generated - no manual creation needed

7. **Next Steps**:
   - How to test the pipeline (see 5.4.1)
   - How to run the pipeline
   - What might need adjustment (if any)
   - How to add icons:
     - Download suggested Lucide icons from https://lucide.dev/icons/{icon-name}
     - Save as SVG files in Base: `{base_path}` → `ui/static/assets/`
     - Ensure file names match the references in UI manifest

### 5.3 User Review: Final Summary

**🔍 REVIEW CHECKPOINT**: Present final summary and get user confirmation:

**Action**: After presenting summary, ask:
- "Does this summary look correct?"
- "Are you satisfied with the generated pipeline?"
- "Would you like me to make any final adjustments?"

**Action**: Get final approval:
- "Pipeline generation is complete. Is there anything else you'd like me to modify or explain?"

### 5.4 Post-Generation Notes

### 5.4.1 Testing Pipeline

**Steps to test generated pipeline**:

1. **Validate Configuration**:
   ```bash
   topaz-agent-kit validate <project_dir>
   ```
   - Fix any validation errors before proceeding

2. **Test Individual Agents** (optional but recommended):
   - Test each agent with sample inputs
   - Verify output format matches expected schema
   - Check error handling with invalid inputs

3. **Test Full Pipeline**:
   - Run end-to-end scenario with realistic input
   - Verify all agents execute in correct order
   - Check that data flows correctly between agents

4. **Test HITL Gates**:
   - Verify gates appear correctly in UI
   - Test all gate actions (approve, reject, continue, retry)
   - Verify user input is stored in context correctly

5. **Test Output**:
   - Verify final output format matches expectations
   - Check that all expected fields are present
   - Verify error handling works correctly

6. **Test Error Handling**:
   - Test with invalid inputs
   - Test with missing required fields
   - Verify error messages are clear

**Action**: Provide guidance on:
- Testing the pipeline (see above)
- Making minor adjustments if needed
- Adding icons:
  - Download suggested Lucide icons from https://lucide.dev/icons/{icon-name}
  - Save as SVG files in Base: `{base_path}` → `ui/static/assets/`
  - Ensure file names match the references in UI manifest
  - Workflow diagram is auto-generated - no manual creation needed
- Adding additional features

## Common Patterns & Examples

### Final Response Agent Pattern

**When to Use**:
- Multiple agents produce outputs that need to be combined into a unified final package
- Conditional agents may or may not run, but final output should always include their results if present
- Complex formatting or combination logic is better handled by an agent than Jinja2 transforms

**Pattern Structure**:
```yaml
pattern:
  type: sequential
  steps:
    - node: response_generator
    - type: sequential
      condition: "sentiment_analyzer.escalation_recommended == true"
      steps:
        - node: escalation_handler
    - node: final_response  # Always runs, combines outputs
```

**Benefits**:
- Cleaner than complex Jinja2 transforms in outputs section
- Agent can intelligently combine and format multiple outputs
- Easier to maintain and understand
- Handles conditional outputs gracefully

**Final Output Configuration**:
```yaml
outputs:
  final:
    node: final_response
    selectors:
      - final_response_package
      - error
```

**Example Use Case**: Complaint Wizard pipeline
- `response_generator` creates customer-facing response
- `escalation_handler` (conditional) creates escalation documentation
- `final_response` combines both into a complete package

### Sequential Pattern
```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - node: agent2
    - node: agent3
```

### Parallel Pattern
```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - type: parallel
      steps:
        - node: agent2
        - node: agent3
    - node: agent4
```

### With HITL Gates
```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - gate: approval_gate
      on_approve: continue
      on_reject: stop
    - node: agent2
    - gate: input_gate
      on_continue: continue
      on_retry: retry_node
      retry_target: agent1
    - node: agent3
```

### Repeat Pattern (Single Agent)
```yaml
pattern:
  type: sequential
  steps:
    - node: problem_parser
    - type: parallel
      repeat:
        node: math_solver
        instances: "problem_parser.problem_count"
        instance_id_template: "{{node_id}}_instance_{{index}}"
        instance_context_key: "problem_instance"
        input_mapping:
          problem_text: "problem_parser.problems[index]"
          problem_index: "index"
    - node: report_generator
```

**Repeat Pattern (Single Agent) Notes**:
- `instances`: Can be integer or expression string (e.g., `"problem_parser.problem_count"`)
- `instance_id_template`: Template for generating unique instance IDs (supports `{{index}}` and `{{node_id}}`)
- `input_mapping`: Maps input variables to templates with `{{index}}` substitution
- `instance_context_key`: Context key for instance metadata (default: "repeat_instance")
- Each instance gets unique agent ID for proper result storage and MCP cleanup
- Results stored in `upstream[instance_id]` for downstream access

### Pipeline as Node Pattern
```yaml
# In parent pipeline config
pipelines:
  - id: math_repeater
    pipeline_file: "pipelines/math_repeater.yml"

nodes:
  - id: file_reader
    config_file: "agents/file_reader.yml"

pattern:
  type: sequential
  steps:
    - node: file_reader
    - pipeline: math_repeater  # Reuse existing pipeline
      input_mapping:
        user_text: "{{file_reader.file_content}}"  # REQUIRED: Map parent context to sub-pipeline inputs
    - node: report_generator
```

**Pipeline as Node Notes**:
- **Pipelines Registry**: Define sub-pipelines in `pipelines:` section (similar to `nodes:`)
- **Input Mapping**: REQUIRED - Maps parent pipeline context to what sub-pipeline's first node expects
- **Output Access**: Access sub-pipeline outputs via:
  - `{pipeline_id}.{node_id}.{field}` - Access specific node output
  - `{pipeline_id}.intermediate.{output_id}.{field}` - Access intermediate outputs
  - `{pipeline_id}.{field}` - Access final output
- **Supported Patterns**: Works in sequential, parallel, loop, switch, handoff, and group_chat patterns
- **Context Sharing**: Sub-pipelines share parent context and can access parent's upstream results
- **Circular Dependencies**: Automatically detected and prevented during validation

### Enhanced Repeat Pattern (Nested Sequential)
```yaml
pattern:
  type: sequential
  steps:
    - node: folder_scanner
    - type: parallel
      repeat:
        type: sequential  # NEW: Enhanced repeat pattern with nested sequential
        instances: "folder_scanner.file_count"
        instance_id_template: "file_{{index}}"
        steps:
          - node: file_reader
          - type: parallel
            repeat:
              node: problem_solver  # Nested single-agent repeat
              instances: "file_reader.problem_count"
              input_mapping:
                problem_text: "file_reader.problems[index]"
              instance_id_template: "{{node_id}}_{{index}}"
          - node: file_report_generator
    - node: final_report_generator
```

**Enhanced Repeat Pattern Notes**:
- **Nested Sequential**: Use `type: sequential` inside `repeat:` to run a sequence of agents for each instance
- **True Parallelization**: Each instance runs its complete sequence independently and in parallel
- **Nested Repeats**: Can nest single-agent repeat patterns inside the sequential steps
- **Shared Instance ID**: All agents in the same instance share the same `instance_id` (e.g., `file_0`)
- **Result Structure**: Results stored as `{instance_id: {agent_id: result}}` for nested structures
- **Access Pattern**: Downstream agents access results via `{base_agent_id}_instances.items()` (e.g., `file_report_generator_instances`)
- **Use Cases**: Processing multiple items through a multi-step pipeline (e.g., RFP pipeline, multi-file processing)

### Loop Pattern (Numeric Iteration)
```yaml
pattern:
  type: sequential
  steps:
    - node: initializer
    - type: loop
      body:
        type: sequential
        steps:
          - node: processor
          - gate: continue_loop
            condition: "processor.has_more == true"
      termination:
        max_iterations: 10
        condition: "processor.has_more == false"  # Optional: early exit
    - node: finalizer
```

**Numeric Loop Pattern Notes**:
- **Max Iterations**: Can be a static integer or expression (e.g., `"min(file_count, 50)"`)
- **Early Termination**: Optional `termination.condition` can stop loop before max iterations
- **Loop Context**: Injects `loop_iteration` (0-based), `iteration` (1-based) into context
- **State Preservation**: Context persists across iterations for stateful processing
- **Use Cases**: Iterative refinement, queue processing, stateful workflows

### Loop Pattern (List Iteration with iterate_over)
```yaml
pattern:
  type: sequential
  steps:
    - node: scanner  # Produces items_list: [{id: 1, path: "..."}, {id: 2, path: "..."}]
    - type: loop
      condition: "scanner.total_count > 0"  # Optional: skip if list is empty
      iterate_over: "scanner.items_list"    # Path to the list/array
      loop_item_key: "current_item"         # Context key (default: "loop_item")
      termination:
        max_iterations: 100  # Optional: safety limit
      body:
        type: sequential
        steps:
          - node: processor  # Accesses current_item.id, current_item.path, etc.
          - node: validator
          - node: recorder
    - node: finalizer
```

**List Iteration Pattern Notes**:
- **`iterate_over`**: Path to list/array from previous agent (e.g., `"scanner.pending_claims_list"`)
- **`loop_item_key`**: Context key where current item is injected (default: `"loop_item"`)
- **Automatic Termination**: Loop terminates when all items in list are processed
- **Accessing Current Item**: Use `{{current_item.field_name}}` in prompts and input mappings
- **Safety Limit**: `max_iterations` is optional but recommended for large lists
- **Pattern-Level Condition**: Optional `condition` to skip loop entirely if list is empty
- **Use Cases**: Processing pending claims, files, emails, orders from a queue or database

**Example: ECI Claims Vetter**:
```yaml
- type: loop
  condition: "eci_pending_claims_scanner.total_pending_count > 0"
  iterate_over: "eci_pending_claims_scanner.pending_claims_list"
  loop_item_key: "current_claim"
  termination:
    max_iterations: 100
  body:
    type: sequential
    steps:
      - node: eci_claims_extractor  # Accesses current_claim.claim_id, current_claim.claim_form_path
      - node: eci_claim_validator    # Accesses current_claim.claim_id
```

**Loop vs Repeat Pattern**:
- **Loop**: Sequential execution (one after another), shared state, order-dependent
- **Repeat**: Parallel execution (all at once), isolated instances, independent processing

### Conditional Logic
```yaml
pattern:
  type: sequential
  steps:
    - node: classifier
    - gate: route_decision
      on_option_a: continue
      on_option_b: branch_to_agent_b
    - node: agent_a
```

## Important Reminders

1. **Production-Ready**: Generate complete, runnable configs, not templates
2. **Use-Case Specific**: All content (prompts, descriptions) should be tailored to the specific use case
3. **Validation**: Always validate before completion
4. **Consistency**: Follow existing patterns and naming conventions
5. **Completeness**: Ensure all required sections are included in each file
6. **References**: Check that all file references are correct
7. **Context Variables**: Ensure prompt inputs reference valid context variables

## Troubleshooting

### Common Validation Errors and Fixes

**1. Intermediate Outputs with `id` Field**:
- **Error**: `Additional properties are not allowed ('id' was unexpected) at outputs.intermediate.0`
- **Cause**: Intermediate outputs schema does NOT allow `id` fields
- **Fix**: Remove `id` from all intermediate output entries. Only use `node`, `selectors`, and optional `transform`
- **Correct Format**:
  ```yaml
  outputs:
    intermediate:
      - node: agent_id
        selectors:
          - field1
          - field2
  ```
- **Incorrect Format**:
  ```yaml
  outputs:
    intermediate:
      - id: output_name  # ❌ WRONG - 'id' not allowed
        node: agent_id
        selectors:
          - field1
  ```

**2. Variables in Prompt Files**:
- **Error**: Variables appearing in prompt `.jinja` files
- **Cause**: Variables should be in agent YML `inputs.inline`, not in prompt files
- **Fix**: 
  - Remove all variables from prompt files (`.jinja`)
  - Move all variables to agent YML `prompt.inputs.inline` section
- **Correct Format**:
  ```jinja
  # Prompt file: prompts/agent_id.jinja
  You are a **Parser Agent**, specializing in extracting structured information.
  
  Tasks:
  1. Extract field1 from input
  2. Extract field2 from input
  ```
  ```yaml
  # Agent YML: agents/agent_id.yml
  prompt:
    instruction:
      jinja: prompts/agent_id.jinja
    inputs:
      inline: |
        User Input: {{user_text}}
        Field1: {{field1}}
  ```
- **Incorrect Format**:
  ```jinja
  # ❌ WRONG - Variables in prompt file
  You are a **Parser Agent**.
  
  User Input: {{user_text}}  # ❌ WRONG
  ```

**3. Agent IDs in Input Variables**:
- **Error**: Variables using agent prefixes like `{{agent_id.field}}`
- **Cause**: Context resolution uses field names directly, not agent prefixes
- **Fix**: Use field names directly: `{{field}}` instead of `{{agent_id.field}}`
- **Correct Format**:
  ```yaml
  inputs:
    inline: |
      Complaint Type: {{complaint_type}}
      Billing Issues: {{billing_issues}}
  ```
- **Incorrect Format**:
  ```yaml
  inputs:
    inline: |
      Complaint Type: {{complaint_wizard_parser.complaint_type}}  # ❌ WRONG
      Billing Issues: {{complaint_wizard_parser.billing_issues}}   # ❌ WRONG
  ```

**4. Python-Style Conditionals in Jinja2 Templates**:
- **Error**: `JSONUtils: Expected JSON but parsing failed` when using Python-style conditionals
- **Cause**: Using Python-style conditionals like `{{var if var is not none else "default"}}` in Jinja2 templates causes parsing errors
- **Fix**: Use proper Jinja2 conditional blocks: `{% if variable %}...{% endif %}`
- **Correct Format**:
  ```yaml
  inputs:
    inline: |
      Complaint Type: {{complaint_type}}
      {% if amount_mentioned %}Amount Mentioned: {{amount_mentioned}}{% endif %}
      {% if timeframe %}Timeframe: {{timeframe}}{% endif %}
  ```
- **Incorrect Format**:
  ```yaml
  inputs:
    inline: |
      Amount Mentioned: {{amount_mentioned if amount_mentioned is not none else "not mentioned"}}  # ❌ WRONG
      Timeframe: {{timeframe if timeframe is not none else "not specified"}}  # ❌ WRONG
  ```

**4. Missing Section Comments in Agent YMLs**:
- **Error**: Agent YML files missing proper section comments
- **Cause**: Section comments help with readability and consistency
- **Fix**: Add properly formatted section comments matching reference format:
  ```yaml
  # =============================================================================
  # PARSER AGENT CONFIGURATION
  # =============================================================================
  #
  # This agent parses user input to extract structured information...
  #
  # =============================================================================
  id: agent_id
  ...
  ```

**5. Dynamic Gate Descriptions**:
- **Pattern**: Gate descriptions can use Jinja2 templates to dynamically display content from upstream agents
- **Use Case**: Show actual analysis results, explanations, or context in gate descriptions instead of static text
- **Simple Inline Format** (for short descriptions):
  ```yaml
  gates:
    - id: approve_root_cause
      type: approval
      title: "Approve Root Cause Analysis"
      description: "{{ agent_id.explanation | default('Review the identified root cause and approve to proceed.') }}"
  ```
- **External Jinja File Format** (for complex descriptions):
  ```yaml
  gates:
    - id: review_claim
      type: selection
      title: "Claim Decision Review"
      description:
        jinja: "hitl/eci_decision_gate.jinja"  # Path relative to config/ directory
  ```
- **When to Use Each**:
  - **Inline**: Simple descriptions (1-10 lines), single-line dynamic content, quick prototypes
  - **External File**: Complex descriptions (50+ lines), multiple sections, extensive tables, complex conditionals
- **Variable Access**: Use `agent_id.field` syntax for explicit access, or `field` if the field name is unique across all upstream agents
- **Examples**: 
  - `eci_decision_gate.jinja` - Complex gate with multiple sections, tables, and validation summaries
  - `tci_recommendation_review_gate.jinja` - Extensive risk assessment display with multiple tables
- **Note**: Both `{{ agent_id.field }}` and `{{ field }}` work, but `agent_id.field` is more explicit and recommended

**6. Final Response Agent Pattern**:
- **Pattern**: When multiple agents produce outputs that need to be combined (e.g., customer response + escalation info), use a final response agent instead of complex transforms
- **Use Case**: Combining outputs from response generator and escalation handler into a unified final package
- **Correct Pattern**:
  ```yaml
  pattern:
    type: sequential
    steps:
      - node: response_generator
      - type: sequential
        condition: "sentiment_analyzer.escalation_recommended == true"
        steps:
          - node: escalation_handler
      - node: final_response  # Always runs, combines outputs
  ```
- **Benefits**: 
  - Cleaner than complex Jinja2 transforms in outputs
  - Allows agent to intelligently combine and format multiple outputs
  - Easier to maintain and understand
- **Final Output**: Use final_response agent output as the pipeline's final output

**7. MCP Tools - Only Add When Needed**:
- **Error**: Adding MCP tools to agents that don't actually need external capabilities
- **Cause**: Not all agents need external tools - some only process data from upstream agents
- **Fix**: Only add MCP configuration when agent truly needs external tools (web search, data retrieval, etc.)
- **When to Add MCP**:
  - Agent needs to search the web or external databases
  - Agent needs to call external APIs
  - Agent needs real-time data not available in context
- **When NOT to Add MCP**:
  - Agent only processes data from upstream agents
  - Agent generates content based on provided context
  - Agent analyzes mock/generated data
- **Example**: Account researcher that analyzes mock account data doesn't need MCP tools - it only processes provided data

**If user requests changes after generation**:
- Make the requested changes
- Re-validate affected files
- Update summary if needed

**If validation fails**:
- Identify the issue using the common errors above
- Fix the problem
- Re-validate
- Explain the fix to the user

**If files already exist**:
- Check with user before overwriting
- Offer to backup existing files
- Show diff if possible

## Workflow Completion

When following this workflow:
1. Work step-by-step with the user through each phase
2. Don't skip steps - ensure user approval at each major decision point
3. Generate files only after final design approval
4. Always validate before declaring completion
5. Provide clear summary of what was generated and next steps

This workflow ensures consistent, production-ready pipeline generation every time.

---

## Jinja2 Filters Reference

The Topaz Agent Kit provides a comprehensive set of Jinja2 filters that are automatically available in all templates, including:
- Pattern descriptions (pipeline YAML files)
- HITL gate descriptions
- Agent input templates (YAML `inputs.inline` sections)

### Number Formatting Filters

**`format_currency(value, decimals=2)`**
- Formats numbers as currency with commas and decimal places
- Example: `{{ 125000 | format_currency }}` → `"125,000.00"`
- Example: `{{ 125000 | format_currency(decimals=0) }}` → `"125,000"`

**`format_number(value, decimals=0, thousands_sep=",")`**
- Generic number formatting with optional decimals and thousands separator
- Example: `{{ 1250.5 | format_number(decimals=2) }}` → `"1,250.50"`

**`format_percentage(value, decimals=1, multiply=True)`**
- Formats numbers as percentages
- Example: `{{ 0.85 | format_percentage }}` → `"85.0%"`
- Example: `{{ 0.8523 | format_percentage(decimals=2) }}` → `"85.23%"`

### Score/Risk Color Coding Filters

**`risk_score_color(value)`**
- Returns color code for risk scores where **lower is better** (0-100 scale)
- Color mapping:
  - 0-25: `#22c55e` (green - low risk)
  - 26-50: `#f59e0b` (amber - medium risk)
  - 51-75: `#ef4444` (red - high risk)
  - 76-100: `#dc2626` (dark red - very high risk)
- Example: `<span style="color: {{ risk_score | risk_score_color }};">{{ risk_score }}</span>`

**`credit_score_color(value)`**
- Returns color code for credit/quality scores where **higher is better** (0-100 scale)
- Color mapping:
  - 85-100: `#22c55e` (green - excellent)
  - 70-84: `#f59e0b` (amber - good)
  - 50-69: `#ef4444` (red - fair)
  - <50: `#dc2626` (dark red - poor)
- Example: `<span style="color: {{ credit_score | credit_score_color }};">{{ credit_score }}</span>`

**`score_color(value, thresholds=None, low_is_better=False)`**
- Generic score color coding with configurable thresholds
- `thresholds`: List of `(threshold, color)` tuples in ascending order
- `low_is_better`: If `True`, lower scores are better (inverts logic)
- Example: `{{ score | score_color(thresholds=[(80, "#green"), (60, "#yellow"), (0, "#red")]) }}`

### Text Formatting Filters

**`truncate_text(value, max_length=100, suffix="...")`**
- Truncates text to maximum length with suffix
- Example: `{{ "Very long text here" | truncate_text(10) }}` → `"Very long..."`

**`pluralize(value, singular, plural=None)`**
- Returns singular or plural form based on count
- Example: `{{ 5 | pluralize("item") }}` → `"items"`
- Example: `{{ 1 | pluralize("child", "children") }}` → `"child"`

**`highlight_text(value, search_terms, highlight_class="highlight")`**
- Highlights search terms in text (wraps in `<mark>` tags)
- Example: `{{ text | highlight_text("search term") }}`

### Date/Time Formatting Filters

**`format_date(value, format_str="%Y-%m-%d")`**
- Formats date/datetime values
- Example: `{{ "2025-01-28" | format_date }}` → `"2025-01-28"`
- Example: `{{ "2025-01-28" | format_date("%B %d, %Y") }}` → `"January 28, 2025"`

**`format_duration(seconds, compact=False)`**
- Formats duration in seconds as human-readable string
- Example: `{{ 3665 | format_duration }}` → `"1 hour 1 minute 5 seconds"`
- Example: `{{ 3665 | format_duration(compact=True) }}` → `"1h 1m 5s"`

### Data Formatting Filters

**`format_file_size(value, binary=False)`**
- Formats bytes as human-readable file size
- Example: `{{ 1572864 | format_file_size }}` → `"1.5 MB"`
- Example: `{{ 1572864 | format_file_size(binary=True) }}` → `"1.5 MiB"`

**`mask_sensitive(value, visible_chars=4, mask_char="*")`**
- Masks sensitive data, showing only first N characters
- Example: `{{ "1234567890" | mask_sensitive(4) }}` → `"1234******"`

**`format_phone(value, format_str="us")`**
- Formats phone numbers
- Example: `{{ "1234567890" | format_phone }}` → `"(123) 456-7890"`
- Options: `"us"`, `"international"`, `"compact"`

### Utility Filters

**`safe_divide(numerator, denominator, default=0)`**
- Safely divides two numbers, returning default if denominator is zero
- Example: `{{ 10 | safe_divide(2) }}` → `5.0`
- Example: `{{ 10 | safe_divide(0, "N/A") }}` → `"N/A"`

**`default_if_none(value, default="N/A")`**
- Returns default value if input is None
- Example: `{{ None | default_if_none("—") }}` → `"—"`

### Markdown Table Formatting in HITL Gates

When using markdown tables in HITL gate descriptions, follow these critical rules to ensure proper rendering:

1. **No Blank Lines Within Tables**: Blank lines between table rows break markdown table formatting
   ```jinja
   ❌ BAD:
   {% if condition %}
   
   | Status | {{ status }} |
   {% endif %}
   
   ✅ GOOD:
   {%- if condition %}
   | Status | {{ status }} |
   {%- endif %}
   ```

2. **Whitespace Control for Conditionals**: Always use `{%-` and `-%}` for conditionals in table cells
   ```jinja
   ❌ BAD:
   | Amount | {% if sym %}{{ sym }}{{ amount | format_currency }}{% else %}N/A{% endif %} |
   
   ✅ GOOD:
   | Amount | {%- if sym %}{{ sym }}{{ amount | format_currency }}{%- else %}N/A{%- endif %} |
   ```

3. **Nested Conditionals**: Apply whitespace control to conditionals, but NOT to `{% set %}` statements (they need newlines for markdown tables)
   ```jinja
   ❌ BAD (whitespace control on set strips newline):
   | Amount | {%- if has_amount %}{%- set sym = currency_symbol %}{%- if sym | length >= 3 %}{{ sym }} {{ amount }}{%- else %}{{ sym }}{{ amount }}{%- endif %}{%- else %}N/A{%- endif %} |
   
   ✅ GOOD (no whitespace control on set, preserves newlines):
   | Amount | {%- if has_amount %}{% set sym = currency_symbol %}{%- if sym | length >= 3 %}{{ sym }} {{ amount }}{%- else %}{{ sym }}{{ amount }}{%- endif %}{%- else %}N/A{%- endif %} |
   ```

4. **checks_table Pattern**: Use `{{ checks_table }}` (not `{{- checks_table -}}`) to preserve newlines, and ensure blank line after `</summary>`. Use `{% if %}` (NOT `{%- if %}`) for conditionals around checks_table to preserve newlines.
   ```jinja
   ❌ BAD (strips newlines, breaks table):
   {%- if agent.checks_table %}{{- agent.checks_table -}}{%- else %}
   **Summary:** {{ agent.details }}
   {%- endif %}
   
   ❌ BAD (no blank line after </summary>, table won't render):
   <details>
   <summary>Test Summary</summary>
   {%- if agent.checks_table %}
   {{ agent.checks_table }}
   {%- endif %}
   </details>
   
   ✅ GOOD (preserves newlines, blank line after </summary>, no whitespace control on if):
   <details>
   <summary>Test Summary</summary>
   
   {% if agent.checks_table %}
   {{ agent.checks_table }}
   
   {% endif %}
   </details>
   ```

5. **Set Statements Before Table Rows**: Use `{% set %}` (NOT `{%- set %}`) when used before markdown tables, especially in `<details>` blocks. The whitespace control strips newlines that markdown tables need.
   ```jinja
   ❌ BAD (whitespace control strips newline, breaks table rendering):
   <details>
   <summary>Test Summary</summary>
   
   {%- set fh_score = assessor.score if assessor else None %}
   {% if agent.checks_table %}
   {{ agent.checks_table }}
   {% endif %}
   </details>
   
   ✅ GOOD (no whitespace control on set, preserves newlines):
   <details>
   <summary>Test Summary</summary>
   
   {% set fh_score = assessor.score if assessor else None %}
   {% if agent.checks_table %}
   {{ agent.checks_table }}
   {% endif %}
   </details>
   ```
   
   **Also**: Put `{% set %}` statements on separate lines before table rows, not inline
   ```jinja
   ❌ BAD (set on same line as table row, breaks formatting):
   | Risk Factor | Score | Weight | Weighted Score |
   |-------------|-------|--------|----------------|
   {% set fh_score_val = tci_financial_health_assessor.score if tci_financial_health_assessor else None %}| Financial Health | {{ fh_score_val | default_if_none }} | 0.22 | {{ fh_weighted | default_if_none }} |
   
   ✅ GOOD (set on separate line before table row):
   | Risk Factor | Score | Weight | Weighted Score |
   |-------------|-------|--------|----------------|
   {% set fh_score_val = tci_financial_health_assessor.score if tci_financial_health_assessor else None %}
   {% set fh_weighted = (fh_score_val * 0.22) | round(2) if fh_score_val is not none else None %}
   | Financial Health | {{ fh_score_val | default_if_none }} | 0.22 | {{ fh_weighted | default_if_none }} |
   ```

6. **Filters Don't Introduce Whitespace**: Filters themselves are safe, but Jinja2 tags need control
   ```jinja
   ✅ SAFE (filters don't add whitespace):
   | Amount | {{ amount | format_currency }} |
   | Status | {{ status | default_if_none }} |
   
   ⚠️ NEEDS CONTROL (tags add whitespace):
   | Amount | {%- set sym = currency_symbol %}{{ amount | format_currency(currency_symbol=sym) }} |
   ```

7. **Tables Inside HTML Tags**: Markdown tables inside HTML tags (like `<details>`) require a blank line after the closing tag
   ```jinja
   ❌ BAD (table starts on same line as </summary>):
   <details>
   <summary>Test Summary</summary>
   | Check | Status |
   |-------|--------|
   | Test | PASS |
   </details>
   
   ✅ GOOD (blank line after </summary>):
   <details>
   <summary>Test Summary</summary>
   
   | Check | Status |
   |-------|--------|
   | Test | PASS |
   </details>
   ```

**Key Learnings from Testing**:
- **Blank lines within tables**: Break markdown rendering - never include blank lines between table rows
- **Blank lines before tables**: Required when tables are inside HTML tags (e.g., `<details>`)
- **checks_table pattern**: Use `{{ checks_table }}` (not `{{- checks_table -}}`) to preserve newlines that are part of the table structure
- **Whitespace control for conditionals**: Use `{%-` and `-%}` for conditionals and loops within table cells
- **Set statements**: Use `{% set %}` (NOT `{%- set %}`) when used before markdown tables - whitespace control strips newlines that markdown parsers need
- **Set statement placement**: Place `{% set %}` statements on separate lines before table rows, not inline

**Testing**: Use the `tests/test_markdown_tables.py` script to validate table formatting before deployment:
```bash
python tests/test_markdown_tables.py
# or
python -m pytest tests/test_markdown_tables.py -v
```

The test script generates markdown files in `tests/output/markdown_tables/` for visual inspection and validates:
- No blank lines within tables
- Tables don't start on the same line as previous content
- Consistent column counts across all table rows
- Proper whitespace control in conditionals

### Usage Examples in Templates

**Pattern Descriptions:**
```yaml
description: |
  ## Current Claim Details
  
  | Field | Value |
  |-------|-------|
  | Claim Amount | {{ current_claim.currency_symbol }}{{ current_claim.invoice_amount | format_currency }} |
  | Risk Score | <span style="color: {{ risk_score | risk_score_color }};">{{ risk_score }}</span>/100 |
```

**HITL Gate Descriptions:**
```yaml
description: |
  **Application ID:** {{ current_application.application_id }}
  **Requested Amount:** {{ current_application.requested_amount | format_currency }}
  **Credit Score:** <span style="color: {{ credit_score | credit_score_color }};">{{ credit_score }}</span>
```

**Markdown Table Formatting in HITL Gates:**

When using markdown tables in HITL gate descriptions, follow these critical rules to ensure proper rendering:

1. **No Blank Lines Within Tables**: Blank lines between table rows break markdown table formatting
   ```jinja
   ❌ BAD:
   {% if condition %}
   
   | Status | {{ status }} |
   {% endif %}
   
   ✅ GOOD:
   {%- if condition %}
   | Status | {{ status }} |
   {%- endif %}
   ```

2. **Whitespace Control for Conditionals**: Always use `{%-` and `-%}` for conditionals in table cells
   ```jinja
   ❌ BAD:
   | Amount | {% if sym %}{{ sym }}{{ amount | format_currency }}{% else %}N/A{% endif %} |
   
   ✅ GOOD:
   | Amount | {%- if sym %}{{ sym }}{{ amount | format_currency }}{%- else %}N/A{%- endif %} |
   ```

3. **Nested Conditionals**: Apply whitespace control to conditionals, but NOT to `{% set %}` statements (they need newlines for markdown tables)
   ```jinja
   ❌ BAD (whitespace control on set strips newline):
   | Amount | {%- if has_amount %}{%- set sym = currency_symbol %}{%- if sym | length >= 3 %}{{ sym }} {{ amount }}{%- else %}{{ sym }}{{ amount }}{%- endif %}{%- else %}N/A{%- endif %} |
   
   ✅ GOOD (no whitespace control on set, preserves newlines):
   | Amount | {%- if has_amount %}{% set sym = currency_symbol %}{%- if sym | length >= 3 %}{{ sym }} {{ amount }}{%- else %}{{ sym }}{{ amount }}{%- endif %}{%- else %}N/A{%- endif %} |
   ```

4. **checks_table Pattern**: Use `{{ checks_table }}` (not `{{- checks_table -}}`) to preserve newlines, and ensure blank line after `</summary>`. Use `{% if %}` (NOT `{%- if %}`) for conditionals around checks_table to preserve newlines.
   ```jinja
   ❌ BAD (strips newlines, breaks table):
   {%- if agent.checks_table %}{{- agent.checks_table -}}{%- else %}
   **Summary:** {{ agent.details }}
   {%- endif %}
   
   ❌ BAD (no blank line after </summary>, table won't render):
   <details>
   <summary>Test Summary</summary>
   {%- if agent.checks_table %}
   {{ agent.checks_table }}
   {%- endif %}
   </details>
   
   ✅ GOOD (preserves newlines, blank line after </summary>, no whitespace control on if):
   <details>
   <summary>Test Summary</summary>
   
   {% if agent.checks_table %}
   {{ agent.checks_table }}
   
   {% endif %}
   </details>
   ```

5. **Filters Don't Introduce Whitespace**: Filters themselves are safe, but Jinja2 tags need control
   ```jinja
   ✅ SAFE (filters don't add whitespace):
   | Amount | {{ amount | format_currency }} |
   | Status | {{ status | default_if_none }} |
   
   ⚠️ NEEDS CONTROL (tags add whitespace):
   | Amount | {%- set sym = currency_symbol %}{{ amount | format_currency(currency_symbol=sym) }} |
   ```

**Testing**: Use the `tests/test_markdown_tables.py` script to validate table formatting before deployment:
```bash
python tests/test_markdown_tables.py
# or
python -m pytest tests/test_markdown_tables.py -v
```
```

**Agent Input Templates:**
```yaml
inputs:
  inline: |
    Amount: {{ amount | format_currency }}
    Percentage: {{ ratio | format_percentage }}
    Date: {{ date | format_date("%B %d, %Y") }}
```

### Best Practices

1. **Use filters consistently**: Always use `format_currency` instead of `round(2)` for monetary values
2. **Color coding**: Use `risk_score_color` or `credit_score_color` instead of inline color logic
3. **Handle None values**: Use `default_if_none` or conditional rendering for optional fields
4. **Readability**: Use filters to improve template readability and maintainability

