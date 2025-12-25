"""
Code Ingestion Tools for Agent Workers

Provides code repository ingestion capabilities directly in the agent worker runtime.
Workers can traverse local filesystems, parse code, and upload to Context Graph API.
"""

import os
import ast
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
import fnmatch
import structlog

try:
    import httpx
except ImportError:
    raise ImportError("httpx is required. Install with: pip install httpx")

logger = structlog.get_logger(__name__)


class CodeIngestionError(Exception):
    """Base exception for code ingestion errors."""
    pass


class SessionExpiredError(CodeIngestionError):
    """Session has expired."""
    pass


class SessionCommittedError(CodeIngestionError):
    """Session already committed, cannot add more files."""
    pass


class CodeIngestionTools:
    """
    Code ingestion tools for agent workers.

    This class is instantiated by the agent worker when the CodeIngestionSkill
    is enabled. It provides methods for ingesting code repositories into the
    knowledge graph.

    Usage:
        tools = CodeIngestionTools(config={
            "batch_size": 50,
            "included_patterns": ["**/*.py", "**/*.js"],
            "context_graph_api_url": "https://graph.kubiya.ai",
            "timeout": 60
        })

        result = await tools.ingest_repository(
            dataset_id="my-dataset-uuid",
            repo_path="/path/to/repo"
        )
    """

    def __init__(
        self,
        config: Dict[str, Any],
        api_token: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize code ingestion tools.

        Args:
            config: Skill configuration from Control Plane
            api_token: API token (defaults to KUBIYA_API_KEY env var)
            **kwargs: Additional worker context (user_email, organization, etc.)
        """
        self.config = config
        self.api_url = config.get("context_graph_api_url", os.getenv("CONTEXT_GRAPH_API_URL", "https://graph.kubiya.ai"))
        self.api_token = api_token or os.getenv("KUBIYA_API_KEY")
        self.timeout = config.get("timeout", 60)
        self.batch_size = config.get("batch_size", 50)
        self.max_retries = 3

        # Worker context
        self.user_email = kwargs.get("user_email")
        self.organization = kwargs.get("organization")

        logger.info(
            "code_ingestion_tools_initialized",
            api_url=self.api_url,
            batch_size=self.batch_size,
            organization=self.organization
        )

    async def ingest_repository(
        self,
        dataset_id: str,
        repo_path: str,
        patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        session_duration_minutes: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict:
        """
        Ingest a local code repository into the knowledge graph.

        Args:
            dataset_id: Target dataset UUID
            repo_path: Path to local repository
            patterns: File patterns to include (overrides config)
            exclude_patterns: Patterns to exclude (overrides config)
            batch_size: Files per batch (overrides config)
            session_duration_minutes: Session timeout (default: 120)
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            Job status dictionary with keys:
            - job_id: UUID
            - status: "completed" | "partial" | "failed"
            - files_processed: int
            - files_failed: int

        Raises:
            CodeIngestionError: On unrecoverable errors
            SessionExpiredError: If session expires mid-upload
            httpx.HTTPError: On API errors
        """
        logger.info(
            "ingest_repository_start",
            dataset_id=dataset_id,
            repo_path=repo_path,
            organization=self.organization
        )

        # Use config values if not overridden
        if patterns is None:
            patterns = self.config.get("included_patterns", [
                "**/*.py", "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx",
                "**/*.go", "**/*.java", "**/*.rs", "**/*.rb", "**/*.php",
                "**/*.c", "**/*.cpp", "**/*.h", "**/*.hpp"
            ])

        if exclude_patterns is None:
            exclude_patterns = self.config.get("excluded_patterns", [
                "**/__pycache__/**", "**/*.pyc", "**/node_modules/**",
                "**/dist/**", "**/build/**", "**/.git/**", "**/.venv/**",
                "**/venv/**", "**/target/**", "**/vendor/**", "**/.next/**"
            ])

        if batch_size is None:
            batch_size = self.batch_size

        if session_duration_minutes is None:
            session_duration_minutes = self.config.get("session_duration_minutes", 120)

        # Validate batch size
        if not 1 <= batch_size <= 100:
            raise ValueError("batch_size must be between 1 and 100")

        # Collect files
        files = self._collect_files(repo_path, patterns, exclude_patterns)
        if not files:
            raise CodeIngestionError(f"No files found matching patterns in {repo_path}")

        total_files = len(files)
        logger.info(
            "files_collected",
            total_files=total_files,
            repo_path=repo_path
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. Start session
            session = await self._start_session(
                client, dataset_id, repo_path, patterns, exclude_patterns, session_duration_minutes
            )
            session_id = session["id"]
            logger.info("session_created", session_id=session_id)

            # 2. Upload batches
            batches = [files[i:i+batch_size] for i in range(0, len(files), batch_size)]
            processed_files = 0

            for batch_num, batch in enumerate(batches):
                batch_files = []
                for file_path in batch:
                    try:
                        content = file_path.read_text(errors="ignore")
                        metadata = self._extract_metadata(file_path, repo_path, content)

                        batch_files.append({
                            "content": content,
                            "metadata": metadata
                        })
                    except Exception as e:
                        logger.warning(
                            "file_read_failed",
                            file_path=str(file_path),
                            error=str(e)
                        )
                        continue

                if not batch_files:
                    continue

                # Upload batch with retry
                await self._upload_batch_with_retry(
                    client, dataset_id, session_id, batch_num, batch_files
                )

                processed_files += len(batch_files)

                # Progress callback
                if progress_callback:
                    progress_callback(processed_files, total_files)

                logger.info(
                    "batch_uploaded",
                    batch_num=batch_num + 1,
                    total_batches=len(batches),
                    processed_files=processed_files,
                    total_files=total_files
                )

            # 3. Commit and cognify
            job = await self._commit_session(client, dataset_id, session_id)
            logger.info("cognify_triggered", job_id=job["job_id"])

            return {
                "job_id": job["job_id"],
                "status": job["status"],
                "files_processed": job.get("processed_records", processed_files),
                "files_failed": job.get("failed_records", 0),
                "session_id": session_id
            }

    async def _start_session(
        self,
        client: httpx.AsyncClient,
        dataset_id: str,
        repo_path: str,
        patterns: List[str],
        exclude_patterns: List[str],
        duration_minutes: int
    ) -> Dict:
        """Start streaming session."""
        url = f"{self.api_url}/api/v1/graph/datasets/{dataset_id}/code/stream/start"
        payload = {
            "session_duration_minutes": duration_minutes,
            "config": {
                "source_type": "local",
                "base_path": repo_path,
                "included_patterns": patterns,
                "excluded_patterns": exclude_patterns
            }
        }

        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {self.api_token}"},
            json=payload
        )
        resp.raise_for_status()
        return resp.json()

    async def _upload_batch_with_retry(
        self,
        client: httpx.AsyncClient,
        dataset_id: str,
        session_id: str,
        batch_num: int,
        files: List[Dict]
    ):
        """Upload batch with retry logic."""
        url = f"{self.api_url}/api/v1/graph/datasets/{dataset_id}/code/stream/batch"
        payload = {
            "session_id": session_id,
            "batch_id": f"batch_{batch_num}",
            "files": files
        }

        for attempt in range(self.max_retries):
            try:
                resp = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json=payload
                )

                if resp.status_code == 400:
                    error = resp.json()
                    if "expired" in error.get("detail", "").lower():
                        raise SessionExpiredError("Session has expired")
                    elif "committed" in error.get("detail", "").lower():
                        raise SessionCommittedError("Session already committed")

                resp.raise_for_status()
                return resp.json()

            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(
                    "batch_upload_retry",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    wait_time=wait_time,
                    error=str(e)
                )
                await asyncio.sleep(wait_time)

    async def _commit_session(
        self,
        client: httpx.AsyncClient,
        dataset_id: str,
        session_id: str
    ) -> Dict:
        """Commit session and trigger cognify."""
        url = f"{self.api_url}/api/v1/graph/datasets/{dataset_id}/code/stream/{session_id}/commit"

        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {self.api_token}"}
        )
        resp.raise_for_status()
        return resp.json()

    def _collect_files(
        self,
        repo_path: str,
        patterns: List[str],
        exclude_patterns: List[str]
    ) -> List[Path]:
        """Collect files matching patterns."""
        base = Path(repo_path)
        if not base.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")

        files = []
        for pattern in patterns:
            matched = list(base.glob(pattern))
            for file_path in matched:
                if not file_path.is_file():
                    continue

                # Check exclusions
                relative_path = str(file_path.relative_to(base))
                if any(fnmatch.fnmatch(relative_path, excl) for excl in exclude_patterns):
                    continue

                # Check file size
                max_size_kb = self.config.get("max_file_size_kb", 1024)
                if file_path.stat().st_size > max_size_kb * 1024:
                    logger.warning(
                        "file_too_large",
                        file_path=relative_path,
                        size_kb=file_path.stat().st_size // 1024,
                        max_size_kb=max_size_kb
                    )
                    continue

                files.append(file_path)

        return files

    def _extract_metadata(self, file_path: Path, repo_path: str, content: str) -> Dict:
        """Extract file metadata."""
        language = self._detect_language(file_path)
        relative_path = str(file_path.relative_to(repo_path))

        metadata = {
            "file_path": relative_path,
            "language": language,
            "size_bytes": len(content.encode()),
            "lines_of_code": len([l for l in content.split("\n") if l.strip()]),
            "dependencies": [],
            "exports": [],
            "file_hash": hashlib.sha256(content.encode()).hexdigest()
        }

        # Extract imports/exports based on language
        if self.config.get("extract_dependencies", True):
            if language == "python":
                metadata.update(self._parse_python(content))
            elif language in ("javascript", "typescript"):
                metadata.update(self._parse_javascript(content))

        return metadata

    def _parse_python(self, content: str) -> Dict:
        """Parse Python code with AST."""
        result = {"dependencies": [], "exports": []}

        try:
            tree = ast.parse(content)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    result["dependencies"].extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["dependencies"].append(node.module)

            # Extract exports
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not node.name.startswith("_"):  # Public exports only
                        result["exports"].append(node.name)

        except SyntaxError:
            logger.debug("python_parse_failed", reason="syntax_error")

        return result

    def _parse_javascript(self, content: str) -> Dict:
        """Parse JavaScript/TypeScript with regex."""
        import re

        result = {"dependencies": [], "exports": []}

        # Extract imports
        import_patterns = [
            r"import\s+.*?\s+from\s+['\"](.+?)['\"]",  # ES6: import X from 'Y'
            r"require\(['\"](.+?)['\"]\)",              # CommonJS: require('X')
        ]
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            result["dependencies"].extend(matches)

        # Extract exports
        export_patterns = [
            r"export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)",
            r"exports\.(\w+)\s*=",  # CommonJS: exports.X = ...
        ]
        for pattern in export_patterns:
            matches = re.findall(pattern, content)
            result["exports"].extend(matches)

        # Deduplicate
        result["dependencies"] = list(set(result["dependencies"]))
        result["exports"] = list(set(result["exports"]))

        return result

    def _detect_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".java": "java",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp"
        }
        return ext_map.get(file_path.suffix, "unknown")
