"""Dataset Usage Examples

This example demonstrates dataset management: creating datasets, adding records
with flexible column-based data, pagination, updates, and deletions.

Each record contains a 'data' field with arbitrary key-value pairs representing columns.
The column structure is user-defined and can vary between records.

Requirements:
    pip install lumenova-beacon

    Set environment variables:
    export BEACON_ENDPOINT=https://your-endpoint.com
    export BEACON_API_KEY=your_api_key
"""

from lumenova_beacon import BeaconClient
from lumenova_beacon.datasets import Dataset, DatasetRecord

# Initialize the client (reads from BEACON_ENDPOINT and BEACON_API_KEY env vars)
client = BeaconClient()


# === List Datasets ===
# List all datasets with pagination
datasets, pagination = Dataset.list(page=1, page_size=20)
print(f"Total datasets: {pagination.total}")

for ds in datasets:
    print(f"  - {ds.name} (ID: {ds.id}, records: {ds.record_count})")


# === Search Datasets ===
# Search by name or description
search_results, _ = Dataset.list(search="evaluation")
print(f"\nDatasets matching 'evaluation': {len(search_results)}")


# === Get Dataset by ID ===
if datasets and datasets[0].id:
    dataset = Dataset.get(str(datasets[0].id))
    print("\nDataset details:")
    print(f"  Name: {dataset.name}")
    print(f"  ID: {dataset.id}")
    print(f"  Description: {dataset.description}")
    print(f"  Record count: {dataset.record_count}")
    print(f"  Created: {dataset.created_at}")


# === Create Dataset ===
# column_schema is required and must have at least one column
dataset = Dataset.create(
    name="qa-evaluation-dataset",
    column_schema=[
        {"name": "prompt", "order": 0},
        {"name": "expected_answer", "order": 1},
        {"name": "difficulty", "order": 2},
        {"name": "category", "order": 3},
    ],
    description="A dataset for testing question answering systems",
)
print(f"\nCreated dataset: {dataset.name} (ID: {dataset.id})")


# === Add Individual Records ===
# Create records one at a time with flexible column-based data
record1 = dataset.create_record(
    data={
        "prompt": "What is the capital of France?",
        "expected_answer": "Paris",
        "confidence": 1.0,
        "difficulty": "easy",
        "category": "geography",
    }
)
print(f"\nCreated record: {record1.id}")

record2 = dataset.create_record(
    data={
        "prompt": "Explain quantum entanglement",
        "expected_answer": "Quantum entanglement is a phenomenon...",
        "difficulty": "hard",
        "category": "physics",
    }
)


# === Bulk Add Records ===
# More efficient for adding multiple records at once
bulk_records = dataset.bulk_create_records([
    {
        "data": {
            "prompt": "What is 2 + 2?",
            "expected_answer": "4",
            "difficulty": "easy",
            "category": "math",
        }
    },
    {
        "data": {
            "prompt": "Who wrote Hamlet?",
            "expected_answer": "William Shakespeare",
            "difficulty": "medium",
            "category": "literature",
        }
    },
    {
        "data": {
            "prompt": "What is the speed of light?",
            "expected_answer": "299,792,458 meters per second",
            "difficulty": "medium",
            "category": "physics",
        }
    },
])
print(f"\nBulk created {len(bulk_records)} records")


# === List Records ===
# List records with pagination
records, pagination = dataset.list_records(page=1, page_size=10)
print(f"\nTotal records in dataset: {pagination.total}")

for record in records:
    print(f"  - {record.id}: {record.data.get('prompt', '')[:50]}...")


# === Get Record by ID ===
if records and dataset.id and records[0].id:
    record = DatasetRecord.get(str(dataset.id), str(records[0].id))
    print("\nRecord details:")
    print(f"  ID: {record.id}")
    print(f"  Data: {record.data}")
    print(f"  Created: {record.created_at}")


# === Update Dataset ===
# Method 1: Use update() method
dataset.update(
    name="qa-evaluation-dataset-v2",
    description="Updated description",
)
print(f"\nUpdated dataset: {dataset.name}")

# Method 2: Set attributes and call save()
dataset.name = "qa-evaluation-dataset-final"
dataset.save()
print(f"Saved dataset: {dataset.name}")


# === Update Record ===
# Update record data with new or modified columns
record1.update(
    data={
        "prompt": "What is the capital of France?",
        "expected_answer": "Paris",
        "actual_answer": "Paris",
        "model": "gpt-4",
        "confidence": 0.95,
        "difficulty": "easy",
        "category": "geography",
        "tested": True,
    }
)
print(f"\nUpdated record: {record1.id}")


# === Import from CSV ===
# Import records from a CSV file with column mapping
# Single column mapping: copies value directly
# Multi-column mapping: combines into a JSON object
records_imported = dataset.import_from_csv(
    "evaluation_data.csv",
    column_mapping={
        "prompt": "question",  # Single column
        "expected_answer": "answer",  # Single column
        "metadata": ["difficulty", "category"],  # Combined into {"difficulty": ..., "category": ...}
    }
)
# print(f"Imported {records_imported} records from CSV")


# === Delete Record ===
record2.delete()
print(f"\nDeleted record: {record2.id}")


# === Delete Dataset ===
# Deleting a dataset cascade deletes all its records
dataset.delete()
print(f"Deleted dataset: {dataset.id}")
