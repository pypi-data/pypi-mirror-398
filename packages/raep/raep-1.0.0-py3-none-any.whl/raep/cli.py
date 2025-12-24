#!/usr/bin/env python3
"""
RAEP Command Line Interface

Usage:
    raep --input data.fasta --output result.json
"""

import argparse
import json
from .model import RAEP


def main():
    """
    Main function, handles command line arguments and performs prediction
    """
    # Create parser
    parser = argparse.ArgumentParser(
        description='RAEP (Rapid Enzyme/Non-Enzyme Prediction) Command Line Tool',
        prog='raep'
    )
    
    # Add arguments
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Input FASTA file path'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output JSON file path'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Initialize predictor
        print("Initializing RAEP predictor...")
        predictor = RAEP()
        
        # Perform prediction
        print(f"Processing FASTA file: {args.input}...")
        results = predictor.predict_fasta(args.input)
        
        # Save results to JSON file
        print(f"Saving results to: {args.output}...")
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Prediction completed!")
        print(f"Successfully predicted {len(results)} sequences")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
