# Mira - Assertion Annotation & Evaluation Tool

**Author:** Chin-Yew Lin  
**Version:** 2.0 (November 2025)

> **✨ Mira** is a comprehensive annotation and evaluation tool for LLM-generated assertions from meeting contexts. It features GPT-5 JJ automated evaluation with span highlighting, a modern command center UI, rich entity card rendering (Chat, Email, File, User), per-section response annotations, and Azure Key Vault integration for Test Tenant access.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features-november-2025)
3. [Quick Start](#quick-start)
4. [Detailed Walkthrough](#detailed-walkthrough)
5. [GPT-5 JJ Automated Evaluation](#gpt-5-jj-automated-evaluation)
6. [Entity Card Rendering](#entity-card-rendering)
7. [Annotation Workflow](#annotation-workflow)
8. [Data Formats](#data-formats)
9. [Project Structure](#project-structure)
10. [Scripts Reference](#scripts-reference)
11. [Recent Changes](#recent-changes-november-2025)

---

## Overview

This project provides tools for generating assertions from meeting contexts and verifying them against generated workback plans. It includes:

- **GPT-5 JJ Automated Evaluation**: Evaluates assertions with supporting span extraction and confidence scoring
- **Mira Annotation Tool**: Interactive Streamlit UI to explore, annotate, and evaluate assertion quality
- **Entity Card Rendering**: Rich display for Chat, Email, File, User, and ChannelMessage entities
- **Offline Matching**: Find evidence in responses that supports specific assertions

For details on how the dataset was created, see [DATA_GENERATION.md](docs/DATA_GENERATION.md).

The methodology for deriving assertions is documented in [deriving_assertions_workback_plan.md](docs/deriving_assertions_workback_plan.md) by Weiwei Cui.

### System Components

| Component | Description | Script |
|-----------|-------------|--------|
| **GPT-5 Evaluation** | Automated PASS/FAIL evaluation with supporting spans | `evaluate_assertions_gpt5.py` |
| **Mira Annotation Tool** | Interactive UI for annotation and review | `mira.py` |
| **Assertion Matching** | Find evidence for assertions | `compute_assertion_matches.py` |
| **HTML Reports** | Generate detailed HTML reports | `show_assertion_details.py` |

## Key Features (November 2025)

### 🤖 GPT-5 JJ Automated Evaluation (NEW!)
- **Automated PASS/FAIL Assessment**: Each assertion is evaluated against the response using GPT-5 JJ
- **Supporting Span Extraction**: Identifies exact text spans that support or contradict each assertion
- **Confidence Scoring**: Each span has a confidence score (0.0-1.0) for color intensity
- **Section Attribution**: Spans include which response section they appear in (e.g., "Task Details", "Timeline")
- **Visual Highlighting**: Color-coded evidence boxes (green=supports, red=contradicts)
- **Verification Checkboxes**: Annotators can verify or reject GPT-5's explanations and evidence

### 📊 Current Evaluation Results
- **103 meetings** evaluated with GPT-5 JJ
- **1,395 assertions** total
- **96.2% pass rate** (1,342 passed, 53 failed)
- **100% span coverage** - all assertions have supporting_spans

### 🎛️ Command Center UI
- **Consolidated Controls**: Judge name, Filter, Save/Export, Reset all in one place at the top
- **Real-time Progress**: Visual progress bar with meeting and assertion statistics
- **Smart Filtering**: Filter meetings by annotation status (All, Fully Judged, Partially Judged, Not Started)

### 👤 Modern User Card
- **Meeting Organizer Display**: Shows organizer name with clickable Azure Key Vault link
- **Avatar with Initials**: Visual avatar displaying user initials
- **Quick Access**: User ID and Mail Nickname displayed in the card

### 📧 Rich Entity Card Rendering (NEW!)
- **Chat Entity Cards**: Two-column layout with chat info + message bubbles
- **Email Entity Cards**: Metadata on left, body preview on right
- **File Entity Cards**: Metadata + content preview with tabs (Preview/Raw)
- **ChannelMessage Cards**: Message info with content display
- **User Entity Cards**: Avatar, name, ID, and Azure Key Vault link
- **Generic Fallback**: Shows Content/Body if present for any entity type

### 📝 Response Annotations
- **Per-Section Annotations**: Expandable annotation boxes for each section of the generated response
- **Section Parsing**: Automatically detects markdown headers, numbered items, and bold headers
- **Overall Comments**: Dedicated text area for overall response assessment
- **Annotation Indicators**: Visual indicators (📝) show which sections have been annotated

### ✅ Assertion Evaluation
- **GPT-5 Status Icons**: ✅/❌ indicators from GPT-5 JJ evaluation in assertion headers
- **Judgment Tracking**: Mark assertions as judged with "📋 Judged" checkbox
- **Correctness Marking**: Check/uncheck assertions as correct or incorrect
- **Confidence Levels**: Indicate confidence in your judgment
- **Notes & Revisions**: Add explanatory notes and suggest improved assertion text

### 🔗 Entity Linking
- **SourceID Navigation**: Click "🔗 View Entity" to jump to referenced entities
- **Visual Highlighting**: Linked entities highlighted with green banner
- **Azure Key Vault Integration**: Direct links to user credentials in Test Tenant

## Quick Start

### Prerequisites

- Python 3.10+
- Microsoft corporate account (for GPT-5 JJ authentication via MSAL broker)

### Setup

1. **Clone the repository**

    ```bash
    git clone https://github.com/cylin-ms/AssertionGeneration.git
    cd AssertionGeneration
    ```

2. **Create and activate a virtual environment**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

### Launch Mira

```bash
streamlit run mira.py
```

Open your browser to `http://localhost:8501` after starting the app.

---

## Detailed Walkthrough

This section provides a complete walkthrough of the Mira annotation tool interface.

### Interface Overview

#### 1. Command Center (Top Bar)

The command center provides all controls in one consolidated row:

| Control | Description |
|---------|-------------|
| **👤 Judge** | Enter your name for attribution in exports |
| **🔍 Filter** | Filter meetings by status: All, Fully Judged, Partially Judged, Not Started |
| **💾 Save** | Save annotations to temp file |
| **📤 Export** | Export all annotations to `docs/annotated_output.jsonl` |
| **🔄 Reset Current** | Reset annotations for current meeting |
| **🗑️ Reset All** | Reset all annotations (with confirmation) |

#### 2. Progress Metrics

Visual progress tracking below the command center:

- **Progress Bar**: Visual completion percentage
- **📗 Complete**: Fully judged meetings count
- **📙 Partial**: Partially judged meetings count
- **✓ Confident**: Confident judgment count
- **? Unsure**: Uncertain judgment count

#### 3. Sidebar (Meeting Navigation)

- **Meeting List**: Click to select a meeting
- **Status Indicators**: 📗 Complete | 📙 Partial | 📕 Not Started
- **Meeting Count**: Shows filtered/total meetings

#### 4. Main Content Area

The main area displays the selected meeting with multiple sections:

**Meeting Header**
- Purple gradient badge with meeting number
- Meeting title with matching purple styling
- Event ID for reference
- "View Meeting Details" button for full event info

**🗣️ Utterance**
- The user's request displayed at the top

**📥 View Input Context (LOD Data)**
- Expandable section with Meeting Organizer card
- Entity cards (Events, Files, Emails, Chats, Users)
- SourceID linking for entity navigation

**🤖 Generated Response**
- Full LLM response with per-section annotation dropdowns
- Click sections to add annotations
- Overall response annotation box

**✅ Assertions**
- Assertion cards with GPT-5 evaluation status
- Expandable details with annotation controls
- Supporting evidence with confidence bars

### Annotation Workflow & Completion Criteria

#### How to Annotate an Assertion

1. **Expand** the assertion card by clicking on it
2. **Review GPT-5 Evaluation**: Check the ✅/❌ status and supporting evidence
3. **Verify GPT-5 Results**: Uncheck evidence boxes if you disagree with GPT-5
4. **Mark correctness**: Check "✅ This assertion is correct" (or uncheck if incorrect)
5. **Set confidence**: Check "🎯 Confident in judgment" (or uncheck if unsure)
6. **Add notes** (optional): Explain why the assertion is incorrect
7. **Suggest revision** (optional): Provide improved assertion text
8. **Mark as judged**: The "📋 Judged" checkbox is auto-checked when you make a judgment

#### Meeting Completion Status

| Status | Icon | Criteria |
|--------|------|----------|
| **Fully Judged** | 📗 | ALL assertions have `is_judged: True` |
| **Partially Judged** | 📙 | At least 1 assertion judged, but not all |
| **Not Started** | 📕 | No assertions have been judged yet |

---

## GPT-5 JJ Automated Evaluation

Mira integrates with GPT-5 JJ (via Microsoft Substrate API) for automated assertion evaluation.

### How It Works

For each assertion, GPT-5 JJ:
1. **Evaluates** whether the response satisfies the assertion (PASS/FAIL)
2. **Extracts** supporting text spans from the response
3. **Assigns** confidence scores (0.0-1.0) to each span
4. **Identifies** which response section contains each span
5. **Provides** reasoning for the evaluation

### Running GPT-5 Evaluation

```powershell
# Evaluate all meetings (resume from checkpoint)
python evaluate_assertions_gpt5.py

# Evaluate specific range
python evaluate_assertions_gpt5.py --start 0 --end 103

# Evaluate single meeting by index (0-based)
python evaluate_assertions_gpt5.py --meeting 5

# Evaluate by UI meeting number (1-based)
python evaluate_assertions_gpt5.py --meeting-num 7

# Force reprocess all meetings
python evaluate_assertions_gpt5.py --force
```

### Evaluation Results

Results are saved to `docs/assertion_scores.json`:

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
      "utterance": "Help me make a workback plan...",
      "assertion_results": [
        {
          "assertion_text": "The response should include...",
          "level": "critical",
          "passed": true,
          "explanation": "The response correctly includes...",
          "supporting_spans": [
            {
              "text": "exact quote from response",
              "section": "Task Details",
              "confidence": 0.95,
              "supports": true,
              "start_index": 150,
              "end_index": 220
            }
          ]
        }
      ]
    }
  ]
}
```

### Viewing Results in Mira

1. **Header Icons**: Each assertion shows ✅ (passed) or ❌ (failed) in the expander header
2. **Evaluation Section**: Expand an assertion to see the full GPT-5 evaluation
3. **Supporting Evidence**: Color-coded boxes show extracted spans
   - 🟢 Green = supports the assertion (confidence-based intensity)
   - 🔴 Red = contradicts the assertion
4. **Confidence Bars**: Visual progress bars show span confidence
5. **Section Attribution**: Each span shows which response section it came from
6. **Verification**: Check/uncheck boxes to accept/reject GPT-5's explanations

### Rate Limiting

The evaluation script includes built-in rate limiting:
- 1 second between assertions
- 3 seconds between meetings
- 10 seconds between batches (10 meetings/batch)

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

This section describes the complete annotation workflow using Mira.

### Step 1: Launch Mira and Set Up

```bash
streamlit run mira.py
```

1. **Enter Your Name**: Type your name in the "👤 Judge" field
2. **Select Filter** (optional): Use "🔍 Filter" to focus on specific meeting types
3. **Select a Meeting**: Click on a meeting in the sidebar (📕 = Not Started)

### Step 2: Review Meeting Context

1. **Check the Utterance**: Read the user's request at the top
2. **Expand Input Context**: Click "📥 View Input Context (LOD Data)"
3. **Review Meeting Organizer**: 
   - See the organizer's name, ID, and avatar
   - Click the name to access Azure Key Vault credentials
4. **Browse Entities**: Review rich entity cards
   - 💬 Chat cards show message history as bubbles
   - ✉️ Email cards show full body preview
   - 📄 File cards have Preview/Raw tabs
   - 👤 User cards link to Test Tenant

### Step 3: Review GPT-5 Evaluation

Before making manual judgments, review the automated evaluation:

1. **Check Header Icons**: Look for ✅ (passed) or ❌ (failed) in assertion headers
2. **Expand an Assertion**: Click to see full GPT-5 evaluation
3. **Review Evidence**: Check the color-coded supporting spans
4. **Verify or Reject**: Uncheck boxes if you disagree with GPT-5's findings

### Step 4: Annotate the Response

1. **Read Section Content**: Review each section of the LLM response
2. **Add Section Annotations**: Click "📝 Add annotation for this section"
3. **Add Overall Comment**: Use "📋 Overall Response Annotation" at the bottom

### Step 5: Evaluate Each Assertion

1. **Expand the Assertion**: Click to see full details
2. **Review GPT-5 Evaluation**: Check PASS/FAIL status and evidence
3. **Verify Evidence**: Accept or reject GPT-5's supporting spans
4. **Check Correctness**: Toggle "✅ This assertion is correct"
5. **Set Confidence**: Check "🎯 Confident in judgment" if you're sure
6. **Mark as Judged**: Check "📋 Judged" when done
7. **Add Notes/Revision** (optional): Explain issues or suggest improvements

### Step 6: Track Progress & Export

- **Progress Bar**: Shows completion percentage
- **Status Indicators**: 📗 Complete | 📙 Partial | 📕 Not Started
- **Auto-Save**: Annotations save to `docs/annotations_temp.json`
- **Export**: Click "📤 Export" to create `docs/annotated_output.jsonl`

### Annotation Data Saved

For each assertion, the following data is captured:

| Field | Description |
|-------|-------------|
| `is_good` | Whether the assertion is correct (true/false) |
| `is_confident` | Whether you're confident in your judgment |
| `is_judged` | Whether the assertion has been reviewed |
| `note` | Optional explanation or comments |
| `revision` | Optional suggested improvement |
| `gpt5_verification` | GPT-5 explanation/span verification status |

### Best Practices

1. **Judge all assertions** in a meeting to mark it as "Fully Judged"
2. **Use the filter** to find meetings that need attention
3. **Save frequently** - click "💾 Save" or wait for auto-save
4. **Export before closing** - click "📤 Export"
5. **Add notes** for incorrect assertions to explain why they fail
6. **Verify GPT-5 results** - the AI isn't always right!

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