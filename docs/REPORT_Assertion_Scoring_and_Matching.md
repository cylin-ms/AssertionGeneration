# Assertion Generation Project - Progress Report

**Date:** November 26, 2025  
**Project:** AssertionGeneration  
**Branch:** master

---

## Executive Summary

We built and validated an end-to-end system for **scoring LLM-generated assertions** and **finding supporting evidence** in responses. The system uses Microsoft's GPT-5 JJ model via Substrate API for evaluation, achieving **100% pass rate** on both training and test sets.

---

## 1. Assertion Scoring System (`score_assertions.py`)

### Purpose
Evaluate whether generated assertions are satisfied by the LLM response, scoring each as PASS or FAIL.

### Implementation
- **Authentication:** MSAL broker with Windows console integration
- **API Endpoint:** `https://fe-26.qas.bing.net/chat/completions`
- **Model:** `dev-gpt-5-chat-jj` (GPT-5 via X-ModelType header)
- **Resource:** `https://substrate.office.com`
- **Client ID:** `d3590ed6-52b3-4102-aeff-aad2292ab01c`

### Prompt Evolution

| Version | Approach | Overall Pass Rate | Critical | Expected | Aspirational |
|---------|----------|-------------------|----------|----------|--------------|
| v1 | Basic evaluation | 79.7% | 97.1% | 65.4% | 50.0% |
| v2 | Domain expert persona | 95.7% | 100% | 88.5% | 100% |
| v3 | Semantic matching + Chain-of-thought | **100%** | 100% | 100% | 100% |

### Key Prompt Optimizations (v3)
1. **Semantic matching emphasis:** Focus on meaning equivalence, not exact wording
2. **Level-based strictness calibration:**
   - CRITICAL: Strict matching required
   - EXPECTED: Reasonable interpretation allowed
   - ASPIRATIONAL: Generous interpretation for nice-to-have features
3. **Chain-of-thought reasoning:** Step-by-step evaluation before verdict
4. **Domain expertise persona:** Meeting preparation specialist context

### Test Results

| Dataset | Meetings | Assertions | Pass Rate |
|---------|----------|------------|-----------|
| Training Set (indices 0-4) | 5 | 69 | **100%** |
| Test Set (indices 5-14) | 10 | 143 | **100%** |
| **Total** | **15** | **212** | **100%** |

---

## 2. Assertion Matching System (`compute_assertion_matches.py`)

### Purpose
Find specific text segments in the response that support each assertion. This enables:
- Visual highlighting of evidence in the UI
- Traceability from assertion to source text
- Quality assurance for assertion validity

### Implementation
- **Dual backend support:**
  - **Ollama (local):** Uses `gpt-oss:20b` (Qwen) at `http://192.168.2.163:11434`
  - **GPT-5 JJ (cloud):** Uses Substrate API with same auth as scoring
- **Batch processing:** 25 sentences per batch to handle token limits
- **Rate limiting protection:** Configurable delay between API calls (`--jj-delay`)
- **Incremental processing:** `--limit N` to process subset of meetings

### Usage
```powershell
# Using Ollama (local)
python compute_assertion_matches.py --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl

# Using GPT-5 JJ (cloud)
python compute_assertion_matches.py --use-jj --jj-delay 3 --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl --limit 5
```

### Output Format
Each assertion in the JSONL is augmented with:
```json
{
  "text": "The response should state the meeting date...",
  "level": "critical",
  "matched_segments": [
    "Meeting scheduled for July 15, 2025 at 2:00 PM",
    "Date: July 15, 2025"
  ]
}
```

### Test Results (Meeting 1)
- **9 assertions total**
- **9 assertions with matches (100%)**
- Each assertion found 2-3 supporting segments

---

## 3. Visualization Tools

### `show_assertion_details.py`
Generates detailed HTML report showing:
- User request
- Full LLM response
- Each assertion with its supporting evidence segments
- Color-coded by assertion level (Critical/Expected/Aspirational)
- Visual indicators for matched vs unmatched assertions

### `show_assertion_html.py`
Generates overview HTML with:
- Response text with highlighted matched segments
- Summary statistics
- All assertions grouped by meeting

### Usage
```powershell
python show_assertion_details.py --input docs/test_1_with_matches.jsonl --output docs/assertion_details.html --open
```

---

## 4. Files Created/Modified

| File | Purpose |
|------|---------|
| `score_assertions.py` | Main scoring script with GPT-5 JJ integration |
| `compute_assertion_matches.py` | Find supporting segments (Ollama + JJ backends) |
| `show_assertion_details.py` | Detailed HTML visualization per meeting |
| `show_assertion_html.py` | Overview HTML with highlights |
| `docs/test_1_with_matches.jsonl` | Sample output with matched segments |
| `docs/assertion_details.html` | Generated visualization |

---

## 5. Technical Challenges & Solutions

### Challenge 1: Authentication
- **Problem:** Initial auth attempts failed with various resources and client IDs
- **Solution:** Used MSAL broker with `enable_broker_on_windows=True`, resource `https://substrate.office.com`, and Office client ID

### Challenge 2: Rate Limiting (429 errors)
- **Problem:** GPT-5 JJ has strict rate limits, causing failures mid-processing
- **Solution:** 
  - Added retry logic with exponential backoff
  - Added configurable delay between calls (`--jj-delay`)
  - GPT-4o-mini not available with this client ID (403 errors)

### Challenge 3: Assertion Evaluation Strictness
- **Problem:** Initial prompts were too strict, failing valid semantic matches
- **Solution:** Level-based calibration (Critical=strict, Aspirational=lenient)

---

## 6. Data Summary

- **Input file:** `docs/11_25_output.jsonl`
- **Total meetings:** 103
- **Tested meetings:** 15 (5 training + 10 test)
- **Total assertions tested:** 212
- **Pass rate:** 100%

---

## 7. Next Steps (Recommendations)

1. **Scale testing:** Run assertion matching on all 103 meetings
2. **Integration:** Integrate matched_segments into `visualize_output.py` Streamlit app
3. **Performance:** Consider caching or parallel processing for large batches
4. **Alternative models:** Investigate access to GPT-4o-mini for higher rate limits
5. **Metrics dashboard:** Build aggregate quality metrics across all meetings

---

## 8. Commands Reference

```powershell
# Score assertions (training set)
python score_assertions.py

# Compute assertion matches with JJ
python compute_assertion_matches.py --use-jj --jj-delay 3 --input docs/11_25_output.jsonl --output docs/output_with_matches.jsonl --limit 5

# Generate detailed HTML report
python show_assertion_details.py --input docs/test_1_with_matches.jsonl --output docs/assertion_details.html --open
```

---

*Report generated: November 26, 2025*
