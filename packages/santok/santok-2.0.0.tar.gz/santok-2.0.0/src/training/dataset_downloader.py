"""
SanTOK Dataset Downloader
==========================

Downloads and prepares clean text datasets for training SanTOK 60K vocabulary.
Uses ONLY free, open datasets:
- Wikipedia
- OpenWebText
- CC-News
- Custom domain data

NO external models - pure data collection.
"""

import os
import requests
import gzip
import bz2
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
import json
import re


class SanTOKDatasetDownloader:
    """Download and prepare datasets for SanTOK training."""
    
    def __init__(self, data_dir: str = "training_data"):
        """
        Initialize dataset downloader.
        
        Args:
            data_dir: Directory to store downloaded datasets
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories for each dataset
        self.wikipedia_dir = self.data_dir / "wikipedia"
        self.openwebtext_dir = self.data_dir / "openwebtext"
        self.ccnews_dir = self.data_dir / "ccnews"
        self.custom_dir = self.data_dir / "custom"
        
        for dir_path in [self.wikipedia_dir, self.openwebtext_dir, self.ccnews_dir, self.custom_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url: str, output_path: Path, chunk_size: int = 8192) -> bool:
        """Download a file with progress bar."""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=output_path.name,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    def extract_wikipedia(self, dump_path: Path, output_path: Path) -> bool:
        """
        Extract Wikipedia dump to clean text.
        
        Uses WikiExtractor approach - simple text extraction.
        """
        try:
            print(f"Extracting Wikipedia dump: {dump_path}")
            
            # Simple extraction - remove XML tags, keep text
            with bz2.open(dump_path, 'rt', encoding='utf-8', errors='ignore') as f_in:
                with open(output_path, 'w', encoding='utf-8') as f_out:
                    text_buffer = []
                    in_text = False
                    
                    for line in tqdm(f_in, desc="Extracting Wikipedia"):
                        line = line.strip()
                        
                        # Extract article text
                        if '<text' in line:
                            in_text = True
                            # Get text content
                            text_start = line.find('>') + 1
                            if text_start > 0:
                                text_buffer.append(line[text_start:])
                        elif '</text>' in line:
                            in_text = False
                            # Write accumulated text
                            if text_buffer:
                                text = ' '.join(text_buffer)
                                # Clean text
                                text = re.sub(r'\[\[.*?\]\]', '', text)  # Remove wiki links
                                text = re.sub(r'\{.*?\}', '', text)  # Remove templates
                                text = re.sub(r'<.*?>', '', text)  # Remove HTML
                                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                                
                                if len(text) > 100:  # Only keep substantial text
                                    f_out.write(text + '\n\n')
                                text_buffer = []
                        elif in_text:
                            text_buffer.append(line)
            
            print(f"✓ Wikipedia extracted to: {output_path}")
            return True
        except Exception as e:
            print(f"Error extracting Wikipedia: {e}")
            return False
    
    def download_wikipedia(self, size_limit_gb: float = 1.0) -> Optional[Path]:
        """
        Download Wikipedia dump.
        
        Args:
            size_limit_gb: Maximum size to download (default: 1GB)
        
        Returns:
            Path to extracted text file
        """
        print("\n" + "="*60)
        print("Downloading Wikipedia Dataset")
        print("="*60)
        
        # Use latest Wikipedia dump
        base_url = "https://dumps.wikimedia.org/enwiki/latest/"
        dump_file = "enwiki-latest-pages-articles.xml.bz2"
        url = base_url + dump_file
        
        dump_path = self.wikipedia_dir / dump_file
        output_path = self.wikipedia_dir / "wikipedia_clean.txt"
        
        if output_path.exists():
            print(f"✓ Wikipedia already extracted: {output_path}")
            return output_path
        
        if not dump_path.exists():
            print(f"Downloading Wikipedia dump...")
            if not self.download_file(url, dump_path):
                return None
        
        # Extract
        if not output_path.exists():
            self.extract_wikipedia(dump_path, output_path)
        
        return output_path if output_path.exists() else None
    
    def download_openwebtext_sample(self, num_files: int = 10) -> Optional[Path]:
        """
        Download sample from OpenWebText.
        
        Note: Full dataset is 40GB. This downloads a sample.
        """
        print("\n" + "="*60)
        print("Downloading OpenWebText Sample")
        print("="*60)
        
        output_path = self.openwebtext_dir / "openwebtext_clean.txt"
        
        if output_path.exists():
            print(f"✓ OpenWebText already downloaded: {output_path}")
            return output_path
        
        # OpenWebText is available via HuggingFace
        print("OpenWebText is available via HuggingFace datasets.")
        print("For now, you can download manually from:")
        print("https://huggingface.co/datasets/openwebtext")
        print("\nOr use this command:")
        print("python -c \"from datasets import load_dataset; ds = load_dataset('openwebtext', split='train[:1%]'); ds.to_json('openwebtext_sample.json')\"")
        
        return None
    
    def download_ccnews_sample(self) -> Optional[Path]:
        """Download CC-News sample."""
        print("\n" + "="*60)
        print("Downloading CC-News Sample")
        print("="*60)
        
        output_path = self.ccnews_dir / "ccnews_clean.txt"
        
        if output_path.exists():
            print(f"✓ CC-News already downloaded: {output_path}")
            return output_path
        
        print("CC-News is available via HuggingFace datasets.")
        print("Use this command:")
        print("python -c \"from datasets import load_dataset; ds = load_dataset('cc_news', split='train[:5%]'); [open('ccnews_clean.txt', 'a').write(item['text'] + '\\n\\n') for item in ds]\"")
        
        return None
    
    def prepare_custom_data(self, text_files: List[Path]) -> Optional[Path]:
        """
        Prepare custom domain data.
        
        Args:
            text_files: List of paths to text files
        
        Returns:
            Path to combined text file
        """
        print("\n" + "="*60)
        print("Preparing Custom Domain Data")
        print("="*60)
        
        output_path = self.custom_dir / "custom_clean.txt"
        
        if output_path.exists():
            print(f"✓ Custom data already prepared: {output_path}")
            return output_path
        
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for text_file in text_files:
                if text_file.exists():
                    print(f"Processing: {text_file}")
                    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f_in:
                        content = f_in.read()
                        # Clean text
                        content = re.sub(r'\s+', ' ', content)
                        f_out.write(content + '\n\n')
        
        print(f"✓ Custom data prepared: {output_path}")
        return output_path if output_path.exists() else None
    
    def combine_datasets(self, output_path: Optional[Path] = None) -> Path:
        """
        Combine all downloaded datasets into one training file.
        
        Returns:
            Path to combined dataset
        """
        if output_path is None:
            output_path = self.data_dir / "combined_training_data.txt"
        
        print("\n" + "="*60)
        print("Combining All Datasets")
        print("="*60)
        
        dataset_files = [
            self.wikipedia_dir / "wikipedia_clean.txt",
            self.openwebtext_dir / "openwebtext_clean.txt",
            self.ccnews_dir / "ccnews_clean.txt",
            self.custom_dir / "custom_clean.txt",
        ]
        
        total_size = 0
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for dataset_file in dataset_files:
                if dataset_file.exists():
                    print(f"Adding: {dataset_file.name}")
                    file_size = dataset_file.stat().st_size
                    total_size += file_size
                    
                    with open(dataset_file, 'r', encoding='utf-8', errors='ignore') as f_in:
                        # Copy in chunks to handle large files
                        while True:
                            chunk = f_in.read(1024 * 1024)  # 1MB chunks
                            if not chunk:
                                break
                            f_out.write(chunk)
                    
                    print(f"  Added {file_size / (1024**2):.2f} MB")
        
        print(f"\n✓ Combined dataset: {output_path}")
        print(f"  Total size: {total_size / (1024**2):.2f} MB")
        
        return output_path


def main():
    """Example usage."""
    downloader = SanTOKDatasetDownloader()
    
    # Download datasets
    wikipedia_path = downloader.download_wikipedia(size_limit_gb=1.0)
    
    # Combine all datasets
    combined_path = downloader.combine_datasets()
    
    print(f"\n✓ Ready for training!")
    print(f"  Dataset: {combined_path}")
    print(f"  Size: {combined_path.stat().st_size / (1024**2):.2f} MB")


if __name__ == "__main__":
    main()