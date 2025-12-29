"""
Batch processing functionality for efficient bulk pincode operations.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Union, Any, Optional
import pandas as pd

from .core import PincodeData
from .exceptions import InvalidPincodeError, DataNotFoundError


class BatchProcessor:
    """Efficient batch processing for multiple pincode operations."""
    
    def __init__(self, pincode_data: Optional[PincodeData] = None):
        self.pincode_data = pincode_data or PincodeData()
    
    def batch_get_states(self, pincodes: List[Union[str, int]]) -> Dict[str, str]:
        """
        Get states for multiple pincodes efficiently.
        
        Args:
            pincodes: List of pincodes to lookup
            
        Returns:
            Dictionary mapping pincode to state name
        """
        if not self.pincode_data.data is not None:
            raise RuntimeError("Data not loaded")
        
        # Convert to strings and validate
        valid_pincodes = []
        for pincode in pincodes:
            try:
                valid_pincodes.append(self.pincode_data._validate_pincode(pincode))
            except InvalidPincodeError:
                continue
        
        # Batch lookup using pandas
        filtered_data = self.pincode_data.data[
            self.pincode_data.data['pincode'].isin(valid_pincodes)
        ]
        
        # Get first state for each pincode (in case of duplicates)
        result = filtered_data.groupby('pincode')['statename'].first().to_dict()
        
        return result
    
    async def async_batch_get_states(self, pincodes: List[Union[str, int]], 
                                   chunk_size: int = 1000) -> Dict[str, str]:
        """
        Async version for very large batches.
        
        Args:
            pincodes: List of pincodes to lookup
            chunk_size: Size of chunks to process concurrently
            
        Returns:
            Dictionary mapping pincode to state name
        """
        chunks = [pincodes[i:i + chunk_size] for i in range(0, len(pincodes), chunk_size)]
        
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, self.batch_get_states, chunk)
                for chunk in chunks
            ]
            
            results = await asyncio.gather(*tasks)
        
        # Merge results
        final_result = {}
        for result in results:
            final_result.update(result)
        
        return final_result


# Convenience functions
def batch_get_states(pincodes: List[Union[str, int]]) -> Dict[str, str]:
    """Convenience function for batch state lookup."""
    processor = BatchProcessor()
    return processor.batch_get_states(pincodes)


async def async_batch_get_states(pincodes: List[Union[str, int]]) -> Dict[str, str]:
    """Async convenience function for batch state lookup."""
    processor = BatchProcessor()
    return await processor.async_batch_get_states(pincodes)