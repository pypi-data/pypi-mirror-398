"""This example demonstrates delayed span sending with nested traced functions.

Child spans complete and are sent immediately when their function returns.
The parent span remains open until all child operations complete, creating
a delay between when the first child span is sent and when the parent span is sent.
"""

import dotenv
import time
from lumenova_beacon import trace

dotenv.load_dotenv()


@trace
def step_1_initialize() -> dict:
    """First step: Initialize data (completes quickly)."""
    print("Step 1: Initializing...")
    time.sleep(0.5)  # Simulate some work
    print("Step 1: Complete (span sent)")
    return {"initialized": True, "timestamp": time.time()}


@trace
def step_2_process_data(data: dict) -> dict:
    """Second step: Process data (takes a bit longer)."""
    print("\nStep 2: Processing data...")
    time.sleep(2.0)  # Simulate processing
    print("Step 2: Complete (span sent)")
    return {**data, "processed": True}


@trace
def step_3_validate(data: dict) -> dict:
    """Third step: Validate results."""
    print("\nStep 3: Validating...")
    time.sleep(3.8)  # Simulate validation
    print("Step 3: Complete (span sent)")
    return {**data, "validated": True}


@trace
def step_4_finalize(data: dict) -> dict:
    """Fourth step: Finalize and save."""
    print("\nStep 4: Finalizing...")
    time.sleep(1.2)  # Simulate final operations
    print("Step 4: Complete (span sent)")
    return {**data, "finalized": True, "final_timestamp": time.time()}


@trace(name="long_running_pipeline")
def execute_pipeline() -> dict:
    """Parent function that orchestrates a multi-step pipeline.

    This function's span will only be sent after ALL child steps complete,
    creating a delay of ~3.5 seconds between the first child span (step_1)
    and this parent span being sent.

    Span sending order:
    1. step_1_initialize span sent at ~0.5s
    2. step_2_process_data span sent at ~1.5s
    3. step_3_validate span sent at ~2.3s
    4. step_4_finalize span sent at ~3.5s
    5. execute_pipeline (parent) span sent at ~3.5s ← This is the delay!
    """
    print("=" * 60)
    print("Starting pipeline execution...")
    print("=" * 60)
    start_time = time.time()

    # Execute steps sequentially - each completes and sends its span
    result = step_1_initialize()
    result = step_2_process_data(result)
    result = step_3_validate(result)
    result = step_4_finalize(result)

    # Additional work in the parent after all children complete
    print("\nParent: Wrapping up...")
    time.sleep(0.5)  # Parent does some final work

    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"Pipeline complete! Total time: {elapsed:.2f}s")
    print("Parent span sent now ← ~4 seconds after first child span")
    print("=" * 60)

    return result


if __name__ == "__main__":
    result = execute_pipeline()
