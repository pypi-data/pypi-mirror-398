import unittest
import unittest.mock

import ddt
import docker.errors
import docker.models.containers
import docker.models.images
import requests.exceptions

from iker.common.utils.dockerutils import *
from iker.common.utils.testutils import return_callee
from iker_tests.docker_fixtures import MockedDockerContainer, MockedDockerImage


@ddt.ddt
class DockerUtilsTest(unittest.TestCase):
    data_image_name = [
        (
            "ubuntu",
            ImageName(None, None, ["ubuntu"], None),
            "",
            "ubuntu",
        ),
        (
            "ubuntu:latest",
            ImageName(None, None, ["ubuntu"], "latest"),
            "",
            "ubuntu",
        ),
        (
            "ubuntu:22.04",
            ImageName(None, None, ["ubuntu"], "22.04"),
            "",
            "ubuntu",
        ),
        (
            "canonical/ubuntu",
            ImageName(None, None, ["canonical", "ubuntu"], None),
            "",
            "canonical/ubuntu",
        ),
        (
            "canonical/ubuntu:latest",
            ImageName(None, None, ["canonical", "ubuntu"], "latest"),
            "",
            "canonical/ubuntu",
        ),
        (
            "canonical/ubuntu:22.04",
            ImageName(None, None, ["canonical", "ubuntu"], "22.04"),
            "",
            "canonical/ubuntu",
        ),
        (
            "hub.docker.com/canonical/ubuntu",
            ImageName("hub.docker.com", None, ["canonical", "ubuntu"], None),
            "hub.docker.com",
            "canonical/ubuntu",
        ),
        (
            "hub.docker.com/canonical/ubuntu:latest",
            ImageName("hub.docker.com", None, ["canonical", "ubuntu"], "latest"),
            "hub.docker.com",
            "canonical/ubuntu",
        ),
        (
            "hub.docker.com/canonical/ubuntu:22.04",
            ImageName("hub.docker.com", None, ["canonical", "ubuntu"], "22.04"),
            "hub.docker.com",
            "canonical/ubuntu",
        ),
        (
            "hub.docker.com:8080/canonical/ubuntu",
            ImageName("hub.docker.com", 8080, ["canonical", "ubuntu"], None),
            "hub.docker.com:8080",
            "canonical/ubuntu",
        ),
        (
            "hub.docker.com:8080/canonical/ubuntu:latest",
            ImageName("hub.docker.com", 8080, ["canonical", "ubuntu"], "latest"),
            "hub.docker.com:8080",
            "canonical/ubuntu",
        ),
        (
            "hub.docker.com:8080/canonical/ubuntu:22.04",
            ImageName("hub.docker.com", 8080, ["canonical", "ubuntu"], "22.04"),
            "hub.docker.com:8080",
            "canonical/ubuntu",
        ),
        (
            "hub.docker.com:8080/ubuntu",
            ImageName("hub.docker.com", 8080, ["ubuntu"], None),
            "hub.docker.com:8080",
            "ubuntu",
        ),
        (
            "hub.docker.com:8080/ubuntu:latest",
            ImageName("hub.docker.com", 8080, ["ubuntu"], "latest"),
            "hub.docker.com:8080",
            "ubuntu",
        ),
        (
            "hub.docker.com:8080/ubuntu:22.04",
            ImageName("hub.docker.com", 8080, ["ubuntu"], "22.04"),
            "hub.docker.com:8080",
            "ubuntu",
        ),
        (
            "hub.docker.com:8080/docker-hub/canonical/ubuntu",
            ImageName("hub.docker.com", 8080, ["docker-hub", "canonical", "ubuntu"], None),
            "hub.docker.com:8080",
            "docker-hub/canonical/ubuntu",
        ),
        (
            "hub.docker.com:8080/docker-hub/canonical/ubuntu:latest",
            ImageName("hub.docker.com", 8080, ["docker-hub", "canonical", "ubuntu"], "latest"),
            "hub.docker.com:8080",
            "docker-hub/canonical/ubuntu",
        ),
        (
            "hub.docker.com:8080/docker-hub/canonical/ubuntu:22.04",
            ImageName("hub.docker.com", 8080, ["docker-hub", "canonical", "ubuntu"], "22.04"),
            "hub.docker.com:8080",
            "docker-hub/canonical/ubuntu",
        ),
    ]

    @ddt.idata(data_image_name)
    @ddt.unpack
    def test_image_name(self, image_name_str, image_name, registry, repository):
        actual = ImageName.parse(image_name_str)

        self.assertEqual(image_name.registry_host, actual.registry_host)
        self.assertEqual(image_name.registry_port, actual.registry_port)
        self.assertEqual(image_name.components, actual.components)
        self.assertEqual(image_name.tag, actual.tag)
        self.assertEqual(image_name.registry, actual.registry)
        self.assertEqual(image_name.repository, actual.repository)

        self.assertEqual(registry, actual.registry)
        self.assertEqual(repository, actual.repository)

    data_image_name__bad_names = [
        ("Ubuntu",),
        ("UBUNTU",),
        ("ubuntu.",),
        ("ubuntu__",),
        ("ubuntu-",),
        ("ubuntu..ubuntu",),
        ("ubuntu___ubuntu",),
        ("ubuntu._ubuntu",),
        ("ubuntu//ubuntu",),
        ("underscore_hostname.dummy.io:12345/ubuntu",),
        ("hostname.dummy.io:bad_port/ubuntu",),
        (
            "ubuntu:tag_is_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_too_long",
        ),
    ]

    @ddt.idata(data_image_name__bad_names)
    @ddt.unpack
    def test_image_name__bad_names(self, image_name_str):
        self.assertIsNone(ImageName.parse(image_name_str))

    def test_docker_create_client(self):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            with docker_create_client("dummy-registry", "dummy_username", "dummy_password"):
                pass

            mock_docker_client.return_value.login.assert_called_with(registry="dummy-registry",
                                                                     username="dummy_username",
                                                                     password="dummy_password",
                                                                     reauth=True)

    def test_docker_create_client__with_exception(self):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_client.return_value.login.side_effect = docker.errors.APIError("")

            with self.assertRaises(docker.errors.APIError):
                with docker_create_client("dummy-registry", "dummy_username", "dummy_password"):
                    pass

            mock_docker_client.return_value.login.assert_called_with(registry="dummy-registry",
                                                                     username="dummy_username",
                                                                     password="dummy_password",
                                                                     reauth=True)

    def test_docker_build_image(self):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_image = MockedDockerImage("dummy_image",
                                                  tags_callee=return_callee("dummy_tags"),
                                                  labels_callee=return_callee("dummy_labels"))
            mock_docker_client.return_value.images.build.return_value = (
                mock_docker_image,
                [{"dummy-log-key": "dummy-log-value"}],
            )

            image_model, build_logs = docker_build_image(mock_docker_client.return_value,
                                                         "dummy_tag",
                                                         "dummy_path",
                                                         "dummy_dockerfile",
                                                         {"dummy_arg": "dummy_value"})

            self.assertEqual(image_model.id, "dummy_image")
            self.assertEqual(image_model.tags, "dummy_tags")
            self.assertEqual(image_model.labels, "dummy_labels")
            self.assertEqual(build_logs, [{"dummy-log-key": "dummy-log-value"}])

            mock_docker_client.return_value.images.build.assert_called_with(tag="dummy_tag",
                                                                            path="dummy_path",
                                                                            dockerfile="dummy_dockerfile",
                                                                            buildargs={"dummy_arg": "dummy_value"},
                                                                            rm=True,
                                                                            forcerm=True,
                                                                            nocache=True)

    data_docker_build_image__with_exception = [
        (docker.errors.BuildError("dummy reason", iter([{"dummy-log-key": "dummy-log-value"}])),),
        (docker.errors.APIError("dummy message"),),
        (Exception(),),
    ]

    @ddt.idata(data_docker_build_image__with_exception)
    @ddt.unpack
    def test_docker_build_image__with_exception(self, exception):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_client.return_value.images.build.side_effect = exception

            with self.assertRaises(type(exception)):
                docker_build_image(mock_docker_client.return_value,
                                   "dummy_tag",
                                   "dummy_path",
                                   "dummy_dockerfile",
                                   {"dummy_arg": "dummy_value"})

            mock_docker_client.return_value.images.build.assert_called_with(tag="dummy_tag",
                                                                            path="dummy_path",
                                                                            dockerfile="dummy_dockerfile",
                                                                            buildargs={"dummy_arg": "dummy_value"},
                                                                            rm=True,
                                                                            forcerm=True,
                                                                            nocache=True)

    def test_docker_get_image(self):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_image = MockedDockerImage("dummy_image",
                                                  tags_callee=return_callee("dummy_tags"),
                                                  labels_callee=return_callee("dummy_labels"))
            mock_docker_client.return_value.images.get.return_value = mock_docker_image

            image_model = docker_get_image(mock_docker_client.return_value, "dummy_image")

            self.assertEqual(image_model.id, "dummy_image")
            self.assertEqual(image_model.tags, "dummy_tags")
            self.assertEqual(image_model.labels, "dummy_labels")

            mock_docker_client.return_value.images.get.assert_called_with("dummy_image")

    data_docker_get_image__with_exception = [
        (docker.errors.ImageNotFound("dummy message"),),
        (docker.errors.APIError("dummy message"),),
        (Exception(),),
    ]

    @ddt.idata(data_docker_get_image__with_exception)
    @ddt.unpack
    def test_docker_get_image__with_exception(self, exception):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_client.return_value.images.get.side_effect = exception

            with self.assertRaises(type(exception)):
                docker_get_image(mock_docker_client.return_value, "dummy_image")

            mock_docker_client.return_value.images.get.assert_called_with("dummy_image")

    def test_docker_pull_image(self):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_get_docker_image = MockedDockerImage("dummy_get_image",
                                                      tags_callee=return_callee("dummy_get_tags"),
                                                      labels_callee=return_callee("dummy_get_labels"))
            mock_docker_client.return_value.images.get.return_value = mock_get_docker_image
            mock_pull_docker_image = MockedDockerImage("dummy_pull_image",
                                                       tags_callee=return_callee("dummy_pull_tags"),
                                                       labels_callee=return_callee("dummy_pull_labels"))
            mock_docker_client.return_value.images.pull.return_value = mock_pull_docker_image

            image_model = docker_pull_image(mock_docker_client.return_value, "dummy_image", fallback_local=True)

            self.assertEqual(image_model.id, "dummy_pull_image")
            self.assertEqual(image_model.tags, "dummy_pull_tags")
            self.assertEqual(image_model.labels, "dummy_pull_labels")

            mock_docker_client.return_value.images.get.assert_not_called()
            mock_docker_client.return_value.images.pull.assert_called_with("dummy_image")

    def test_docker_pull_image__fallback(self):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_image = MockedDockerImage("dummy_get_image",
                                                  tags_callee=return_callee("dummy_get_tags"),
                                                  labels_callee=return_callee("dummy_get_labels"))
            mock_docker_client.return_value.images.get.return_value = mock_docker_image
            mock_docker_client.return_value.images.pull.side_effect = docker.errors.APIError("dummy message")

            image_model = docker_pull_image(mock_docker_client.return_value, "dummy_image", fallback_local=True)

            self.assertEqual(image_model.id, "dummy_get_image")
            self.assertEqual(image_model.tags, "dummy_get_tags")
            self.assertEqual(image_model.labels, "dummy_get_labels")

            mock_docker_client.return_value.images.get.assert_called_with("dummy_image")
            mock_docker_client.return_value.images.pull.assert_called_with("dummy_image")

    data_docker_pull_image__with_exception = [
        (docker.errors.ImageNotFound("dummy message"),),
        (docker.errors.APIError("dummy message"),),
        (Exception(),),
    ]

    @ddt.idata(data_docker_pull_image__with_exception)
    @ddt.unpack
    def test_docker_pull_image__with_exception(self, exception):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_client.return_value.images.get.side_effect = docker.errors.APIError("dummy message")

            mock_docker_client.return_value.images.pull.side_effect = exception

            with self.assertRaises(type(exception)):
                docker_pull_image(mock_docker_client.return_value, "dummy_image", fallback_local=False)

            mock_docker_client.return_value.images.get.assert_not_called()
            mock_docker_client.return_value.images.pull.assert_called_with("dummy_image")

    data_docker_pull_image__fallback_with_exception = [
        (docker.errors.ImageNotFound("dummy message"),),
        (docker.errors.APIError("dummy message"),),
        (Exception(),),
    ]

    @ddt.idata(data_docker_pull_image__fallback_with_exception)
    @ddt.unpack
    def test_docker_pull_image__fallback_with_exception(self, exception):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_client.return_value.images.get.side_effect = exception
            mock_docker_client.return_value.images.pull.side_effect = docker.errors.APIError("dummy message")

            with self.assertRaises(type(exception)):
                docker_pull_image(mock_docker_client.return_value, "dummy_image", fallback_local=True)

            mock_docker_client.return_value.images.get.assert_called_with("dummy_image")
            mock_docker_client.return_value.images.pull.assert_called_with("dummy_image")

    def test_docker_fetch_image(self):
        with (
            unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client,
            unittest.mock.patch("iker.common.utils.dockerutils.docker_get_image") as mock_docker_get_image,
            unittest.mock.patch("iker.common.utils.dockerutils.docker_pull_image") as mock_docker_pull_image,
        ):
            docker_fetch_image(mock_docker_client.return_value, "dummy_image")

            mock_docker_get_image.assert_called_with(mock_docker_client.return_value, "dummy_image")
            mock_docker_pull_image.assert_not_called()

    def test_docker_fetch_image__force_pull(self):
        with (
            unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client,
            unittest.mock.patch("iker.common.utils.dockerutils.docker_get_image") as mock_docker_get_image,
            unittest.mock.patch("iker.common.utils.dockerutils.docker_pull_image") as mock_docker_pull_image,
        ):
            docker_fetch_image(mock_docker_client.return_value, "dummy_image", force_pull=True)

            mock_docker_get_image.assert_not_called()
            mock_docker_pull_image.assert_called_with(mock_docker_client.return_value,
                                                      "dummy_image",
                                                      fallback_local=True)

    def test_docker_fetch_image__get_image_failed(self):
        with (
            unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client,
            unittest.mock.patch("iker.common.utils.dockerutils.docker_get_image") as mock_docker_get_image,
            unittest.mock.patch("iker.common.utils.dockerutils.docker_pull_image") as mock_docker_pull_image,
        ):
            mock_docker_get_image.side_effect = docker.errors.APIError("dummy message")

            docker_fetch_image(mock_docker_client.return_value, "dummy_image")

            mock_docker_get_image.assert_called_with(mock_docker_client.return_value, "dummy_image")
            mock_docker_pull_image.assert_called_with(mock_docker_client.return_value,
                                                      "dummy_image",
                                                      fallback_local=False)

    def test_docker_run_detached(self):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            mock_docker_container = MockedDockerContainer("dummy_container",
                                                          status_callee=return_callee("dummy_status"),
                                                          wait_callee=return_callee({"dummy_key": "dummy_value"}),
                                                          logs_callee=return_callee("dummy log"),
                                                          stop_callee=return_callee(),
                                                          remove_callee=return_callee())
            mock_docker_client.return_value.containers.run.return_value = mock_docker_container

            result, log = docker_run_detached(mock_docker_client.return_value,
                                              "dummy_image",
                                              "dummy_container",
                                              "dummy_command",
                                              {"/dummy/src/path": {"bind": "/dummy/dst/path", "mode": "rw"}},
                                              {"DUMMY_ENV_KEY": "DUMMY_ENV_VALUE"},
                                              {"dummy.ip.address": "127.0.0.1"},
                                              1000,
                                              dummy_kwarg="dummy_value")

            self.assertEqual(result, {"dummy_key": "dummy_value"})
            self.assertEqual(log, "dummy log")

            mock_docker_client.return_value.containers.run.assert_called_with(
                image="dummy_image",
                name="dummy_container",
                command="dummy_command",
                volumes={"/dummy/src/path": {"bind": "/dummy/dst/path", "mode": "rw"}},
                environment={"DUMMY_ENV_KEY": "DUMMY_ENV_VALUE"},
                extra_hosts={"dummy.ip.address": "127.0.0.1"},
                detach=True,
                dummy_kwarg="dummy_value",
            )
            mock_docker_container.status_callee.assert_called_once()
            mock_docker_container.wait_callee.assert_called_once_with()(timeout=1000)
            mock_docker_container.wait_callee.assert_called_once_with()()
            mock_docker_container.logs_callee.assert_called_once()
            mock_docker_container.stop_callee.assert_called_once()
            mock_docker_container.remove_callee.assert_called_once()

    data_docker_run_detached__with_exception_on_wait = [
        (requests.exceptions.ReadTimeout(),),
        (docker.errors.ImageNotFound("dummy message"),),
        (
            docker.errors.ContainerError("dummy container",
                                         "dummy exit status",
                                         "dummy command",
                                         "dummy image",
                                         "dummy stderr"),
        ),
        (docker.errors.APIError("dummy message"),),
        (Exception(),),
    ]

    @ddt.idata(data_docker_run_detached__with_exception_on_wait)
    @ddt.unpack
    def test_docker_run_detached__with_exception_on_wait(self, exception):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            def mock_containers_run_wait_valuer(*args, **kwargs):
                if kwargs == dict(timeout=1000):
                    raise exception

            mock_docker_container = MockedDockerContainer("dummy_container",
                                                          status_callee=return_callee("dummy_status"),
                                                          wait_callee=return_callee(mock_containers_run_wait_valuer),
                                                          logs_callee=return_callee("dummy log"),
                                                          stop_callee=return_callee(),
                                                          remove_callee=return_callee())
            mock_docker_client.return_value.containers.run.return_value = mock_docker_container

            with self.assertRaises(type(exception)):
                docker_run_detached(mock_docker_client.return_value,
                                    "dummy_image",
                                    "dummy_container",
                                    "dummy_command",
                                    {"/dummy/src/path": {"bind": "/dummy/dst/path", "mode": "rw"}},
                                    {"DUMMY_ENV_KEY": "DUMMY_ENV_VALUE"},
                                    {"dummy.ip.address": "127.0.0.1"},
                                    1000,
                                    dummy_kwarg="dummy_value")

            mock_docker_client.return_value.containers.run.assert_called_with(
                image="dummy_image",
                name="dummy_container",
                command="dummy_command",
                volumes={"/dummy/src/path": {"bind": "/dummy/dst/path", "mode": "rw"}},
                environment={"DUMMY_ENV_KEY": "DUMMY_ENV_VALUE"},
                extra_hosts={"dummy.ip.address": "127.0.0.1"},
                detach=True,
                dummy_kwarg="dummy_value",
            )
            mock_docker_container.status_callee.assert_called_once()
            mock_docker_container.wait_callee.assert_called_once_with()(timeout=1000)
            mock_docker_container.wait_callee.assert_called_once_with()()
            mock_docker_container.logs_callee.assert_not_called()
            mock_docker_container.stop_callee.assert_called_once()
            mock_docker_container.remove_callee.assert_called_once()

    data_docker_run_detached__with_exception_on_stop = [
        (docker.errors.ImageNotFound("dummy message"),),
        (
            docker.errors.ContainerError("dummy container",
                                         "dummy exit status",
                                         "dummy command",
                                         "dummy image",
                                         "dummy stderr"),
        ),
        (docker.errors.APIError("dummy message"),),
    ]

    @ddt.idata(data_docker_run_detached__with_exception_on_stop)
    @ddt.unpack
    def test_docker_run_detached__with_exception_on_stop(self, exception):
        with unittest.mock.patch("iker.common.utils.dockerutils.docker.DockerClient") as mock_docker_client:
            def mock_containers_run_stop_valuer(*args, **kwargs):
                raise exception

            mock_docker_container = MockedDockerContainer("dummy_container",
                                                          status_callee=return_callee("dummy_status"),
                                                          wait_callee=return_callee({"dummy_key": "dummy_value"}),
                                                          logs_callee=return_callee("dummy log"),
                                                          stop_callee=return_callee(mock_containers_run_stop_valuer),
                                                          remove_callee=return_callee())
            mock_docker_client.return_value.containers.run.return_value = mock_docker_container

            result, log = docker_run_detached(mock_docker_client.return_value,
                                              "dummy_image",
                                              "dummy_container",
                                              "dummy_command",
                                              {"/dummy/src/path": {"bind": "/dummy/dst/path", "mode": "rw"}},
                                              {"DUMMY_ENV_KEY": "DUMMY_ENV_VALUE"},
                                              {"dummy.ip.address": "127.0.0.1"},
                                              1000,
                                              dummy_kwarg="dummy_value")

            self.assertEqual(result, {"dummy_key": "dummy_value"})
            self.assertEqual(log, "dummy log")

            mock_docker_client.return_value.containers.run.assert_called_with(
                image="dummy_image",
                name="dummy_container",
                command="dummy_command",
                volumes={"/dummy/src/path": {"bind": "/dummy/dst/path", "mode": "rw"}},
                environment={"DUMMY_ENV_KEY": "DUMMY_ENV_VALUE"},
                extra_hosts={"dummy.ip.address": "127.0.0.1"},
                detach=True,
                dummy_kwarg="dummy_value",
            )
            mock_docker_container.status_callee.assert_called_once()
            mock_docker_container.wait_callee.assert_called_once_with()(timeout=1000)
            mock_docker_container.wait_callee.assert_called_once_with()()
            mock_docker_container.logs_callee.assert_called_once()
            mock_docker_container.stop_callee.assert_called_once()
            mock_docker_container.remove_callee.assert_called_once()
