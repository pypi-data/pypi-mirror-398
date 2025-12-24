"""
TEMPORAL INFERENCE ENGINE - COMPREHENSIVE DOCUMENTATION
========================================================

This document explains the linguistic rules, their theoretical foundations,
and how to use the system to answer your research questions.

"""

# ============================================================================
# PART 1: LINGUISTIC RULES AND THEORETICAL FOUNDATIONS
# ============================================================================

"""
The inference engine implements 11 linguistic rules based on established
theories in formal semantics, aspect theory, and discourse representation.

RULE 1: TENSE-BASED ORDERING
-----------------------------
Theory: Reichenbach (1947) - Temporal framework with S (speech time), 
        E (event time), R (reference time)

Rule: Events with different tenses have temporal ordering
  - Past < Present < Future
  - Past tense: E before S
  - Present tense: E overlaps S  
  - Future tense: E after S

Example from your anchor story:
  T40 "follows" (Present) vs T41 "named" (Past Perfective)
  → "named" occurred before "follows" in the timeline

Confidence: 0.9 (very reliable)


RULE 2: ASPECT AND DURATION
----------------------------
Theory: Smith (1991) - Aspectual viewpoint theory

Rule: Aspect determines boundedness and duration
  - Perfective: Completed, bounded event
  - Progressive: Ongoing, unbounded process
  - Two perfective events → sequential (narrative progression)
  - Progressive + Perfective → overlap

Example from your anchor story:
  T43 "Beginning" (Present Progressive) + T44 "established" (Past Perfective)
  → "Beginning" overlaps with "established"

Confidence: 0.6-0.7 (moderate to strong)


RULE 3: EVENT TYPE TEMPORAL PROPERTIES
---------------------------------------
Theory: Vendler (1957), Moens & Steedman (1988) - Event classification

Rule: Event types have inherent temporal properties
  - STATE: Durative, stable, no change
    • Can overlap extensively with other events
    • No natural endpoint
    
  - PROCESS: Dynamic, atelic, durative
    • Has internal stages
    • No inherent culmination point
    
  - TRANSITION: Dynamic, telic, bounded
    • Has culmination point
    • Results in change of state
    • Subsumes achievements and accomplishments

Temporal implications:
  - TRANSITION → STATE: result state relation
  - TRANSITION → TRANSITION: sequential
  - STATE overlaps with PROCESS/TRANSITION
  - PROCESS can precede TRANSITION

Example from your anchor story:
  T46 "based" (STATE) can overlap with T47 "established" (STATE)
  T54 "issued" (TRANSITION) → T65 "valid" (STATE): result state

Confidence: 0.65-0.75


RULE 4: TRANSITION CONSEQUENCE
-------------------------------
Theory: Moens & Steedman (1988) - Consequent state of transitions

Rule: TRANSITION events produce result states
  - Every TRANSITION has a consequent state
  - If a STATE follows a TRANSITION → likely causal/temporal link

Example from your anchor story:
  T54 "issued" (TRANSITION) → following STATE event
  The act of issuing creates a state where something exists

Confidence: 0.7


RULE 5: STATE OVERLAP
---------------------
Theory: Stative predicates (Dowty 1979)

Rule: STATES tend to overlap with other events
  - States provide background conditions
  - Other events occur "during" states

Example from your anchor story:
  T65 "valid" (STATE) can overlap with multiple events
  T67 "threat" (STATE) provides background for actions

Confidence: 0.6


RULE 6: PROCESS DURATION
------------------------
Theory: Atelic events (Vendler 1957)

Rule: PROCESS events have duration and can co-occur
  - Processes don't have natural endpoints
  - Multiple processes can overlap temporally

Example from your anchor story:
  T60 "cooperate" (PROCESS) + T61 "drill" (PROCESS)
  → These can occur simultaneously

Confidence: 0.5


RULE 7: PERFECTIVE COMPLETION
------------------------------
Theory: Reichenbach (1947) - E before S

Rule: Perfective + Past = completed before speech time
  - Anchors events to "now"
  - E < S

Example from your anchor story:
  T44 "established" (Past Perfective)
  → Completed before the story's reference time

Confidence: 0.95 (very reliable)


RULE 8: PARTICIPLE RESULT STATE
--------------------------------
Theory: Kratzer (1994) - Participial constructions

Rule: Past participles denote result states
  - "written" = result of writing
  - "established" = result of establishing

Example from your anchor story:
  T44 "established" (Past Participle)
  T45 "based" (Past Participle)
  → Both denote ongoing result states

Confidence: 0.75


RULE 9: TEMPORAL ANCHOR
-----------------------
Theory: Explicit temporal grounding

Rule: Events with temporal expressions are anchored
  - Uses TLINK annotations between events and times

Example from your anchor story:
  T77 "2025" anchors events happening in that year

Confidence: 1.0 (explicit annotation)


RULE 10: NARRATIVE PROGRESSION
-------------------------------
Theory: Kamp & Reyle (1993) - Discourse Representation Theory

Rule: In narrative, same-tense events follow discourse order
  - Foreground events (TRANSITION/PROCESS) advance narrative
  - Background events (STATE) don't advance time

Example from your anchor story:
  T40 "follows" → T41 "named" → T42 "act"
  Sequential interpretation in narrative discourse

Confidence: 0.65


RULE 11: CAUSAL-TEMPORAL INFERENCE
-----------------------------------
Theory: Hobbs (1985) - Coherence relations

Rule: Semantic relations imply temporal ordering
  - Agent/cause precedes patient/effect
  - Instrumental relations have temporal structure

Example from your anchor story:
  SRLINK_agent relations indicate who performs which actions
  This implies temporal structure of agency

Confidence: 0.8
"""


# ============================================================================
# PART 2: ANSWERING YOUR RESEARCH QUESTIONS
# ============================================================================

"""
RQ1: Does the type of event convey helpful information to expand time relations?
--------------------------------------------------------------------------------

APPROACH:
1. Baseline: DRS with NER + SRL (no event types)
2. Enriched: DRS with NER + SRL + Event Types

Compare the number and quality of inferred temporal relations.

Expected findings:
- Event types enable rules 3, 4, 5, 6 (event_type_temporal, transition_consequence,
  state_overlap, process_duration)
- These rules rely specifically on STATE/PROCESS/TRANSITION distinctions
- Without event types, you can only use rules 1, 2, 7, 8, 9, 10, 11

EVALUATION METRICS:
- Number of temporal relations inferred
- Precision/Recall against gold standard temporal annotations
- Coverage: % of event pairs with inferred relations

CODE EXAMPLE:

```python
# Baseline: Disable event-type-dependent rules
engine = TemporalInferenceEngine()
engine.rules = {k: v for k, v in engine.rules.items() 
               if k not in ['event_type_temporal', 'transition_consequence',
                           'state_overlap', 'process_duration']}

baseline_inferred = engine.apply_all_rules(ann_dict, dexpr_list)

# Enriched: Use all rules including event types
engine_full = TemporalInferenceEngine()
enriched_inferred = engine_full.apply_all_rules(ann_dict, dexpr_list)

print(f"Baseline relations: {len(baseline_inferred)}")
print(f"Enriched relations: {len(enriched_inferred)}")
print(f"Gain from event types: {len(enriched_inferred) - len(baseline_inferred)}")
```

RQ2: What is the influence of linguistic rules in enrichment of DRS?
--------------------------------------------------------------------

APPROACH: Ablation study - remove each rule individually

Use the ablation_study() function provided in temporal_inference_integration.py

This will create:
- no_inference: Baseline with no inference
- all_rules: All rules enabled
- only_tense: Only tense-based rules
- only_aspect: Only aspect-based rules
- only_event_type: Only event type rules
- only_narrative: Only narrative progression
- no_X: All rules except X

EVALUATION METRICS:
- Δ relations for each ablation
- Precision/Recall for each configuration
- Qualitative analysis: which rules produce most useful relations?

CODE EXAMPLE:

```python
from temporal_inference_integration import ablation_study

results = ablation_study('your_ann_dir/', output_dir='ablation_results/')

# Results will be saved in ablation_results/ with subdirectories for each config
# Compare DRS files and evaluate against gold standard
```

EXPECTED FINDINGS:
- Tense rules: High precision, moderate coverage
- Aspect rules: Moderate precision, specific scenarios
- Event type rules: High precision for STATE/TRANSITION patterns
- Narrative rules: Lower precision but high coverage


RQ3: Does enriched DRS aid model learning?
------------------------------------------

APPROACH: Train similarity model on enriched vs baseline DRS

Experimental setup:
1. Create two versions of DRS for each story:
   - Baseline: Manual annotations only
   - Enriched: Manual + inferred temporal relations

2. Train two models:
   - Model_baseline: Learns from baseline DRS
   - Model_enriched: Learns from enriched DRS

3. Evaluate on narrative similarity task (A vs B given anchor)

MODEL ARCHITECTURES TO CONSIDER:
- Graph Neural Network (GNN) on DRS graphs
- Graph Matching Network
- Siamese network with graph kernels
- Transformer over linearized DRS

EVALUATION METRICS:
- Accuracy on A vs B selection
- Correlation with human judgments
- Graph similarity metrics (Graph Edit Distance)

CODE EXAMPLE:

```python
# Generate both versions
baseline_drs = process_without_inference(ann_dict)
enriched_drs, inferred = integrate_inference_engine(ann_dict, baseline_drs)

# Train models (pseudo-code)
model_baseline = train_similarity_model(baseline_drs_dataset)
model_enriched = train_similarity_model(enriched_drs_dataset)

# Evaluate
acc_baseline = evaluate(model_baseline, test_triplets)
acc_enriched = evaluate(model_enriched, test_triplets)

print(f"Baseline accuracy: {acc_baseline}")
print(f"Enriched accuracy: {acc_enriched}")
print(f"Improvement: {acc_enriched - acc_baseline}")
```

EXPECTED FINDINGS:
- Enriched DRS provides more structured temporal information
- This should help model learn better temporal ordering patterns
- Especially helpful for stories with implicit temporal relations
"""


# ============================================================================
# PART 3: PRACTICAL USAGE EXAMPLES
# ============================================================================

"""
EXAMPLE 1: Processing Your Anchor Story
----------------------------------------

Input: 0_anchor.txt (BRAT annotation)
Events include:
- T40 "follows" (Present, Verb)
- T41 "named" (Past Perfective, Participle)
- T46 "based" (STATE, Past Perfective, Participle)
- T54 "issued" (TRANSITION, Past Perfective, Participle)
- T60 "cooperate" (PROCESS, Present)
- etc.

Processing:
"""

def example_process_anchor():
    from brat2drs import read_file, file_parser, assign_variable, attributes_events
    from temporal_inference_engine import TemporalInferenceEngine
    
    # Load annotations
    filecontent = read_file('sample/0_anchor.ann')
    f_parser = file_parser(filecontent)
    
    # Build basic DRS
    dexpr_list, f_parser = assign_variable(f_parser)
    dr_set, dexpr_list = attributes_events(dexpr_list, f_parser)
    
    # Apply inference
    engine = TemporalInferenceEngine()
    inferred = engine.apply_all_rules(f_parser, dexpr_list)
    
    print(f"\n{'='*80}")
    print("INFERRED TEMPORAL RELATIONS")
    print("="*80)
    
    for i, rel in enumerate(inferred[:10], 1):
        print(f"\n[{i}] {rel['relation']}")
        print(f"    Rule: {rel['rule']}")
        print(f"    Confidence: {rel['confidence']:.2f}")
        print(f"    {rel['explanation']}")
    
    # Add to DRS
    dexpr_list = engine.add_to_drs(dexpr_list, inferred, min_confidence=0.6)
    
    # Generate report
    report = engine.generate_report()
    print("\n" + report)
    
    return dexpr_list, inferred


"""
EXAMPLE 2: Comparing Two Stories
---------------------------------

To measure narrative similarity between anchor and candidate stories:
"""

def example_compare_stories():
    """
    Compare temporal structure of two stories.
    """
    from temporal_inference_engine import TemporalInferenceEngine
    import numpy as np
    
    # Process both stories
    engine1 = TemporalInferenceEngine()
    inferred1 = engine1.apply_all_rules(story1_ann, story1_drs)
    
    engine2 = TemporalInferenceEngine()
    inferred2 = engine2.apply_all_rules(story2_ann, story2_drs)
    
    # Extract temporal features
    def get_temporal_features(inferred_relations):
        features = {
            'num_before': 0,
            'num_after': 0,
            'num_overlaps': 0,
            'num_during': 0,
            'num_result_state': 0,
            'avg_confidence': 0
        }
        
        for rel in inferred_relations:
            rel_type = rel['relation']
            if 'Before' in rel_type:
                features['num_before'] += 1
            elif 'After' in rel_type:
                features['num_after'] += 1
            elif 'overlaps' in rel_type:
                features['num_overlaps'] += 1
            elif 'during' in rel_type:
                features['num_during'] += 1
            elif 'result' in rel_type.lower():
                features['num_result_state'] += 1
        
        if inferred_relations:
            features['avg_confidence'] = np.mean([r['confidence'] 
                                                  for r in inferred_relations])
        
        return features
    
    feat1 = get_temporal_features(inferred1)
    feat2 = get_temporal_features(inferred2)
    
    # Compute similarity (cosine similarity of feature vectors)
    from sklearn.metrics.pairwise import cosine_similarity
    
    vec1 = np.array(list(feat1.values())).reshape(1, -1)
    vec2 = np.array(list(feat2.values())).reshape(1, -1)
    
    similarity = cosine_similarity(vec1, vec2)[0][0]
    
    print(f"Temporal structure similarity: {similarity:.3f}")
    
    return similarity, feat1, feat2


"""
EXAMPLE 3: Analyzing Rule Contributions
----------------------------------------

Understand which rules contribute most to your dataset:
"""

def example_analyze_rules():
    """
    Analyze which rules fire most frequently in your dataset.
    """
    from temporal_inference_integration import get_rule_statistics
    
    stats = get_rule_statistics('your_ann_dir/')
    
    # Results show:
    # - Most frequent rules
    # - Most frequent relation types
    # - Distribution across dataset
    
    return stats


"""
EXAMPLE 4: Confidence Threshold Selection
------------------------------------------

Find optimal confidence threshold for your task:
"""

def example_find_threshold():
    """
    Analyze different confidence thresholds.
    """
    from temporal_inference_integration import analyze_confidence_thresholds
    
    stats = analyze_confidence_thresholds(
        'your_ann_dir/', 
        thresholds=[0.5, 0.6, 0.7, 0.8, 0.9]
    )
    
    # Evaluate precision/recall at each threshold
    # Select threshold that balances precision and coverage
    
    return stats


# ============================================================================
# PART 4: INTEGRATION WITH YOUR PIPELINE
# ============================================================================

"""
STEP-BY-STEP INTEGRATION:

1. Copy files to your project:
   - temporal_inference_engine.py
   - temporal_inference_integration.py

2. Modify brat2drs.py:
   
   # At the top
   from temporal_inference_engine import integrate_inference_engine
   
   # In main() function, after event_event_relation():
   dexpr_list = event_event_relation(f_parser, dexpr_list)
   
   # >>> Add inference <<<
   report_file = os.path.join(DRS_DIR, f"{base_name}_inference.txt")
   dexpr_list, inferred = integrate_inference_engine(
       f_parser, 
       dexpr_list, 
       min_confidence=0.6,
       report_file=report_file
   )
   # >>> End inference <<<
   
   actors, actors_sr = actors_relation(f_parser)
   # ... rest of pipeline

3. Run on your dataset:
   python brat2drs.py

4. For research questions:
   - RQ1: Run ablation_study() with/without event type rules
   - RQ2: Run full ablation_study() 
   - RQ3: Use enriched DRS for model training

5. Evaluate results:
   - Compare DRS files in output directory
   - Read inference reports for each document
   - Analyze statistics across dataset
"""


# ============================================================================
# PART 5: EXPECTED OUTPUT
# ============================================================================

"""
When processing your anchor story (0_anchor.txt), you should see output like:

================================================================================
APPLYING TEMPORAL INFERENCE RULES
================================================================================
✓ tense_ordering: 45 relations inferred
✓ aspect_duration: 23 relations inferred
✓ event_type_temporal: 31 relations inferred
✓ transition_consequence: 12 relations inferred
✓ state_overlap: 28 relations inferred
✓ process_duration: 8 relations inferred
✓ perfective_completion: 38 relations inferred
✓ participle_result_state: 15 relations inferred
✓ temporal_anchor: 3 relations inferred
✓ narrative_progression: 29 relations inferred
✓ causal_temporal: 18 relations inferred

✓ Added 142 temporal relations to DRS (confidence >= 0.6)

Example inferred relations:

[1] occursBefore
    Events: a -> b
    Rule: tense_ordering
    Confidence: 0.90
    Explanation: Past tense (named) before Present (follows)

[2] resultState
    Events: g -> h
    Rule: transition_consequence
    Confidence: 0.70
    Explanation: TRANSITION (issued) results in STATE (valid)

[3] overlaps
    Events: m -> n
    Rule: event_type_temporal
    Confidence: 0.65
    Explanation: STATE (threat) overlaps PROCESS (cooperate)

etc.

The enriched DRS will now include these inferred temporal relations
alongside your manually annotated relations, creating a richer
temporal representation for similarity learning.
"""


# ============================================================================
# PART 6: TROUBLESHOOTING
# ============================================================================

"""
COMMON ISSUES:

1. "No inferred relations"
   → Check that events have Type, Tense, Aspect attributes
   → Verify BRAT annotations are properly formatted
   → Try lowering confidence threshold

2. "Too many inferred relations"
   → Increase confidence threshold (try 0.7 or 0.8)
   → Disable lower-confidence rules
   → Review and filter by specific rule types

3. "Conflicting relations"
   → Normal - different rules may propose different relations
   → Use confidence scores to resolve
   → Consider consistency checking post-processing

4. "Performance issues"
   → Rule application is O(n²) in events
   → For large documents, consider batching
   → Or limit rules to adjacent events (window size)

5. "Integration errors"
   → Ensure nltk.sem.drt is installed
   → Check that dexpr_list has correct format
   → Verify event variables are properly assigned
"""

if __name__ == "__main__":
    print(__doc__)