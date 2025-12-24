"""Evaluations Usage Examples

This example demonstrates evaluation management: listing evaluators, creating evaluations,
running them on traces or datasets, and viewing results.

Evaluations apply an evaluator (LLM-as-judge or code-based) to traces or dataset records.
- Trace-based evaluations: Use filter_rules to select traces, can auto-run on new traces
- Dataset-based evaluations: Run on all records in a dataset

Requirements:
    pip install lumenova-beacon

    Set environment variables:
    export BEACON_ENDPOINT=https://your-endpoint.com
    export BEACON_API_KEY=your_api_key
"""

from lumenova_beacon import BeaconClient
from lumenova_beacon.evaluations import (
    Evaluation,
    EvaluationRun,
    Evaluator,
    EvaluationRunStatus,
)

# Initialize the client (reads from BEACON_ENDPOINT and BEACON_API_KEY env vars)
client = BeaconClient()


# === List Available Evaluators ===
# Evaluators are templates that define how to evaluate (LLM prompts or Python code)
evaluators, pagination = Evaluator.list(page=1, page_size=20)
print(f"Available evaluators: {pagination.total}")

for evaluator in evaluators:
    print(f"  - {evaluator.name} ({evaluator.evaluator_type})")
    if evaluator.score_config:
        print(f"    Score type: {evaluator.score_config.get('type')}")


# === Get Evaluator Details ===
# Fetch a specific evaluator to see its configuration
if evaluators:
    evaluator = Evaluator.get(evaluators[0].id)
    print(f"\nEvaluator: {evaluator.name}")
    print(f"  Type: {evaluator.evaluator_type}")
    print(f"  Predefined: {evaluator.is_predefined}")
    print(f"  Description: {evaluator.description}")

    # LLM evaluators have prompt templates
    if evaluator.prompt_template:
        print(f"  Prompt template: {evaluator.prompt_template[:100]}...")

    # Code evaluators have Python code and parameters
    if evaluator.code:
        print(f"  Code: {len(evaluator.code)} characters")
    if evaluator.code_parameters:
        print(f"  Parameters: {[p['name'] for p in evaluator.code_parameters]}")


# === Create Trace-Based Evaluation ===
# Trace evaluations apply to spans matching filter rules
trace_evaluation = Evaluation.create(
    name="Response Quality Check",
    evaluator_id="your-evaluator-uuid",  # Replace with actual evaluator ID
    variable_mappings={
        "question": "span.input",     # Map evaluator variable to span input
        "answer": "span.output",      # Map evaluator variable to span output
    },
    filter_rules={
        "logic": "AND",
        "rules": [
            {"field": "span.name", "operator": "contains", "value": "chat"}
        ],
    },
    active=True,  # Auto-run on new matching traces
    description="Evaluates chat response quality",
)
print(f"\nCreated trace evaluation: {trace_evaluation.name}")
print(f"  ID: {trace_evaluation.id}")
print(f"  Active: {trace_evaluation.active}")
print(f"  Score type: {trace_evaluation.score_type}")


# === Create Dataset-Based Evaluation ===
# Dataset evaluations run on all records in a dataset
dataset_evaluation = Evaluation.create(
    name="Dataset QA Evaluation",
    evaluator_id="your-evaluator-uuid",  # Replace with actual evaluator ID
    variable_mappings={
        "question": "input",           # Map to dataset column 'input'
        "answer": "output",            # Map to dataset column 'output'
        "expected": "ground_truth",    # Map to dataset column 'ground_truth'
    },
    dataset_id="your-dataset-uuid",    # Replace with actual dataset ID
)
print(f"\nCreated dataset evaluation: {dataset_evaluation.name}")


# === Get Evaluation by ID ===
evaluation = Evaluation.get(trace_evaluation.id)
print(f"\nFetched evaluation: {evaluation.name}")


# === Get Evaluation with Statistics ===
# Include statistics to see run counts and average scores
evaluation = Evaluation.get(
    trace_evaluation.id,
    include_evaluator=True,
    include_statistics=True,
)

if evaluation.statistics:
    stats = evaluation.statistics
    print("\nEvaluation statistics:")
    print(f"  Total runs: {stats['total_runs']}")
    print(f"  Completed: {stats['completed_runs']}")
    print(f"  Failed: {stats['failed_runs']}")
    print(f"  Average score: {stats.get('avg_score')}")


# === List Evaluations ===
evaluations, pagination = Evaluation.list(page=1, page_size=20)
print(f"\nTotal evaluations: {pagination.total}")

for eval in evaluations:
    eval_type = "trace" if eval.filter_rules else "dataset"
    print(f"  - {eval.name} ({eval_type}, active={eval.active})")

# Filter by evaluator
evaluations, _ = Evaluation.list(evaluator_id="your-evaluator-uuid")

# Search by name
evaluations, _ = Evaluation.list(search="quality")


# === Run Evaluation on Single Trace ===
# Run evaluation on a specific trace
run = evaluation.run(trace_id="your-trace-id")
print(f"\nCreated run: {run.id}")
print(f"  Status: {run.status.value}")

# For dataset evaluations, use dataset_record_id instead:
# run = evaluation.run(dataset_record_id="your-record-id")


# === Execute Evaluation on All Targets ===
# Run evaluation on all matching traces or dataset records
result = evaluation.execute()
print("\nExecution result:")
print(f"  Total targets: {result['total_targets']}")
print(f"  Runs created: {result['runs_created']}")


# === List Evaluation Runs ===
runs, pagination = evaluation.list_runs(page=1, page_size=20)
print(f"\nEvaluation runs: {pagination.total}")

for run in runs:
    # score_data contains typed score: {type: 'percent'|'numeric'|'categorical', value: ...}
    score_info = run.score_data if run.score_data else {"value": run.score}
    print(f"  - {run.id}: {run.status.value}, score={score_info.get('value')}")


# === Filter Runs by Status ===
# Get only completed runs
completed_runs, _ = evaluation.list_runs(status=EvaluationRunStatus.COMPLETED)
print(f"\nCompleted runs: {len(completed_runs)}")

for run in completed_runs:
    print(f"  Score: {run.score_data}")
    if run.result:
        print(f"  Result: {run.result}")

# Get failed runs to investigate errors
failed_runs, _ = evaluation.list_runs(status=EvaluationRunStatus.FAILED)
for run in failed_runs:
    print(f"  Error: {run.error_message}")


# === Get Evaluation Run Details ===
if runs:
    run = EvaluationRun.get(runs[0].id)
    print("\nRun details:")
    print(f"  ID: {run.id}")
    print(f"  Evaluation: {run.evaluation_name}")
    print(f"  Status: {run.status.value}")
    print(f"  Score: {run.score}")
    print(f"  Score data: {run.score_data}")
    print(f"  Trace ID: {run.trace_id}")
    print(f"  Created: {run.created_at}")
    print(f"  Completed: {run.completed_at}")


# === List All Runs (across evaluations) ===
all_runs, pagination = EvaluationRun.list(page=1, page_size=50)
print(f"\nAll evaluation runs: {pagination.total}")

# Filter by evaluation
runs, _ = EvaluationRun.list(evaluation_id=evaluation.id)

# Filter by trace
runs, _ = EvaluationRun.list(trace_id="your-trace-id")

# Filter by status
runs, _ = EvaluationRun.list(status=EvaluationRunStatus.COMPLETED)


# === Update Evaluation ===
evaluation.update(
    name="Updated Evaluation Name",
    description="Updated description",
    active=False,  # Disable auto-run
)
print(f"\nUpdated evaluation: {evaluation.name}")


# === Bulk Delete Evaluation Runs ===
# Delete multiple runs at once
if runs:
    run_ids = [run.id for run in runs[:2]]  # Delete first 2 runs
    result = EvaluationRun.bulk_delete(run_ids)
    print(f"\nBulk deleted runs: {result}")


# === Bulk Delete Evaluations ===
# Delete multiple evaluations (cascades to their runs)
result = Evaluation.bulk_delete([trace_evaluation.id, dataset_evaluation.id])
print(f"\nBulk deleted evaluations: {result}")


# === Delete Single Evaluation ===
# Deleting an evaluation also deletes all its runs
# evaluation.delete()
# print("Evaluation deleted")
