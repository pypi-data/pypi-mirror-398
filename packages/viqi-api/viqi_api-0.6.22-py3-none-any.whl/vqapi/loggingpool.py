# Written by gemini
import logging
import queue  # For queue.Empty exception
import time

from requests.adapters import HTTPAdapter
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.exceptions import EmptyPoolError, MaxRetryError, TimeoutError  # noqa
from urllib3.poolmanager import PoolManager

logger = logging.getLogger(__name__)


class LoggingHTTPConnectionPool(HTTPConnectionPool):
    def _get_conn(self, timeout=None):
        conn = None
        # logger.info("HTTP CONNECTION")
        try:
            # Condition for potential blocking:
            # self.block is True, the pool of available connections is empty,
            # and we are at max capacity for connections.
            will_block = (
                self.block
                and self.pool  # Check if pool exists
                and self.pool.empty()
                and self.num_connections >= self.pool.maxsize
            )

            if will_block:
                logger.warning(
                    "Pool for %s:%s is full (size %s/%s). Request will block waiting for a connection.",
                    self.host,
                    self.port,
                    self.num_connections,
                    self.pool.maxsize,
                )
                block_start_time = time.monotonic()

            conn = super()._get_conn(timeout=timeout)

            if will_block:
                block_duration = time.monotonic() - block_start_time
                logger.info(
                    "Request for %s:%s was blocked for %.4f s before acquiring connection.",
                    self.host,
                    self.port,
                    block_duration,
                )
            return conn
        except queue.Empty:  # This is the exception from pool.get() when it times out with block=True
            if self.block:  # Should always be true if we reach here due to pool.get timeout
                logger.error(
                    "Pool for %s:%s exhausted and blocking timed out. Pool size: %s/%s.",
                    self.host,
                    self.port,
                    self.num_connections,
                    self.pool.maxsize,
                )
            raise  # Re-raise the EmptyPoolError to be handled by urllib3/requests
        except Exception:
            # Handle other potential errors during _get_conn if necessary
            raise


class LoggingHTTPSConnectionPool(HTTPSConnectionPool):
    # Implement _get_conn similarly to LoggingHTTPConnectionPool
    def _get_conn(self, timeout=None):
        conn = None
        # logger.info("HTTPS CONNECTION")
        try:
            will_block = self.block and self.pool and self.pool.empty() and self.num_connections >= self.pool.maxsize
            if will_block:
                logger.warning(
                    "SSL Pool for %s:%s is full (size %s/%s). Request will block waiting for a connection.",
                    self.host,
                    self.port,
                    self.num_connections,
                    self.pool.maxsize,
                )
                block_start_time = time.monotonic()

            conn = super()._get_conn(timeout=timeout)

            if will_block:
                block_duration = time.monotonic() - block_start_time
                logger.info(
                    "SSL Request for %s:%s was blocked for %.4fs before acquiring connection.",
                    self.host,
                    self.port,
                    block_duration,
                )
            return conn
        except queue.Empty:
            if self.block:
                logger.error(
                    "SSL Pool for %s:%s exhausted and blocking timed out. Pool size: %s/%s.",
                    self.host,
                    self.port,
                    self.num_connections,
                    self.pool.maxsize,
                )
            raise
        except Exception:
            raise


class LoggingPoolManager(PoolManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override the default pool_classes_by_scheme to use your logging pools
        self.pool_classes_by_scheme = {
            "http": LoggingHTTPConnectionPool,
            "https": LoggingHTTPSConnectionPool,
        }


class LoggingHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        # Pass block=True or your desired config to LoggingPoolManager
        self.poolmanager = LoggingPoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,  # This is where pool_block from HTTPAdapter is used
            **pool_kwargs,
        )
