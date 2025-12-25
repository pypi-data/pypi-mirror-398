import docker
import docker.errors
import docker.models.containers
import docker.models.images
import docker.models.resource

from iker.common.utils.testutils import CalleeMock
from iker.common.utils.testutils import return_callee

__all__ = [
    "MockedDockerClient",
    "MockedDockerImage",
    "MockedDockerContainer",
]


class MockedDockerClient(docker.DockerClient):
    def __init__(self):
        # Do not call superclass init to avoid underlying API client being initialized
        pass

    def close(self):
        pass


class MockedDockerImage(docker.models.resource.Model):
    def __init__(
        self,
        model_id: str,
        *,
        tags_callee: CalleeMock = return_callee(),
        labels_callee: CalleeMock = return_callee(),
    ):
        super(MockedDockerImage, self).__init__({docker.models.resource.Model.id_attribute: model_id})
        self.tags_callee = tags_callee
        self.labels_callee = labels_callee

    @property
    def tags(self):
        return self.tags_callee()

    @property
    def labels(self):
        return self.labels_callee()


class MockedDockerContainer(docker.models.resource.Model):
    def __init__(
        self,
        model_id: str,
        *,
        status_callee: CalleeMock = return_callee(),
        wait_callee: CalleeMock = return_callee(),
        logs_callee: CalleeMock = return_callee(),
        stop_callee: CalleeMock = return_callee(),
        remove_callee: CalleeMock = return_callee(),
    ):
        super(MockedDockerContainer, self).__init__({docker.models.resource.Model.id_attribute: model_id})
        self.status_callee = status_callee
        self.wait_callee = wait_callee
        self.logs_callee = logs_callee
        self.stop_callee = stop_callee
        self.remove_callee = remove_callee

    @property
    def status(self):
        return self.status_callee()

    def wait(self, **kwargs):
        return self.wait_callee(**kwargs)

    def logs(self, **kwargs):
        return self.logs_callee(**kwargs)

    def stop(self, **kwargs):
        return self.stop_callee(**kwargs)

    def remove(self, **kwargs):
        return self.remove_callee(**kwargs)
