"""
Basic example of using ProteoRift for peptide database search
"""

from proteorift import ProteoRiftSearch

if __name__ == '__main__':
    # Initialize search with default parameters
    searcher = ProteoRiftSearch()

    # Run search with your own data
    results = searcher.search(
        mgf_dir="path/to/your/spectra",      # Directory with MGF files
        peptide_db="path/to/your/database",  # Directory with FASTA files
        output_dir="./results"               # Where to save results
    )

    print(f"Search complete!")
    print(f"Target PSMs: {results['target_pin']}")
    print(f"Decoy PSMs: {results['decoy_pin']}")

    # Analyze results with Percolator (optional, requires crux installation)
    # cd ./results
    # crux percolator target.pin decoy.pin --list-of-files T --overwrite T
