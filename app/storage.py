"""Storage and cache management for assets."""

import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional


class AssetStorage:
    """Manages local asset storage and caching."""

    def __init__(self, base_dir: str = "./outputs"):
        """Initialize asset storage.

        Args:
            base_dir: Base directory for storing assets
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.products_dir = self.base_dir / "products"
        self.products_dir.mkdir(parents=True, exist_ok=True)
        self.cache: Dict[str, Path] = {}

    def _get_cache_key(self, product: str, region: str, message: str) -> str:
        """Generate cache key for an asset.

        Args:
            product: Product name
            region: Target region
            message: Campaign message

        Returns:
            Cache key hash
        """
        combined = f"{product.lower()}:{region.lower()}:{message.lower()}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    def ensure_product_dir(self, product: str) -> Path:
        """Create product directory if it doesn't exist.

        Args:
            product: Product name

        Returns:
            Path to product directory
        """
        product_dir = self.products_dir / product
        product_dir.mkdir(parents=True, exist_ok=True)
        return product_dir

    def ensure_ratio_dir(self, product: str, aspect_ratio: str) -> Path:
        """Create aspect ratio subdirectory for a product.

        Args:
            product: Product name
            aspect_ratio: Aspect ratio (e.g., '1:1')

        Returns:
            Path to ratio directory
        """
        ratio_dir = self.ensure_product_dir(product) / aspect_ratio.replace(":", "-")
        ratio_dir.mkdir(parents=True, exist_ok=True)
        return ratio_dir

    def get_cache_path(
        self, product: str, region: str, message: str, aspect_ratio: str
    ) -> Optional[Path]:
        """Check if a similar asset exists in cache.

        Args:
            product: Product name
            region: Target region
            message: Campaign message
            aspect_ratio: Aspect ratio

        Returns:
            Path to cached file or None
        """
        ratio_dir = self.ensure_ratio_dir(product, aspect_ratio)
        # Simple heuristic: look for existing files
        png_files = list(ratio_dir.glob("*.png"))
        if png_files:
            # Return most recent file as cache hit (simplified)
            return max(png_files, key=lambda p: p.stat().st_mtime)
        return None

    def save_file(
        self, product: str, aspect_ratio: str, file_name: str, file_path: str
    ) -> Path:
        """Save a file to the appropriate storage location.

        Args:
            product: Product name
            aspect_ratio: Aspect ratio
            file_name: Name of file to save
            file_path: Source file path

        Returns:
            Path where file was saved
        """
        dest_dir = self.ensure_ratio_dir(product, aspect_ratio)
        dest_path = dest_dir / file_name

        # Copy file to destination
        if Path(file_path).exists():
            shutil.copy2(file_path, dest_path)

        return dest_path

    def list_outputs(self, product: Optional[str] = None) -> Dict[str, list]:
        """List all generated outputs.

        Args:
            product: Optional product filter

        Returns:
            Dictionary mapping products to list of aspect ratios and files
        """
        outputs = {}

        if product:
            # Prefer new structure: outputs/products/{product}/{ratio}
            product_dir = self.products_dir / product
            # Backward compatibility: outputs/{product}/{ratio}
            legacy_product_dir = self.base_dir / product
            selected_dir = product_dir if product_dir.exists() else legacy_product_dir
            if selected_dir.exists():
                for ratio_dir in selected_dir.iterdir():
                    if ratio_dir.is_dir():
                        outputs[ratio_dir.name] = [
                            f.name for f in ratio_dir.glob("*.png")
                        ]
        else:
            discovered_product_dirs = {}

            # New structure
            if self.products_dir.exists():
                for product_dir in self.products_dir.iterdir():
                    if product_dir.is_dir():
                        discovered_product_dirs[product_dir.name] = product_dir

            # Legacy structure fallback — exclude hidden dirs and known non-product dirs
            _EXCLUDED_DIRS = {"products", ".tmp", "reports"}
            for product_dir in self.base_dir.iterdir():
                if (
                    product_dir.is_dir()
                    and not product_dir.name.startswith(".")
                    and product_dir.name not in _EXCLUDED_DIRS
                    and product_dir.name not in discovered_product_dirs
                ):
                    discovered_product_dirs[product_dir.name] = product_dir

            for product_name, product_dir in discovered_product_dirs.items():
                outputs[product_name] = {}
                for ratio_dir in product_dir.iterdir():
                    if ratio_dir.is_dir():
                        outputs[product_name][ratio_dir.name] = [
                            f.name for f in ratio_dir.glob("*.png")
                        ]

        return outputs
