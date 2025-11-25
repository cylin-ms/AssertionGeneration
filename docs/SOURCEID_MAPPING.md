# SourceID to Entity Type Mapping

**Author:** Chin-Yew Lin  
**Date:** November 26, 2025

## Overview

The `sourceID` field in assertion justifications references entity IDs from the LOD (Line of Data) input context. This document provides the mapping between sourceID values and their corresponding entity types.

## Entity ID Field Mapping

| Entity Type | ID Field Name | Count in LOD | Description |
|-------------|---------------|--------------|-------------|
| **File** | `FileId` | 360 | Document files (docx, xlsx, pptx, pdf) |
| **Chat** | `ChatId` | 114 | Teams chat conversations |
| **User** | `id` | 104 | User profile identifier (e.g., `lod_tisaodon`) |
| **Event** | `EventId` | 20 | Calendar events/meetings |
| **ChannelMessage** | `ChannelMessageId` | 13 | Teams channel messages |
| **ChannelMessage** | `ChannelId` | 7 | Teams channel identifier |
| **ChannelMessageReply** | `ChannelMessageReplyId` | 6 | Replies to channel messages |
| **Email** | `EmailId` | 5 | Email messages |
| **OnlineMeeting** | `OnlineMeetingId` | 4 | Teams online meeting sessions |

**Note:** Some ID fields appear in multiple entity types:
- `ChatId` is used by both **Chat** and **OnlineMeeting** entities
- `EventId` is used by **Event**, **Chat**, and **OnlineMeeting** entities

## Statistics (from 11_25_output.jsonl)

Based on analysis of the current output data:

### Entity IDs Available in LOD Data
| Entity Type | ID Field | Count |
|-------------|----------|-------|
| File | `FileId` | 360 |
| Chat | `ChatId` | 114 |
| ChatMessage | `ChatMessageId` | 277 (nested in Chat) |
| User | `id` | 104 |
| Event | `EventId` | 20 |
| ChannelMessage | `ChannelMessageId` | 13 |
| ChannelMessage | `ChannelId` | 7 |
| ChannelMessageReply | `ChannelMessageReplyId` | 6 |
| Email | `EmailId` | 5 |
| OnlineMeeting | `OnlineMeetingId` | 4 |

**Total unique IDs in LOD data:** 553

### SourceID Match Rate
| Category | Count | Percentage |
|----------|-------|------------|
| **Total sourceIDs** | 1,395 | 100% |
| **Matched to Entity IDs** | 510 | 36.6% |
| **Unmatched (synthetic)** | 885 | 63.4% |

**Note:** Unmatched sourceIDs are synthetic/generated UUIDs that don't exist in the LOD input data. These may be hallucinated or placeholder IDs created during the assertion generation process.

## Format Comparison

### New Format (11_25_output.jsonl)
```json
{
  "justification": {
    "reason": "Explanation of why this assertion matters",
    "sourceID": "af38c57d-5071-4833-a25b-4d53c7331b54"
  }
}
```

### Old Format (output_v2.jsonl)
```json
{
  "reasoning": {
    "reason": "Explanation of why this assertion matters",
    "source": "Descriptive text about the source"
  }
}
```

## Key Differences

| Aspect | Old Format | New Format |
|--------|-----------|------------|
| Container field | `reasoning` | `justification` |
| Source reference | `source` (descriptive text) | `sourceID` (entity UUID) |
| Traceability | Low (text description) | High (direct entity link) |

## Usage in Visualization App

When `sourceID` matches an entity ID in the LOD data:
- A **"🔗 View Entity"** button appears
- Clicking links to the entity in the Input Context section
- The linked entity is highlighted with a green banner

When `sourceID` doesn't match:
- Shows **"🔍 No match"** indicator
- The sourceID is still displayed for reference

## Notes

- Unmatched sourceIDs may be synthetic/generated during assertion creation
- Future data generation should ensure sourceIDs reference actual entity IDs from input
- The visualization app supports both formats for backward compatibility
