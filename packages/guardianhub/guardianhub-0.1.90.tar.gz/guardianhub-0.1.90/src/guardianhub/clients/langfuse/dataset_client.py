"""Langfuse dataset management client.

This module provides a client for managing datasets in Langfuse.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from langfuse import Langfuse
from langfuse._client.datasets import DatasetClient as LangfuseDatasetClient
from langfuse.model import Dataset, DatasetItem, DatasetRun

from guardianhub import get_logger
from .manager import LangfuseManager

LOGGER = get_logger(__name__)


class DatasetClient:
    """Client for Langfuse dataset management."""

    def __init__(
        self,
        client: Optional[Langfuse] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        **kwargs
    ):
        """Initialize the DatasetClient.
        
        Args:
            client: Optional Langfuse client instance. If not provided, will use LangfuseManager.
            public_key: Langfuse public key. If not provided, will use LANGFUSE_PUBLIC_KEY from environment.
            secret_key: Langfuse secret key. If not provided, will use LANGFUSE_SECRET_KEY from environment.
            host: Langfuse host URL. If not provided, will use LANGFUSE_HOST from environment or default.
            **kwargs: Additional arguments to pass to Langfuse client initialization.
        """
        if client is not None:
            self._client = client
        else:
            self._client = LangfuseManager.get_instance(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
                **kwargs
            )

    def create_dataset(self, name: str) -> Dataset:
        """Create a new dataset.
        
        Args:
            name: Name of the dataset to create.
            
        Returns:
            The created Dataset object.
        """
        return self._client.create_dataset(name=name)

    def get_dataset(self, name: str) -> LangfuseDatasetClient:
        """Get a dataset by name.
        
        Args:
            name: Name of the dataset to retrieve.
            
        Returns:
            The Dataset object if found, None otherwise.
            
        Raises:
            ValueError: If the Langfuse client is not initialized.
        """
        if self._client is None:
            raise ValueError("Langfuse client is not initialized")
        return self._client.get_dataset(name=name)

    def list_datasets(self) -> List[Dataset]:
        """List all datasets.
        
        Returns:
            List of Dataset objects.
            
        Raises:
            ValueError: If the Langfuse client is not initialized.
        """
        if self._client is None:
            raise ValueError("Langfuse client is not initialized")
        return self._client.list_datasets()

    def create_dataset_item(
        self,
        dataset_name: str,
        input: Union[Dict[str, Any], List[Dict[str, Any]]],
        expected_output: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        **kwargs
    ) -> DatasetItem:
        """Create a new item in a dataset.
        
        Args:
            dataset_name: Name of the dataset to add the item to.
            input: Input data for the dataset item.
            expected_output: Expected output for the dataset item.
            **kwargs: Additional arguments for the dataset item.
            
        Returns:
            The created DatasetItem object.
        """
        return self._client.create_dataset_item(
            dataset_name=dataset_name,
            input=input,
            expected_output=expected_output,
            **kwargs
        )

    def get_dataset_items(self, dataset_name: str) -> List[DatasetItem]:
        """Get all items in a dataset.
        
        Args:
            dataset_name: Name of the dataset.
            
        Returns:
            List of DatasetItem objects.
        """
        return self._client.get_dataset_items(dataset_name=dataset_name)

    def create_dataset_run(
        self,
        dataset_name: str,
        run_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DatasetRun:
        """Create a new dataset run.
        
        Args:
            dataset_name: Name of the dataset.
            run_name: Name for the run.
            metadata: Optional metadata for the run.
            
        Returns:
            The created DatasetRun object.
        """
        return self._client.create_dataset_run(
            dataset_name=dataset_name,
            run_name=run_name,
            metadata=metadata or {}
        )

    def get_dataset_run(self, run_id: str) -> Optional[DatasetRun]:
        """Get a dataset run by ID.
        
        Args:
            run_id: ID of the run to retrieve.
            
        Returns:
            The DatasetRun object if found, None otherwise.
        """
        return self._client.get_dataset_run(id=run_id)
