"""
Example: Task Management with Median SDK

This script demonstrates how to:
1. Create inference tasks
2. Commit results with commit-reveal scheme
3. Reveal results
4. Query task status and consensus
"""

import sys
import os
import random

# Add parent directory to path to import median_sdk
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from median_sdk import MedianSDK, create_sdk


def main():
    # Initialize the SDK
    print("=" * 60)
    print("Median SDK - Task Management Example")
    print("=" * 60)

    sdk = create_sdk(api_url="http://localhost:1317", chain_id="median")

    # Example addresses
    alice_address = "cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l"
    bob_address = "cosmos16x0recwjm2cc03l9t2q7jwpwg90jkp9cv4yspt"

    # Task details
    task_id = f"task_{random.randint(1000, 9999)}"
    description = "Predict the price of BTC in 24 hours"
    input_data = "BTC/USD current price: $50000"

    # 1. Create a new task
    print("\n1. Creating a new inference task...")
    print(f"   Task ID: {task_id}")
    print(f"   Description: {description}")
    print(f"   Input Data: {input_data}")
    print("\n   NOTE: This requires proper transaction signing.")

    # Uncomment to actually create (requires proper signing)
    # try:
    #     result = sdk.create_task(
    #         creator_address=alice_address,
    #         task_id=task_id,
    #         description=description,
    #         input_data=input_data
    #     )
    #     print(f"   Task created: {result}")
    # except Exception as e:
    #     print(f"   Error: {e}")

    # 2. Commit results (commit-reveal phase)
    print("\n2. Committing results (commit phase)...")
    print("   NOTE: This demonstrates the commit-reveal scheme.")

    # Validator 1 (Alice) commits
    alice_result = 52000  # Alice predicts $52,000
    alice_nonce = random.randint(1000000, 9999999)
    alice_hash = sdk._compute_hash(alice_result, alice_nonce)

    print(f"\n   Alice's commitment:")
    print(f"     Result: {alice_result} (hidden)")
    print(f"     Nonce: {alice_nonce} (hidden)")
    print(f"     Hash: {alice_hash} (public)")

    # Validator 2 (Bob) commits
    bob_result = 51500  # Bob predicts $51,500
    bob_nonce = random.randint(1000000, 9999999)
    bob_hash = sdk._compute_hash(bob_result, bob_nonce)

    print(f"\n   Bob's commitment:")
    print(f"     Result: {bob_result} (hidden)")
    print(f"     Nonce: {bob_nonce} (hidden)")
    print(f"     Hash: {bob_hash} (public)")

    # Uncomment to actually commit (requires proper signing)
    # try:
    #     alice_commit = sdk.commit_result(
    #         validator_address=alice_address,
    #         task_id=task_id,
    #         result=alice_result,
    #         nonce=alice_nonce
    #     )
    #     print(f"   Alice's commit: {alice_commit}")
    #
    #     bob_commit = sdk.commit_result(
    #         validator_address=bob_address,
    #         task_id=task_id,
    #         result=bob_result,
    #         nonce=bob_nonce
    #     )
    #     print(f"   Bob's commit: {bob_commit}")
    # except Exception as e:
    #     print(f"   Error: {e}")

    # 3. Reveal results
    print("\n3. Revealing results (reveal phase)...")
    print("   NOTE: After commit deadline passes, validators reveal their actual results.")

    print(f"\n   Alice reveals:")
    print(f"     Result: {alice_result}")
    print(f"     Nonce: {alice_nonce}")
    print(f"     Verification: Hash matches? {alice_hash == sdk._compute_hash(alice_result, alice_nonce)}")

    print(f"\n   Bob reveals:")
    print(f"     Result: {bob_result}")
    print(f"     Nonce: {bob_nonce}")
    print(f"     Verification: Hash matches? {bob_hash == sdk._compute_hash(bob_result, bob_nonce)}")

    # Uncomment to actually reveal (requires proper signing)
    # try:
    #     alice_reveal = sdk.reveal_result(
    #         validator_address=alice_address,
    #         task_id=task_id,
    #         result=alice_result,
    #         nonce=alice_nonce
    #     )
    #     print(f"   Alice's reveal: {alice_reveal}")
    #
    #     bob_reveal = sdk.reveal_result(
    #         validator_address=bob_address,
    #         task_id=task_id,
    #         result=bob_result,
    #         nonce=bob_nonce
    #     )
    #     print(f"   Bob's reveal: {bob_reveal}")
    # except Exception as e:
    #     print(f"   Error: {e}")

    # 4. Calculate median (what the blockchain would do)
    print("\n4. Consensus calculation (median with ±20% bounds)...")
    all_results = [alice_result, bob_result]
    median = sum(all_results) // len(all_results)
    threshold = median // 5  # 20%
    lower_bound = median - threshold
    upper_bound = median + threshold

    print(f"\n   Median result: {median}")
    print(f"   Valid range: [{lower_bound}, {upper_bound}] (±20%)")

    valid_validators = []
    invalid_validators = []

    for name, result in [("Alice", alice_result), ("Bob", bob_result)]:
        if lower_bound <= result <= upper_bound:
            valid_validators.append(name)
            print(f"   ✓ {name}'s result ({result}) is VALID")
        else:
            invalid_validators.append(name)
            print(f"   ✗ {name}'s result ({result}) is INVALID")

    # 5. Query task information
    print("\n5. Querying task information...")
    print("   NOTE: This would retrieve task status from the blockchain.")

    # Uncomment to actually query (requires task to exist)
    # try:
    #     task_info = sdk.get_task(task_id)
    #     print(f"   Task: {task_info}")
    #
    #     consensus = sdk.get_consensus_result(task_id)
    #     print(f"   Consensus: {consensus}")
    # except Exception as e:
    #     print(f"   Error: {e}")

    # 6. Query all tasks
    print("\n6. Querying all tasks...")
    try:
        all_tasks = sdk.get_all_tasks()
        print(f"   Total tasks: {len(all_tasks)}")
        if all_tasks:
            print("\n   Recent tasks:")
            for task in all_tasks[:5]:  # Show first 5
                print(f"     - {task.get('task_id', 'N/A')}: {task.get('description', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    print("\nKey concepts demonstrated:")
    print("1. Commit-reveal scheme prevents result manipulation")
    print("2. Median calculation with outlier detection (±20% bounds)")
    print("3. Validator voting power can be weighted (using staking)")
    print("4. Invalid results are detected and excluded from consensus")


if __name__ == "__main__":
    main()
