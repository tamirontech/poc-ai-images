"""Asset input management — detects user-provided images for products."""

from pathlib import Path
from typing import Dict, Optional, Tuple


class AssetInputManager:
    """Detect user-provided input images for products."""

    def __init__(self, input_dir: str = "./input_assets", cache_dir: str = "./outputs/products"):
        self.input_dir = Path(input_dir)
        self.cache_dir = Path(cache_dir)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def find_input_asset(self, product: str) -> Optional[Path]:
        """Check if user provided an input asset for this product.

        Convention:
            Input assets named: {product}.png, {product}.jpg, {product}_input.png, etc.

        Args:
            product: Product name

        Returns:
            Path to input asset or None
        """
        if not self.input_dir.exists():
            return None

        # Look for files matching product name
        for pattern in [
            f"{product}.png",
            f"{product}.jpg",
            f"{product}.jpeg",
            f"{product}_input.png",
            f"{product}_input.jpg",
            f"{product}_source.png",
        ]:
            potential = self.input_dir / pattern
            if potential.exists():
                return potential

        return None

    def list_input_assets(self) -> Dict[str, Path]:
        """List all available input assets.

        Returns:
            Dictionary mapping product names to asset paths
        """
        assets = {}
        
        if not self.input_dir.exists():
            return assets

        for file in self.input_dir.glob("*"):
            if file.is_file() and file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                # Extract product name (before extension or _input suffix)
                stem = file.stem
                if stem.endswith("_input"):
                    stem = stem[:-6]  # Remove "_input"
                elif stem.endswith("_source"):
                    stem = stem[:-7]  # Remove "_source"
                
                assets[stem] = file

        return assets

    def get_input_asset_info(self) -> str:
        """Get formatted info about input assets in the system.

        Returns:
            Human-readable summary
        """
        assets = self.list_input_assets()
        
        if not assets:
            return f"No input assets found in {self.input_dir}"

        info = f"Input Assets in {self.input_dir}:\n"
        for product, path in assets.items():
            size = path.stat().st_size / 1024  # KB
            info += f"  • {product}: {path.name} ({size:.1f} KB)\n"

        return info

    def validate_input_asset(self, input_asset: Path) -> Tuple[bool, str]:
        """Validate input asset file.

        Args:
            input_asset: Path to asset file

        Returns:
            Tuple of (is_valid, message)
        """
        if not input_asset.exists():
            return False, f"File does not exist: {input_asset}"

        if input_asset.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
            return False, f"Unsupported format: {input_asset.suffix}"

        size_kb = input_asset.stat().st_size / 1024
        if size_kb > 50000:  # 50MB limit
            return False, f"File too large: {size_kb:.1f} KB (max 50 MB)"

        if size_kb < 10:  # 10KB minimum
            return False, f"File too small: {size_kb:.1f} KB (min 10 KB)"

        return True, "Valid input asset"
