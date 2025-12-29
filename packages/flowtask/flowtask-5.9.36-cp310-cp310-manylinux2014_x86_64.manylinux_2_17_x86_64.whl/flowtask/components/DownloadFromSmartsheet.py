"""
DownloadFromSmartsheet
Download attachments from SmartSheet sheets or rows with advanced filtering.

Example:

```yaml
DownloadFromSmartsheet:
  comments: Download only "Full Packet.pdf" files from approved rows
  sheet_id: '8504624500658052'
  directory: /home/ubuntu/symbits/smartsheet/attachments/
  overwrite: false
  filename_filter: 'Full Packet\.pdf$'
  column_filter:
    Document Status: 'Send to TROC Processing'
  filename_columns:
    - lead_id
    - Company Name
```
"""
from pathlib import Path
from typing import List, Optional, Dict
from ..exceptions import ComponentError, ConfigError
from .flow import FlowComponent
from ..interfaces.smartsheet import SmartSheetClient


class DownloadFromSmartsheet(SmartSheetClient, FlowComponent):
    """
    DownloadFromSmartsheet

    Overview

        Download attachments from SmartSheet sheets or specific rows with advanced filtering.
        Supports:
        - Unique filenames using row data
        - Filename regex filtering
        - Column value filtering
        - Extension filtering

        Filename format: {row_id}_{column1_value}_{column2_value}_{original_filename}
        Example: 62_3547_Comfortable-Heating_Full-Packet.pdf

    Properties

        :widths: auto

        | api_key            |   No     | The SmartSheet API key (can be provided as an environment variable or directly   |
        |                    |          | set as a property). If not provided, tries to use the `SMARTSHEET_API_KEY`       |
        |                    |          | environment variable.                                                            |
        | sheet_id           |   Yes    | The ID of the SmartSheet sheet containing the attachments.                       |
        | row_id             |   No     | The ID of the specific row to download attachments from. If not provided,        |
        |                    |          | downloads all attachments (subject to filters).                                  |
        | directory          |   Yes    | Directory path where attachments will be saved.                                  |
        | overwrite          |   No     | Boolean flag indicating whether to overwrite existing files (default: False).    |
        | attachment_filter  |   No     | List of file extensions to filter (e.g., ['.pdf', '.xlsx']).                     |
        | filename_columns   |   No     | List of column names to include in filename. Default: ['lead_id', 'Company Name']|
        | filename_filter    |   No     | Regular expression pattern to match filenames.                                   |
        |                    |          | Example: 'Full Packet\.pdf$' matches files ending with "Full Packet.pdf"         |
        |                    |          | Only files matching this pattern will be downloaded.                             |
        | column_filter      |   No     | Dictionary of column_name: value pairs to filter rows.                           |
        |                    |          | Example: {'Document Status': 'Send to TROC Processing'}                          |
        |                    |          | Only attachments from matching rows will be downloaded.                          |
        | use_row_number     |   No     | Boolean flag to use visual row number (16) instead of internal row ID            |
        |                    |          | (7075005843705732) in filename. Default: False.                                  |
        |                    |          | True: 16_Pool-Spa_file.pdf | False: 7075005843705732_Pool-Spa_file.pdf          |

    Return

        Returns a dictionary containing:
        - downloaded: List of successfully downloaded file paths
        - skipped: List of skipped files with reasons
        - failed: List of failed downloads with error messages
        - total: Total number of attachments found
        - filtered_by_column: Number of attachments skipped by column filter
        - filtered_by_filename: Number of attachments skipped by filename filter
        - directory: The directory where files were saved

    Example: Download "Full Packet.pdf" from approved rows


    Example: Multiple filter conditions


    Example: Filename patterns


    Example Programmatic Usage

    ```python
    from flowtask.components import DownloadFromSmartsheet
    import asyncio

    component = DownloadFromSmartsheet(
        sheet_id='8504624500658052',
        directory='/home/ubuntu/data/attachments/',
        filename_filter=r'Full Packet\.pdf$',
        column_filter={'Document Status': 'Send to TROC Processing'},
        filename_columns=['lead_id', 'Company Name']
    )

    results = asyncio.run(component.run())

    print(f"Downloaded: {len(results['downloaded'])}")
    print(f"Filtered by column: {results['filtered_by_column']}")
    print(f"Filtered by filename: {results['filtered_by_filename']}")
    ```

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          name: Download Full Packets for Processing
          description: Download only Full Packet.pdf files from rows ready for processing
          steps:
          - DownloadFromSmartsheet:
          sheet_id: '8504624500658052'
          directory: /home/ubuntu/data/troc_processing/
          filename_filter: 'Full Packet\.pdf$'
          column_filter:
          Document Status: 'Send to TROC Processing'
          filename_columns:
          - lead_id
          - Company Name
        ```
    """
    _version = "1.0.0"

    def __init__(self, *args, **kwargs):
        # Extract DownloadFromSmartsheet specific parameters
        self.sheet_id: str = kwargs.pop('sheet_id', None)
        self.row_id: Optional[str] = kwargs.pop('row_id', None)
        self.directory: Path = kwargs.pop('directory', None)
        self.overwrite: bool = kwargs.pop('overwrite', False)
        self.attachment_filter: Optional[List[str]] = kwargs.pop('attachment_filter', None)
        self.filename_columns: Optional[List[str]] = kwargs.pop('filename_columns', None)
        self.filename_filter: Optional[str] = kwargs.pop('filename_filter', None)
        self.column_filter: Optional[Dict[str, str]] = kwargs.pop('column_filter', None)
        self.use_row_number: bool = kwargs.pop('use_row_number', False)

        # Initialize parent classes
        super().__init__(*args, **kwargs)

    async def start(self, **kwargs) -> bool:
        """
        Validate configuration parameters before execution.
        """
        await super().start(**kwargs)

        # Validate required parameters
        if not self.sheet_id:
            raise ConfigError(
                "DownloadFromSmartsheet: sheet_id is required"
            )

        if not self.directory:
            raise ConfigError(
                "DownloadFromSmartsheet: directory is required"
            )

        # Convert directory to Path if it's a string
        if isinstance(self.directory, str):
            self.directory = Path(self.directory)

        # Validate attachment_filter format if provided
        if self.attachment_filter:
            if not isinstance(self.attachment_filter, list):
                raise ConfigError(
                    "DownloadFromSmartsheet: attachment_filter must be a list of file extensions"
                )
            # Ensure extensions start with a dot
            self.attachment_filter = [
                ext if ext.startswith('.') else f'.{ext}'
                for ext in self.attachment_filter
            ]

        # Validate filename_columns format if provided
        if self.filename_columns is not None:
            if not isinstance(self.filename_columns, list):
                raise ConfigError(
                    "DownloadFromSmartsheet: filename_columns must be a list of column names"
                )

        # Validate filename_filter format if provided
        if self.filename_filter is not None:
            if not isinstance(self.filename_filter, str):
                raise ConfigError(
                    "DownloadFromSmartsheet: filename_filter must be a string regex pattern"
                )

        # Validate column_filter format if provided
        if self.column_filter is not None:
            if not isinstance(self.column_filter, dict):
                raise ConfigError(
                    "DownloadFromSmartsheet: column_filter must be a dict of column_name: value pairs"
                )

    async def run(self):
        """
        Execute the attachment download process.

        Returns
        -------
        dict
            Dictionary containing download results:
            - downloaded: List of successfully downloaded file paths
            - skipped: List of skipped files with reasons
            - failed: List of failed downloads with error messages
            - total: Total number of attachments found
            - filtered_by_column: Number skipped by column filter
            - filtered_by_filename: Number skipped by filename filter
            - directory: The directory where files were saved
        """
        self._logger.info(
            f"Starting SmartSheet attachment download for sheet {self.sheet_id}"
        )

        if self.row_id:
            self._logger.info(f"Downloading attachments from row {self.row_id}")
        else:
            self._logger.info("Downloading all sheet attachments")

        # Log filter configuration
        if self.column_filter:
            filter_str = ", ".join([f"{k}='{v}'" for k, v in self.column_filter.items()])
            self._logger.info(f"Applying column filter: {filter_str}")

        if self.filename_filter:
            self._logger.info(f"Applying filename pattern: '{self.filename_filter}'")

        if self.attachment_filter:
            self._logger.info(f"Filtering extensions: {', '.join(self.attachment_filter)}")

        # Log filename column configuration
        if self.filename_columns:
            self._logger.info(
                f"Using columns for unique filenames: {', '.join(self.filename_columns)}"
            )
        else:
            self._logger.info("Using default columns: lead_id, Company Name")

        try:
            # Call the download_attachments method from SmartSheetClient
            results = await self.download_attachments(
                sheet_id=self.sheet_id,
                row_id=self.row_id,
                directory=self.directory,
                overwrite=self.overwrite,
                attachment_filter=self.attachment_filter,
                filename_columns=self.filename_columns,
                filename_filter=self.filename_filter,
                column_filter=self.column_filter,
                use_row_number=self.use_row_number
            )

            # Add directory to results
            results['directory'] = str(self.directory)

            # Log summary
            self._logger.info(
                f"Download complete: {len(results['filenames'])} downloaded, "
                f"{len(results['skipped'])} skipped, "
                f"{len(results['failed'])} failed out of {results['total']} total attachments"
            )

            self.add_metric(
                "smartsheet_attachments_downloaded", len(results['filenames'])
            )

            # Log filter statistics
            if results.get('filtered_by_column', 0) > 0:
                self._logger.info(
                    f"Filtered by column criteria: {results['filtered_by_column']} attachments"
                )

            if results.get('filtered_by_filename', 0) > 0:
                self._logger.info(
                    f"Filtered by filename pattern: {results['filtered_by_filename']} attachments"
                )

            # Log downloaded files (show first 10)
            file_list = results.get('filenames', [])
            self.add_metric("smartsheet_downloaded_files", file_list)

            if results['filenames']:
                self._logger.notice("Successfully downloaded files:")
                display_count = min(10, len(results['filenames']))
                for file_path in results['filenames'][:display_count]:
                    filename = Path(file_path).name
                    self._logger.notice(f"  - {filename}")
                if len(results['filenames']) > 10:
                    self._logger.notice(f"  ... and {len(results['filenames']) - 10} more files")

            # Log skipped files (show first 5)
            if results['skipped']:
                self._logger.info(f"Skipped {len(results['skipped'])} files:")
                display_count = min(5, len(results['skipped']))
                for item in results['skipped'][:display_count]:
                    self._logger.info(f"  - {item['file']}: {item['reason']}")
                if len(results['skipped']) > 5:
                    self._logger.info(f"  ... and {len(results['skipped']) - 5} more skipped")

            # Log failed files
            if results['failed']:
                self._logger.warning(f"Failed {len(results['failed'])} downloads:")
                for item in results['failed']:
                    self._logger.warning(f"  - {item['file']}: {item['error']}")

            # Store result for later access
            self._result = results
            return results

        except ComponentError:
            raise
        except Exception as err:
            raise ComponentError(
                f"DownloadFromSmartsheet: Unexpected error during execution: {err}"
            ) from err

    async def close(self, **kwargs) -> bool:
        """
        Clean up resources and close connections.
        """
        return True
