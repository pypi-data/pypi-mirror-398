import ensurepip
import importlib
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from loguru import logger
from sqlmodel import select

from pushikoo.db import PipIndex as PipIndexDB
from pushikoo.db import get_session


# Regex for valid package spec: package names with optional version specifiers
# Examples: pushikoo-adapter-test, pushikoo>=1.0.0, package[extra]==1.0
_PACKAGE_SPEC_PATTERN = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?(\[[a-zA-Z0-9,._-]+\])?(([<>=!~]=?|===?)[a-zA-Z0-9.*,<>=!~\[\]]+)?$"
)


def validate_pip_spec(spec: str) -> tuple[bool, str]:
    """
    Validate a pip install specification.

    Allowed formats:
    - Package name with optional version: pushikoo>=1.0.0, package[extra]==1.0
    - Local path (must exist and contain pyproject.toml, setup.py, or be a .whl file)
    - VCS URL: git+https://github.com/user/repo.git
    - HTTPS URL ending with .whl

    Returns:
        (is_valid, error_message) - error_message is empty if valid
    """
    spec = spec.strip()

    if not spec:
        return False, "Empty package specification"

    # Package name with optional version specifier
    if _PACKAGE_SPEC_PATTERN.match(spec):
        return True, ""

    # VCS URLs (git+, hg+, svn+, bzr+)
    if spec.startswith(("git+", "hg+", "svn+", "bzr+")):
        # Check for dangerous shell chars in VCS URL
        dangerous = [";", "&", "|", "`", "$", "(", ")", "{", "}", "\n", "\r"]
        for char in dangerous:
            if char in spec:
                return False, f"Invalid character in VCS URL: {char!r}"
        # Extract the URL part after the prefix
        url_part = spec.split("+", 1)[1]
        parsed = urlparse(url_part)
        if parsed.scheme in ("https", "http", "ssh") and parsed.netloc:
            return True, ""
        return False, "Invalid VCS URL format"

    # HTTPS/HTTP URLs (for wheels or archives)
    if spec.startswith(("https://", "http://")):
        # Check for dangerous shell chars
        dangerous = [";", "&", "|", "`", "$", "(", ")", "{", "}", "\n", "\r"]
        for char in dangerous:
            if char in spec:
                return False, f"Invalid character in URL: {char!r}"
        parsed = urlparse(spec)
        if parsed.netloc and (
            spec.endswith(".whl") or spec.endswith(".tar.gz") or spec.endswith(".zip")
        ):
            return True, ""
        return False, "HTTP URLs must point to .whl, .tar.gz, or .zip files"

    # Local path (starts with . or / or drive letter on Windows)
    if (
        spec.startswith(".")
        or spec.startswith("/")
        or (len(spec) > 1 and spec[1] == ":")
    ):
        # Check for dangerous shell chars in path
        dangerous = [";", "&", "|", "`", "$", "(", ")", "{", "}", "\n", "\r"]
        for char in dangerous:
            if char in spec:
                return False, f"Invalid character in path: {char!r}"
        path = Path(spec).resolve()
        if not path.exists():
            return False, f"Path does not exist: {path}"
        if path.is_file():
            if path.suffix == ".whl":
                return True, ""
            return False, "File must be a .whl wheel"
        if path.is_dir():
            # Check for valid Python project indicators
            if (path / "pyproject.toml").exists():
                return True, ""
            if (path / "setup.py").exists():
                return True, ""
            if (path / "setup.cfg").exists():
                return True, ""
            return (
                False,
                "Directory must contain pyproject.toml, setup.py, or setup.cfg",
            )
        return False, f"Invalid path: {path}"

    # For unrecognized patterns, check dangerous chars
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "{", "}", "\n", "\r"]
    for char in dangerous_chars:
        if char in spec:
            return False, f"Invalid character in spec: {char!r}"

    return False, f"Invalid package specification format: {spec}"


def validate_pip_url(url: str) -> tuple[bool, str]:
    """
    Validate a pip index URL.

    Returns:
        (is_valid, error_message) - error_message is empty if valid
    """
    if not url:
        return False, "Empty URL"

    # Check for dangerous characters
    dangerous_chars = [
        ";",
        "&",
        "|",
        "`",
        "$",
        "(",
        ")",
        "{",
        "}",
        "<",
        ">",
        "\n",
        "\r",
        " ",
    ]
    for char in dangerous_chars:
        if char in url:
            return False, f"Invalid character in URL: {char!r}"

    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        return False, "URL must use https or http scheme"
    if not parsed.netloc:
        return False, "URL must have a valid host"

    return True, ""


def _join_output(stdout: str, stderr: str) -> str:
    stdout = stdout or ""
    stderr = stderr or ""
    if stdout and stderr:
        return stdout.rstrip() + "\n" + stderr.lstrip()
    return stdout or stderr


class PIPService:
    """Service for managing adapter packages using pip."""

    @staticmethod
    def _ensure_pip():
        if importlib.util.find_spec("pip") is None:
            ensurepip.bootstrap()

    @staticmethod
    def _reload_adapters_if_needed(pip_output: str = "") -> None:
        """
        Reload adapter packages after a pip operation.

        This is only concerned with distributions that expose the
        'pushikoo.adapter' entry point group, and will:
        - purge their loaded modules from sys.modules (only if mentioned in pip_output)
        - re-initialize AdapterInstanceService
        - reload CronService to ensure scheduler uses fresh instances

        Args:
            pip_output: The stdout/stderr from pip command. Only adapters mentioned
                        in this output will be purged.
        """
        # TODO: Refactor the cyclic import.
        from importlib import metadata as _metadata  # local import

        from pushikoo.service.adapter import (
            ADAPTER_ENTRY_GROUP,
            AdapterInstanceService,
        )

        try:
            adapter_dist_names: set[str] = set()
            for dist in _metadata.distributions():
                try:
                    entry_points = dist.entry_points
                except Exception:
                    continue
                for ep in entry_points:
                    if ep.group == ADAPTER_ENTRY_GROUP:
                        dist_name = dist.metadata.get("Name")
                        if dist_name:
                            adapter_dist_names.add(dist_name)
                        break

            if not adapter_dist_names:
                return

            # Only purge adapters that are mentioned in the pip output
            purged_adapters: set[str] = set()
            for dist_name in adapter_dist_names:
                # Check if this adapter's name appears in pip output
                # Normalize both for comparison (replace - with _ and vice versa)
                dist_normalized = dist_name.lower().replace("-", "_")
                output_normalized = pip_output.lower().replace("-", "_")
                if dist_normalized in output_normalized:
                    PIPService._purge_modules_by_distribution(dist_name)
                    purged_adapters.add(dist_name)

            if purged_adapters:
                AdapterInstanceService.reload(purged_adapters)
                logger.info(
                    "Reloaded adapter instances after pip operation "
                    f"for distributions: {sorted(purged_adapters)}"
                )
            else:
                logger.debug(
                    "No adapter distributions found in pip output; skipping reload."
                )
        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"Failed to reload adapters after pip operation: {e}")

    @staticmethod
    def _purge_modules_by_distribution(dist_name: str) -> None:
        """Purge all modules belonging to a given installed distribution, using importlib.metadata."""
        try:
            dist = metadata.distribution(dist_name)
        except metadata.PackageNotFoundError:
            logger.warning(f"Distribution '{dist_name}' not found; nothing to purge.")
            return

        # Gets all top-level packages (directory names) corresponding to this distribution package
        top_levels = set()
        try:
            top_level_text = dist.read_text("top_level.txt")
            if top_level_text:
                for line in top_level_text.splitlines():
                    name = line.strip()
                    if name:
                        top_levels.add(name)
        except FileNotFoundError:
            # Some packages do not have top_level.txt, so the next best choice is to use the package name to infer
            top_levels.add(dist.metadata["Name"].replace("-", "_"))

        logger.debug(f"Purging modules for dist '{dist_name}': {sorted(top_levels)}")

        removed_any = False
        for mod in list(sys.modules):
            if any(mod == top or mod.startswith(top + ".") for top in top_levels):
                del sys.modules[mod]
                removed_any = True
                logger.debug(f"Unloaded module: {mod}")

        if removed_any:
            logger.info(f"Purged modules from distribution '{dist_name}'.")
        else:
            logger.info(f"No loaded modules found for distribution '{dist_name}'.")

    @staticmethod
    def add_index(url: str) -> str:
        """Add a new index URL."""
        with get_session() as session:
            # Check if URL already exists
            existing = session.exec(
                select(PipIndexDB).where(PipIndexDB.url == url)
            ).first()
            if existing:
                raise ValueError(f"Index URL '{url}' already exists")

            db_obj = PipIndexDB(url=url)
            session.add(db_obj)
            session.commit()
            logger.info(f"Added index URL: {url}")
            return url

    @staticmethod
    def list_indexes(
        *, limit: int | None = None, offset: int | None = None
    ) -> list[str]:
        """List all index URLs."""
        with get_session() as session:
            q = select(PipIndexDB).order_by(PipIndexDB.url)
            if offset is not None:
                q = q.offset(offset)
            if limit is not None:
                q = q.limit(limit)
            rows = session.exec(q).all()
            return [row.url for row in rows]

    @staticmethod
    def delete_index(url: str) -> bool:
        """Delete an index URL by URL string."""
        with get_session() as session:
            db_obj = session.exec(
                select(PipIndexDB).where(PipIndexDB.url == url)
            ).first()
            if db_obj:
                session.delete(db_obj)
                session.commit()
                logger.info(f"Deleted index URL: {url}")
                return True
            return False

    @staticmethod
    def install(
        spec: str | Path,
        *,
        force: bool = False,
        upgrade: bool = False,
        index_url: str | None = None,
        extra_index_urls: list[str] | None = None,
        extra_args: Iterable[str] | None = None,
    ) -> dict[str, object]:
        """
        Install a package using pip.

        Args:
            spec: Package specification or path to install
            force: Force reinstall even if already installed
            upgrade: Upgrade package if already installed
            index_url: Primary index URL (--index-url), None means use default PyPI
            extra_index_urls: List of extra index URLs (--extra-index-url)
            extra_args: Additional arguments to pass to pip

        Raises:
            ValueError: If spec or URLs fail validation
        """
        PIPService._ensure_pip()
        target = (
            str(spec.expanduser().resolve()) if isinstance(spec, Path) else spec.strip()
        )

        # Validate the package specification
        is_valid, error = validate_pip_spec(target)
        if not is_valid:
            logger.warning(f"Invalid package spec rejected: {target} - {error}")
            return {
                "ok": False,
                "target": target,
                "output": f"Invalid package specification: {error}",
            }

        # Validate index URLs
        if index_url is not None:
            is_valid, error = validate_pip_url(index_url)
            if not is_valid:
                logger.warning(f"Invalid index URL rejected: {index_url} - {error}")
                return {
                    "ok": False,
                    "target": target,
                    "output": f"Invalid index URL: {error}",
                }

        if extra_index_urls:
            for url in extra_index_urls:
                is_valid, error = validate_pip_url(url)
                if not is_valid:
                    logger.warning(f"Invalid extra index URL rejected: {url} - {error}")
                    return {
                        "ok": False,
                        "target": target,
                        "output": f"Invalid extra index URL: {error}",
                    }

        cmd = [sys.executable, "-m", "pip", "install", target]
        if force:
            cmd.append("--force-reinstall")
        if upgrade:
            cmd.append("--upgrade")

        # Add index URL if specified (not None)
        if index_url is not None:
            cmd.extend(["--index-url", index_url])

        # Add extra index URLs
        if extra_index_urls:
            for url in extra_index_urls:
                cmd.extend(["--extra-index-url", url])

        if extra_args:
            cmd.extend(list(extra_args))

        logger.info(f"Installing package: {target}")
        logger.debug(f"Executing command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        logger.debug(f"pip stdout:\n{stdout.strip()}")
        if stderr.strip():
            logger.warning(f"pip stderr:\n{stderr.strip()}")

        output = _join_output(stdout, stderr)

        if result.returncode != 0:
            logger.error(f"Installation failed for {target} (code={result.returncode})")
            return {
                "ok": False,
                "target": target,
                "output": output,
            }

        logger.info(f"Successfully installed package: {target}")

        # After a successful install, refresh adapter-related packages so that
        # newly installed adapter versions are picked up without restarting.
        PIPService._reload_adapters_if_needed(output)

        return {
            "ok": True,
            "target": target,
            "output": f"Successfully installed package: {target}",
        }

    @staticmethod
    def uninstall(
        package_name: str, *, remove_loaded_modules: bool = True
    ) -> dict[str, object]:
        """
        Uninstall a package using pip.

        Args:
            package_name: Name of the package to uninstall
            remove_loaded_modules: Whether to remove loaded modules from memory
        """
        PIPService._ensure_pip()

        # Pre-check if package is installed so that "not installed" is exposed clearly.
        try:
            metadata.distribution(package_name)
        except metadata.PackageNotFoundError:
            logger.warning(f"Cannot uninstall '{package_name}': not installed")
            return {
                "ok": False,
                "target": package_name,
                "output": f"Package '{package_name}' is not installed",
            }
        logger.info(f"Uninstalling package: {package_name}")

        cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]
        logger.debug(f"Executing command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        logger.debug(f"pip stdout:\n{stdout.strip()}")
        if stderr.strip():
            logger.warning(f"pip stderr:\n{stderr.strip()}")

        output = _join_output(stdout, stderr)

        if result.returncode != 0:
            logger.error(
                f"Uninstallation failed for {package_name} (code={result.returncode})"
            )
            return {
                "ok": False,
                "target": package_name,
                "output": output,
            }

        logger.info(f"Package uninstalled successfully: {package_name}")

        if remove_loaded_modules:
            logger.debug(f"Purging loaded modules for distribution: {package_name}")
            PIPService._purge_modules_by_distribution(package_name)
            logger.info(f"Modules purged for distribution: {package_name}")

        # After a successful uninstall, also refresh adapter-related packages so
        # that in-memory state is consistent with the new environment.
        PIPService._reload_adapters_if_needed(output)

        return {
            "ok": True,
            "target": package_name,
            "output": f"Package uninstalled successfully: {package_name}",
        }
