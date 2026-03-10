"""Test management and execution system."""

import json
import shlex
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RequirementLevel(str, Enum):
    """Requirement importance level."""
    CORE = "core"
    OPTIONAL = "optional"


@dataclass
class TestCase:
    """Individual test case definition."""
    id: str
    name: str
    description: str
    requirement: str
    requirement_level: RequirementLevel
    command: str
    expected_output: Optional[str] = None
    verification_script: Optional[str] = None
    timeout: int = 300
    tags: List[str] = None
    status: TestStatus = TestStatus.PENDING
    result: Optional[str] = None
    duration: float = 0.0
    last_run: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self):
        """Convert to dictionary."""
        data = asdict(self)
        data['requirement_level'] = self.requirement_level.value
        data['status'] = self.status.value
        return data


@dataclass
class TestSuite:
    """Collection of tests grouped by category."""
    id: str
    name: str
    description: str
    test_ids: List[str]
    estimated_duration: int
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TestManager:
    """Manages test execution and tracking."""

    def __init__(self, config_file: str = "tests/test_config.json"):
        """Initialize test manager.
        
        Args:
            config_file: Path to test configuration file
        """
        self.config_file = Path(config_file)
        self.tests: Dict[str, TestCase] = {}
        self.suites: Dict[str, TestSuite] = {}
        self.load_config()

    def load_config(self):
        """Load test configuration from file."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                config = json.load(f)
                
                # Load test cases
                for test_data in config.get('tests', []):
                    test = TestCase(
                        id=test_data['id'],
                        name=test_data['name'],
                        description=test_data['description'],
                        requirement=test_data['requirement'],
                        requirement_level=RequirementLevel(test_data['requirement_level']),
                        command=test_data['command'],
                        expected_output=test_data.get('expected_output'),
                        verification_script=test_data.get('verification_script'),
                        timeout=test_data.get('timeout', 300),
                        tags=test_data.get('tags', []),
                    )
                    self.tests[test.id] = test
                
                # Load test suites
                for suite_data in config.get('suites', []):
                    suite = TestSuite(
                        id=suite_data['id'],
                        name=suite_data['name'],
                        description=suite_data['description'],
                        test_ids=suite_data['test_ids'],
                        estimated_duration=suite_data['estimated_duration'],
                        tags=suite_data.get('tags', []),
                    )
                    self.suites[suite.id] = suite
        else:
            self._create_default_config()

    def _create_default_config(self):
        """Create default test configuration."""
        # Define default tests
        self.tests = {
            'brief-json': TestCase(
                id='brief-json',
                name='JSON Brief Parsing',
                description='Verify JSON campaign brief parsing',
                requirement='Campaign Brief Acceptance',
                requirement_level=RequirementLevel.CORE,
                command='python -m pytest tests/unit/test_parsers.py -v -k json',
                expected_output='passed',
                tags=['parsing', 'core', 'input'],
            ),
            'brief-yaml': TestCase(
                id='brief-yaml',
                name='YAML Brief Parsing',
                description='Verify YAML campaign brief parsing',
                requirement='Campaign Brief Acceptance',
                requirement_level=RequirementLevel.CORE,
                command='python -m pytest tests/unit/test_parsers.py -v -k yaml',
                expected_output='passed',
                tags=['parsing', 'core', 'input'],
            ),
            'aspect-ratios': TestCase(
                id='aspect-ratios',
                name='Aspect Ratio Generation',
                description='Verify 1:1, 9:16, and 16:9 aspect ratios',
                requirement='Image Generation (Multiple Aspect Ratios)',
                requirement_level=RequirementLevel.CORE,
                command='python -m pytest tests/unit/test_processor.py -v -k aspect',
                expected_output='passed',
                tags=['generation', 'core', 'images'],
            ),
            'asset-reuse': TestCase(
                id='asset-reuse',
                name='Asset Reuse',
                description='Verify existing assets are reused',
                requirement='Asset Input & Reuse',
                requirement_level=RequirementLevel.CORE,
                command='python -m pytest tests/unit/test_asset_manager.py -v',
                expected_output='passed',
                tags=['assets', 'core', 'efficiency'],
            ),
            'output-org': TestCase(
                id='output-org',
                name='Output Organization',
                description='Verify outputs organized by product and aspect ratio',
                requirement='Output Organization',
                requirement_level=RequirementLevel.CORE,
                command='python -m pytest tests/unit/test_storage.py -v',
                expected_output='passed',
                tags=['organization', 'core', 'structure'],
            ),
            'text-overlay': TestCase(
                id='text-overlay',
                name='Campaign Message Display',
                description='Verify text overlay on images',
                requirement='Campaign Message Display',
                requirement_level=RequirementLevel.CORE,
                command='python -m pytest tests/unit/test_processor.py -v -k overlay',
                expected_output='passed',
                tags=['messaging', 'core', 'overlay'],
            ),
            'compliance-check': TestCase(
                id='compliance-check',
                name='Compliance Checking',
                description='Verify brand and legal compliance checks',
                requirement='Brand Compliance & Legal Checks',
                requirement_level=RequirementLevel.OPTIONAL,
                command='python -m pytest tests/unit/test_compliance.py -v',
                expected_output='passed',
                tags=['compliance', 'optional', 'validation'],
            ),
            'logging': TestCase(
                id='logging',
                name='Logging & Reporting',
                description='Verify logs and reports are generated',
                requirement='Logging & Reporting',
                requirement_level=RequirementLevel.CORE,
                command='python -m pytest tests/unit/test_logger.py -v',
                expected_output='passed',
                tags=['logging', 'core', 'reporting'],
            ),
            'multi-products': TestCase(
                id='multi-products',
                name='Multiple Products Support',
                description='Verify support for 2+ products',
                requirement='Multiple Products',
                requirement_level=RequirementLevel.CORE,
                command='python -m pytest tests/unit/test_parsers.py -v -k products',
                expected_output='passed',
                tags=['products', 'core', 'multi'],
            ),
        }

        # Define test suites
        self.suites = {
            'quick': TestSuite(
                id='quick',
                name='Quick Tests',
                description='5-minute smoke test of core features',
                test_ids=['brief-json', 'brief-yaml', 'aspect-ratios', 'output-org', 'logging'],
                estimated_duration=300,
                tags=['quick', 'smoke', 'core'],
            ),
            'full': TestSuite(
                id='full',
                name='Full Test Suite',
                description='Complete test of all requirements',
                test_ids=['brief-json', 'brief-yaml', 'aspect-ratios', 'asset-reuse', 'output-org', 'text-overlay', 'compliance-check', 'logging', 'multi-products'],
                estimated_duration=900,
                tags=['full', 'comprehensive', 'all'],
            ),
            'compliance': TestSuite(
                id='compliance',
                name='Compliance Tests',
                description='Focus on brand and legal compliance',
                test_ids=['compliance-check', 'brief-json', 'brief-yaml'],
                estimated_duration=450,
                tags=['compliance', 'focused', 'validation'],
            ),
        }

        # Save configuration
        self.save_config()

    def save_config(self):
        """Save test configuration to file."""
        config = {
            'tests': [test.to_dict() for test in self.tests.values()],
            'suites': [asdict(suite) for suite in self.suites.values()],
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_tests(self) -> List[Dict]:
        """Get all tests as dictionaries."""
        return [test.to_dict() for test in self.tests.values()]

    def get_suites(self) -> List[Dict]:
        """Get all test suites."""
        return [asdict(suite) for suite in self.suites.values()]

    def get_test(self, test_id: str) -> Optional[Dict]:
        """Get specific test."""
        if test_id in self.tests:
            return self.tests[test_id].to_dict()
        return None

    def get_suite(self, suite_id: str) -> Optional[Dict]:
        """Get specific test suite."""
        if suite_id in self.suites:
            return asdict(self.suites[suite_id])
        return None

    def run_test(self, test_id: str) -> Dict:
        """Run a single test.
        
        Args:
            test_id: ID of test to run
            
        Returns:
            Test result with status and output
        """
        if test_id not in self.tests:
            return {'error': f'Test {test_id} not found'}

        test = self.tests[test_id]
        test.status = TestStatus.RUNNING
        
        start_time = datetime.now()
        
        try:
            # Execute test command — shell=False prevents shell injection
            result = subprocess.run(
                shlex.split(test.command),
                shell=False,
                capture_output=True,
                text=True,
                timeout=test.timeout,
                cwd=Path(__file__).parent.parent,
            )
            
            test.duration = (datetime.now() - start_time).total_seconds()
            test.result = result.stdout + result.stderr
            test.last_run = datetime.now().isoformat()
            
            # Check if output matches expected
            if test.expected_output and test.expected_output in test.result:
                test.status = TestStatus.PASSED
            elif result.returncode == 0:
                test.status = TestStatus.PASSED
            else:
                test.status = TestStatus.FAILED
                
        except subprocess.TimeoutExpired:
            test.status = TestStatus.FAILED
            test.result = f'Test timed out after {test.timeout} seconds'
            test.duration = test.timeout
            test.last_run = datetime.now().isoformat()
        except Exception as e:
            test.status = TestStatus.FAILED
            test.result = str(e)
            test.duration = (datetime.now() - start_time).total_seconds()
            test.last_run = datetime.now().isoformat()
        
        self.save_config()
        return test.to_dict()

    def run_suite(self, suite_id: str) -> Dict:
        """Run all tests in a suite.
        
        Args:
            suite_id: ID of suite to run
            
        Returns:
            Suite results with individual test statuses
        """
        if suite_id not in self.suites:
            return {'error': f'Suite {suite_id} not found'}

        suite = self.suites[suite_id]
        results = []
        
        for test_id in suite.test_ids:
            if test_id in self.tests:
                result = self.run_test(test_id)
                results.append(result)
        
        # Calculate suite statistics
        passed = sum(1 for r in results if r.get('status') == 'passed')
        failed = sum(1 for r in results if r.get('status') == 'failed')
        total = len(results)
        
        return {
            'suite_id': suite_id,
            'suite_name': suite.name,
            'passed': passed,
            'failed': failed,
            'total': total,
            'pass_rate': f'{int(passed/total*100)}%' if total > 0 else '0%',
            'tests': results,
            'timestamp': datetime.now().isoformat(),
        }

    def get_requirements_status(self) -> Dict:
        """Get status of all requirements.
        
        Returns:
            Dict with requirement status and coverage
        """
        requirements = {}
        
        for test in self.tests.values():
            req = test.requirement
            if req not in requirements:
                requirements[req] = {
                    'requirement': req,
                    'level': test.requirement_level.value,
                    'tests': [],
                    'passed': 0,
                    'failed': 0,
                    'pending': 0,
                }
            
            requirements[req]['tests'].append({
                'id': test.id,
                'name': test.name,
                'status': test.status.value,
            })
            
            if test.status == TestStatus.PASSED:
                requirements[req]['passed'] += 1
            elif test.status == TestStatus.FAILED:
                requirements[req]['failed'] += 1
            else:
                requirements[req]['pending'] += 1
        
        return {
            'requirements': list(requirements.values()),
            'core_requirements': sum(1 for r in requirements.values() if r['level'] == 'core'),
            'optional_requirements': sum(1 for r in requirements.values() if r['level'] == 'optional'),
            'timestamp': datetime.now().isoformat(),
        }

    def add_test(self, test_data: Dict) -> Dict:
        """Add a new test.
        
        Args:
            test_data: Test configuration
            
        Returns:
            Created test
        """
        test = TestCase(
            id=test_data['id'],
            name=test_data['name'],
            description=test_data['description'],
            requirement=test_data['requirement'],
            requirement_level=RequirementLevel(test_data['requirement_level']),
            command=test_data['command'],
            expected_output=test_data.get('expected_output'),
            verification_script=test_data.get('verification_script'),
            timeout=test_data.get('timeout', 300),
            tags=test_data.get('tags', []),
        )
        
        self.tests[test.id] = test
        self.save_config()
        return test.to_dict()

    def update_test(self, test_id: str, test_data: Dict) -> Optional[Dict]:
        """Update an existing test.
        
        Args:
            test_id: ID of test to update
            test_data: Updated configuration
            
        Returns:
            Updated test or None if not found
        """
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        # Update fields
        if 'name' in test_data:
            test.name = test_data['name']
        if 'description' in test_data:
            test.description = test_data['description']
        if 'command' in test_data:
            test.command = test_data['command']
        if 'expected_output' in test_data:
            test.expected_output = test_data['expected_output']
        if 'timeout' in test_data:
            test.timeout = test_data['timeout']
        if 'tags' in test_data:
            test.tags = test_data['tags']
        
        self.save_config()
        return test.to_dict()

    def delete_test(self, test_id: str) -> bool:
        """Delete a test.
        
        Args:
            test_id: ID of test to delete
            
        Returns:
            True if deleted, False if not found
        """
        if test_id in self.tests:
            del self.tests[test_id]
            self.save_config()
            return True
        return False
