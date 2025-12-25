"""
Example: Account Management with Median SDK

This script demonstrates how to:
1. Query existing accounts
2. Check account balances
3. Create new accounts dynamically
"""

import sys
import os

# Add parent directory to path to import median_sdk
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from median_sdk import MedianSDK, create_sdk


def main():
    # Initialize the SDK
    print("=" * 60)
    print("Median SDK - Account Management Example")
    print("=" * 60)

    sdk = create_sdk(api_url="http://localhost:1317", chain_id="median")

    # Example addresses (these are from the running blockchain)
    alice_address = "cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l"
    bob_address = "cosmos16x0recwjm2cc03l9t2q7jwpwg90jkp9cv4yspt"
    authority_address = "cosmos10d07y265gmmuvt4z0w9aw880jnsr700j6zn9kn"

    # 1. Get node information
    print("\n1. Getting blockchain node information...")
    try:
        node_info = sdk.get_node_info()
        print(f"   Chain ID: {node_info.get('default_node_info', {}).get('network', 'N/A')}")
        print(f"   Node Version: {node_info.get('application_version', {}).get('version', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")

    # 2. Query Alice's account
    print("\n2. Querying Alice's account...")
    try:
        alice_account = sdk.get_account(alice_address)
        print(f"   Address: {alice_address}")
        print(f"   Account Type: {alice_account.get('account', {}).get('@type', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Check Alice's balance
    print("\n3. Checking Alice's balance...")
    try:
        alice_balance = sdk.get_account_balance(alice_address)
        if alice_balance:
            for coin in alice_balance:
                print(f"   {coin.amount} {coin.denom}")
        else:
            print("   No coins in account")
    except Exception as e:
        print(f"   Error: {e}")

    # 4. Check Bob's balance
    print("\n4. Checking Bob's balance...")
    try:
        bob_balance = sdk.get_account_balance(bob_address)
        if bob_balance:
            for coin in bob_balance:
                print(f"   {coin.amount} {coin.denom}")
        else:
            print("   No coins in account")
    except Exception as e:
        print(f"   Error: {e}")

    # 5. Get total supply
    print("\n5. Getting total token supply...")
    try:
        supply = sdk.get_supply()
        supply_list = supply.get('supply', [])
        if supply_list:
            for coin in supply_list:
                print(f"   {coin.get('amount', 'N/A')} {coin.get('denom', 'N/A')}")
        else:
            print("   No supply data available")
    except Exception as e:
        print(f"   Error: {e}")

    # 6. Create a new account (requires authority)
    print("\n6. Creating a new account...")
    print("   NOTE: This requires authority permissions and proper transaction signing.")
    print("   In this example, we'll show the structure but won't actually execute it.")

    new_account_address = "cosmos1newaccountaddress123456789example"
    print(f"   Would create account: {new_account_address}")
    print(f"   Using authority: {authority_address}")

    # Uncomment the following to actually create an account (requires proper signing)
    # try:
    #     result = sdk.create_account(
    #         creator_address=authority_address,
    #         new_account_address=new_account_address
    #     )
    #     print(f"   Result: {result}")
    # except Exception as e:
    #     print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
