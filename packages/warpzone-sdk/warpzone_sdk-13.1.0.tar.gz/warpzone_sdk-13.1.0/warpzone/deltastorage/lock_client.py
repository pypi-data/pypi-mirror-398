import datetime as dt
import os
import time
from contextlib import contextmanager

from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.storage.blob import BlobClient, BlobLeaseClient

import warpzone as wz
from warpzone.monitor import logs

logger = logs.get_logger(__name__)

CONTAINER_NAME = "locks"

DEFAULT_WAIT_FOR_LOCK_TIMEOUT_SECONDS = 60
DEFAULT_SLEEP_BETWEEN_RETRIES_SECONDS = 2


class LockClient:
    def __init__(
        self,
        wz_blob_client: wz.WarpzoneBlobClient,
        lock_names: list[str],
        wait_for_lock_timeout_seconds: int = DEFAULT_WAIT_FOR_LOCK_TIMEOUT_SECONDS,
        sleep_between_retries_seconds: int = DEFAULT_SLEEP_BETWEEN_RETRIES_SECONDS,
    ):
        self.wz_blob_client = wz_blob_client
        self.blob_lock_clients = self._create_blob_lock_clients(lock_names)

        self.wait_for_lock_timeout_seconds = wait_for_lock_timeout_seconds
        self.sleep_between_retries_seconds = sleep_between_retries_seconds

    @classmethod
    def from_func_env_variables(
        cls,
        lock_names: list[str],
        wait_for_lock_timeout_seconds: int = DEFAULT_WAIT_FOR_LOCK_TIMEOUT_SECONDS,
        sleep_between_retries_seconds: int = DEFAULT_SLEEP_BETWEEN_RETRIES_SECONDS,
    ):
        data_store_name = os.environ["OPERATIONAL_DATA_STORAGE_ACCOUNT"]
        wz_blob_client = wz.WarpzoneBlobClient.from_resource_name(data_store_name)
        return cls(
            wz_blob_client,
            lock_names,
            wait_for_lock_timeout_seconds,
            sleep_between_retries_seconds,
        )

    def _create_blob_lock_clients(
        self, lock_names: list[str]
    ) -> list["BlobLockClient"]:
        """Create BlobLockClients for each lock name, based on the WarpzoneBlobClient.

        Args:
            lock_names (list[str]): Names of the locks to create BlobLeaseClients for.
        """
        blob_lock_clients = []
        for name in lock_names:
            blob_client = self.wz_blob_client._blob_service_client.get_blob_client(
                CONTAINER_NAME, name
            )
            blob_lock_client = BlobLockClient(blob_client)
            blob_lock_client.create_blob_if_not_exist()

            blob_lock_clients.append(blob_lock_client)

        return blob_lock_clients

    def break_expired_locks(self):
        """Break leases that have expired for all BlobLockClients
        in the blob_lock_clients attribute.
        """
        for blob_lock_client in self.blob_lock_clients:
            if blob_lock_client.is_expired():
                blob_lock_client.break_lock()

    @contextmanager
    def lock(self):
        """Context manager to acquire and release leases for given lock names.
        Args:
            lock_names (list[str]): Names of the locks to acquire locks for.

        Yields:
            LockClient: The LockClient instance with acquired locks.
        """
        self.break_expired_locks()

        try:
            self.acquire_locks_with_timeout()
            yield self
        finally:
            self.release_locks()

    def acquire_locks_with_timeout(self):
        """Try to acquire leases for all BlobLeaseClients
        in the lease_clients attribute within a timeout period.
        """
        start_time = time.time()
        while time.time() - start_time < self.wait_for_lock_timeout_seconds:
            try:
                finished = self.acquire_locks()
                if finished:
                    return
            except (ResourceExistsError, HttpResponseError) as e:
                # Error as some locks are already held by others.
                # Release all acquired leases, wait and try again until timed out.
                self.release_locks()
                logger.info(
                    f"Could not acquire all locks, retrying... Error: {e.error_code}"
                )
                time.sleep(self.sleep_between_retries_seconds)
        raise TimeoutError("Could not acquire all locks within the timeout period.")

    def acquire_locks(self) -> bool:
        """Try to acquire leases for all BlobLeaseClients
        in the lease_clients attribute.
        """
        # Sort on lock names to avoid deadlocks when multiple LockClients
        # are used concurrently
        for blob_lock_client in sorted(self.blob_lock_clients, key=lambda x: x.name):
            blob_lock_client.acquire_lock()
        return True

    def release_locks(self):
        """Try to release all leases held by the BlobLeaseClients
        in the lease_clients attribute.
        """
        for blob_lock_client in self.blob_lock_clients:
            blob_lock_client.release_lock()


class BlobLockClient:
    """Combine BlobClient and BlobLeaseClient to implement locking functionality."""

    LOCK_DURATION_SECONDS = (
        10 * 60
    )  # Seconds. Needs to match function timeout settings.
    LOCKED_TIME_UTC_COLUMN_NAME = "locked_time_utc"

    # _LEASE_DURATION is used to specify infinite lease duration for BlobLeaseClient
    _INFINITE_LEASE_DURATION = -1

    def __init__(self, blob_client: BlobClient):
        self.blob_client = blob_client
        self.lease_client = BlobLeaseClient(self.blob_client)
        self.name = blob_client.blob_name

    def is_expired(self) -> bool:
        """Check if the lease held by the BlobLeaseClient has expired.

        Returns:
            bool: True if the lease has expired,
            False if not expired, or if metadata does not yet exist.
        """
        properties = self.blob_client.get_blob_properties()
        locked_time_str = properties.metadata.get(
            self.LOCKED_TIME_UTC_COLUMN_NAME, None
        )
        locked_time_utc = dt.datetime.fromisoformat(locked_time_str)
        lease_duration = self.LOCK_DURATION_SECONDS
        expiration_time_utc = locked_time_utc + dt.timedelta(seconds=lease_duration)
        return dt.datetime.now(dt.timezone.utc) > expiration_time_utc

    def create_blob_if_not_exist(self) -> None:
        """Create blobs if they do not exist and add metadata:
        Set `locked_time_utc` to 1999-01-01, such that the lock will be expired.
        The blob does not contain any data, but the name is used for handling locks.
        """
        if not self.blob_client.exists():
            try:
                self.blob_client.upload_blob(
                    b"",
                    overwrite=True,
                    metadata={
                        self.LOCKED_TIME_UTC_COLUMN_NAME: dt.datetime(
                            1999, 1, 1, tzinfo=dt.timezone.utc
                        ).isoformat()
                    },
                )
            except HttpResponseError as e:
                if e.error_code == "LeaseIdMissing":
                    # Blob was created by another process in the meantime,
                    # which now has the lease. Ignore this error and continue
                    # using the existing blob.
                    return
                else:
                    # Re-raise unexpected errors
                    raise

    def acquire_lock(self) -> bool:
        """Try to acquire lease for the BlobLeaseClient.
        Before acquiring the lease, metadata is updated with the current time.
        This is done beforehand, such that the time the lease was acquired is updated
        before locking.

        Returns:
            bool: True if lease was acquired successfully, False otherwise.

        Raises:
            HttpResponseError: When updating metadata and blob is already leased.
            Exception: If lease acquisition fails.
        """
        logger.info(f"Try acquiring lease on: '{self.name}'")
        # Update metadata with current time before acquiring lease
        # This will fail if another process has already acquired the lease.
        self.blob_client.set_blob_metadata(
            {
                self.LOCKED_TIME_UTC_COLUMN_NAME: dt.datetime.now(
                    dt.timezone.utc
                ).isoformat()
            }
        )
        self.lease_client.acquire(lease_duration=self._INFINITE_LEASE_DURATION)
        logger.info(f"Lease acquired on: '{self.name}'")

    def release_lock(self):
        """Try to release lease held by the BlobLeaseClient.
        Log errors if release fails.
        """
        try:
            self.lease_client.release()
            logger.info(f"Lease released on: '{self.name}'")
        except (ResourceExistsError, ValueError):
            # ResourceExistsError: Lease is already released
            # ValueError: Lease ID is not set. Another process may
            # have acquired the lease, but not written lease ID yet.
            pass

    def break_lock(self):
        """Break the lease held by the BlobLeaseClient.
        Log errors if breaking fails.
        """
        try:
            self.lease_client.break_lease()
            logger.info(f"Lease broken on: '{self.name}'")
        except ResourceExistsError:
            pass  # Lease is already available
