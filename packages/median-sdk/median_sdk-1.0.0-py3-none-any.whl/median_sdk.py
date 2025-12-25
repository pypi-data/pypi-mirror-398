"""
Median Blockchain Python SDK

This SDK provides Python bindings for the Median blockchain APIs,
including account management and coin operations.
"""

__version__ = "1.0.0"
__author__ = "Median Team"
__email__ = "contact@median.network"
__license__ = "Apache-2.0"

import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib


@dataclass
class Coin:
    """Represents a coin amount with denomination"""
    denom: str
    amount: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "denom": self.denom,
            "amount": self.amount
        }


class MedianSDK:
    """
    Python SDK for interacting with the Median blockchain.

    Features:
    - Create accounts dynamically
    - Mint coins to addresses
    - Burn coins from module account
    - Query blockchain state
    - Create and manage inference tasks
    """

    def __init__(
        self,
        api_url: str = "http://localhost:1317",
        chain_id: str = "median",
        timeout: int = 30
    ):
        """
        Initialize the Median SDK.

        Args:
            api_url: Base URL of the blockchain API (default: http://localhost:1317)
            chain_id: Chain ID (default: median)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_url = api_url.rstrip('/')
        self.chain_id = chain_id
        self.timeout = timeout
        self.session = requests.Session()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the blockchain API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters

        Returns:
            Response JSON data

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.api_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    # ==================== Account Management ====================

    def create_account(
        self,
        creator_address: str,
        new_account_address: str,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new account on the blockchain.

        Args:
            creator_address: Address of the account creator (must be authority)
            new_account_address: Address for the new account
            private_key: Private key for signing (optional, for future tx signing)

        Returns:
            Transaction response

        Note:
            This operation requires authority permissions.
        """
        msg = {
            "body": {
                "messages": [{
                    "@type": "/median.median.MsgCreateAccount",
                    "creator": creator_address,
                    "new_account_address": new_account_address
                }]
            },
            "auth_info": {
                "signer_infos": [],
                "fee": {
                    "amount": [{"denom": "stake", "amount": "200"}],
                    "gas_limit": "200000"
                }
            },
            "signatures": []
        }

        return self._broadcast_tx(msg)

    def get_account(self, address: str) -> Dict[str, Any]:
        """
        Get account information by address.

        Args:
            address: Account address

        Returns:
            Account information
        """
        endpoint = f"/cosmos/auth/v1beta1/accounts/{address}"
        return self._make_request("GET", endpoint)

    def get_account_balance(self, address: str) -> List[Coin]:
        """
        Get account balance.

        Args:
            address: Account address

        Returns:
            List of coins held by the account
        """
        endpoint = f"/cosmos/bank/v1beta1/balances/{address}"
        response = self._make_request("GET", endpoint)

        balances = response.get("balances", [])
        return [Coin(denom=b["denom"], amount=b["amount"]) for b in balances]

    # ==================== Coin Management ====================

    def mint_coins(
        self,
        authority_address: str,
        recipient_address: str,
        amount: List[Coin],
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mint new coins and send to recipient.

        Args:
            authority_address: Address with minting authority
            recipient_address: Address to receive minted coins
            amount: List of coins to mint
            private_key: Private key for signing (optional, for future tx signing)

        Returns:
            Transaction response

        Note:
            This operation requires authority permissions.
        """
        msg = {
            "body": {
                "messages": [{
                    "@type": "/median.median.MsgMintCoins",
                    "authority": authority_address,
                    "recipient": recipient_address,
                    "amount": [coin.to_dict() for coin in amount]
                }]
            },
            "auth_info": {
                "signer_infos": [],
                "fee": {
                    "amount": [{"denom": "stake", "amount": "200"}],
                    "gas_limit": "200000"
                }
            },
            "signatures": []
        }

        return self._broadcast_tx(msg)

    def burn_coins(
        self,
        authority_address: str,
        amount: List[Coin],
        from_address: str = "",
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Burn coins from the module account.

        Args:
            authority_address: Address with burning authority
            amount: List of coins to burn
            from_address: Source address (currently only module account supported)
            private_key: Private key for signing (optional, for future tx signing)

        Returns:
            Transaction response

        Note:
            This operation requires authority permissions.
            Currently only supports burning from module account.
        """
        msg = {
            "body": {
                "messages": [{
                    "@type": "/median.median.MsgBurnCoins",
                    "authority": authority_address,
                    "from": from_address,
                    "amount": [coin.to_dict() for coin in amount]
                }]
            },
            "auth_info": {
                "signer_infos": [],
                "fee": {
                    "amount": [{"denom": "stake", "amount": "200"}],
                    "gas_limit": "200000"
                }
            },
            "signatures": []
        }

        return self._broadcast_tx(msg)

    # ==================== Task Management ====================

    def create_task(
        self,
        creator_address: str,
        task_id: str,
        description: str,
        input_data: str,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new inference task.

        Args:
            creator_address: Address of the task creator
            task_id: Unique identifier for the task
            description: Task description
            input_data: Input data for the task
            private_key: Private key for signing (optional)

        Returns:
            Transaction response
        """
        msg = {
            "body": {
                "messages": [{
                    "@type": "/median.median.MsgCreateTask",
                    "creator": creator_address,
                    "task_id": task_id,
                    "description": description,
                    "input_data": input_data
                }]
            },
            "auth_info": {
                "signer_infos": [],
                "fee": {
                    "amount": [{"denom": "stake", "amount": "200"}],
                    "gas_limit": "200000"
                }
            },
            "signatures": []
        }

        return self._broadcast_tx(msg)

    def commit_result(
        self,
        validator_address: str,
        task_id: str,
        result: int,
        nonce: int,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Commit a result hash for a task.

        Args:
            validator_address: Address of the validator
            task_id: Task identifier
            result: The actual result value
            nonce: Random nonce to prevent hash collision
            private_key: Private key for signing (optional)

        Returns:
            Transaction response
        """
        result_hash = self._compute_hash(result, nonce)

        msg = {
            "body": {
                "messages": [{
                    "@type": "/median.median.MsgCommitResult",
                    "validator": validator_address,
                    "task_id": task_id,
                    "result_hash": result_hash,
                    "nonce": str(nonce)
                }]
            },
            "auth_info": {
                "signer_infos": [],
                "fee": {
                    "amount": [{"denom": "stake", "amount": "200"}],
                    "gas_limit": "200000"
                }
            },
            "signatures": []
        }

        return self._broadcast_tx(msg)

    def reveal_result(
        self,
        validator_address: str,
        task_id: str,
        result: int,
        nonce: int,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reveal the actual result for a task.

        Args:
            validator_address: Address of the validator
            task_id: Task identifier
            result: The actual result value
            nonce: Nonce used in commit phase
            private_key: Private key for signing (optional)

        Returns:
            Transaction response
        """
        msg = {
            "body": {
                "messages": [{
                    "@type": "/median.median.MsgRevealResult",
                    "validator": validator_address,
                    "task_id": task_id,
                    "result": str(result),
                    "nonce": str(nonce)
                }]
            },
            "auth_info": {
                "signer_infos": [],
                "fee": {
                    "amount": [{"denom": "stake", "amount": "200"}],
                    "gas_limit": "200000"
                }
            },
            "signatures": []
        }

        return self._broadcast_tx(msg)

    # ==================== Query Methods ====================

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get task information by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task information
        """
        endpoint = f"/median/median/task/{task_id}"
        return self._make_request("GET", endpoint)

    def get_consensus_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get consensus result for a task.

        Args:
            task_id: Task identifier

        Returns:
            Consensus result information
        """
        endpoint = f"/median/median/consensus/{task_id}"
        return self._make_request("GET", endpoint)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks.

        Returns:
            List of all tasks
        """
        endpoint = "/median/median/tasks"
        response = self._make_request("GET", endpoint)
        return response.get("tasks", [])

    # ==================== Utility Methods ====================

    def _broadcast_tx(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Broadcast a transaction to the blockchain.

        Args:
            tx: Transaction data

        Returns:
            Transaction response

        Note:
            This is a simplified version. In production, you would:
            1. Sign the transaction with a private key
            2. Encode it properly
            3. Use the /cosmos/tx/v1beta1/txs endpoint
        """
        endpoint = "/cosmos/tx/v1beta1/txs"
        return self._make_request("POST", endpoint, data=tx)

    @staticmethod
    def _compute_hash(result: int, nonce: int) -> str:
        """
        Compute hash for commit-reveal scheme.

        Args:
            result: Result value
            nonce: Nonce value

        Returns:
            Hex-encoded hash string
        """
        data = f"{result}{nonce}".encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    def get_node_info(self) -> Dict[str, Any]:
        """
        Get blockchain node information.

        Returns:
            Node information including chain ID, version, etc.
        """
        endpoint = "/cosmos/base/tendermint/v1beta1/node_info"
        return self._make_request("GET", endpoint)

    def get_latest_block(self) -> Dict[str, Any]:
        """
        Get the latest block information.

        Returns:
            Latest block data
        """
        endpoint = "/cosmos/base/tendermint/v1beta1/blocks/latest"
        return self._make_request("GET", endpoint)

    def get_supply(self, denom: Optional[str] = None) -> Dict[str, Any]:
        """
        Get token supply information.

        Args:
            denom: Specific denomination to query (optional)

        Returns:
            Supply information
        """
        if denom:
            endpoint = f"/cosmos/bank/v1beta1/supply/{denom}"
        else:
            endpoint = "/cosmos/bank/v1beta1/supply"
        return self._make_request("GET", endpoint)


# ==================== Helper Functions ====================

def create_sdk(
    api_url: str = "http://localhost:1317",
    chain_id: str = "median"
) -> MedianSDK:
    """
    Convenience function to create a MedianSDK instance.

    Args:
        api_url: Base URL of the blockchain API
        chain_id: Chain ID

    Returns:
        Initialized MedianSDK instance
    """
    return MedianSDK(api_url=api_url, chain_id=chain_id)
