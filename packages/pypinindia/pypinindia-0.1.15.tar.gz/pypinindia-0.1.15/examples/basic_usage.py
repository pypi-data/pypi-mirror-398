#!/usr/bin/env python3
"""
Basic usage examples for pypinindia library.

This script demonstrates the main functionality of the pypinindia library
for Indian pincode lookup and geographical information.
"""

from pypinindia import (
    get_pincode_info,
    get_state,
    get_district,
    get_taluk,
    get_offices,
    search_by_state,
    search_by_district,
    get_states,
    get_districts,
    PincodeData,
)
from pypinindia.exceptions import InvalidPincodeError, DataNotFoundError


def main():
    """Demonstrate basic usage of pypinindia library."""
    
    print("=" * 60)
    print("PyPinIndia - Indian Pincode Lookup Examples")
    print("=" * 60)
    
    # Example 1: Basic pincode lookup
    print("\n1. Basic Pincode Lookup")
    print("-" * 30)
    
    try:
        pincode = "110001"  # New Delhi
        print(f"Looking up pincode: {pincode}")
        
        # Get complete information
        info = get_pincode_info(pincode)
        print(f"Found {len(info)} office(s) for this pincode:")
        
        for i, office in enumerate(info, 1):
            print(f"\n  Office {i}:")
            print(f"    Name: {office['officename']}")
            print(f"    Type: {office['officetype']}")
            print(f"    Delivery Status: {office['Deliverystatus']}")
            print(f"    State: {office['statename']}")
            print(f"    District: {office['districtname']}")
            print(f"    Taluk: {office['taluk']}")
    
    except (InvalidPincodeError, DataNotFoundError) as e:
        print(f"Error: {e}")
    
    # Example 2: Quick lookups
    print("\n\n2. Quick Information Lookup")
    print("-" * 30)
    
    test_pincodes = ["110001", "400001", "600001", "700001"]
    
    for pincode in test_pincodes:
        try:
            state = get_state(pincode)
            district = get_district(pincode)
            print(f"Pincode {pincode}: {district}, {state}")
        except (InvalidPincodeError, DataNotFoundError) as e:
            print(f"Pincode {pincode}: Error - {e}")
    
    # Example 3: Search by state
    print("\n\n3. Search Pincodes by State")
    print("-" * 30)
    
    try:
        state_name = "GOA"
        pincodes = search_by_state(state_name)
        print(f"Found {len(pincodes)} pincodes in {state_name}")
        print(f"First 10 pincodes: {pincodes[:10]}")
    
    except Exception as e:
        print(f"Error searching by state: {e}")
    
    # Example 4: Search by district
    print("\n\n4. Search Pincodes by District")
    print("-" * 30)
    
    try:
        district_name = "Mumbai"
        state_name = "MAHARASHTRA"
        pincodes = search_by_district(district_name, state_name)
        print(f"Found {len(pincodes)} pincodes in {district_name}, {state_name}")
        print(f"Sample pincodes: {pincodes[:5]}")
    
    except Exception as e:
        print(f"Error searching by district: {e}")
    
    # Example 5: List all states
    print("\n\n5. Available States and Territories")
    print("-" * 30)
    
    try:
        states = get_states()
        print(f"Total states/territories: {len(states)}")
        print("States/Territories:")
        for i, state in enumerate(states, 1):
            print(f"  {i:2d}. {state}")
    
    except Exception as e:
        print(f"Error getting states: {e}")
    
    # Example 6: Using PincodeData class
    print("\n\n6. Using PincodeData Class")
    print("-" * 30)
    
    try:
        # Create a PincodeData instance
        pincode_data = PincodeData()
        
        # Get statistics
        stats = pincode_data.get_statistics()
        print("Dataset Statistics:")
        print(f"  Total records: {stats['total_records']:,}")
        print(f"  Unique pincodes: {stats['unique_pincodes']:,}")
        print(f"  Unique states: {stats['unique_states']}")
        print(f"  Unique districts: {stats['unique_districts']:,}")
        print(f"  Unique offices: {stats['unique_offices']:,}")
        
        # Search by office name
        print("\n  Searching for offices containing 'Airport':")
        airport_offices = pincode_data.search_by_office("Airport")
        print(f"  Found {len(airport_offices)} offices with 'Airport' in name")
        
        if airport_offices:
            for office in airport_offices[:3]:  # Show first 3
                print(f"    - {office['officename']} ({office['pincode']}) - {office['statename']}")
    
    except Exception as e:
        print(f"Error using PincodeData class: {e}")
    
    # Example 7: Error handling
    print("\n\n7. Error Handling Examples")
    print("-" * 30)
    
    # Invalid pincode format
    try:
        get_state("12345")  # Too short
    except InvalidPincodeError as e:
        print(f"Invalid pincode format: {e}")
    
    # Non-existent pincode
    try:
        get_state("999999")  # Doesn't exist
    except DataNotFoundError as e:
        print(f"Pincode not found: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
