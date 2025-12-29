"""Base class for Ray executors with shared runtime env logic."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from synapse_sdk.plugins.context import PluginEnvironment
from synapse_sdk.plugins.enums import PackageManager


def read_requirements(file_path: str | Path) -> list[str] | None:
    """Read and parse a requirements.txt file.

    Args:
        file_path: Path to the requirements.txt file.

    Returns:
        List of requirement strings, or None if file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        return None

    requirements = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            requirements.append(stripped)
    return requirements


class BaseRayExecutor:
    """Base class for Ray executors with shared runtime env building logic."""

    def __init__(
        self,
        env: PluginEnvironment | dict[str, Any] | None = None,
        *,
        runtime_env: dict[str, Any] | None = None,
        working_dir: str | Path | None = None,
        requirements_file: str | Path | None = None,
        package_manager: PackageManager | Literal['pip', 'uv'] = PackageManager.PIP,
        package_manager_options: list[str] | None = None,
        wheels_dir: str = 'wheels',
        ray_address: str = 'auto',
        include_sdk: bool = False,
    ) -> None:
        """Initialize base Ray executor.

        Args:
            env: Environment config for the action. If None, loads from os.environ.
            runtime_env: Ray runtime environment config.
            working_dir: Plugin working directory.
            requirements_file: Path to requirements.txt.
            package_manager: Package manager to use ('pip' or 'uv').
            package_manager_options: Additional options for the package manager.
            wheels_dir: Directory containing .whl files relative to working_dir.
            ray_address: Ray cluster address (for detecting remote mode).
            include_sdk: If True, bundle local SDK with upload (for development).
        """
        if env is None:
            self._env = PluginEnvironment.from_environ()
        elif isinstance(env, dict):
            self._env = PluginEnvironment(env)
        else:
            self._env = env

        self._runtime_env = runtime_env or {}
        self._working_dir = Path(working_dir) if working_dir else None
        self._requirements_file = Path(requirements_file) if requirements_file else None
        self._package_manager = PackageManager(package_manager)
        self._package_manager_options = package_manager_options
        self._wheels_dir = wheels_dir
        self._ray_address = ray_address
        self._include_sdk = include_sdk
        self._gcs_uri: str | None = None  # Cached GCS URI

    def _ray_init(self) -> None:
        """Initialize Ray connection with SDK bundling if requested."""
        import ray

        if ray.is_initialized():
            return

        # Build init kwargs
        init_kwargs: dict[str, Any] = {
            'address': self._ray_address,
            'ignore_reinit_error': True,
        }

        # Build runtime_env for init level
        runtime_env: dict[str, Any] = {}

        # Include SDK at init level (directories only work here, not at actor level)
        if self._include_sdk:
            import synapse_sdk

            sdk_path = str(Path(synapse_sdk.__file__).parent)
            runtime_env['py_modules'] = [sdk_path]

        # Include working_dir at init level for local mode
        # (local paths are only supported at ray.init() level, not at actor level)
        if self._working_dir and not self._is_remote_cluster():
            runtime_env['working_dir'] = str(self._working_dir)

        if runtime_env:
            init_kwargs['runtime_env'] = runtime_env

        ray.init(**init_kwargs)

    def _is_remote_cluster(self) -> bool:
        """Check if connecting to a remote Ray cluster."""
        # Remote if address starts with ray:// protocol
        return self._ray_address.startswith('ray://')

    def _get_working_dir_uri(self) -> str | None:
        """Get working directory URI, uploading to GCS for remote clusters."""
        if not self._working_dir:
            return None

        # For remote clusters, upload to GCS
        if self._is_remote_cluster():
            if self._gcs_uri is None:
                from synapse_sdk.plugins.executors.ray.packaging import upload_working_dir_to_gcs

                self._gcs_uri = upload_working_dir_to_gcs(self._working_dir)
            return self._gcs_uri

        # Local mode - use path directly
        return str(self._working_dir)

    def _build_runtime_env(self) -> dict[str, Any]:
        """Build runtime environment with working_dir, requirements, and env vars."""
        runtime_env = {**self._runtime_env}

        # Set working_dir if provided (uploads to GCS for remote clusters)
        # Note: Local paths are only supported at ray.init() level, not at actor level
        if self._working_dir and 'working_dir' not in runtime_env:
            if self._is_remote_cluster():
                working_dir_uri = self._get_working_dir_uri()
                if working_dir_uri:
                    runtime_env['working_dir'] = working_dir_uri
            # For local mode, working_dir is passed at ray.init() level

        # Build package manager config with requirements and wheels
        pm_key = str(self._package_manager)  # 'pip' or 'uv'
        requirements = self._get_requirements() or []
        wheel_files = self._get_wheel_files()

        # Combine requirements and wheel files
        all_packages = requirements + wheel_files

        if all_packages:
            # Initialize package manager config
            if pm_key not in runtime_env:
                runtime_env[pm_key] = {'packages': []}
            elif isinstance(runtime_env[pm_key], list):
                runtime_env[pm_key] = {'packages': runtime_env[pm_key]}

            runtime_env[pm_key].setdefault('packages', [])
            runtime_env[pm_key]['packages'].extend(all_packages)

        # Apply package manager options
        pm_options = self._get_package_manager_options()
        if pm_options and pm_key in runtime_env:
            for key, value in pm_options.items():
                runtime_env[pm_key][key] = value

        # Add env vars
        runtime_env.setdefault('env_vars', {})
        runtime_env['env_vars'].update(self._env.to_dict())

        # Include Synapse credentials for backend client on workers
        from synapse_sdk.utils.auth import ENV_SYNAPSE_ACCESS_TOKEN, ENV_SYNAPSE_HOST, load_credentials

        host, token = load_credentials()
        if host and ENV_SYNAPSE_HOST not in runtime_env['env_vars']:
            runtime_env['env_vars'][ENV_SYNAPSE_HOST] = host
        if token and ENV_SYNAPSE_ACCESS_TOKEN not in runtime_env['env_vars']:
            runtime_env['env_vars'][ENV_SYNAPSE_ACCESS_TOKEN] = token

        return runtime_env

    def _get_package_manager_options(self) -> dict[str, Any]:
        """Get package manager options with defaults.

        Returns:
            Dict of package manager options.
        """
        user_options = self._package_manager_options or []

        if self._package_manager == PackageManager.UV:
            defaults = ['--no-cache']
            options_list = defaults.copy()
            for opt in user_options:
                if opt not in options_list:
                    options_list.append(opt)
            return {'uv_pip_install_options': options_list}
        else:
            # pip - use pip_install_options with --upgrade flag
            defaults = ['--upgrade']
            options_list = defaults.copy()
            for opt in user_options:
                if opt not in options_list:
                    options_list.append(opt)
            return {'pip_install_options': options_list}

    def _get_requirements(self) -> list[str] | None:
        """Get requirements from file.

        Returns:
            List of requirements, or None if no requirements file found.
        """
        # Explicit requirements file takes priority
        if self._requirements_file:
            return read_requirements(self._requirements_file)

        # Auto-discover from working_dir
        if self._working_dir:
            req_path = self._working_dir / 'requirements.txt'
            return read_requirements(req_path)

        return None

    def _get_wheel_files(self) -> list[str]:
        """Get wheel file paths for Ray runtime env.

        Scans the wheels_dir for .whl files and returns them as Ray-compatible
        paths using ${RAY_RUNTIME_ENV_CREATE_WORKING_DIR}.

        Returns:
            List of wheel file paths for Ray.
        """
        if not self._working_dir:
            return []

        wheels_path = self._working_dir / self._wheels_dir
        if not wheels_path.exists():
            return []

        wheel_files = []
        for whl in wheels_path.glob('*.whl'):
            # Use Ray's working dir variable for the path
            ray_path = f'${{RAY_RUNTIME_ENV_CREATE_WORKING_DIR}}/{self._wheels_dir}/{whl.name}'
            wheel_files.append(ray_path)

        return wheel_files


__all__ = ['BaseRayExecutor', 'read_requirements']
