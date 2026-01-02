"""
Fragment API Test Application

Fill in your FRAGMENT_HASH and FRAGMENT_COOKIE below to use the library.
"""

import asyncio
from afragment import (
    AsyncFragmentClient,
    FragmentAPIError,
    AuthenticationError,
    PriceChangedError,
    InvalidRecipientError,
    extract_ref_id,
    extract_transaction_text,
    format_transaction_comment,
    nano_to_ton,
)

# ============================================
# YOUR CREDENTIALS
# ============================================
FRAGMENT_HASH = "058607f449e6b366f5"
FRAGMENT_COOKIE = "stel_ssid=356fcbc0bc5f534084_1169402249720117667; stel_dt=480; stel_token=73676e56735445e81a379cafdf21b95573676e4c736761b28c26a9d636da5858ea959; stel_ton_token=9rNB6BN76bmiae7ZeTpLVpf9HEaziOFyDVcokkFRiFqcdnvdOdQvP8VqAdVNySfBWnUPTqVfO1s-9NHNjw22MzmP_Ytv0s1N-7VFJh0ljhh3qQKYyBZvY25gEQweK9kWFD1SpdFBX9z8Ya1ovrCFJS9M29ZVy18nUA80br2SWK9vCIVq34Vc6WBhuAMAg-s8n8oDnhpY"
# ============================================


# Wallet configuration (only address required)
WALLET_ACCOUNT = {
    "address": "UQBb8vnBJTfSNa9mvxRfpcWEqD4lPV6ICVbYbsBbeUjPUySP",
}

async def buy_stars(username: str, quantity: int):
    """Purchase Telegram Stars for a user."""
    print(f"\n{'='*50}")
    print(f"Purchasing {quantity} Stars for @{username}")
    print('='*50)

    async with AsyncFragmentClient(FRAGMENT_HASH, FRAGMENT_COOKIE) as client:
        # Step 1: Search recipient
        print("\n[1/3] Searching for recipient...")
        search = await client.search_stars_recipient(username, quantity)
        recipient = search["found"]["recipient"]
        name = search["found"]["name"]
        print(f"  Found: {name}")

        # Step 2: Initialize purchase (with retry for price changes)
        print("\n[2/3] Initializing purchase...")
        for attempt in range(3):
            try:
                init = await client.init_buy_stars_request(recipient, quantity)
                break
            except PriceChangedError:
                print(f"  Price changed, retrying... ({attempt + 1}/3)")
                await asyncio.sleep(1)
        else:
            raise Exception("Failed after 3 attempts due to price changes")

        req_id = init["req_id"]
        amount = init["amount"]
        print(f"  Request ID: {req_id}")
        print(f"  Price: {amount} TON")

        # Step 3: Get transaction details
        print("\n[3/3] Getting transaction details...")
        tx = await client.get_buy_stars_link(req_id, WALLET_ACCOUNT)

        message = tx["transaction"]["messages"][0]
        address = message["address"]
        amount_nano = int(message["amount"])
        payload = message["payload"]

        # Extract transaction text directly from payload
        comment = extract_transaction_text(payload, "stars", quantity=quantity)
        if not comment:
            # Fallback: use formatted comment with req_id
            ref_id = extract_ref_id(payload) or req_id
            comment = format_transaction_comment("stars", quantity=quantity, ref_id=ref_id)
        
        ref_id = extract_ref_id(payload) or req_id

        print(f"\n  Transaction Details:")
        print(f"  - Send to: {address}")
        print(f"  - Amount: {nano_to_ton(amount_nano)} TON ({amount_nano} nanoTON)")
        print(f"  - Comment: {comment.replace(chr(10), ' ')}")
        print(f"  - Ref ID: {ref_id}")

        return tx


async def gift_premium(username: str, months: int):
    """Gift Telegram Premium to a user."""
    print(f"\n{'='*50}")
    print(f"Gifting {months} months Premium to @{username}")
    print('='*50)

    async with AsyncFragmentClient(FRAGMENT_HASH, FRAGMENT_COOKIE) as client:
        # Step 1: Search recipient
        print("\n[1/3] Searching for recipient...")
        search = await client.search_premium_gift_recipient(username)
        recipient = search["found"]["recipient"]
        name = search["found"]["name"]
        print(f"  Found: {name}")

        # Step 2: Initialize purchase
        print("\n[2/3] Initializing purchase...")
        for attempt in range(3):
            try:
                init = await client.init_gift_premium_request(recipient, months)
                break
            except PriceChangedError:
                print(f"  Price changed, retrying... ({attempt + 1}/3)")
                await asyncio.sleep(1)
        else:
            raise Exception("Failed after 3 attempts due to price changes")

        req_id = init["req_id"]
        amount = init["amount"]
        print(f"  Request ID: {req_id}")
        print(f"  Price: {amount} TON")

        # Step 3: Get transaction details
        print("\n[3/3] Getting transaction details...")
        tx = await client.get_gift_premium_link(req_id, WALLET_ACCOUNT)

        message = tx["transaction"]["messages"][0]
        address = message["address"]
        amount_nano = int(message["amount"])
        payload = message["payload"]

        # Extract transaction text directly from payload
        comment = extract_transaction_text(payload, "premium")
        if not comment:
            # Fallback: use formatted comment with req_id
            ref_id = extract_ref_id(payload) or req_id
            comment = format_transaction_comment("premium", months=months, ref_id=ref_id)
        
        ref_id = extract_ref_id(payload) or req_id

        print(f"\n  Transaction Details:")
        print(f"  - Send to: {address}")
        print(f"  - Amount: {nano_to_ton(amount_nano)} TON ({amount_nano} nanoTON)")
        print(f"  - Comment: {comment.replace(chr(10), ' ')}")
        print(f"  - Ref ID: {ref_id}")

        return tx


async def topup_ton(username: str, amount: int):
    """Topup TON balance for a user."""
    print(f"\n{'='*50}")
    print(f"Topping up {amount} TON for @{username}")
    print('='*50)

    async with AsyncFragmentClient(FRAGMENT_HASH, FRAGMENT_COOKIE) as client:
        # Step 1: Search recipient
        print("\n[1/3] Searching for recipient...")
        search = await client.search_ads_topup_recipient(username)
        recipient = search["found"]["recipient"]
        name = search["found"]["name"]
        print(f"  Found: {name}")

        # Step 2: Initialize topup
        print("\n[2/3] Initializing topup...")
        init = await client.init_ads_topup_request(recipient, amount)
        req_id = init["req_id"]
        print(f"  Request ID: {req_id}")

        # Step 3: Get transaction details
        print("\n[3/3] Getting transaction details...")
        tx = await client.get_ads_topup_link(req_id, WALLET_ACCOUNT)

        message = tx["transaction"]["messages"][0]
        address = message["address"]
        amount_nano = int(message["amount"])
        payload = message["payload"]

        # Extract transaction text directly from payload
        comment = extract_transaction_text(payload, "topup")
        if not comment:
            # Fallback: use formatted comment with req_id
            ref_id = extract_ref_id(payload) or req_id
            comment = format_transaction_comment("topup", ref_id=ref_id)
        
        ref_id = extract_ref_id(payload) or req_id

        print(f"\n  Transaction Details:")
        print(f"  - Send to: {address}")
        print(f"  - Amount: {nano_to_ton(amount_nano)} TON ({amount_nano} nanoTON)")
        print(f"  - Comment: {comment.replace(chr(10), ' ')}")
        print(f"  - Ref ID: {ref_id}")

        return tx


async def main():
    """Main entry point with interactive menu."""
    
    # Check credentials
    if not FRAGMENT_HASH or not FRAGMENT_COOKIE:
        print("\n" + "="*50)
        print("ERROR: Please fill in your credentials!")
        print("="*50)
        print("\nOpen app.py and set:")
        print("  FRAGMENT_HASH = 'your_hash'")
        print("  FRAGMENT_COOKIE = 'your_cookie'")
        return

    print("\n" + "="*50)
    print("   Fragment API Test Application")
    print("="*50)
    print("\nSelect an action:")
    print("  1. Buy Telegram Stars")
    print("  2. Gift Telegram Premium")
    print("  3. TON Balance Topup")
    print("  0. Exit")

    choice = input("\nYour choice: ").strip()

    try:
        if choice == "1":
            username = input("Username (without @): ").strip()
            quantity = int(input("Quantity of Stars: ").strip())
            await buy_stars(username, quantity)

        elif choice == "2":
            username = input("Username (without @): ").strip()
            print("Duration options: 3, 6, or 12 months")
            months = int(input("Months: ").strip())
            await gift_premium(username, months)

        elif choice == "3":
            username = input("Username (without @): ").strip()
            amount_str = input("Amount in TON (whole number, min 1): ").strip()
            # Validate whole number
            if "." in amount_str or "," in amount_str:
                raise ValueError("Amount must be a whole number (no decimals)")
            amount = int(amount_str)
            await topup_ton(username, amount)

        elif choice == "0":
            print("Goodbye!")
            return

        else:
            print("Invalid choice!")

    except InvalidRecipientError as e:
        print(f"\nError: User not found or not eligible")
        print(f"  Details: {e}")
    except AuthenticationError as e:
        print(f"\nError: Authentication failed - {e}")
        print("Please check your FRAGMENT_HASH and FRAGMENT_COOKIE")
    except FragmentAPIError as e:
        print(f"\nAPI Error: {e}")
    except ValueError as e:
        print(f"\nInput Error: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

    print("\n" + "="*50)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())



