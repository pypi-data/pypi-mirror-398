---
description: Create architecture decision records (ADR) using MADR format through guided questioning workflow.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan that incorporates the decisions documented in docs/decisions/
    send: false
scripts:
  sh: scripts/bash/setup-decide.sh --json "{ARGS}"
  ps: scripts/powershell/setup-decide.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON output:
   - `REPO_ROOT`: Repository root path
   - `DECISIONS_DIR`: docs/decisions/ directory path
   - `ADR_NUMBER`: Next available ADR number in 4-digit format (0001, 0002, etc.)
   - `TEMPLATE_PATH`: Path to decide-template.md

2. **Initial Context Gathering**:
   - If user provided a decision topic in arguments, use it as the starting point
   - Otherwise, ask: "What architectural decision needs to be made?"
   - Extract the core problem/question to be decided

3. **Interactive Questioning Workflow**:

   Ask questions sequentially, building the ADR structure:

   a. **Decision Title & Problem Statement**:
      - "What is a concise title for this decision? (e.g., 'Use PostgreSQL for Data Persistence')"
        - Wait for user response
        - Generate short-name from title (steps below)
      - "Describe the context and problem this decision addresses (2-3 sentences)"
        - Wait for user response

   b. **Decision Drivers** (Optional):
      - "Does this decision have key drivers or forces? Examples: performance requirements, team expertise, cost constraints, scalability needs (yes/skip)"
      - If yes:
        - "List the decision drivers (one per line)"
        - Wait for user response
      - If skip: mark as skipped

   c. **Considered Options**:
      - "What options are you considering? (You need at least 2 alternatives)"
      - For each option:
        - "Option title: [user enters title]"
        - "Brief description: [user enters description]"
        - "Pros (list 2-4 points): [user enters pros]"
        - "Cons (list 2-4 points): [user enters cons]"
      - After collecting option 1 and 2:
        - "Are there more options to consider? (yes/no)"
        - If yes, repeat for option 3, etc.
        - If no, proceed to Decision Outcome

   d. **Decision Outcome**:
      - Present the list of considered options
      - "Which option did you choose? [user selects one]"
      - "Why did you choose this option? What makes it better than the alternatives?"
        - Wait for user response (justification)
      - "Decision Status? (options: proposed, accepted, rejected, deprecated, superseded by ADR-XXXX)"
        - Default to "proposed"
        - Wait for user response

   e. **Consequences** (Optional):
      - "Does this decision have notable consequences? (yes/skip)"
      - If yes:
        - "Positive consequences (list 2-4 points): [user enters positive impacts]"
        - "Negative consequences or trade-offs (list 2-4 points): [user enters negative impacts]"
      - If skip: mark as skipped

   f. **Confirmation** (Optional):
      - "How will you validate/confirm this decision is implemented correctly? (skip for none)"
      - Examples: "code review checklist, automated tests, architecture validation"
      - Wait for user response

4. **Generate Short Name from Title**:
   - Convert title to lowercase
   - Replace spaces with hyphens
   - Remove special characters (keep only alphanumeric, hyphens, and underscores)
   - Remove leading/trailing hyphens
   - Replace multiple consecutive hyphens with single hyphen
   - Limit to 50 characters (truncate if longer)
   - If empty after processing, use "untitled"
   - Example: "Use PostgreSQL for Data Persistence" ’ "use-postgresql-for-data-persistence"
   - Example: "Use C++ & Rust for Performance-Critical APIs" ’ "use-c-rust-for-performance-critical-apis"

5. **Generate ADR File**:
   - Read `TEMPLATE_PATH` (decide-template.md)
   - Create ADR file at: `{DECISIONS_DIR}/{ADR_NUMBER}-{short-name}.md`
   - Fill in sections based on user responses:
     - Title: Use the decision title provided by user
     - YAML Frontmatter:
       - status: User-provided or default "proposed"
       - date: Current date in YYYY-MM-DD format
       - decision-makers: Ask user or use "Development Team" as default
       - consulted: Ask if applicable (optional)
       - informed: Ask if applicable (optional)
     - Context and Problem Statement: Use user response
     - Decision Drivers: Use collected items (if provided)
     - Considered Options: List titles only
     - Pros and Cons of the Options: Use collected points for each option
     - Decision Outcome: "Chosen option: '{chosen_title}', because {justification}"
     - Consequences: Use collected positive/negative impacts (if provided)
     - Confirmation: Use validation approach (if provided)
     - More Information: Leave as template (user can fill later)
   - Remove sections marked as skipped:
     - Delete "## Decision Drivers" section if skipped
     - Delete "### Consequences" section if skipped
     - Delete "### Confirmation" section if skipped
     - Clean up any excess blank lines (max 2 consecutive blank lines)

6. **Validation & File Writing**:
   - Verify ADR file path is valid (no path traversal)
   - Verify filename doesn't exceed filesystem limits
   - Write file with UTF-8 encoding
   - If write fails, report error with specific reason

7. **Summary & Next Steps**:
   - Display the ADR file path created: `docs/decisions/{ADR_NUMBER}-{short-name}.md`
   - Show a summary of the decision:
     - Title
     - Chosen option
     - Status
   - Suggest: "Run `/speckit.plan` to update your implementation plan based on this decision"
   - List the new ADR for reference:
     - "New ADR: {ADR_NUMBER} - {title}"
     - Link to: docs/decisions/{ADR_NUMBER}-{short-name}.md

## Guidelines

### Question Flow Best Practices

Present each question clearly with:
- Bold label for the question topic
- Clear instructions and examples
- Inline suggestions where helpful
- Allow "skip" or "yes/no" for optional sections

### MADR Compliance

- Follow https://adr.github.io/madr/ template structure
- Keep the format clean and scannable
- Preserve markdown formatting
- Use proper heading hierarchy (# for title, ## for sections)
- Remove optional sections if user didn't provide content

### Error Handling

- If user provides invalid input, re-ask with clarification
- If ADR_NUMBER cannot be determined, start with 0001
- If docs/decisions/ directory doesn't exist, the script creates it
- Validate status is one of: proposed, rejected, accepted, deprecated, superseded by ADR-XXXX
- If user enters custom status not in list, ask for clarification

### File Name Generation Best Practices

- Remove all special characters except hyphens and underscores
- Convert multiple consecutive hyphens to single hyphen
- Ensure filename is filesystem-safe (no reserved names)
- Truncate at 50 characters if too long (this avoids filesystem limits)
- Log the mapping: "Title: '{title}' ’ File: '{ADR_NUMBER}-{short-name}.md'"

### Content Guidelines

- Focus on the decision, not the implementation
- Each option should be briefly described (2-3 sentences max)
- Pros and cons should be concise (bullets, not paragraphs)
- Justification should explain trade-offs clearly
- Keep language professional but conversational

## Implementation Notes

- The script `{SCRIPT}` provides the next ADR number and template path
- Parse the JSON output carefully to extract these values
- Use TEMPLATE_PATH to load the base MADR template
- Replace placeholders in the template with user-provided content
- Ensure empty sections are completely removed (including HTML comments)
- Write to disk only after all validation passes
