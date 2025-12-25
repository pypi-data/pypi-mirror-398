"""
Example: Coin Management with Median SDK

This script demonstrates how to:
1. Check coin balances
2. Mint new coins (requires authority)
3. Burn coins (requires authority)
"""

import sys
import os

# Add parent directory to path to import median_sdk
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from median_sdk import MedianSDK, Coin, create_sdk


def main():
    # Initialize the SDK
    print("=" * 60)
    print("Median SDK - Coin Management Example")
    print("=" * 60)

    sdk = create_sdk(api_url="http://localhost:1317", chain_id="median")

    # Example addresses
    alice_address = "cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l"
    bob_address = "cosmos16x0recwjm2cc03l9t2q7jwpwg90jkp9cv4yspt"
    authority_address = "cosmos10d07y265gmmuvt4z0w9aw880jnsr700j6zn9kn"

    # 1. Check current balances
    print("\n1. Checking current balances...")

    print("\n   Alice's balance:")
    try:
        alice_balance = sdk.get_account_balance(alice_address)
        if alice_balance:
            for coin in alice_balance:
                print(f"     {coin.amount} {coin.denom}")
        else:
            print("     No coins")
    except Exception as e:
        print(f"     Error: {e}")

    print("\n   Bob's balance:")
    try:
        bob_balance = sdk.get_account_balance(bob_address)
        if bob_balance:
            for coin in bob_balance:
                print(f"     {coin.amount} {coin.denom}")
        else:
            print("     No coins")
    except Exception as e:
        print(f"     Error: {e}")

    # 2. Mint coins (example structure - requires proper signing)
    print("\n2. Minting coins...")
    print("   NOTE: This requires authority permissions and proper transaction signing.")
    print("   In this example, we'll show the structure but won't actually execute it.")

    coins_to_mint = [
        Coin(denom="token", amount="1000"),
        Coin(denom="stake", amount="5000")
    ]

    print(f"\n   Would mint to Alice:")
    for coin in coins_to_mint:
        print(f"     {coin.amount} {coin.denom}")

    # Uncomment to actually mint (requires proper signing)
    # try:
    #     result = sdk.mint_coins(
    #         authority_address=authority_address,
    #         recipient_address=alice_address,
    #         amount=coins_to_mint
    #     )
    #     print(f"   Mint result: {result}")
    # except Exception as e:
    #     print(f"   Error: {e}")

    # 3. Burn coins (example structure - requires proper signing)
    print("\n3. Burning coins...")
    print("   NOTE: This requires authority permissions and proper transaction signing.")

    coins_to_burn = [
        Coin(denom="token", amount="500")
    ]

    print(f"\n   Would burn from module account:")
    for coin in coins_to_burn:
        print(f"     {coin.amount} {coin.denom}")

    # Uncomment to actually burn (requires proper signing)
    # try:
    #     result = sdk.burn_coins(
    #         authority_address=authority_address,
    #         amount=coins_to_burn
    #     )
    #     print(f"   Burn result: {result}")
    # except Exception as e:
    #     print(f"   Error: {e}")

    # 4. Get supply information
    print("\n4. Getting token supply information...")
    try:
        supply = sdk.get_supply()
        supply_list = supply.get('supply', [])
        if supply_list:
            print("\n   Total supply:")
            for coin in supply_list:
                print(f"     {coin.get('amount', 'N/A')} {coin.get('denom', 'N/A')}")
        else:
            print("   No supply data")
    except Exception as e:
        print(f"   Error: {e}")

    # 5. Get supply for specific denom
    print("\n5. Getting 'stake' token supply...")
    try:
        stake_supply = sdk.get_supply(denom="stake")
        amount = stake_supply.get('amount', {})
        print(f"   Stake supply: {amount.get('amount', 'N/A')} {amount.get('denom', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    print("\nTo actually execute minting/burning operations:")
    print("1. Implement proper transaction signing with private keys")
    print("2. Use the authority account with proper permissions")
    print("3. Ensure the blockchain is running and accessible")


if __name__ == "__main__":
    main()
