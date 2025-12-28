"""
Example using sample data from HuggingFace Datasets
"""

from proteorift import ProteoRiftSearch

if __name__ == '__main__':
    # Initialize searcher
    searcher = ProteoRiftSearch()

    # Quick demo with preprocessed sample data (fastest)
    print("Running search with preprocessed sample data...")
    results = searcher.search_with_sample_data(
        output_dir="./sample_output",
        use_preprocessed=True  # Use cached preprocessed data
    )

    print(f"\nResults saved to: {results['output_dir']}")
    print(f"Target PSMs: {results['target_pin']}")
    print(f"Decoy PSMs: {results['decoy_pin']}")

    # Or reprocess from raw MGF files (slower, but shows full pipeline)
    # results = searcher.search_with_sample_data(
    #     output_dir="./sample_output",
    #     use_preprocessed=False
    # )
