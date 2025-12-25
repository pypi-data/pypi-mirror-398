from ..db.aws import S3Manager, S3WithMongo, S3
from .dockermongo import DockerMongoManager, MockDockerMongoManager
from .mockaws import MockS3Manager, MockS3WithMongo


class S3WithDockerMongoManager(S3Manager, DockerMongoManager):
    """Database manager for connecting to real AWS S3 and a MongoDB docker container. The registry and volume
    microservices need to be running."""

    def get_database(self) -> S3WithMongo:
        return S3WithMongo(config=self.config, managed=True)

    @classmethod
    def database_types(self) -> list[str]:
        return ['system|awss3', 'system|mongo']


class MockS3WithMockDockerMongoManager(MockS3Manager, MockDockerMongoManager):
    """
    Database manager for mocking AWS S3 buckets with moto. Mark test fixture data that is managed in S3 buckets with
    this database manager in unit test environments. Furthermore, connections to boto3/moto clients normally require
    access to the registry and volume microservices. This database manager mocks those connections. Mark
    component, volume, and filesystem test collections with this database manager to make them available in unit
    testing environments. This class is not designed to be subclassed.
    """

    def get_database(self) -> MockS3WithMongo:
        return MockS3WithMongo(config=self.config, managed=True)

    @classmethod
    def database_types(self) -> list[str]:
        return ['system|awss3', 'system|mongo']
