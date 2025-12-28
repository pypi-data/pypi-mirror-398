"""
Quick test script to verify the dataset generation works correctly.

This script generates a small sample of 10 examples (2 from each bucket)
to test the generation process without using too many API credits.
"""

import os
import logging
from generate_dataset import PlannerDatasetGenerator, StratificationBucket

# Configure logging to see details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test the generation process with a small sample."""

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        return

    print("=" * 80)
    print("Testing Planner Dataset Generation")
    print("=" * 80)

    # Create generator
    generator = PlannerDatasetGenerator(api_key=api_key, model="gpt-4o-mini")

    # Test with different complexity buckets
    test_buckets = [
        StratificationBucket(
            name="test_simple_2agent",
            min_agents=2, max_agents=2,
            min_steps=2, max_steps=2,
            complexity="simple_chain",
            target_count=2
        ),
        StratificationBucket(
            name="test_medium_branch",
            min_agents=3, max_agents=5,
            min_steps=3, max_steps=6,
            complexity="multi_branch",
            target_count=2
        ),
        StratificationBucket(
            name="test_complex_tree",
            min_agents=6, max_agents=8,
            min_steps=6, max_steps=10,
            complexity="complex_tree",
            target_count=2
        ),
    ]

    examples = []

    for bucket in test_buckets:
        print(f"\n{'='*80}")
        print(f"Testing bucket: {bucket.name}")
        print(f"{'='*80}")

        for i in range(bucket.target_count):
            print(f"\nGenerating example {i+1}/{bucket.target_count}...")

            try:
                example = generator.generate_example(bucket)
                examples.append(example)

                print(f"\n--- Example {i+1} ---")
                print(f"Scenario: {example.scenario}")
                print(f"Valid: {example.is_valid}")
                print(f"Agents used: {example.agents_used}")
                print(f"Num agents: {example.num_agents}, Num steps: {example.num_steps}")

                if not example.is_valid:
                    print(f"ERROR: {example.error_message}")
                    print(f"\nGenerated YAML:")
                    print(example.workflow_yaml[:500])  # First 500 chars
                else:
                    print(f"\nWorkflow YAML (first 300 chars):")
                    print(example.workflow_yaml[:300])
                    print("...")

            except Exception as e:
                print(f"EXCEPTION during generation: {e}")
                import traceback
                traceback.print_exc()

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total examples generated: {len(examples)}")
    valid_count = sum(1 for ex in examples if ex.is_valid)
    print(f"Valid examples: {valid_count}/{len(examples)} ({valid_count/len(examples)*100:.1f}%)")

    if valid_count < len(examples):
        print(f"\nInvalid examples found. Common errors:")
        error_counts = {}
        for ex in examples:
            if not ex.is_valid and ex.error_message:
                error_msg = ex.error_message.split(':')[0]  # Get first part of error
                error_counts[error_msg] = error_counts.get(error_msg, 0) + 1

        for error, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"  - {error}: {count} times")

    print(f"\n{'='*80}")
    print("Test complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
