import asyncio
from typing import List, Union
from collections.abc import Callable
import importlib
from pathlib import Path, PurePath
from parrot.loaders import AbstractLoader, Document, AVAILABLE_LOADERS
from ..flow import FlowComponent
from ...exceptions import ConfigError, ComponentError


class ParrotLoader(FlowComponent):
    """
    ParrotLoader.

    Overview:

    Getting a list of documents and convert them using Parrot Loaders.


        Example:

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          ParrotLoader:
          path: /home/ubuntu/symbits/lg/bot/products_positive
          source_type: Product-Top-Reviews
          loader: HTMLLoader
          chunk_size: 2048
        ```
    """
    _version = "1.0.0"

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        self.extensions: list = kwargs.pop('extensions', [])
        self.encoding: str = kwargs.get('encoding', 'utf-8')
        self.path: str = kwargs.pop('path', None)
        self.skip_directories: List[str] = kwargs.pop('skip_directories', [])
        self._chunk_size = kwargs.get('chunk_size', 2048)
        self.source_type: str = kwargs.pop('source_type', 'document')
        self.doctype: str = kwargs.pop('doctype', 'document')
        # LLM (if required)
        self._llm = kwargs.pop('llm', None)
        # Table settings for PDFTablesLoader
        self.table_settings = kwargs.pop('table_settings', {})
        super().__init__(
            loop=loop, job=job, stat=stat, **kwargs
        )
        self._device: str = kwargs.get('device', 'cpu')
        self._cuda_number: int = kwargs.get('cuda_number', 0)

    async def close(self):
        # Destroy effectively all Models.
        pass

    async def start(self, **kwargs):
        await super().start(**kwargs)
        
        # Check if path comes from previous component (like FileList)
        if not self.path and self.previous and self.input:
            # Handle input from previous component (FileList passes filename in kwargs)
            filename = kwargs.get('filename')
            if filename:
                self.path = filename
                print(f"ParrotLoader: Received file from previous component: {self.path}")
            else:
                # Fallback: try to use input directly
                self.path = self.input
                print(f"ParrotLoader: Using input as path: {self.path}")
        
        if self.path:
            if isinstance(self.path, str):
                self.path = self.mask_replacement_recursively(self.path)
                # Check if it's a URL (for video loaders like YouTube)
                if self.path.startswith(('http://', 'https://', 'ftp://')):
                    # For URLs, keep as string - don't convert to Path
                    print(f"Loading from URL: {self.path}")
                else:
                    # For local files, convert to Path and validate existence
                    self.path = Path(self.path).resolve()
                    if not self.path.exists():
                        raise ComponentError(
                            f"ParrotLoader: {self.path} doesn't exist."
                        )
            elif isinstance(self.path, Path):
                # Already a Path object (from FileList)
                if not self.path.exists():
                    raise ComponentError(
                        f"ParrotLoader: {self.path} doesn't exist."
                    )
        else:
            raise ConfigError(
                "Provide at least one directory or filename in *path* attribute or ensure previous component provides input."
            )

    def _get_loader_by_extension(self, suffix: str, source_path: Union[Path, List] = None) -> AbstractLoader:
        """Get a Document Loader based on file extension."""
        suffix = suffix.lower()
        if suffix not in AVAILABLE_LOADERS:
            raise ComponentError(
                f"ParrotLoader: No loader available for extension '{suffix}'. "
                f"Available extensions: {list(AVAILABLE_LOADERS.keys())}"
            )

        loader_class = AVAILABLE_LOADERS[suffix]

        doctype = f"{self.source_type}-{suffix.lstrip('.')}"

        # Common Arguments for Parrot loaders
        args = {
            "source": source_path or self.path,
            "chunk_size": self._chunk_size,
            "encoding": self.encoding,
            "source_type": self.source_type,
            "doctype": doctype,
            "device": self._device,
            "cuda_number": self._cuda_number,
        }

        return loader_class(**args)

    def _load_loader_by_name(self, name: str) -> AbstractLoader:
        """Dynamically imports a loader class from parrot.loaders module."""
        try:
            module_path = "parrot.loaders"
            module = importlib.import_module(module_path, package=__package__)
            cls = getattr(module, name)
            if cls:
                # Parrot loaders require 'source' as first positional argument
                args = {
                    "source": self.path,
                    "chunk_size": self._chunk_size,
                    "encoding": self.encoding,
                    "source_type": self.source_type,
                    "doctype": self.doctype,
                }

                # Only add device parameters if they are properly configured for non-video loaders
                # Video loaders have a bug with device handling, so we skip these parameters for them
                if name not in ['YoutubeLoader', 'VideoLoader']:
                    args["device"] = self._device
                    args["cuda_number"] = self._cuda_number

                # Pass through any additional parameters from the component configuration
                for key, value in self._attrs.items():
                    if key not in args and key not in ['loader', 'path', 'extensions', 'skip_directories']:
                        args[key] = value

                # Handle table_settings specifically for PDFTablesLoader
                if hasattr(self, 'table_settings') and isinstance(self.table_settings, dict):
                    args.update(self.table_settings)

                loader = cls(**args)
                print(f'Loading Parrot loader: {loader}')
                return loader
        except (ModuleNotFoundError, AttributeError) as e:
            raise ImportError(
                f"Unable to load the Parrot loader '{name}': {e}"
            ) from e

    async def run(self):
        documents = []

        if hasattr(self, 'loader'):
            # Use specific loader by name
            loader = self._load_loader_by_name(self.loader)
            documents = await loader.load(self.path)
        else:
            # Check if path is a URL or file/directory
            if isinstance(self.path, str) and self.path.startswith(('http://', 'https://', 'ftp://')):
                # For URLs, we need to determine the appropriate loader
                # For now, assume YouTube for youtube.com URLs
                if 'youtube.com' in self.path or 'youtu.be' in self.path:
                    loader = self._load_loader_by_name('YoutubeLoader')
                    documents = await loader.load(self.path)
                else:
                    raise ComponentError(
                        f"ParrotLoader: URL type not supported: {self.path}"
                    )
            else:
                # Use automatic loader detection by file extension for local files
                if self.path.is_dir():
                    _file_buckets = {}
                    # Process directory
                    if self.extensions:
                        # Process specific extensions
                        for ext in self.extensions:
                            for item in self.path.glob(f'*{ext}'):
                                if item.is_file() and set(item.parts).isdisjoint(self.skip_directories):
                                    ext = item.suffix.lower()
                                    _file_buckets.setdefault(ext, []).append(item)
                    else:
                        # Process all files
                        for item in self.path.glob('*.*'):
                            if item.is_file() and set(item.parts).isdisjoint(self.skip_directories):
                                ext = item.suffix.lower()
                                _file_buckets.setdefault(ext, []).append(item)
                elif self.path.is_file():
                    # Process single file
                    ext = self.path.suffix.lower()
                    if not self.extensions or ext in self.extensions:
                        if set(self.path.parts).isdisjoint(self.skip_directories):
                            _file_buckets.setdefault(ext, []).append(self.path)
                else:
                    raise ValueError(
                        f"ParrotLoader: Invalid path: {self.path}"
                    )
                if not _file_buckets:
                    raise FileNotFoundError(
                        f"ParrotLoader: No files found in {self.path}"
                    )
                for ext, files in _file_buckets.items():
                    try:
                        loader = self._get_loader_by_extension(ext, source_path=files)
                        docs = await loader.load()
                        documents.extend(docs)
                    except ComponentError as ce:
                        print(f"Warning: {ce}")
                        continue

        self._result = documents
        self.add_metric('NUM_DOCUMENTS', len(documents))
        return True
