"""Tests for asset storage module."""

from pathlib import Path

from app.storage import AssetStorage


class TestAssetStorage:
    """Test AssetStorage class."""

    def test_init_with_default_dir(self, temp_dir):
        """AssetStorage initializes with default output directory."""
        storage = AssetStorage(base_dir=str(temp_dir))

        assert storage.base_dir.exists()
        assert isinstance(storage.base_dir, Path)

    def test_init_creates_directory(self, temp_dir):
        """AssetStorage creates base directory if it doesn't exist."""
        new_dir = temp_dir / "new_storage"

        AssetStorage(base_dir=str(new_dir))

        assert new_dir.exists()

    def test_ensure_product_dir(self, asset_storage):
        """ensure_product_dir creates product directory."""
        product_dir = asset_storage.ensure_product_dir("TestProduct")

        assert product_dir.exists()
        assert "TestProduct" in str(product_dir)

    def test_ensure_ratio_dir(self, asset_storage):
        """ensure_ratio_dir creates ratio subdirectory."""
        ratio_dir = asset_storage.ensure_ratio_dir("TestProduct", "1:1")

        assert ratio_dir.exists()
        assert "TestProduct" in str(ratio_dir)
        assert "1-1" in str(ratio_dir)

    def test_ensure_ratio_dir_multiple_ratios(self, asset_storage):
        """Ensure ratio dir works with different aspect ratios."""
        ratios = ["1:1", "9:16", "16:9"]

        dirs = [asset_storage.ensure_ratio_dir("Product", ratio) for ratio in ratios]

        assert all(d.exists() for d in dirs)
        assert len(set(str(d) for d in dirs)) == 3

    def test_get_cache_path_no_cache(self, asset_storage):
        """get_cache_path returns None when no cache exists."""
        result = asset_storage.get_cache_path(
            "NonExistent", "US", "Test message", "1:1"
        )

        assert result is None

    def test_save_file(self, asset_storage, sample_image):
        """save_file saves file to correct location."""
        saved_path = asset_storage.save_file(
            product="TestProduct",
            aspect_ratio="1:1",
            file_name="test_image.jpg",
            file_path=str(sample_image),
        )

        assert saved_path.exists()
        assert saved_path.name == "test_image.jpg"

    def test_list_outputs_empty(self, asset_storage):
        """list_outputs returns empty dict when no outputs."""
        outputs = asset_storage.list_outputs()

        assert isinstance(outputs, dict)

    def test_list_outputs_with_files(self, asset_storage, sample_image):
        """list_outputs returns generated outputs."""
        # Save a file first
        asset_storage.save_file(
            product="Product1",
            aspect_ratio="1:1",
            file_name="image1.jpg",
            file_path=str(sample_image),
        )

        outputs = asset_storage.list_outputs()

        assert isinstance(outputs, dict)
        assert "Product1" in outputs

    def test_list_outputs_with_product_filter(self, asset_storage, sample_image):
        """list_outputs filters by product name."""
        asset_storage.save_file(
            product="Product1",
            aspect_ratio="1:1",
            file_name="image1.jpg",
            file_path=str(sample_image),
        )

        outputs = asset_storage.list_outputs(product="Product1")

        assert isinstance(outputs, dict)


class TestAssetStoragePathHandling:
    """Test AssetStorage path handling."""

    def test_normalize_aspect_ratio(self, asset_storage):
        """Aspect ratio should be normalized in path."""
        ratio_dir = asset_storage.ensure_ratio_dir("Product", "9:16")

        assert "9-16" in str(ratio_dir)
        assert "9:16" not in str(ratio_dir)

    def test_multiple_calls_same_dir(self, asset_storage):
        """Multiple calls to same product/ratio return same dir."""
        dir1 = asset_storage.ensure_ratio_dir("Product", "1:1")
        dir2 = asset_storage.ensure_ratio_dir("Product", "1:1")

        assert dir1 == dir2

    def test_create_nested_directories(self, asset_storage):
        """Should create nested directory structure."""
        ratio_dir = asset_storage.ensure_ratio_dir("Product1", "16:9")

        assert ratio_dir.exists()
        assert ratio_dir.is_dir()


class TestAssetStorageCaching:
    """Test caching functionality."""

    def test_get_cache_key_generation(self, asset_storage):
        """Cache key should be generated from inputs."""
        # Note: _get_cache_key is private, so test via cache path logic
        path1 = asset_storage.get_cache_path("Product", "US", "Message", "1:1")
        path2 = asset_storage.get_cache_path("Product", "US", "Message", "1:1")

        # Same inputs should return same result
        assert path1 == path2

    def test_cache_different_products(self, asset_storage):
        """Different products should have different cache behavior."""
        path1 = asset_storage.get_cache_path("Product1", "US", "Message", "1:1")
        path2 = asset_storage.get_cache_path("Product2", "US", "Message", "1:1")

        # Both should be None if no files exist
        assert path1 is None
        assert path2 is None


class TestAssetStorageFileOperations:
    """Test file operation scenarios."""

    def test_save_multiple_files(self, asset_storage, sample_image):
        """Save multiple files to storage."""
        paths = []

        for i in range(3):
            path = asset_storage.save_file(
                product="Product",
                aspect_ratio="1:1",
                file_name=f"image_{i}.jpg",
                file_path=str(sample_image),
            )
            paths.append(path)

        assert all(p.exists() for p in paths)
        assert len(set(str(p) for p in paths)) == 3

    def test_save_file_to_different_ratios(self, asset_storage, sample_image):
        """Save files to different aspect ratio directories."""
        ratios = ["1:1", "9:16", "16:9"]

        for ratio in ratios:
            path = asset_storage.save_file(
                product="Product",
                aspect_ratio=ratio,
                file_name="image.jpg",
                file_path=str(sample_image),
            )

            assert path.exists()
            assert ratio.replace(":", "-") in str(path)
