# Assertion Generation & Matching

**Author:** Chin-Yew Lin

> **New Feature:** Users can now **revise and evaluate assertions in-place** using the visualization tool—mark assertions as good/bad, add notes, suggest improvements, then **export results** for further analysis.

This project provides tools for generating assertions from meeting contexts and verifying them against generated workback plans. It includes an offline matching system using LLMs to validate assertions and a visualization tool to inspect the results.

For details on how the dataset (meeting contexts, assertions, and plans) was created, please refer to [DATA_GENERATION.md](docs/DATA_GENERATION.md).

Additionally, the methodology for deriving assertions for workback plans is documented in [deriving_assertions_workback_plan.md](docs/deriving_assertions_workback_plan.md) by Weiwei Cui. This document outlines the key attributes of a good workback plan (e.g., reverse schedule, clear owners, dependencies) and the two-stage approach used to generate high-quality assertions from meeting context.

## Overview

The system consists of two main components:

1. **Assertion Matching**: An offline script that uses GPT-5 JJ (Microsoft Substrate API) to find evidence in generated responses that supports specific assertions.
2. **Visualization**: A Streamlit application to interactively explore the generated plans, assertions, and their matched evidence.

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

### Visualize Results

The assertion results are stored in `docs/11_25_output.jsonl`. There are two visualization tools available:

#### Main Visualization App

```bash
streamlit run visualize_output.py
```

This is the full-featured visualization app with:
- **Card View**: Professional cards for Users, Files, Events, and other entities
- **Two-column layout**: Response and Assertions side-by-side
- **Evidence highlighting**: Click "Show Evidence" to highlight matching text in the response
- **Entity grouping**: Entities organized by type with expand/collapse controls
- **Entity linking**: Click "View Entity" next to a sourceID to jump to the referenced entity in Input Context

Open your browser to `http://localhost:8501` after starting the app.

### Entity ID Linking

The new output format includes `sourceID` fields that reference specific entities in the input context (LOD Data). The visualization app provides **clickable links** from each assertion's sourceID to the corresponding entity:

1. In the Assertions panel, look for the **"🔗 View Entity"** button next to a sourceID
2. Click the button to:
   - Auto-expand the "📥 View Input Context (LOD Data)" section
   - Highlight the linked entity with a green banner
   - Auto-expand the entity group containing the linked entity
3. Click "❌ Clear Link" to remove the highlighting

This feature helps quickly verify that assertions reference the correct source entities.

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

This section describes the workflow for annotating and evaluating assertions.

### Step 1: Annotate Assertions in the Visualization App

```bash
streamlit run visualize_output.py
```

1. **Select a Meeting**: Use the sidebar to browse through the 103 meetings in `docs/11_25_output.jsonl`

2. **Review Each Assertion**: Click on an assertion to expand it and see:
   - **Full Assertion Text**: The complete assertion statement
   - **Justification**: Why this assertion was generated
   - **Source ID**: Link to the source entity (click "🔗 View Entity" to verify)

3. **Annotate the Assertion**:
   - **✅ Checkbox "This assertion is correct"**: 
     - Keep checked if the assertion is valid and correctly grounded
     - **Uncheck** if the assertion is incorrect, irrelevant, or poorly written
   - **📝 Note** (optional): Explain why the assertion is incorrect or needs improvement
   - **✏️ Revision** (optional): Suggest an improved version of the assertion text

4. **Track Progress**: The sidebar shows annotation stats (e.g., "8/10 marked good | 2 new added")

5. **Save & Export**:
   - Annotations auto-save to `docs/annotations_temp.json`
   - Click "Export Annotations" to save to `docs/annotated_output.jsonl`

### Step 2: Score Assertions (Automated PASS/FAIL Evaluation)

```bash
python score_assertions.py
```

This evaluates each assertion against the response using GPT-5 JJ:
- **Critical assertions**: Strict evaluation - must be explicitly present
- **Expected assertions**: Moderate - reasonable interpretation allowed
- **Aspirational assertions**: Lenient - nice-to-have features

Results show pass/fail per assertion and overall statistics.

### Step 3: Find Supporting Evidence

```bash
python compute_assertion_matches.py --use-jj --jj-delay 3 --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl --limit 5
```

This finds specific text segments in the response that support each assertion:
- Processes responses in batches of 25 sentences
- Uses GPT-5 JJ to score relevance (0.0-1.0)
- Returns top 3 matching segments per assertion
- Adds `matched_segments` field to each assertion in the output

### Step 4: Generate HTML Report

```bash
python show_assertion_details.py --input docs/output_with_matches.jsonl --output docs/assertion_details.html --open
```

This generates a detailed HTML report showing:
- User request and full response
- Each assertion card with level indicator
- Matched text segments that support each assertion
- Visual indicators (green border = matches found, red = no matches)

### Annotation Output Format

When you export annotations, each assertion includes:
```json
{
  "text": "Original assertion text...",
  "level": "critical",
  "is_good": false,
  "note": "This assertion references wrong date",
  "revised_text": "The response should state July 15, not July 14"
}
```

## Project Structure

- `compute_assertion_matches.py`: Script for computing matches between assertions and response text (supports Ollama and GPT-5 JJ backends).
- `score_assertions.py`: Script for evaluating assertions as PASS/FAIL using GPT-5 JJ.
- `show_assertion_details.py`: Generate detailed HTML reports showing assertions with supporting evidence.
- `show_assertion_html.py`: Generate overview HTML with highlighted matches.
- `visualize_output.py`: Main Streamlit application for visualization (full-featured).
- `docs/`: Contains input/output data files and documentation.
  - `11_25_output.jsonl`: Current output file with assertions (103 records, new format from Kening)
  - `output_v2.jsonl`: Legacy output file (97 records, old format)
  - `LOD_1121.jsonl`: Input meeting context data
  - `OUTPUT_FILE_COMPARISON.md`: Detailed comparison between old and new output formats
  - `REPORT_Assertion_Scoring_and_Matching.md`: Full report on assertion scoring and matching results
- `README_ASSERTION_MATCHING.md`: Detailed documentation on the matching methodology.

## Recent Changes (November 2025)

### New: Assertion Scoring & Evaluation Tools

We've added new tools for **scoring assertions** and **finding supporting evidence** using GPT-5 JJ (Microsoft Substrate API):

#### 1. Score Assertions (`score_assertions.py`)

Evaluate whether assertions are satisfied by the LLM response:

```bash
python score_assertions.py
```

- Uses GPT-5 JJ via Microsoft Substrate API
- Level-based evaluation (Critical=strict, Expected=moderate, Aspirational=lenient)
- Achieved **100% pass rate** on 212 assertions across 15 meetings

#### 2. Compute Assertion Matches (`compute_assertion_matches.py`)

Find specific text segments in responses that support each assertion:

```bash
# Using Ollama (local)
python compute_assertion_matches.py --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl

# Using GPT-5 JJ (cloud) - recommended
python compute_assertion_matches.py --use-jj --jj-delay 3 --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl --limit 5
```

Options:
- `--use-jj`: Use GPT-5 JJ instead of local Ollama
- `--jj-delay N`: Delay in seconds between API calls (avoids rate limiting)
- `--limit N`: Process only first N meetings

#### 3. Visualize Assertion Details (`show_assertion_details.py`)

Generate detailed HTML reports showing each assertion with its supporting evidence:

```bash
python show_assertion_details.py --input docs/test_1_with_matches.jsonl --output docs/assertion_details.html --open
```

The HTML report shows:
- User request and full response
- Each assertion with level (Critical/Expected/Aspirational)
- Matched text segments that support each assertion
- Visual indicators for assertions with/without matches

### New Data Format from Kening (November 25, 2025)

The output file `docs/11_25_output.jsonl` uses an updated format:

**Old Format (`output_v2.jsonl`):**
```json
{
  "assertions": [{
    "text": "...",
    "level": "critical",
    "reasoning": {
      "reason": "...",
      "source": "Event"
    }
  }]
}
```

**New Format (`11_25_output.jsonl`):**
```json
{
  "assertions": [{
    "text": "...",
    "level": "critical",
    "justification": {
      "reason": "...",
      "sourceID": "0788e132-56ad-45de-a531-4553a88af64a"
    }
  }]
}
```

Key changes:
- `reasoning` → `justification`
- `source` → `sourceID` (now uses entity UUIDs for precise traceability)
- 103 meetings total (vs 97 in old format)

### Other Updates

- **Entity ID Linking**: Click "🔗 View Entity" to navigate from assertion sourceID to the referenced entity in Input Context
  - Auto-expands Input Context section
  - Highlights the linked entity with a green banner
  - Auto-expands the entity group containing the linked entity
- **Backward Compatibility**: Visualization apps handle both old and new formats
- See `docs/OUTPUT_FILE_COMPARISON.md` for detailed format differences
- See `docs/REPORT_Assertion_Scoring_and_Matching.md` for full evaluation report
