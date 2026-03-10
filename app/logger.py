"""Logging and reporting utilities."""

import html
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class PipelineLogger:
    """Structured logger for the creative automation pipeline."""

    def __init__(
        self,
        name: str = "creative_pipeline",
        log_dir: str = "./logs",
        log_level: str = "INFO",
    ):
        """Initialize logger.

        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level for console output (DEBUG, INFO, WARNING, ERROR)
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        level = getattr(logging, log_level.upper(), logging.INFO)

        # File handler — always captures DEBUG and above
        log_file = self.log_dir / "pipeline.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console handler — respects the requested log level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def exception(self, message: str):
        """Log exception message with traceback."""
        self.logger.exception(message)


class PipelineReport:
    """Report generator for pipeline execution."""

    def __init__(self, output_dir: str = "./outputs"):
        """Initialize report generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.start_time = datetime.now()
        self.results: Dict[str, Any] = {
            "timestamp": self.start_time.isoformat(),
            "status": "in_progress",
            "products": {},
            "compliance_summary": {
                "total_checks": 0,
                "passed": 0,
                "warnings": [],
            },
            "generation_stats": {
                "total_requested": 0,
                "generated": 0,
                "cached": 0,
                "failed": 0,
                "cost_estimate_usd": 0.0,
            },
        }

    def add_product_result(
        self,
        product: str,
        aspect_ratio: str,
        status: str,
        file_path: str = None,
        compliance_notes: List[str] = None,
        cached: bool = False,
    ):
        """Add result for a generated creative.

        Args:
            product: Product name
            aspect_ratio: Aspect ratio (e.g., '1:1')
            status: 'success', 'failed', etc.
            file_path: Path to generated file
            compliance_notes: List of compliance warnings
            cached: Whether file was loaded from cache
        """
        if product not in self.results["products"]:
            self.results["products"][product] = []

        self.results["products"][product].append(
            {
                "aspect_ratio": aspect_ratio,
                "status": status,
                "file_path": str(file_path) if file_path else None,
                "compliance_notes": compliance_notes or [],
                "cached": cached,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.results["generation_stats"]["total_requested"] += 1
        if status == "success":
            if cached:
                self.results["generation_stats"]["cached"] += 1
            else:
                self.results["generation_stats"]["generated"] += 1
        elif status == "failed":
            self.results["generation_stats"]["failed"] += 1

    def add_compliance_result(self, passed: bool, warnings: List[str] = None):
        """Add compliance check result.

        Args:
            passed: Whether compliance check passed
            warnings: List of warning messages
        """
        self.results["compliance_summary"]["total_checks"] += 1
        if passed:
            self.results["compliance_summary"]["passed"] += 1
        if warnings:
            self.results["compliance_summary"]["warnings"].extend(warnings)

    def estimate_cost(self, num_generated: int, provider: str = "dalle"):
        """Estimate generation cost. Only DALL-E 3 pricing (~$0.03 per image) is known.

        Args:
            num_generated: Number of images generated
            provider: Image generation provider (cost estimate only available for 'dalle')
        """
        if provider.lower() == "dalle":
            cost_per_image = 0.03  # ~$0.03 per standard 1024x1024 image for DALL-E 3
        else:
            cost_per_image = 0.0  # pricing unknown for this provider
        self.results["generation_stats"]["cost_estimate_usd"] = num_generated * cost_per_image

    def _generate_html_report(self, report_path: Path) -> Path:
        """Generate HTML version of report from JSON data.

        Args:
            report_path: Path to the JSON report file

        Returns:
            Path to the generated HTML report
        """
        html_path = report_path.with_suffix(".html")
        
        stats = self.results["generation_stats"]
        compliance = self.results["compliance_summary"]
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Campaign Generation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{ 
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 1.1em; }}
        .content {{ padding: 40px; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ 
            color: #333;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h3 {{ color: #666; font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px; }}
        .stat-card .value {{ font-size: 2.5em; font-weight: bold; color: #667eea; }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .status-completed {{ background: #d4edda; color: #155724; }}
        .status-failed {{ background: #f8d7da; color: #721c24; }}
        .products-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .products-table th {{
            background: #f8f9fa;
            color: #333;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #667eea;
        }}
        .products-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        .products-table tr:hover {{ background: #f8f9fa; }}
        .status-success {{ color: #28a745; font-weight: bold; }}
        .status-error {{ color: #dc3545; font-weight: bold; }}
        .warning-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
            font-size: 0.9em;
        }}
        .compliance-pass {{ color: #28a745; font-weight: bold; }}
        .compliance-fail {{ color: #dc3545; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Campaign Generation Report</h1>
            <p>{self.results['timestamp']}</p>
            <span class="status-badge status-{self.results['status'].split('_')[0]}">
                {self.results['status'].upper()}
            </span>
        </div>
        
        <div class="content">
            <!-- Summary Stats -->
            <div class="section">
                <h2>📊 Generation Summary</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Requested</h3>
                        <div class="value">{stats['total_requested']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Generated</h3>
                        <div class="value" style="color: #28a745;">{stats['generated']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Cached</h3>
                        <div class="value" style="color: #007bff;">{stats['cached']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Failed</h3>
                        <div class="value" style="color: #dc3545;">{stats['failed']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Duration</h3>
                        <div class="value">{self.results.get('duration_seconds', 0):.1f}s</div>
                    </div>
                    <div class="stat-card">
                        <h3>Est. Cost</h3>
                        <div class="value">${stats['cost_estimate_usd']:.2f}</div>
                    </div>
                </div>
            </div>

            <!-- Compliance Summary -->
            <div class="section">
                <h2>✅ Compliance Summary</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Checks</h3>
                        <div class="value">{compliance['total_checks']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Passed</h3>
                        <div class="value compliance-pass">{compliance['passed']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Warnings</h3>
                        <div class="value" style="color: #ffc107;">{len(compliance['warnings'])}</div>
                    </div>
                </div>
                {self._render_warnings_html(compliance['warnings'])}
            </div>

            <!-- Products Generated -->
            <div class="section">
                <h2>🎯 Products Generated</h2>
                <table class="products-table">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Aspect Ratio</th>
                            <th>Status</th>
                            <th>File</th>
                            <th>Cached</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._render_products_html()}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Report generated on {self.results['timestamp']}</p>
            <p>Creative Automation Pipeline v1.0</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(html_path, "w") as f:
            f.write(html_content)
        
        return html_path

    def _render_warnings_html(self, warnings: List[str]) -> str:
        """Render compliance warnings as HTML."""
        if not warnings:
            return '<p style="color: #28a745; font-weight: bold;">✓ All checks passed!</p>'

        warning_items = "".join(
            [f'<div class="warning-box">⚠️ {html.escape(w)}</div>' for w in warnings]
        )
        return f'<div>{warning_items}</div>'

    def _render_products_html(self) -> str:
        """Render products table rows as HTML."""
        rows = []
        for product, items in self.results["products"].items():
            for item in items:
                status_class = "status-success" if item["status"] == "success" else "status-error"
                raw_path = item.get("file_path")
                file_display = html.escape(raw_path.split("/")[-1]) if raw_path else "N/A"
                cached_badge = "✓ Yes" if item.get("cached") else "No"
                status_text = html.escape(item.get("status", "unknown").upper())
                ratio_text = html.escape(item.get("aspect_ratio", "N/A"))

                rows.append(f"""
                    <tr>
                        <td>{html.escape(product)}</td>
                        <td>{ratio_text}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{file_display}</td>
                        <td>{cached_badge}</td>
                    </tr>
                """)
        return "".join(rows)

    def finalize(self, status: str = "completed"):
        """Finalize report and save to disk as JSON and HTML.

        Args:
            status: Final status ('completed', 'failed', etc.)
        
        Returns:
            Tuple of (json_path, html_path)
        """
        self.results["status"] = status
        self.results["duration_seconds"] = (
            datetime.now() - self.start_time
        ).total_seconds()

        # Save JSON report
        report_path = (
            self.output_dir / f"report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        # Generate HTML report
        html_path = self._generate_html_report(report_path)

        return report_path, html_path
