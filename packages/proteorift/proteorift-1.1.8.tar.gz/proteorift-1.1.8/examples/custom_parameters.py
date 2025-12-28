"""
Advanced example with custom parameters
"""

from proteorift import ProteoRiftSearch

if __name__ == '__main__':
    # Initialize with custom search parameters
    searcher = ProteoRiftSearch(
        precursor_tolerance=10,              # Wider tolerance
        precursor_tolerance_type="ppm",      # ppm or Da
        charge=3,                            # Different charge state
        length_filter=True,                  # Enable length filtering
        missed_cleavages_filter=True,        # Enable cleavage filtering
        modification_filter=True,            # Enable modification filtering
        device="cuda",                       # Force GPU (or "cpu")
    )

    # Run search
    results = searcher.search(
        mgf_dir="path/to/spectra",
        peptide_db="path/to/database",
        output_dir="./custom_results",
        prep_dir="./preprocessing",          # Save preprocessed data
        use_cached_prep=False                # Force reprocessing
    )

    print(f"Search complete! Results in {results['output_dir']}")
