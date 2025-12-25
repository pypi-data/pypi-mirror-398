"""
TBUSD Escrow SDK - Core escrow functionality
"""

from enum import IntEnum
from typing import Optional, List, Dict, Any
from web3 import Web3
from eth_account import Account

# Contract addresses on Base mainnet
ESCROW_FACTORY = "0x1fFA195A86d7E7872EBC2D1d24899addD3f1eB8c"
TBUSD_TOKEN = "0x0d02E2E2a7ADaF2372ca0C69845c8b159A24a595"
BASE_RPC = "https://mainnet.base.org"

# ABIs (minimal for escrow operations)
FACTORY_ABI = [
    {"inputs":[{"name":"_depositor","type":"address"},{"name":"_beneficiary","type":"address"},{"name":"_arbitrator","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_releaseType","type":"uint8"},{"name":"_arbitrationMode","type":"uint8"},{"name":"_autoReleaseTime","type":"uint256"},{"name":"_autoCancelTime","type":"uint256"}],"name":"createEscrow","outputs":[{"name":"","type":"address"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"depositor","type":"address"}],"name":"getEscrowsByDepositor","outputs":[{"name":"","type":"address[]"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"beneficiary","type":"address"}],"name":"getEscrowsByBeneficiary","outputs":[{"name":"","type":"address[]"}],"stateMutability":"view","type":"function"},
]

ESCROW_ABI = [
    {"inputs":[],"name":"depositor","outputs":[{"name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"beneficiary","outputs":[{"name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"amount","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"funded","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"released","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"cancelled","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"release","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"cancel","outputs":[],"stateMutability":"nonpayable","type":"function"},
]

ERC20_ABI = [
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
]


class ReleaseType(IntEnum):
    """Escrow release type"""
    MUTUAL = 0           # Both parties must agree
    BUYER_PROTECTED = 1  # Buyer can release, seller needs arbitration
    SELLER_PROTECTED = 2 # Seller can release, buyer needs arbitration
    TIME_LOCKED = 3      # Auto-release after time


class ArbitrationMode(IntEnum):
    """Arbitration mode"""
    NONE = 0      # No arbitration
    OPTIONAL = 1  # Arbitrator can be invoked
    REQUIRED = 2  # Arbitrator must approve


class TBUSDEscrow:
    """Single escrow instance"""
    
    def __init__(self, address: str, w3: Web3, account: Optional[Account] = None):
        self.address = Web3.to_checksum_address(address)
        self.w3 = w3
        self.account = account
        self.contract = w3.eth.contract(address=self.address, abi=ESCROW_ABI)
    
    @property
    def depositor(self) -> str:
        return self.contract.functions.depositor().call()
    
    @property
    def beneficiary(self) -> str:
        return self.contract.functions.beneficiary().call()
    
    @property
    def amount(self) -> int:
        return self.contract.functions.amount().call()
    
    @property
    def amount_formatted(self) -> float:
        return self.amount / 1e6  # TBUSD has 6 decimals
    
    @property
    def funded(self) -> bool:
        return self.contract.functions.funded().call()
    
    @property
    def released(self) -> bool:
        return self.contract.functions.released().call()
    
    @property
    def cancelled(self) -> bool:
        return self.contract.functions.cancelled().call()
    
    @property
    def status(self) -> str:
        if self.cancelled:
            return "cancelled"
        if self.released:
            return "released"
        if self.funded:
            return "funded"
        return "pending"
    
    def release(self) -> str:
        """Release funds to beneficiary. Returns tx hash."""
        if not self.account:
            raise ValueError("Account required for transactions")
        tx = self.contract.functions.release().build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
        })
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()
    
    def cancel(self) -> str:
        """Cancel escrow and return funds. Returns tx hash."""
        if not self.account:
            raise ValueError("Account required for transactions")
        tx = self.contract.functions.cancel().build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
        })
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "depositor": self.depositor,
            "beneficiary": self.beneficiary,
            "amount": self.amount_formatted,
            "status": self.status,
        }


class EscrowClient:
    """Client for creating and managing TBUSD escrows"""
    
    def __init__(self, private_key: Optional[str] = None, rpc_url: str = BASE_RPC):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key) if private_key else None
        self.factory = self.w3.eth.contract(
            address=Web3.to_checksum_address(ESCROW_FACTORY), 
            abi=FACTORY_ABI
        )
        self.tbusd = self.w3.eth.contract(
            address=Web3.to_checksum_address(TBUSD_TOKEN),
            abi=ERC20_ABI
        )
    
    def create_escrow(
        self,
        beneficiary: str,
        amount: float,
        release_type: ReleaseType = ReleaseType.MUTUAL,
        arbitrator: str = "0x0000000000000000000000000000000000000000",
        arbitration_mode: ArbitrationMode = ArbitrationMode.NONE,
        auto_release_time: int = 0,
        auto_cancel_time: int = 0,
    ) -> TBUSDEscrow:
        """
        Create a new escrow contract.
        
        Args:
            beneficiary: Address to receive funds
            amount: Amount in TBUSD (e.g., 100.0 for $100)
            release_type: How funds can be released
            arbitrator: Optional arbitrator address
            arbitration_mode: Arbitration requirements
            auto_release_time: Unix timestamp for auto-release (0 = disabled)
            auto_cancel_time: Unix timestamp for auto-cancel (0 = disabled)
        
        Returns:
            TBUSDEscrow instance
        """
        if not self.account:
            raise ValueError("Private key required to create escrow")
        
        amount_wei = int(amount * 1e6)  # TBUSD has 6 decimals
        
        tx = self.factory.functions.createEscrow(
            self.account.address,
            Web3.to_checksum_address(beneficiary),
            Web3.to_checksum_address(arbitrator),
            amount_wei,
            release_type,
            arbitration_mode,
            auto_release_time,
            auto_cancel_time,
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 500000,
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Get escrow address from logs
        escrow_address = receipt['logs'][0]['address']
        return TBUSDEscrow(escrow_address, self.w3, self.account)
    
    def fund_escrow(self, escrow_address: str, amount: float) -> str:
        """
        Fund an escrow with TBUSD.
        
        Args:
            escrow_address: Address of the escrow contract
            amount: Amount in TBUSD
        
        Returns:
            Transaction hash
        """
        if not self.account:
            raise ValueError("Private key required to fund escrow")
        
        amount_wei = int(amount * 1e6)
        
        # Transfer TBUSD to escrow
        tx = self.tbusd.functions.transfer(
            Web3.to_checksum_address(escrow_address),
            amount_wei
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()
    
    def get_escrow(self, address: str) -> TBUSDEscrow:
        """Get an escrow instance by address"""
        return TBUSDEscrow(address, self.w3, self.account)
    
    def get_my_escrows_as_depositor(self) -> List[TBUSDEscrow]:
        """Get all escrows where you are the depositor"""
        if not self.account:
            raise ValueError("Private key required")
        addresses = self.factory.functions.getEscrowsByDepositor(self.account.address).call()
        return [TBUSDEscrow(addr, self.w3, self.account) for addr in addresses]
    
    def get_my_escrows_as_beneficiary(self) -> List[TBUSDEscrow]:
        """Get all escrows where you are the beneficiary"""
        if not self.account:
            raise ValueError("Private key required")
        addresses = self.factory.functions.getEscrowsByBeneficiary(self.account.address).call()
        return [TBUSDEscrow(addr, self.w3, self.account) for addr in addresses]
    
    def balance(self, address: Optional[str] = None) -> float:
        """Get TBUSD balance"""
        addr = address or (self.account.address if self.account else None)
        if not addr:
            raise ValueError("Address required")
        balance = self.tbusd.functions.balanceOf(Web3.to_checksum_address(addr)).call()
        return balance / 1e6
