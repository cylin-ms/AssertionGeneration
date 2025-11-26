# Mira - Assertion Annotation Tool

**Author:** Chin-Yew Lin

> **✨ Mira** is a comprehensive annotation tool for evaluating LLM-generated assertions from meeting contexts. It features a modern command center UI, per-section response annotations, and Azure Key Vault integration for Test Tenant access.

This project provides tools for generating assertions from meeting contexts and verifying them against generated workback plans. It includes an offline matching system using LLMs to validate assertions and a visualization tool to inspect and annotate the results.

For details on how the dataset (meeting contexts, assertions, and plans) was created, please refer to [DATA_GENERATION.md](docs/DATA_GENERATION.md).

Additionally, the methodology for deriving assertions for workback plans is documented in [deriving_assertions_workback_plan.md](docs/deriving_assertions_workback_plan.md) by Weiwei Cui. This document outlines the key attributes of a good workback plan (e.g., reverse schedule, clear owners, dependencies) and the two-stage approach used to generate high-quality assertions from meeting context.

## Overview

The system consists of two main components:

1. **Assertion Matching**: An offline script that uses GPT-5 JJ (Microsoft Substrate API) to find evidence in generated responses that supports specific assertions.
2. **Mira Annotation Tool**: A Streamlit application to interactively explore the generated plans, assertions, annotate responses, and evaluate assertion quality.

## Key Features (November 2025)

### 🎛️ Command Center UI
- **Consolidated Controls**: Judge name, Filter, Save/Export, Reset all in one place at the top
- **Real-time Progress**: Visual progress bar with meeting and assertion statistics
- **Smart Filtering**: Filter meetings by annotation status (All, Fully Judged, Partially Judged, Not Started)

### 👤 Modern User Card
- **Meeting Organizer Display**: Shows organizer name with clickable Azure Key Vault link
- **Avatar with Initials**: Visual avatar displaying user initials
- **Quick Access**: User ID and Mail Nickname displayed in the card

### 📝 Response Annotations
- **Per-Section Annotations**: Expandable annotation boxes for each section of the generated response
- **Section Parsing**: Automatically detects markdown headers, numbered items, and bold headers
- **Overall Comments**: Dedicated text area for overall response assessment
- **Annotation Indicators**: Visual indicators (📝) show which sections have been annotated

### ✅ Assertion Evaluation
- **Judgment Tracking**: Mark assertions as judged with "📋 Judged" checkbox
- **Correctness Marking**: Check/uncheck assertions as correct or incorrect
- **Confidence Levels**: Indicate confidence in your judgment
- **Notes & Revisions**: Add explanatory notes and suggest improved assertion text

### 🔗 Entity Linking
- **SourceID Navigation**: Click "🔗 View Entity" to jump to referenced entities
- **Visual Highlighting**: Linked entities highlighted with green banner
- **Azure Key Vault Integration**: Direct links to user credentials in Test Tenant

## Prerequisites

- Python 3.10+
- Microsoft corporate account (for GPT-5 JJ authentication via MSAL broker)

## Setup

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

## Usage

### Launch Mira Annotation Tool

The assertion results are stored in `docs/11_25_output.jsonl`. Launch the Mira annotation tool:

```bash
streamlit run visualize_output.py
```

Open your browser to `http://localhost:8501` after starting the app.

### Interface Overview

#### Command Center (Top)
| Control | Description |
|---------|-------------|
| **👤 Judge** | Enter your name for attribution in exports |
| **🔍 Filter** | Filter meetings by status: All, Fully Judged, Partially Judged, Not Started |
| **💾 Save** | Save annotations to temp file |
| **📤 Export** | Export all annotations to `docs/annotated_output.jsonl` |
| **🔄 Reset Current** | Reset annotations for current meeting |
| **🗑️ Reset All** | Reset all annotations (with confirmation) |

#### Progress Metrics
- **Progress Bar**: Visual completion indicator
- **📗 Complete**: Fully judged meetings count
- **📙 Partial**: Partially judged meetings count
- **✓ Confident**: Confident judgment count
- **? Unsure**: Uncertain judgment count

#### Sidebar (Meeting Navigation)
- **Meeting List**: Click to select a meeting (📗📙📕 status indicators)
- **Meeting Count**: Shows filtered/total meetings

#### Main Content Area
- **🗣️ Utterance**: The user's request
- **📥 View Input Context**: Expandable LOD data with Meeting Organizer card
- **🤖 Generated Response**: Response with per-section annotation dropdowns
- **✅ Assertions**: Assertion cards with evaluation controls

### Context Files & Azure Key Vault Integration

The project uses context files (LOD - LiveOak Data) with user URLs for Test Tenant access:

| File | Description | Features |
|------|-------------|----------|
| `docs/LOD_1121.WithUserUrl.jsonl` | **Current** - with Azure Key Vault URLs | User links to Test Tenant |
| `docs/LOD_1125.jsonl` | Previous version (Nov 25, 2025) | 99% SourceID match rate |
| `docs/LOD_1121.jsonl` | Original version (Nov 21, 2025) | Basic entity data |

**Azure Key Vault Integration:**
- Each meeting organizer has a clickable name linking to Azure Key Vault
- URLs format: `https://ms.portal.azure.com/#@microsoft.onmicrosoft.com/asset/Microsoft_Azure_KeyVault/Secret/...`
- Enables quick access to Test Tenant user credentials


### Data Format

The output file uses the following assertion format:

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

**Note:** The visualization app supports both the new format (`justification`/`sourceID`) and the legacy format (`reasoning`/`source`) for backward compatibility.

### (Optional) Re-compute Assertion Matches

If you want to re-run the matching process using GPT-5 JJ:

```bash
# Using GPT-5 JJ (recommended)
python compute_assertion_matches.py --use-jj --jj-delay 3 --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl

# Process only first N meetings (useful for testing)
python compute_assertion_matches.py --use-jj --jj-delay 3 --input docs/11_25_output.jsonl --output docs/test_5_with_matches.jsonl --limit 5
```

Options:
- `--use-jj`: Use GPT-5 JJ via Microsoft Substrate API (default and recommended)
- `--jj-delay N`: Delay in seconds between API calls to avoid rate limiting (default: 2.0)
- `--limit N`: Process only first N meetings

**Note:** The script also supports Ollama as a fallback backend (omit `--use-jj` flag), but JJ is recommended for better quality.

## Walkthrough: Annotation & Evaluation Workflow

This section describes the complete workflow for annotating and evaluating assertions using Mira.

### Step 1: Launch Mira and Set Up

```bash
streamlit run visualize_output.py
```

1. **Enter Your Name**: Type your name in the "👤 Judge" field at the top
2. **Select Filter** (optional): Use the "🔍 Filter" dropdown to focus on specific meeting types
3. **Select a Meeting**: Click on a meeting in the sidebar (look for 📕 Not Started meetings)

### Step 2: Review Meeting Context

1. **Check the Utterance**: Read the user's request at the top
2. **Expand Input Context**: Click "📥 View Input Context (LOD Data)"
3. **Review Meeting Organizer**: 
   - See the organizer's name and ID
   - Click the name to access Azure Key Vault credentials (for Test Tenant)
4. **Browse Entities**: Check related entities (Events, Files, Emails, etc.)

### Step 3: Annotate the Generated Response

The response is automatically parsed into sections. For each section:

1. **Read the Section Content**: Review what the LLM generated
2. **Add Section Annotation** (optional): 
   - Click "📝 Add annotation for this section"
   - Enter your comments about this specific section
3. **Add Overall Comment**: 
   - Scroll to "📋 Overall Response Annotation" at the bottom
   - Enter your overall assessment of the response quality

### Step 4: Evaluate Each Assertion

For each assertion card:

1. **Expand the Assertion**: Click to see full details
2. **Check Correctness**: 
   - Keep "✅ This assertion is correct" checked if valid
   - Uncheck if the assertion is incorrect or poorly grounded
3. **Set Confidence**: Check "🎯 Confident in judgment" if you're sure
4. **Mark as Judged**: Check "📋 Judged" when done reviewing
5. **Add Notes** (optional): Explain issues or concerns
6. **Suggest Revision** (optional): Provide improved assertion text

### Step 5: Track Progress

Monitor your progress in the command center:
- **Progress Bar**: Shows meetings completion percentage
- **📗 Complete**: Number of fully judged meetings
- **Status Indicators**: 
  - 📗 = All assertions judged
  - 📙 = Some assertions judged  
  - 📕 = No assertions judged yet

### Step 6: Save & Export

1. **Auto-Save**: Annotations automatically save to `docs/annotations_temp.json`
2. **Manual Save**: Click "💾 Save" to force save
3. **Export**: Click "📤 Export" to create `docs/annotated_output.jsonl`

### Export Format

The exported file includes all original data plus your annotations:

```json
{
  "utterance": "Help me make a workback plan...",
  "response": "Here's your workback plan...",
  "assertions": [...],
  "annotations": [
    {
      "assertion_index": 0,
      "original_text": "The response should include...",
      "is_good": true,
      "is_confident": true,
      "is_judged": true,
      "note": "Well grounded in the event data",
      "revised_text": null
    }
  ],
  "response_annotations": {
    "section_0": "Good introduction",
    "section_1": "Missing deadline details",
    "overall": "Generally good but needs more specificity"
  },
  "judge": "Your Name",
  "annotation_stats": {
    "total": 5,
    "good": 4,
    "not_good": 1,
    "judged": 5,
    "revised": 1
  }
}
```

## Automated Tools

### Score Assertions (PASS/FAIL Evaluation)

```bash
python score_assertions.py
```

Evaluates each assertion against the response using GPT-5 JJ:
- **Critical assertions**: Strict evaluation - must be explicitly present
- **Expected assertions**: Moderate - reasonable interpretation allowed
- **Aspirational assertions**: Lenient - nice-to-have features

### Find Supporting Evidence

```bash
python compute_assertion_matches.py --use-jj --jj-delay 3 --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl --limit 5
```

Options:
- `--use-jj`: Use GPT-5 JJ via Microsoft Substrate API
- `--jj-delay N`: Delay in seconds between API calls
- `--limit N`: Process only first N meetings

### Generate HTML Report

```bash
python show_assertion_details.py --input docs/output_with_matches.jsonl --output docs/assertion_details.html --open
```

This generates a detailed HTML report showing:
- User request and full response
- Each assertion card with level indicator
- Matched text segments that support each assertion
- Visual indicators (green border = matches found, red = no matches)

## Project Structure

```
AssertionGeneration/
├── visualize_output.py          # 🎯 Mira - Main annotation tool
├── compute_assertion_matches.py # Find evidence for assertions
├── score_assertions.py          # Automated PASS/FAIL evaluation
├── show_assertion_details.py    # Generate HTML reports
├── check_sourceid_recovery.py   # Verify SourceID mappings
├── requirements.txt             # Python dependencies
├── docs/
│   ├── 11_25_output.jsonl           # Current assertions (103 meetings)
│   ├── LOD_1121.WithUserUrl.jsonl   # 📌 Context with Azure Key Vault URLs
│   ├── LOD_1125.jsonl               # Context file (99% SourceID match)
│   ├── LOD_1121.jsonl               # Original context file
│   ├── annotations_temp.json        # Auto-saved annotations
│   ├── annotated_output.jsonl       # Exported annotations
│   ├── DATA_GENERATION.md           # Dataset creation docs
│   ├── deriving_assertions_workback_plan.md  # Assertion methodology
│   ├── OUTPUT_FILE_COMPARISON.md    # Format comparison
│   └── REPORT_Assertion_Scoring_and_Matching.md  # Evaluation report
└── README.md
```

## Data Formats

### Assertion Format (11_25_output.jsonl)

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

### Context File Format (LOD_1121.WithUserUrl.jsonl)

```json
{
  "UTTERANCE": {"text": "User request..."},
  "USER": {
    "id": "lod_username",
    "displayName": "Full Name",
    "mailNickName": "lod_username",
    "url": "https://ms.portal.azure.com/#@microsoft.onmicrosoft.com/asset/Microsoft_Azure_KeyVault/Secret/..."
  },
  "ENTITIES_TO_USE": [
    {"type": "Event", "EventId": "...", "Subject": "..."},
    {"type": "File", "FileId": "...", "FileName": "..."}
  ]
}
```

## Recent Changes (November 2025)

### Mira UX Redesign (Nov 26, 2025)

**New Features:**
- 🎛️ **Command Center**: Consolidated controls at top (Judge, Filter, Actions, Reset)
- 👤 **Modern User Card**: Meeting organizer with avatar and Azure Key Vault link
- 📝 **Response Annotations**: Per-section dropdowns + overall comment box
- 📊 **Enhanced Progress Tracking**: Visual bar with detailed statistics
- 🔍 **Smart Filtering**: Filter by annotation status
- ✨ **Mira Branding**: Project renamed to Mira

**Azure Key Vault Integration:**
- New context file `LOD_1121.WithUserUrl.jsonl` with user URLs
- Direct links to Test Tenant credentials
- Enables easy access to synthetic user accounts

### Previous Updates

#### Assertion Scoring & Evaluation Tools (Nov 25, 2025)

- **score_assertions.py**: Uses GPT-5 JJ for PASS/FAIL evaluation
- Level-based evaluation (Critical=strict, Expected=moderate, Aspirational=lenient)
- Achieved **100% pass rate** on 212 assertions across 15 meetings

#### Entity ID Linking


- Click "🔗 View Entity" to navigate from assertion sourceID to referenced entity
- Auto-expands Input Context section and highlights linked entity
- Supports all entity types (Events, Files, Emails, etc.)

#### Data Format Update (Nov 25, 2025)

The output file `docs/11_25_output.jsonl` uses an updated format:
- `reasoning` → `justification`
- `source` → `sourceID` (now uses entity UUIDs for precise traceability)
- 103 meetings total (vs 97 in old format)

See `docs/OUTPUT_FILE_COMPARISON.md` for detailed format differences.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Microsoft Internal Use Only