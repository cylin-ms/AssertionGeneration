#!/usr/bin/env python
"""
Script to check SourceID recovery using the new LOD_1125.jsonl context file.
Compares assertion sourceIDs against entity IDs in the context file.
"""

import json
import os
from collections import defaultdict

# File paths
CONTEXT_FILE = os.path.join("docs", "LOD_1125.jsonl")
OUTPUT_FILE = os.path.join("docs", "11_25_output.jsonl")
OLD_CONTEXT_FILE = os.path.join("docs", "LOD_1121.jsonl")

def extract_entity_ids_from_context(context_file):
    """Extract all entity IDs from the context file, including user names and file paths."""
    entity_ids = {}
    entity_types = defaultdict(set)
    
    with open(context_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entities = data.get('ENTITIES_TO_USE', [])
                
                for entity in entities:
                    entity_type = entity.get('type', 'Unknown')
                    
                    # Extract different ID fields based on entity type
                    id_fields = ['EventId', 'FileId', 'ChatMessageId', 'OnlineMeetingId', 
                                 'EmailId', 'ChannelMessageId', 'ChatId']
                    
                    for id_field in id_fields:
                        if id_field in entity:
                            entity_id = entity[id_field]
                            entity_ids[entity_id] = {
                                'type': entity_type,
                                'id_field': id_field,
                                'line': line_num
                            }
                            entity_types[entity_type].add(entity_id)
                    
                    # Extract User mailNickName as valid sourceID
                    if entity_type == 'User' and 'MailNickName' in entity:
                        user_id = entity['MailNickName']
                        entity_ids[user_id] = {
                            'type': 'User',
                            'id_field': 'MailNickName',
                            'line': line_num,
                            'display_name': entity.get('DisplayName', '')
                        }
                        entity_types['User'].add(user_id)
                    
                    # Extract File paths (FileLocation) as valid sourceID
                    if entity_type == 'File' and 'FileLocation' in entity:
                        file_path = entity['FileLocation']
                        entity_ids[file_path] = {
                            'type': 'File',
                            'id_field': 'FileLocation',
                            'line': line_num,
                            'file_name': entity.get('FileName', '')
                        }
                        entity_types['FilePath'].add(file_path)
                    
                    # Also check nested chat messages
                    if 'ChatMessages' in entity:
                        for msg in entity['ChatMessages']:
                            if 'ChatMessageId' in msg:
                                msg_id = msg['ChatMessageId']
                                entity_ids[msg_id] = {
                                    'type': 'ChatMessage',
                                    'id_field': 'ChatMessageId',
                                    'line': line_num
                                }
                                entity_types['ChatMessage'].add(msg_id)
                                
            except json.JSONDecodeError as e:
                print(f"  Error parsing line {line_num}: {e}")
    
    return entity_ids, entity_types

def extract_source_ids_from_output(output_file):
    """Extract all sourceIDs from the assertions in the output file."""
    source_ids = defaultdict(list)  # sourceID -> list of (utterance, assertion_idx)
    all_assertions = []
    
    with open(output_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                utterance = data.get('utterance', '')[:50] + '...'
                assertions = data.get('assertions', [])
                
                for idx, assertion in enumerate(assertions):
                    # Check both 'justification' and 'reasoning' fields
                    justification = assertion.get('justification', assertion.get('reasoning', {}))
                    
                    if isinstance(justification, dict):
                        source_id = justification.get('sourceID') or justification.get('sourceId')
                        if source_id:
                            source_ids[source_id].append({
                                'line': line_num,
                                'utterance': utterance,
                                'assertion_idx': idx,
                                'assertion_text': assertion.get('text', '')[:60] + '...'
                            })
                            all_assertions.append({
                                'line': line_num,
                                'source_id': source_id,
                                'utterance': utterance,
                                'assertion_text': assertion.get('text', '')[:80]
                            })
                                
            except json.JSONDecodeError as e:
                print(f"  Error parsing line {line_num}: {e}")
    
    return source_ids, all_assertions

def main():
    print("=" * 80)
    print("SourceID Recovery Check")
    print("=" * 80)
    
    # Check if files exist
    if not os.path.exists(CONTEXT_FILE):
        print(f"ERROR: Context file not found: {CONTEXT_FILE}")
        return
    if not os.path.exists(OUTPUT_FILE):
        print(f"ERROR: Output file not found: {OUTPUT_FILE}")
        return
    
    # Extract data from new context file (LOD_1125)
    print(f"\n1. Extracting entity IDs from NEW context file: {CONTEXT_FILE}")
    new_entity_ids, new_entity_types = extract_entity_ids_from_context(CONTEXT_FILE)
    print(f"   Found {len(new_entity_ids)} unique entity IDs")
    print(f"   Entity types breakdown:")
    for etype, ids in sorted(new_entity_types.items()):
        print(f"     - {etype}: {len(ids)} IDs")
    
    # Extract data from old context file if it exists
    old_entity_ids = {}
    if os.path.exists(OLD_CONTEXT_FILE):
        print(f"\n2. Extracting entity IDs from OLD context file: {OLD_CONTEXT_FILE}")
        old_entity_ids, old_entity_types = extract_entity_ids_from_context(OLD_CONTEXT_FILE)
        print(f"   Found {len(old_entity_ids)} unique entity IDs")
    
    # Extract sourceIDs from output file
    print(f"\n3. Extracting sourceIDs from output file: {OUTPUT_FILE}")
    source_ids, all_assertions = extract_source_ids_from_output(OUTPUT_FILE)
    print(f"   Found {len(source_ids)} unique sourceIDs referenced in assertions")
    print(f"   Total assertions with sourceID: {len(all_assertions)}")
    
    # Check recovery with NEW context file
    print(f"\n4. Checking sourceID recovery with NEW context file (LOD_1125.jsonl)")
    print("-" * 60)
    
    matched_new = []
    unmatched_new = []
    
    for source_id in source_ids.keys():
        if source_id in new_entity_ids:
            matched_new.append(source_id)
        else:
            unmatched_new.append(source_id)
    
    print(f"   MATCHED: {len(matched_new)} / {len(source_ids)} ({100*len(matched_new)/len(source_ids):.1f}%)")
    print(f"   UNMATCHED: {len(unmatched_new)} / {len(source_ids)} ({100*len(unmatched_new)/len(source_ids):.1f}%)")
    
    # Check recovery with OLD context file
    if old_entity_ids:
        print(f"\n5. Checking sourceID recovery with OLD context file (LOD_1121.jsonl)")
        print("-" * 60)
        
        matched_old = []
        unmatched_old = []
        
        for source_id in source_ids.keys():
            if source_id in old_entity_ids:
                matched_old.append(source_id)
            else:
                unmatched_old.append(source_id)
        
        print(f"   MATCHED: {len(matched_old)} / {len(source_ids)} ({100*len(matched_old)/len(source_ids):.1f}%)")
        print(f"   UNMATCHED: {len(unmatched_old)} / {len(source_ids)} ({100*len(unmatched_old)/len(source_ids):.1f}%)")
        
        # Compare improvement
        print(f"\n6. Improvement Analysis")
        print("-" * 60)
        improvement = len(matched_new) - len(matched_old)
        if improvement > 0:
            print(f"   NEW file recovers {improvement} more sourceIDs than OLD file!")
        elif improvement < 0:
            print(f"   OLD file recovers {-improvement} more sourceIDs than NEW file.")
        else:
            print(f"   Both files recover the same number of sourceIDs.")
    
    # Show details of matched sourceIDs
    print(f"\n7. Sample of MATCHED sourceIDs (showing first 10)")
    print("-" * 60)
    for i, source_id in enumerate(matched_new[:10]):
        entity_info = new_entity_ids[source_id]
        usages = source_ids[source_id]
        print(f"   {i+1}. {source_id}")
        print(f"      Entity Type: {entity_info['type']} ({entity_info['id_field']})")
        print(f"      Used in {len(usages)} assertion(s)")
    
    # Show details of unmatched sourceIDs
    if unmatched_new:
        print(f"\n8. UNMATCHED sourceIDs (missing from context)")
        print("-" * 60)
        for i, source_id in enumerate(unmatched_new):
            usages = source_ids[source_id]
            print(f"   {i+1}. {source_id}")
            print(f"      Used in {len(usages)} assertion(s)")
            for usage in usages[:2]:  # Show first 2 usages
                print(f"        - Line {usage['line']}: {usage['assertion_text'][:50]}...")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total unique sourceIDs in assertions: {len(source_ids)}")
    print(f"Matched with LOD_1125.jsonl: {len(matched_new)} ({100*len(matched_new)/len(source_ids):.1f}%)")
    print(f"Unmatched: {len(unmatched_new)} ({100*len(unmatched_new)/len(source_ids):.1f}%)")
    
    if len(matched_new) == len(source_ids):
        print("\n✅ ALL sourceIDs can be recovered from the NEW context file!")
    else:
        print(f"\n⚠️  {len(unmatched_new)} sourceID(s) cannot be found in the context file.")
    
    # Save detailed report
    report_file = os.path.join("docs", "sourceid_recovery_report.json")
    report = {
        "context_file": CONTEXT_FILE,
        "output_file": OUTPUT_FILE,
        "total_source_ids": len(source_ids),
        "matched_count": len(matched_new),
        "unmatched_count": len(unmatched_new),
        "match_rate": f"{100*len(matched_new)/len(source_ids):.1f}%",
        "matched_source_ids": matched_new,
        "unmatched_source_ids": unmatched_new,
        "entity_types_in_context": {k: len(v) for k, v in new_entity_types.items()}
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
