"""Simplified search API for ProteoRift"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from typing import Optional, Dict, Any

from .models import get_model_paths, load_sample_data
from .src.atlesconfig import config
from . import run_search
from . import read_spectra


class ProteoRiftSearch:
    """Main interface for ProteoRift peptide database search"""
    
    def __init__(
        self,
        precursor_tolerance: float = 7,
        precursor_tolerance_type: str = "ppm",
        charge: int = 4,
        length_filter: bool = True,
        missed_cleavages_filter: bool = True,
        modification_filter: bool = True,
        device: str = "auto",
        cache_dir: Optional[str] = None,
    ):
        """Initialize ProteoRift search
        
        Args:
            precursor_tolerance: Precursor tolerance for search (default: 7)
            precursor_tolerance_type: Either 'ppm' or 'Da' (default: 'ppm')
            charge: Charge state to use (default: 4)
            length_filter: Enable length filtering (default: True)
            missed_cleavages_filter: Enable missed cleavages filtering (default: True)
            modification_filter: Enable modification filtering (default: True)
            device: Device to use ('cuda', 'cpu', or 'auto')
            cache_dir: Custom cache directory for models
        """
        self.config_params = {
            'precursor_tolerance': precursor_tolerance,
            'precursor_tolerance_type': precursor_tolerance_type,
            'charge': charge,
            'length_filter': length_filter,
            'missed_cleavages_filter': missed_cleavages_filter,
            'modification_filter': modification_filter,
        }
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.cache_dir = cache_dir
        self.model_paths = None
        
    def _load_models(self):
        """Load models from HuggingFace Hub"""
        if self.model_paths is None:
            print("Loading models from HuggingFace Hub...")
            self.model_paths = get_model_paths(self.cache_dir)
        return self.model_paths
    
    def _create_config_file(self, mgf_dir, prep_path, pep_dir, out_dir):
        """Create temporary config file with search parameters"""
        proteorift_model, specollate_model = self._load_models()
        
        print(f"DEBUG _create_config_file: mgf_dir='{mgf_dir}', prep_path='{prep_path}', pep_dir='{pep_dir}', out_dir='{out_dir}'")
        
        config_content = f"""[preprocess]

[input]
spec_size: 50000
charge: 5
use_mods: False
master_port: 12355

[search]
mgf_dir: {mgf_dir}
prep_path: {prep_path}
pep_dir: {pep_dir}
out_pin_dir: {out_dir}

model_name: {proteorift_model}
specollate_model_path: {specollate_model}

spec_batch_size: 16384
pep_batch_size: 16384
search_spec_batch_size: 256

precursor_tolerance: {self.config_params['precursor_tolerance']}
precursor_tolerance_type: {self.config_params['precursor_tolerance_type']}
keep_psms: 5
num_mods: 1
charge: {self.config_params['charge']}

[filter]
length_filter: {self.config_params['length_filter']}
len_tol_neg: -1
len_tol_pos: 1
missed_cleavages_filter: {self.config_params['missed_cleavages_filter']}
modification_filter: {self.config_params['modification_filter']}

[ooc]
chunk_size: 10000000

[ml]
batch_size: 1024
test_size: 0.2
max_spec_len: 200
min_pep_len: 7
max_pep_len: 30
pep_seq_len: 36
max_clvs: 2
embedding_dim: 1024
encoder_layers: 4
num_heads: 16
train_count: 0
ce_weight_clv: 1
ce_weight_mod: 1
mse_weight: 3
dropout: 0.3
lr: 0.0001
weight_decay: 0.0001
epochs: 5
margin: 0.2
read_split_listing: False

[default]
msp_file: /data/human_consensus_final_true_lib.msp
mgf_files: /data/
spec_size: 50000
charge: 5
use_mods: False
batch_size: 1024
"""
        
        # Write to temporary file
        config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        config_file.write(config_content)
        config_file.close()
        
        print(f"DEBUG: Config file written to {config_file.name}")
        print("DEBUG: Config file contents:")
        with open(config_file.name, 'r') as f:
            print(f.read())
        
        return config_file.name
    
    def _preprocess_spectra(self, mgf_dir, prep_dir):
        """Preprocess MGF files"""
        print("Preprocessing spectra...")
        
        # Reset config cache to ensure fresh config is loaded
        config.config_dict = None
        
        # Set config for preprocessing
        config_file = self._create_config_file(mgf_dir, prep_dir, "", "")
        config.param_path = config_file
        
        # Run preprocessing directly (bypassing argparse)
        read_spectra.preprocess_mgfs_unlabelled(mgf_dir, prep_dir)
        
        # Cleanup
        os.unlink(config_file)
        print("Preprocessing complete!")
        
    def search(
        self,
        mgf_dir: str,
        peptide_db: str,
        output_dir: str = "./proteorift_output",
        prep_dir: Optional[str] = None,
        use_cached_prep: bool = False
    ) -> Dict[str, Any]:
        """Run peptide database search
        
        Args:
            mgf_dir: Directory containing MGF spectra files
            peptide_db: Path to peptide database directory (FASTA files)
            output_dir: Output directory for results (default: ./proteorift_output)
            prep_dir: Directory for preprocessed files (default: temp directory)
            use_cached_prep: Use existing preprocessed files if available
            
        Returns:
            dict: Search results with paths to output files
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Setup preprocessing directory
        if prep_dir is None:
            prep_dir = tempfile.mkdtemp(prefix="proteorift_prep_")
            cleanup_prep = True
        else:
            os.makedirs(prep_dir, exist_ok=True)
            cleanup_prep = False
        
        # Check if preprocessing needed
        prep_file = Path(prep_dir) / "specs.pkl"
        if not use_cached_prep or not prep_file.exists():
            self._preprocess_spectra(mgf_dir, prep_dir)
        else:
            print(f"Using cached preprocessed data: {prep_file}")
        
        # Create config file
        print(f"DEBUG: Creating config with peptide_db = {peptide_db}")
        # Reset config cache to ensure new config is loaded
        config.config_dict = None
        config_file = self._create_config_file(mgf_dir, prep_dir, peptide_db, output_dir)
        config.param_path = config_file
        
        # Run search
        print("Running database search...")
        
        # Run target and decoy searches sequentially without distributed setup
        print("Running target search...")
        run_search.run_specollate_par(rank=0, world_size=1, gConfig=config_file, forced_rank=0, use_distributed=False)
        
        print("Running decoy search...")
        run_search.run_specollate_par(rank=1, world_size=1, gConfig=config_file, forced_rank=1, use_distributed=False)
        
        # Cleanup
        os.unlink(config_file)
        if cleanup_prep:
            shutil.rmtree(prep_dir)
        
        print(f"\nSearch complete! Results saved to: {output_dir}")
        
        return {
            'output_dir': output_dir,
            'target_pin': os.path.join(output_dir, 'target.pin'),
            'decoy_pin': os.path.join(output_dir, 'decoy.pin'),
        }
    
    def search_with_sample_data(
        self,
        output_dir: str = "./proteorift_output",
        use_preprocessed: bool = True
    ) -> Dict[str, Any]:
        """Run search using sample data from HuggingFace Datasets
        
        Args:
            output_dir: Output directory for results (default: ./proteorift_output)
            use_preprocessed: Use preprocessed sample data (faster) or reprocess from raw
            
        Returns:
            dict: Search results with paths to output files
        """
        print("Loading sample data from HuggingFace...")
        sample_data = load_sample_data(self.cache_dir, use_preprocessed)
        
        # Check if we got preprocessed data or raw data
        if 'prep_path' in sample_data:
            # Use preprocessed data directly
            print(f"DEBUG: peptide_db = {sample_data['peptide_db']}")
            print(f"DEBUG: prep_path = {sample_data['prep_path']}")
            
            # Reset config cache to ensure new config is loaded
            config.config_dict = None
            
            config_file = self._create_config_file(
                "",  # Not needed for preprocessed
                sample_data['prep_path'],
                sample_data['peptide_db'],
                output_dir
            )
            config.param_path = config_file
            
            os.makedirs(output_dir, exist_ok=True)
            
            print("Running database search with preprocessed sample data...")
            
            num_gpus = torch.cuda.device_count() if torch.cuda.is_available() else 1
            
            # Run target and decoy searches sequentially without distributed setup
            print("Running target search...")
            run_search.run_specollate_par(rank=0, world_size=1, gConfig=config_file, forced_rank=0, use_distributed=False)
            
            print("Running decoy search...")
            run_search.run_specollate_par(rank=1, world_size=1, gConfig=config_file, forced_rank=1, use_distributed=False)
            
            os.unlink(config_file)
        else:
            # Process from raw MGF files
            return self.search(
                mgf_dir=sample_data['mgf_dir'],
                peptide_db=sample_data['peptide_db'],
                output_dir=output_dir
            )
        
        print(f"\nSearch complete! Results saved to: {output_dir}")
        
        return {
            'output_dir': output_dir,
            'target_pin': os.path.join(output_dir, 'target.pin'),
            'decoy_pin': os.path.join(output_dir, 'decoy.pin'),
        }
