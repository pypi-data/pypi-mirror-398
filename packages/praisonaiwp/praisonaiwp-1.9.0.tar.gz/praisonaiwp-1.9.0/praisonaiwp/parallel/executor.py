"""Python-Node.js bridge for parallel execution"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


class ParallelExecutor:
    """Execute operations in parallel using Node.js"""

    def __init__(self, nodejs_path: str = None):
        """
        Initialize parallel executor

        Args:
            nodejs_path: Path to Node.js scripts directory
        """
        if nodejs_path is None:
            # Default to nodejs directory in parallel module
            self.nodejs_path = Path(__file__).parent / "nodejs"
        else:
            self.nodejs_path = Path(nodejs_path)

        logger.debug(f"ParallelExecutor initialized with path: {self.nodejs_path}")

    def execute_parallel(
        self,
        operation: str,
        data: List[Dict[str, Any]],
        server_config: Dict[str, Any],
        workers: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Execute operations in parallel

        Args:
            operation: Operation type ('create', 'update', etc.)
            data: List of operations to perform
            server_config: Server configuration
            workers: Number of parallel workers

        Returns:
            List of results
        """
        # Prepare input data for Node.js
        input_data = {
            'operation': operation,
            'data': data,
            'server': server_config,
            'workers': workers
        }

        input_json = json.dumps(input_data)

        logger.info(f"Executing {len(data)} operations in parallel with {workers} workers")

        try:
            # Execute Node.js script
            result = subprocess.run(
                ['node', str(self.nodejs_path / 'index.js')],
                input=input_json,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Node.js execution failed: {result.stderr}")
                raise Exception(f"Parallel execution failed: {result.stderr}")

            # Parse results
            results = json.loads(result.stdout)

            logger.info(f"Parallel execution completed: {len(results)} results")

            return results

        except subprocess.TimeoutExpired:
            logger.error("Parallel execution timed out")
            raise Exception("Parallel execution timed out after 5 minutes")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Node.js output: {e}")
            raise Exception(f"Failed to parse parallel execution results: {e}")

        except Exception as e:
            logger.error(f"Parallel execution error: {e}")
            raise

    def is_available(self) -> bool:
        """
        Check if Node.js is available

        Returns:
            True if Node.js is installed and scripts exist
        """
        try:
            # Check if node is installed
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                timeout=5
            )

            if result.returncode != 0:
                return False

            # Check if scripts exist
            index_js = self.nodejs_path / 'index.js'
            if not index_js.exists():
                logger.warning(f"Node.js scripts not found at {self.nodejs_path}")
                return False

            return True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
