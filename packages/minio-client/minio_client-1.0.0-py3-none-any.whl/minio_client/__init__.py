"""
MinIO client factory
https://docs.min.io/docs/python-client-api-reference
https://github.com/minio/minio-py/tree/release/examples
"""

import json
import logging

from func_timeout import FunctionTimedOut, func_set_timeout  # type: ignore
from minio import Minio
from minio.credentials import MinioClientConfigProvider
from minio.error import S3Error
from urllib3.exceptions import RequestError


log = logging.getLogger(__name__)


LOCAL_SERVER_ALIAS = 'local_tmp'


class MinioClientEndpointConfigProvider(MinioClientConfigProvider):
    """Too bad the original provider doesn't handle this."""

    @property
    def endpoint(self) -> tuple[bool, str]:
        """Retrieve endpoint value from MinIO client configuration file."""
        try:
            with open(self._filename, encoding="utf-8") as conf_file:
                config = json.load(conf_file)
            aliases = config.get("hosts") or config.get("aliases")
            if not aliases:
                raise ValueError(f"invalid configuration in file {self._filename}")
            creds = aliases.get(self._alias)
            if not creds:
                raise ValueError(f"alias {self._alias} not found in MinIO client configuration file {self._filename}")
            protocol, endpoint = creds.get("url").split('://')
            return protocol == 'https', endpoint
        except OSError as exc:
            raise ValueError(f"error in reading file {self._filename}") from exc

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def alias(self) -> str:
        return self._alias


def get_client(alias: str = LOCAL_SERVER_ALIAS, test_server: bool = True) -> Minio | None:
    """MinIO client factory"""
    try:
        provider = MinioClientEndpointConfigProvider(alias=alias)
        secure, endpoint = provider.endpoint
    except ValueError as e:
        log.error(e)
        return None

    log.debug(f"MinIO: filename {provider.filename}; alias {provider.alias}; secure {secure}; endpoint {endpoint}")
    client = Minio(
        endpoint,
        secure=secure,
        credentials=provider,
    )

    if test_server:
        local_client = client if alias == LOCAL_SERVER_ALIAS else get_client(test_server=False)
        if not local_client:
            return None
        attempts = 10
        while attempts > 0:
            # The first attempt may trigger launchd to start minio, but the client connection will hang.
            # Keep trying with new connections until the service is running.
            try:
                if not _test_server(local_client):
                    return None
                break
            except FunctionTimedOut:
                log.warning('MinIO connection timed out')
            attempts -= 1
        if attempts == 0:
            return None

    return client


@func_set_timeout(3)  # type: ignore[untyped-decorator]
def _test_server(local_client: Minio) -> bool:  # type: ignore[misc]
    """True if the server responds."""
    try:
        local_client.bucket_exists('test')
    except RequestError:
        # This takes longer to throw than the timeout, so we never get here.
        log.error('MinIO connection failed')
        return False
    return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    client: Minio | None = None
    try:
        client = get_client()
        print("client:", client)
        if client:
            print("asiatrip:", client.bucket_exists("asiatrip"))
            print("bucket1:", client.bucket_exists("bucket1"))
    except S3Error as e:
        print("error occurred.", e)

    if client and client.bucket_exists("bucket1"):
        res = client.fget_object("bucket1", "bookmarks.html", '/tmp/test.html')
        print()
        print('res', type(res), res)
        print(res.size)
        print(res.etag)
        print(res.last_modified)
        print(res.content_type)
        try:
            print()
            with client.get_object("bucket1", "bookmarks.html") as res:
                print('response1', type(res), res)
                print(res.headers)
                print(res.headers['ETag'])
        finally:
            res.release_conn()
