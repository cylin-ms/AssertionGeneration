# Mira - Assertion Quality Evaluation Tool

**Version:** 2.0 (November 2025)

> **✨ Mira** is a tool for **judges to evaluate the quality of LLM-generated assertions**. Judges review each assertion to determine if it is well-grounded in the meeting context and appropriately evaluates workback plan quality. GPT-5 JJ evaluation results are provided as **hints** to help judges quickly identify supporting evidence and make informed decisions.

---

## 🙏 Acknowledgments

| Contributor | Contribution |
|-------------|--------------|
| **Weiwei Cui** | Meeting Context Data (LOD - LiveOak Data), assertion methodology documentation |
| **Kening Ren** | Workback Plan response generation, assertions with justification and sourceID |
| **Chin-Yew Lin** | Mira annotation tool, GPT-5 JJ evaluation experiment, documentation |

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Judge's Guide: Evaluating Assertions](#judges-guide-evaluating-assertions)
4. [Using GPT-5 Results as Hints](#using-gpt-5-results-as-hints)
5. [Meeting Context & Entity Cards](#meeting-context--entity-cards)
6. [Optional: Response Annotations](#optional-response-annotations)
7. [Entity Card Rendering](#entity-card-rendering)
8. [Annotation Workflow](#annotation-workflow)
9. [Data Formats](#data-formats)
10. [Project Structure](#project-structure)
11. [Scripts Reference](#scripts-reference)
12. [Recent Changes](#recent-changes-november-2025)

---

## Overview

### What is Mira?

Mira is designed for **judges to evaluate assertion quality**. Each assertion is a statement about what a good workback plan response should contain, grounded in the meeting context data.

**Your task as a judge:**
1. Review each assertion and its justification
2. Check if the assertion is well-grounded in the meeting context (using the sourceID link)
3. Determine if the assertion is a good quality assertion (correct, clear, verifiable)
4. Mark the assertion as correct or incorrect, with optional notes

### Data Sources

| Data | Created By | Description |
|------|------------|-------------|
| **Meeting Context (LOD)** | Weiwei Cui | Entities (Events, Files, Emails, Chats, Users) that provide context |
| **Workback Plan Response** | Kening Ren | LLM-generated response to user's request |
| **Assertions** | Kening Ren | Statements about what the response should contain, with justification and sourceID |
| **GPT-5 Evaluation** | Chin-Yew Lin | Automated evaluation results to help judges (used as hints) |

### How GPT-5 Results Help Judges

The GPT-5 JJ evaluation was conducted as an **experiment** to:
1. **Verify real-world applicability**: Test how assertions might be used to automatically evaluate workback plan quality
2. **Provide hints for judges**: Help judges quickly find supporting evidence in the response
3. **Speed up annotation**: Judges can use GPT-5's pass/fail status and evidence spans as starting points

> **Note:** GPT-5 results are **hints only**. Judges should make their own independent judgment about assertion quality.

### Dataset Statistics

- **103 meetings** with workback plan requests
- **1,395 assertions** total (~13.5 per meeting)
- **GPT-5 evaluation**: 96.2% pass rate (used as reference, not ground truth)
- **SourceID Navigation**: Click "🔗 View Entity" to jump to referenced entities
- **Visual Highlighting**: Linked entities highlighted with green banner
- **Azure Key Vault Integration**: Direct links to user credentials in Test Tenant

---

## Quick Start

### Prerequisites

- Python 3.10+
- Microsoft corporate account (for Azure Key Vault access)

### Setup

```bash
git clone https://github.com/cylin-ms/AssertionGeneration.git
cd AssertionGeneration
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### Launch Mira

```bash
streamlit run mira.py
```

Open your browser to `http://localhost:8501`.

---

## Judge's Guide: Evaluating Assertions

This is the **primary task** for judges using Mira.

### What You're Evaluating

Each assertion is a statement like:
> "The response should include the project deadline of December 15th mentioned in the kickoff meeting."

Your job is to determine if this assertion is **well-formed and correctly grounded** in the meeting context.

### Step-by-Step Annotation Process

#### Step 1: Select a Meeting

1. Click on a meeting in the sidebar (📕 = Not Started, 📙 = Partially Done, 📗 = Complete)
2. Enter your name in the "👤 Judge" field at the top

#### Step 2: Review the Assertion

For each assertion card:

1. **Read the assertion text** - What is it claiming the response should contain?
2. **Check the level** - Is it Critical, Expected, or Aspirational?
3. **Review the justification** - Why was this assertion created?

#### Step 3: Verify Grounding in Meeting Context

1. **Look for the sourceID** - Each assertion links to a specific entity
2. **Click "🔗 View Entity"** - This expands the Meeting Context and highlights the source
3. **Review the source entity** - Does the assertion correctly reference this data?
4. **Check if the assertion is accurate** - Is the claim factually correct based on the entity?

#### Step 4: Make Your Judgment

| Checkbox | Meaning |
|----------|---------|
| **✅ This assertion is correct** | The assertion is well-grounded and accurate |
| **🎯 Confident in judgment** | You're sure about your decision |
| **📋 Judged** | You've finished reviewing this assertion |

#### Step 5: Add Notes (Optional)

- **Note**: Explain why an assertion is incorrect or problematic
- **Revision**: Suggest improved assertion text

### Completion Criteria

| Status | Icon | Meaning |
|--------|------|---------|
| **Fully Judged** | 📗 | All assertions in the meeting have been reviewed |
| **Partially Judged** | 📙 | Some assertions reviewed, but not all |
| **Not Started** | 📕 | No assertions reviewed yet |

### Saving Your Work

- **Auto-save**: Annotations save automatically
- **Manual save**: Click "💾 Save" anytime
- **Export**: Click "📤 Export" to create `docs/annotated_output.jsonl`

---

## Using GPT-5 Results as Hints

GPT-5 JJ was used to automatically evaluate assertions against the response. These results are provided as **hints** to help you work faster.

### How GPT-5 Results Appear

Each assertion shows a GPT-5 status in its header:
- **✅** = GPT-5 determined the assertion PASSED (response satisfies it)
- **❌** = GPT-5 determined the assertion FAILED (response doesn't satisfy it)

### What GPT-5 Provides

When you expand an assertion, you'll see:

1. **Pass/Fail Status**: GPT-5's automated judgment
2. **Explanation**: Why GPT-5 made this decision
3. **Supporting Spans**: Exact quotes from the response that GPT-5 identified as evidence
4. **Confidence Scores**: How confident GPT-5 is about each piece of evidence
5. **Section Attribution**: Which part of the response contains each span

### How to Use GPT-5 Hints

| GPT-5 Says | What You Should Do |
|------------|-------------------|
| ✅ PASSED | Use the supporting spans to quickly verify the assertion is good |
| ❌ FAILED | Check if GPT-5 is correct, or if the assertion is actually fine |
| High confidence spans | These are likely reliable evidence |
| Low confidence spans | Review these more carefully |

### Verifying or Rejecting GPT-5 Results

You can **verify or reject** GPT-5's findings:

1. **Explanation checkbox**: Uncheck if you disagree with GPT-5's reasoning
2. **Span checkboxes**: Uncheck individual evidence spans you think are wrong
3. Rejected items appear crossed out in the UI

> **Remember:** GPT-5 results are hints, not ground truth. Your judgment is what matters!

### GPT-5 Experiment Statistics

The GPT-5 evaluation was run on all 103 meetings:
- **1,395 assertions** evaluated
- **96.2% pass rate** (1,342 passed, 53 failed)
- **100% span coverage** (all assertions have supporting evidence)

---

## Meeting Context & Entity Cards

The Meeting Context contains all the source data used to generate assertions.

### Why Meeting Context Matters

Assertions reference specific entities via `sourceID`. To verify an assertion, you need to check the actual entity it references.

### Accessing Meeting Context

1. **Notice the blue banner**: "📋 Meeting Context Available"
2. **Click the expander**: "📥 View Meeting Context"
3. **Browse entities**: Each entity type has a rich card display

### Entity Card Types

| Entity Type | Icon | What It Shows |
|-------------|------|---------------|
| **Event** | 📅 | Meeting subject, time, attendees, location |
| **File** | 📄 | Document name, content preview with tabs |
| **Chat** | 💬 | Chat messages displayed as bubbles |
| **Email** | ✉️ | Subject, recipients, body preview |
| **User** | 👤 | Name, avatar, Azure Key Vault link |
| **ChannelMessage** | 📢 | Teams message with content |

### SourceID Linking

When you click "🔗 View Entity" on an assertion:
1. The Meeting Context section auto-expands
2. The referenced entity is highlighted with a green banner
3. You can verify if the assertion correctly references the entity

---

## Optional: Response Annotations

Judges can **optionally** annotate the generated response itself. This is **not mandatory**.

### Per-Section Annotations

The response is parsed into sections. For each section:
1. Click "📝 Add annotation for this section"
2. Enter comments about that specific section

### Overall Response Comment

At the bottom, there's an "📋 Overall Response Annotation" box for general comments about the response quality.

> **Note:** Response annotations are optional and separate from assertion evaluation.

---

## Entity Card Rendering

Mira provides rich card rendering for different entity types found in the meeting context.

### Chat Entity Cards 💬

Displays chat conversations with a two-column layout:

| Left Column | Right Column |
|-------------|--------------|
| Chat metadata (ID, topic) | Message bubbles |
| Member count | Sender, content, timestamp |

Each message is rendered as a styled bubble with:
- 👤 Sender name in blue
- Message content
- Timestamp aligned right

### Email Entity Cards ✉️

Displays email with metadata and body preview:

| Left Column | Right Column |
|-------------|--------------|
| Subject, From, Date | Email body |
| To/Cc recipients | Rendered content |

### File Entity Cards 📄

Displays document files with content preview:

| Left Column | Right Column |
|-------------|--------------|
| File name, type, size | Content tabs |
| Metadata table | 📄 Preview / ℹ️ Raw Source |

### User Entity Cards 👤

Displays user information with avatar:

- Visual avatar with initials
- Display name and user ID
- Mail nickname
- 🔗 Azure Key Vault link for Test Tenant access

### ChannelMessage Cards 📢

Displays Teams channel messages:

| Left Column | Right Column |
|-------------|--------------|
| Message info | Content |
| Sender, timestamp | Full message body |

### Generic Entity Card

For any entity type with a `Content` or `Body` field, automatically displays the content.

---

## Annotation Workflow

This section describes the complete annotation workflow using Mira for **evaluating assertion quality**.

### Step 1: Launch Mira and Set Up

```bash
streamlit run mira.py
```

1. **Enter Your Name**: Type your name in the "👤 Judge" field
2. **Select Filter** (optional): Use "🔍 Filter" to focus on specific meeting types
3. **Select a Meeting**: Click on a meeting in the sidebar (📕 = Not Started)

### Step 2: Review Meeting Context (Important!)

> **📋 Note:** The Meeting Context section contains all the source data that was used to generate the assertions. Reviewing this context is **essential** for verifying assertion quality.

1. **Notice the Banner**: A prominent blue banner "📋 Meeting Context Available" alerts you to the available context
2. **Expand Meeting Context**: Click "📥 View Meeting Context (Entities, Organizer, Source Data)"
3. **Review Meeting Organizer**: 
   - See the organizer's name, ID, and avatar
   - Click the name to access Azure Key Vault credentials (for Test Tenant login)
4. **Browse Entity Cards**: These are the source entities referenced by assertions
   - 📅 **Event cards**: Meeting details, attendees, time/location
   - 💬 **Chat cards**: Message history displayed as styled bubbles
   - ✉️ **Email cards**: Subject, recipients, and full body preview
   - 📄 **File cards**: Document content with Preview/Raw tabs
   - 👤 **User cards**: User info with Azure Key Vault link
5. **Check SourceID Links**: When you click "🔗 View Entity" on an assertion, it will:
   - Auto-expand the Meeting Context section
   - Highlight the linked entity with a green banner
   - Help you verify if the assertion is correctly grounded in source data

### Step 3: Evaluate Each Assertion (Primary Task)

**This is the main task.** For each assertion, you need to determine if it's a high-quality assertion:

1. **Expand the Assertion**: Click to see full details
2. **Use GPT-5 Results as Hints** (if available):
   - Look for ✅ (passed) or ❌ (failed) icons in the header
   - Review the color-coded supporting spans
   - These are **hints to assist your decision**, not final verdicts
   - You can verify or reject GPT-5's findings using the checkboxes
3. **Review the Assertion Content**:
   - Is the assertion clear and specific?
   - Is it properly grounded in the source data (check SourceID)?
   - Is the level (critical/expected/aspirational) appropriate?
   - Is the justification reasonable?
4. **Make Your Judgment**:
   - Toggle "✅ This assertion is correct" based on your evaluation
   - Check "🎯 Confident in judgment" if you're sure
   - Check "📋 Judged" to mark as reviewed
5. **Add Notes/Revision** (optional): Explain issues or suggest improvements

### Step 4: Annotate the Response (Optional)

> **Note:** Response annotation is **optional**. The primary goal is evaluating assertions.

If you choose to also evaluate the response:

1. **Read Section Content**: Review each section of the LLM response
2. **Add Section Annotations**: Click "📝 Add annotation for this section"
3. **Add Overall Comment**: Use "📋 Overall Response Annotation" at the bottom

### Step 5: Track Progress & Export

- **Progress Bar**: Shows assertion completion percentage
- **Status Indicators**: 📗 Complete | 📙 Partial | 📕 Not Started
- **Auto-Save**: Annotations save to `docs/annotations_temp.json`
- **Export**: Click "📤 Export" to create `docs/annotated_output.jsonl`

### Annotation Data Saved

For each assertion, the following data is captured:

| Field | Description |
|-------|-------------|
| `is_good` | Whether the assertion is a high-quality assertion (true/false) |
| `is_confident` | Whether you're confident in your judgment |
| `is_judged` | Whether the assertion has been reviewed |
| `note` | Optional explanation or comments |
| `revision` | Optional suggested improvement |
| `gpt5_verification` | GPT-5 explanation/span verification status |

### Best Practices for Assertion Evaluation

1. **Judge all assertions** in a meeting to mark it as "Fully Judged"
2. **Use the Meeting Context** to verify assertion grounding
3. **Use GPT-5 results as hints** - they can help you quickly identify potential issues
4. **Don't blindly trust GPT-5** - always verify with source data
5. **Add notes** for incorrect assertions to explain why they fail
6. **Save frequently** - click "💾 Save" or wait for auto-save
7. **Export before closing** - click "📤 Export"

---

## Data Formats

### Assertion Output Format (11_25_output.jsonl)

```json
{
  "utterance": "Help me make a workback plan for...",
  "response": "Here's your workback plan...",
  "assertions": [
    {
      "text": "The response should include...",
      "level": "critical|expected|aspirational",
      "justification": {
        "reason": "Explanation of why this assertion matters",
        "sourceID": "entity-uuid-reference"
      }
    }
  ]
}
```

**Note:** The app supports both new format (`justification`/`sourceID`) and legacy format (`reasoning`/`source`).

### Context File Format (LOD_1121.WithUserUrl.jsonl)

```json
{
  "UTTERANCE": {"text": "User request..."},
  "USER": {
    "id": "lod_username",
    "displayName": "Full Name",
    "mailNickName": "lod_username",
    "url": "https://ms.portal.azure.com/#@microsoft.onmicrosoft.com/..."
  },
  "ENTITIES_TO_USE": [
    {"type": "Event", "EventId": "...", "Subject": "..."},
    {"type": "File", "FileId": "...", "FileName": "...", "Content": "..."},
    {"type": "Chat", "ChatId": "...", "ChatMessages": [...]},
    {"type": "Email", "EmailId": "...", "Body": "..."}
  ]
}
```

### GPT-5 Scores Format (assertion_scores.json)

```json
{
  "timestamp": "2025-11-26T22:35:47",
  "num_samples": 103,
  "overall_stats": {
    "total_assertions": 1395,
    "passed_assertions": 1342,
    "pass_rate": 96.2
  },
  "meetings": [
    {
      "utterance": "...",
      "assertion_results": [
        {
          "assertion_text": "...",
          "level": "critical",
          "passed": true,
          "explanation": "...",
          "supporting_spans": [...]
        }
      ]
    }
  ]
}
```

### Export Format (annotated_output.jsonl)

```json
{
  "utterance": "...",
  "response": "...",
  "assertions": [...],
  "annotations": [
    {
      "assertion_index": 0,
      "original_text": "...",
      "is_good": true,
      "is_confident": true,
      "is_judged": true,
      "note": "...",
      "revised_text": null,
      "gpt5_verification": {...}
    }
  ],
  "response_annotations": {
    "section_0": "...",
    "overall": "..."
  },
  "judge": "Your Name"
}
```

### Context Files

| File | Description |
|------|-------------|
| `docs/LOD_1121.WithUserUrl.jsonl` | **Current** - with Azure Key Vault URLs |
| `docs/LOD_1125.jsonl` | Previous version (Nov 25, 2025) |
| `docs/LOD_1121.jsonl` | Original version (Nov 21, 2025) |

---

## Project Structure

```
AssertionGeneration/
├── mira.py                      # 🎯 Main annotation tool (Streamlit)
├── evaluate_assertions_gpt5.py  # 🤖 GPT-5 JJ automated evaluation
├── compute_assertion_matches.py # Find evidence for assertions
├── score_assertions.py          # Automated PASS/FAIL evaluation
├── show_assertion_details.py    # Generate HTML reports
├── check_sourceid_recovery.py   # Verify SourceID mappings
├── requirements.txt             # Python dependencies
├── docs/
│   ├── 11_25_output.jsonl           # Assertions (103 meetings)
│   ├── assertion_scores.json        # GPT-5 evaluation results
│   ├── LOD_1121.WithUserUrl.jsonl   # 📌 Context with Azure Key Vault URLs
│   ├── LOD_1125.jsonl               # Context file (99% SourceID match)
│   ├── LOD_1121.jsonl               # Original context file
│   ├── annotations_temp.json        # Auto-saved annotations
│   ├── annotated_output.jsonl       # Exported annotations
│   ├── DATA_GENERATION.md           # Dataset creation docs
│   ├── deriving_assertions_workback_plan.md  # Assertion methodology
│   └── screenshots/                 # UI screenshots
└── README.md
```

---

## Scripts Reference

### Primary Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| `mira.py` | Main annotation tool | `streamlit run mira.py` |
| `evaluate_assertions_gpt5.py` | GPT-5 automated evaluation | `python evaluate_assertions_gpt5.py` |

### Evaluation Scripts

| Script | Description |
|--------|-------------|
| `evaluate_assertions_gpt5.py` | Full GPT-5 evaluation with span extraction |
| `score_assertions.py` | Simple PASS/FAIL scoring |
| `compute_assertion_matches.py` | Find evidence for assertions |

### Utility Scripts

| Script | Description |
|--------|-------------|
| `show_assertion_details.py` | Generate HTML reports |
| `show_assertion_html.py` | Additional HTML output |
| `check_sourceid_recovery.py` | Verify SourceID mappings |
| `check_models.py` | Check available models |

### Command Reference

```powershell
# Launch Mira annotation tool
streamlit run mira.py

# Run GPT-5 evaluation on all meetings
python evaluate_assertions_gpt5.py --start 0 --end 103

# Evaluate single meeting
python evaluate_assertions_gpt5.py --meeting-num 7

# Force re-evaluate all
python evaluate_assertions_gpt5.py --force

# Compute assertion matches
python compute_assertion_matches.py --use-jj --jj-delay 3 --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl

# Generate HTML report
python show_assertion_details.py --input docs/output_with_matches.jsonl --output docs/assertion_details.html --open
```

---

## Recent Changes (November 2025)

### v2.0 - GPT-5 JJ Integration & Entity Cards (Nov 26, 2025)

**Major Features:**

🤖 **GPT-5 JJ Automated Evaluation**
- Full evaluation of 103 meetings, 1,395 assertions (96.2% pass rate)
- Supporting span extraction with confidence scoring
- Section attribution for each evidence span
- Visual highlighting in Mira UI
- Annotator verification checkboxes for GPT-5 results

📧 **Rich Entity Card Rendering**
- `render_chat_card()`: Chat entities with message bubbles
- `render_email_card()`: Email with body preview
- `render_channel_message_card()`: Teams messages with content
- `render_user_card()`: User avatar with Azure Key Vault link
- `render_file_card()`: File metadata + content with tabs
- `render_generic_card()`: Fallback for Content/Body fields

🎨 **UI Improvements**
- Meeting title styled with purple gradient (matches badge)
- File renamed from `visualize_output.py` to `mira.py`
- Entity type detection fix (actual_entity_type from data)
- MailNickName added to User entity indexing

### v1.5 - Command Center UI (Nov 25, 2025)

- 🎛️ Consolidated command center at top
- 👤 Modern user card with avatar
- 📝 Per-section response annotations
- 📊 Enhanced progress tracking
- 🔍 Smart filtering by annotation status

### v1.0 - Initial Release (Nov 24, 2025)

- Basic assertion visualization
- Entity linking with SourceID navigation
- Azure Key Vault integration
- Annotation export functionality

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

Microsoft Internal Use Only