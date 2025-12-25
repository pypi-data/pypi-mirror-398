from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any

class ContractType(Enum):
    """
    Enumeration representing different types of financial contracts.
    
    Attributes:
        STOCK (str): Stock contract type.
        FUT (str): Futures contract type.
        FOP (str): Futures option contract type.
        OPT (str): Option contract type.
        SWAP (str): Swap contract type.
        FX (str): Foreign exchange contract type.
        ETF (str): Exchange-traded fund contract type.
    """
    STOCK = 'STOCK'
    FUT = 'FUT'
    FOP = 'FOP'
    OPT = 'OPT'
    SWAP = 'SWAP'
    FX = 'FX'
    ETF = 'ETF'

MANDATORY_FIELDS = {
    ContractType.STOCK:     ['symbol', 'exchange', 'currency'],
    ContractType.FUT:       ['symbol', 'exchange', 'expiry', 'currency', 'contract_size'],
    ContractType.FOP:       ['symbol', 'exchange', 'expiry', 'currency', 'contract_size', 'option_type', 'strike'],
    ContractType.OPT:       ['symbol', 'exchange', 'expiry', 'currency', 'option_type', 'strike'],
    ContractType.SWAP:      ['symbol', 'exchange', 'currency', 'underlying'],
    ContractType.FX:        ['symbol', 'base_currency', 'quote_currency'],
    ContractType.ETF:       ['symbol', 'exchange', 'currency', 'underlying'],
}

@dataclass
class Symbol:
    """
    Represents a financial symbol with a specific contract type and associated fields.
    
    Attributes:
        contract_type (ContractType): The type of contract this symbol represents.
        fields (Dict[str, Any]): A dictionary containing field names and their corresponding values.
    
    Methods:
        __post_init__(): Validates that all mandatory fields for the given contract type are present and not None.
        __getitem__(item): Allows dictionary-like access to the fields.
        __setitem__(key, value): Allows setting field values using dictionary-like syntax.
    
    Raises:
        ValueError: If any mandatory fields for the specified contract type are missing or None.
    """
    contract_type: ContractType
    fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Validates that all mandatory fields for the given contract type are present and not None.
        
        Raises:
            ValueError: If any mandatory field for the contract type is missing or has a value of None.
        """
        required = MANDATORY_FIELDS[self.contract_type]
        missing = [f for f in required if f not in self.fields or self.fields[f] is None]
        if missing:
            raise ValueError(f"Missing mandatory fields for {self.contract_type.value}: {missing}")

    def __getitem__(self, item):
        """
        Retrieve the value associated with the given key from the fields dictionary.
        
        Parameters:
            item: The key to look up in the fields dictionary.
        
        Returns:
            The value corresponding to the specified key.
        
        Raises:
            KeyError: If the key is not found in the fields dictionary.
        """
        return self.fields[item]

    def __setitem__(self, key, value):
        """
        Sets the value associated with the given key in the fields dictionary.
        
        Parameters:
        key: The key for which the value needs to be set.
        value: The value to be assigned to the specified key.
        """
        self.fields[key] = value
