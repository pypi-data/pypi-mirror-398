"""Experiments Usage Examples

This example demonstrates experiment management: creating experiments to batch-test
prompt configurations against datasets, monitoring progress, and viewing results.

Experiments run multiple prompt/model configurations against every record in a dataset,
generating a result dataset with all outputs for comparison.

Requirements:
    pip install lumenova-beacon

    Set environment variables:
    export BEACON_ENDPOINT=https://your-endpoint.com
    export BEACON_API_KEY=your_api_key
"""

from lumenova_beacon import BeaconClient
from lumenova_beacon.datasets import Dataset
from lumenova_beacon.experiments import Experiment, ExperimentConfig, ExperimentStatus
from lumenova_beacon.llm_configs import LLMConfig
from lumenova_beacon.prompts import Prompt

# Initialize the client (reads from BEACON_ENDPOINT and BEACON_API_KEY env vars)
client = BeaconClient()


# === List All Experiments ===
# List experiments with pagination
experiments, pagination = Experiment.list(page=1, page_size=10)
print(f"Total experiments: {pagination.total}")

for exp in experiments:
    print(f"  - {exp.name}")
    print(f"    ID: {exp.id}")
    print(f"    Status: {exp.status.name}")
    print(f"    Records: {exp.record_count}, Configurations: {exp.configuration_count}")


# === Filter by Status ===
# Get only running experiments
running, _ = Experiment.list(status=ExperimentStatus.RUNNING)
print(f"\nRunning experiments: {len(running)}")

# Get completed experiments
completed, _ = Experiment.list(status=ExperimentStatus.COMPLETED)
print(f"Completed experiments: {len(completed)}")

# Get failed experiments
failed, _ = Experiment.list(status=ExperimentStatus.FAILED)
print(f"Failed experiments: {len(failed)}")


# === Search Experiments ===
# Search by name or description
search_results, _ = Experiment.list(search="comparison")
print(f"\nExperiments matching 'comparison': {len(search_results)}")


# === Get Experiment by ID ===
if experiments:
    experiment = Experiment.get(experiments[0].id)
    print("\nExperiment details:")
    print(f"  Name: {experiment.name}")
    print(f"  ID: {experiment.id}")
    print(f"  Status: {experiment.status.name}")
    print(f"  Dataset: {experiment.dataset_name} ({experiment.dataset_id})")
    print(f"  Records: {experiment.record_count}")
    print(f"  Configurations: {experiment.configuration_count}")
    if experiment.description:
        print(f"  Description: {experiment.description}")
    if experiment.variable_mappings:
        print(f"  Variable mappings: {experiment.variable_mappings}")
    print(f"  Created: {experiment.created_at}")
    if experiment.started_at:
        print(f"  Started: {experiment.started_at}")
    if experiment.completed_at:
        print(f"  Completed: {experiment.completed_at}")


# === List Available LLM Configs ===
# List LLM configurations available for experiments
llm_configs = LLMConfig.list()
print(f"\nAvailable LLM configs: {len(llm_configs)}")
for cfg in llm_configs:
    print(f"  - {cfg.name}: {cfg.provider}/{cfg.litellm_model}")


# === Create New Experiment ===
# First, get a dataset to run the experiment on
datasets, _ = Dataset.list(page=1, page_size=1)
prompts = Prompt.list(page=1, page_size=1)

if datasets and datasets[0].id and prompts and llm_configs:
    dataset = datasets[0]
    prompt = prompts[0]
    print(f"\nUsing dataset: {dataset.name} (ID: {dataset.id})")
    print(f"Using prompt: {prompt.name} (v{prompt.version})")

    # Get two different LLM configs for comparison (or use the same with different params)
    llm_a = llm_configs[0]
    llm_b = llm_configs[1] if len(llm_configs) > 1 else llm_configs[0]

    # Create experiment with typed configurations
    # Each ExperimentConfig combines a Prompt with an LLMConfig
    experiment = Experiment.create(
        name="Model Comparison Experiment",
        dataset_id=str(dataset.id),
        description="Compare different model configurations",
        configurations=[
            ExperimentConfig(
                label="A",
                prompt=prompt,
                llm_config=llm_a,
                model_parameters={
                    "temperature": 0.7,
                    "max_tokens": 100,
                },
            ),
            ExperimentConfig(
                label="B",
                prompt=prompt,
                llm_config=llm_b,
                model_parameters={
                    "temperature": 0.9,
                    "max_tokens": 100,
                },
            ),
        ],
        variable_mappings={
            "name": "input.user_name",
            "context": "input.context",
        },
    )

    print(f"\nCreated experiment: {experiment.name}")
    print(f"  ID: {experiment.id}")
    print(f"  Status: {experiment.status.name}")
    print(f"  Configurations: {experiment.configuration_count}")


# === Start Experiment ===
# Experiments are created in DRAFT status - start to begin execution
experiment.start()
print(f"Experiment started! Status: {experiment.status.name}")


# === Monitor Progress ===
# Check progress while experiment is running
if experiments:
    exp = experiments[0]
    if exp.status in [ExperimentStatus.RUNNING, ExperimentStatus.QUEUED]:
        progress = exp.get_progress()
        print("\nExperiment progress:")
        print(f"  Total runs: {progress['total_runs']}")
        print(f"  Completed: {progress['completed_runs']}")
        print(f"  Failed: {progress['failed_runs']}")
        print(f"  Progress: {progress['progress_percent']:.1f}%")

# Example: Poll until complete (uncomment to use)
import time
while experiment.status in [ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]:
    progress = experiment.get_progress()
    print(f"Progress: {progress['progress_percent']:.1f}% "
          f"({progress['completed_runs']}/{progress['total_runs']})")
    experiment = Experiment.get(experiment.id)  # Refresh status
    time.sleep(5)
print(f"Finished! Status: {experiment.status.name}")


# === Get Source Dataset ===
# Access the source dataset used for the experiment
if experiments:
    exp = experiments[0]
    source_dataset = exp.get_dataset()
    print(f"\nSource dataset: {source_dataset.name}")
    print(f"  ID: {source_dataset.id}")
    print(f"  Record count: {source_dataset.record_count}")


# === Get Result Dataset ===
# After completion, results are saved to a new dataset
if experiments:
    exp = experiments[0]
    if exp.status == ExperimentStatus.COMPLETED and exp.result_dataset_id:
        result_dataset = exp.get_result_dataset()
        if result_dataset:
            print(f"\nResult dataset: {result_dataset.name}")
            print(f"  ID: {result_dataset.id}")
            print(f"  Record count: {result_dataset.record_count}")

            # View sample results
            records, _ = result_dataset.list_records(page=1, page_size=3)
            print(f"\n  Sample results (first {len(records)} records):")
            for record in records:
                print(f"    - Record {record.id}")


# === Cancel Experiment ===
# Cancel a running or queued experiment
# running, _ = Experiment.list(status=ExperimentStatus.RUNNING)
# if running:
#     exp = running[0]
#     exp.cancel()
#     print(f"Cancelled experiment: {exp.name}")
#     print(f"New status: {exp.status.name}")


# === Update Experiment ===
# Update experiment name or description
if experiments:
    exp = experiments[0]
    exp.update(
        name="Updated Experiment Name",
        description="Updated description",
    )
    print(f"\nUpdated experiment: {exp.name}")


# === Delete Experiment ===
# Delete an experiment (commented out to prevent accidental deletion)
# if experiments:
#     exp = experiments[0]
#     exp.delete()
#     print(f"Deleted experiment: {exp.id}")
