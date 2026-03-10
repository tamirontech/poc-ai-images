"""Main entry point: CLI and FastAPI web server."""

import argparse
import sys
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
import json

from app.config import settings
from app.parsers import BriefParser, CampaignBrief
from app.generator import (
    ImageGeneratorBase,
    DALLEImageGenerator,
    HuggingFaceImageGenerator,
    ReplicateImageGenerator,
)
from app.firefly_generator import FireflyImageGenerator
from app.google_generator import GoogleImageGenerator
from app.processor import ImageProcessor
from app.storage import AssetStorage
from app.asset_manager import AssetInputManager
from app.compliance import ComplianceChecker
from app.logger import PipelineLogger, PipelineReport
from app.test_manager import TestManager


class CreativeAutomationPipeline:
    """Main pipeline orchestrator."""

    RATIO_TO_GENERATION_SIZE = {
        "1:1": "1024x1024",
        "9:16": "1024x1792",
        "16:9": "1792x1024",
    }

    def __init__(
        self,
        output_dir: str = "./outputs",
        provider: str = "dalle",
        log_level: str = "INFO",
    ):
        """Initialize pipeline.

        Args:
            output_dir: Directory for outputs
            provider: Image generation provider ('dalle', 'huggingface', 'replicate', 'firefly', 'google')
            log_level: Logging level
        """
        self.output_dir = output_dir
        self.provider = provider
        self.logger = PipelineLogger(log_dir="./logs", log_level=log_level)
        init_msg = (
            f"Initializing Creative Automation Pipeline "
            f"(provider={provider})"
        )
        self.logger.info(init_msg)

        self.storage = AssetStorage(output_dir)
        self.asset_manager = AssetInputManager(
            input_dir="./input_assets",
            cache_dir=str(Path(output_dir) / "products")
        )
        self.processor = ImageProcessor()
        self.checker = ComplianceChecker()

        # Initialize image generator based on provider
        self.generator = self._create_generator(provider)

    def _create_generator(self, provider: str) -> ImageGeneratorBase:
        """Create image generator based on provider.

        Args:
            provider: Provider name ('dalle', 'huggingface', 'replicate', 'firefly', 'google')

        Returns:
            ImageGeneratorBase instance
        """
        provider_lower = provider.lower().strip()

        try:
            if provider_lower == "dalle":
                self.logger.info("Using DALL-E 3 image generator")
                model = settings.image_generation_model or "dall-e-3"
                return DALLEImageGenerator(model=model)

            elif provider_lower == "huggingface":
                self.logger.info("Using Hugging Face Inference API generator")
                # Uses env var HUGGINGFACE_API_KEY from config
                model = settings.huggingface_model or "stable-diffusion-3"
                return HuggingFaceImageGenerator(model=model)

            elif provider_lower == "replicate":
                self.logger.info("Using Replicate API generator")
                # Uses env var REPLICATE_API_TOKEN from config
                model = settings.replicate_model or "stable-diffusion-3"
                return ReplicateImageGenerator(model=model)

            elif provider_lower == "firefly":
                self.logger.info("Using Adobe Firefly generator")
                # Uses env var FIREFLY_API_KEY from config
                return FireflyImageGenerator()

            elif provider_lower == "google":
                self.logger.info("Using Google Gemini Nano Banana generator")
                # Uses env var GOOGLE_API_KEY from config
                model = "nano-banana-2"  # Default to fastest model
                return GoogleImageGenerator(model=model)

            else:
                raise ValueError(f"Unknown provider: {provider}")

        except ValueError as e:
            self.logger.error(f"Failed to initialize {provider} generator: {e}")
            raise

    def _get_generation_size(self, aspect_ratio: str) -> str:
        """Resolve image generation size for the requested aspect ratio."""
        return self.RATIO_TO_GENERATION_SIZE.get(aspect_ratio, settings.image_size)

    def _process_and_save(
        self,
        source_path: str,
        product: str,
        aspect_ratio: str,
        brief: "CampaignBrief",
    ):
        """Process a source image and save it to the output directory.

        Returns:
            Tuple of (processed_img, output_path, post_warnings)
        """
        processed_img = self.processor.process_image(
            source_path,
            aspect_ratio=aspect_ratio,
            overlay_text=brief.campaign_message,
            language=brief.language,
            logo_path=brief.logo_path,
            logo_position=brief.logo_position,
            logo_scale=brief.logo_scale,
        )
        file_name = (
            f"{product}_{aspect_ratio.replace(':', '-')}_"
            f"{int(datetime.now().timestamp())}.png"
        )
        output_dir = str(self.storage.ensure_ratio_dir(product, aspect_ratio))
        output_path = self.processor.save_image(processed_img, f"{output_dir}/{file_name}")
        self.logger.info(f"    Saved: {output_path}")

        _, dim_warnings = self.checker.check_image_dimensions(
            processed_img.width, processed_img.height, aspect_ratio
        )
        _, color_warnings = self.checker.check_brand_colors(output_path, brief.brand_colors)
        _, text_warnings = self.checker.check_text_overlay_presence(brief.campaign_message)
        post_warnings = dim_warnings + color_warnings + text_warnings
        if post_warnings:
            self.logger.warning(f"    Compliance warnings: {post_warnings}")

        return processed_img, output_path, post_warnings

    def process_campaign(self, brief: CampaignBrief) -> dict:
        """Process a single campaign brief.

        Args:
            brief: Parsed campaign brief

        Returns:
            Processing results dictionary
        """
        report = PipelineReport(self.output_dir)
        self.logger.info(
            f"Processing campaign: {brief.target_region} | Products: {', '.join(brief.products)}"
        )

        total_to_generate = len(brief.products) * len(brief.aspect_ratios)
        generated_count = 0
        failed_count = 0

        # Run compliance check once per campaign brief
        compliance_passed, compliance_warnings = self.checker.check_message_compliance(
            brief.campaign_message
        )
        report.add_compliance_result(compliance_passed, compliance_warnings)
        if compliance_warnings:
            self.logger.warning(f"Compliance check: {compliance_warnings}")

        tmp_dir = Path(settings.temp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        for product in brief.products:
            self.logger.info(f"  Processing product: {product}")

            for aspect_ratio in brief.aspect_ratios:
                try:
                    self.logger.debug(f"    Aspect ratio: {aspect_ratio}")

                    input_asset = self.asset_manager.find_input_asset(product)
                    if input_asset and input_asset.exists():
                        self.logger.info(f"    Using input asset: {input_asset.name}")
                        _, output_path, post_warnings = self._process_and_save(
                            str(input_asset), product, aspect_ratio, brief
                        )
                    else:
                        generation_size = self._get_generation_size(aspect_ratio)
                        self.logger.info(
                            f"    Generating {product} ({aspect_ratio}) via {self.provider} [size={generation_size}]"
                        )
                        image_url = self.generator.generate_image(
                            product=product,
                            region=brief.target_region,
                            audience=brief.target_audience,
                            message=brief.campaign_message,
                            additional_context=brief.additional_context,
                            size=generation_size,
                            brand_colors=brief.brand_colors,
                            logo_path=brief.logo_path,
                            logo_position=brief.logo_position,
                            logo_scale=brief.logo_scale,
                            reference_image_path=brief.reference_image_path,
                        )
                        temp_file = str(
                            tmp_dir / f"{product}_{int(datetime.now().timestamp())}.png"
                        )
                        self.generator.download_image(image_url, temp_file)
                        _, output_path, post_warnings = self._process_and_save(
                            temp_file, product, aspect_ratio, brief
                        )
                        Path(temp_file).unlink(missing_ok=True)

                    report.add_product_result(
                        product, aspect_ratio, "success", output_path, post_warnings, cached=False
                    )
                    generated_count += 1

                except Exception as e:
                    self.logger.exception(
                        f"    Failed: product={product}, ratio={aspect_ratio}, provider={self.provider}"
                    )
                    report.add_product_result(product, aspect_ratio, "failed", None, [str(e)])
                    failed_count += 1

        # Estimate cost (only DALL-E pricing is known; other providers show $0)
        report.estimate_cost(generated_count, provider=self.provider)
        json_report, html_report = report.finalize("completed" if failed_count == 0 else "completed_with_errors")

        self.logger.info(
            f"Campaign processing complete: {generated_count} generated, {failed_count} failed"
        )
        self.logger.info("Reports saved:")
        self.logger.info(f"  - JSON: {json_report}")
        self.logger.info(f"  - HTML: {html_report}")

        return {
            "status": "success" if failed_count == 0 else "partial",
            "products_processed": len(brief.products),
            "total_creatives": total_to_generate,
            "generated": generated_count,
            "failed": failed_count,
            "report_json": str(json_report),
            "report_html": str(html_report),
            "outputs": self.storage.list_outputs(),
        }


# ============================================================================
# CLI Interface
# ============================================================================


def run_cli(args: argparse.Namespace) -> int:
    """Run campaign processing from parsed CLI arguments."""
    try:
        # Parse brief
        brief = BriefParser.parse_file(args.brief)

        # Initialize pipeline with selected provider
        pipeline = CreativeAutomationPipeline(
            output_dir=args.output, provider=args.provider
        )

        # Process campaign
        result = pipeline.process_campaign(brief)

        # Print summary
        print("\n" + "=" * 80)
        print("CAMPAIGN PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Status: {result['status']}")
        print(f"Products: {result['products_processed']}")
        print(f"Generated: {result['generated']} / {result['total_creatives']}")
        print(f"Failed: {result['failed']}")
        print(f"Output directory: {args.output}")
        print(f"JSON report: {result['report_json']}")
        print(f"HTML report: {result['report_html']}")
        print("=" * 80 + "\n")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Pipeline Error: {e}", file=sys.stderr)
        return 1


# ============================================================================
# FastAPI Web Server
# ============================================================================


def create_app(provider: str = "dalle") -> FastAPI:
    """Create FastAPI application.

    Args:
        provider: Image generation provider ('dalle', 'huggingface', 'replicate', 'firefly', 'google')

    Returns:
        FastAPI app instance
    """
    app = FastAPI(
        title="Creative Automation Pipeline",
        description="AI-powered creative asset generation for social campaigns",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Lazy pipeline — initialized on first use so the server starts even without an API key
    _pipeline: list[CreativeAutomationPipeline] = []
    _pipeline_lock = threading.Lock()

    def get_pipeline() -> CreativeAutomationPipeline:
        if not _pipeline:
            with _pipeline_lock:
                if not _pipeline:  # double-checked locking
                    _pipeline.append(CreativeAutomationPipeline(provider=provider))
        return _pipeline[0]

    # Static files
    static_dir = Path("./static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    async def home():
        """Serve main campaign generation UI."""
        try:
            with open("./templates/index.html", "r") as f:
                return HTMLResponse(f.read())
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="UI template not found")

    @app.get("/dashboard")
    async def dashboard():
        """Serve test dashboard UI."""
        try:
            with open("./templates/dashboard.html", "r") as f:
                return HTMLResponse(f.read())
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dashboard template not found")

    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok", "service": "creative-automation-pipeline"}

    @app.post("/api/generate")
    async def generate(brief_json: str = Form(...)):
        """Generate creatives from campaign brief.

        Args:
            brief_json: JSON string of campaign brief

        Returns:
            JSON with generation results
        """
        try:
            # Parse brief from JSON string
            brief_data = json.loads(brief_json)
            brief = BriefParser.parse_dict(brief_data)

            # Process campaign
            result = await run_in_threadpool(get_pipeline().process_campaign, brief)

            return JSONResponse(content=result)

        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"Invalid brief: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {e}") from e

    @app.get("/api/outputs")
    async def get_outputs(product: Optional[str] = None):
        """List generated outputs.

        Args:
            product: Optional product filter

        Returns:
            Dictionary of outputs organized by product
        """
        try:
            outputs = get_pipeline().storage.list_outputs(product)
            return {"outputs": outputs}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/outputs/{product}/{ratio}/{filename}")
    async def get_output_file(product: str, ratio: str, filename: str):
        """Serve generated creative file."""
        # Belt-and-suspenders: reject any segment containing a path separator or traversal
        for segment in (product, ratio, filename):
            if ".." in segment or "/" in segment or "\\" in segment:
                raise HTTPException(status_code=400, detail="Invalid path segment")

        p = get_pipeline()
        safe_root = Path(p.output_dir).resolve()

        products_root = safe_root / "products"
        file_path = (products_root / product / ratio / filename).resolve()
        if not file_path.is_relative_to(safe_root):
            raise HTTPException(status_code=400, detail="Invalid file path")

        if not file_path.exists():
            # Backward compatibility with legacy output layout.
            legacy_path = (safe_root / product / ratio / filename).resolve()
            if not legacy_path.is_relative_to(safe_root):
                raise HTTPException(status_code=400, detail="Invalid file path")
            file_path = legacy_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(file_path, media_type="image/png")

    # =====================================================================
    # Test Management Endpoints
    # =====================================================================

    test_manager = TestManager()

    @app.get("/api/tests")
    async def get_tests():
        """Get all tests."""
        return {
            "tests": test_manager.get_tests(),
            "suites": test_manager.get_suites(),
        }

    @app.get("/api/tests/{test_id}")
    async def get_test(test_id: str):
        """Get specific test details."""
        test = test_manager.get_test(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return test

    @app.post("/api/tests/{test_id}/run")
    async def run_test(test_id: str):
        """Run a single test."""
        try:
            result = test_manager.run_test(test_id)
            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/suites/{suite_id}/run")
    async def run_suite(suite_id: str):
        """Run all tests in a suite."""
        try:
            result = test_manager.run_suite(suite_id)
            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/requirements")
    async def get_requirements():
        """Get requirements status."""
        return test_manager.get_requirements_status()

    @app.post("/api/tests")
    async def create_test(test_data: dict):
        """Create a new test."""
        try:
            result = test_manager.add_test(test_data)
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.put("/api/tests/{test_id}")
    async def update_test(test_id: str, test_data: dict):
        """Update an existing test."""
        result = test_manager.update_test(test_id, test_data)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return result

    @app.delete("/api/tests/{test_id}")
    async def delete_test(test_id: str):
        """Delete a test."""
        if not test_manager.delete_test(test_id):
            raise HTTPException(status_code=404, detail="Test not found")
        return {"status": "deleted"}

    return app


def run_server(host: str = "0.0.0.0", port: int = 8000, provider: str = "dalle"):
    """Run FastAPI web server.

    Args:
        host: Host to bind to
        port: Port to bind to
        provider: Image generation provider
    """
    print(f"🚀 Starting Creative Automation Pipeline server on http://{host}:{port}")
    print(f"   Provider: {provider}")
    app = create_app(provider=provider)
    uvicorn.run(app, host=host, port=port)


def build_cli_parser() -> argparse.ArgumentParser:
    """Build CLI parser with run/serve subcommands."""
    parser = argparse.ArgumentParser(
        description="Creative Automation Pipeline for Social Asset Generation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    providers = ["dalle", "huggingface", "replicate", "firefly", "google"]

    run_parser = subparsers.add_parser("run", help="Process a campaign brief")
    run_parser.add_argument(
        "--brief",
        type=str,
        required=True,
        help="Path to campaign brief (JSON or YAML)",
    )
    run_parser.add_argument(
        "--output",
        type=str,
        default="./outputs",
        help="Output directory for generated creatives",
    )
    run_parser.add_argument(
        "--provider",
        type=str,
        choices=providers,
        default="dalle",
        help="Image generation provider (default: dalle)",
    )

    serve_parser = subparsers.add_parser("serve", help="Run the FastAPI web server")
    serve_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind web server (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind web server (default: 8000)",
    )
    serve_parser.add_argument(
        "--provider",
        type=str,
        choices=providers,
        default="dalle",
        help="Image generation provider for API requests (default: dalle)",
    )

    return parser


def normalize_legacy_cli_args(argv: list[str]) -> list[str]:
    """Normalize legacy CLI shapes into subcommand-based CLI."""
    if not argv:
        return argv

    # Legacy web mode: python -m app.main --serve [8080]
    if argv[0] == "--serve":
        normalized = ["serve"]
        if len(argv) > 1 and argv[1].isdigit():
            normalized.extend(["--port", argv[1]])
            normalized.extend(argv[2:])
        else:
            normalized.extend(argv[1:])
        return normalized

    # Legacy run mode: python -m app.main --brief ...
    if "--brief" in argv and argv[0] not in {"run", "serve"}:
        return ["run", *argv]

    return argv


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    parser = build_cli_parser()
    raw_args = sys.argv[1:]
    args = parser.parse_args(normalize_legacy_cli_args(raw_args))

    if args.command == "serve":
        run_server(host=args.host, port=args.port, provider=args.provider)
        return

    sys.exit(run_cli(args))


if __name__ == "__main__":
    main()
