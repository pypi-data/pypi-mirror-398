import contextlib
import dataclasses
import re
from collections.abc import Generator, Iterator
from typing import Any

import docker
import docker.errors
import docker.models.containers
import docker.models.images
import requests.exceptions

from iker.common.utils import logger
from iker.common.utils.strutils import parse_int_or, trim_to_empty

__all__ = [
    "ImageName",
    "docker_create_client",
    "docker_build_image",
    "docker_get_image",
    "docker_pull_image",
    "docker_fetch_image",
    "docker_run_detached",
]


@dataclasses.dataclass
class ImageName(object):
    registry_host: str | None
    registry_port: int | None
    components: list[str]
    tag: str | None

    @property
    def registry(self) -> str:
        if self.registry_host is None and self.registry_port is None:
            return ""
        if self.registry_port is None:
            return self.registry_host
        return f"{self.registry_host}:{self.registry_port}"

    @property
    def repository(self) -> str:
        return "/".join(self.components)

    @staticmethod
    def parse(s: str):

        # Registry absent version
        matcher = re.compile(
            r"^(?P<components>[a-z0-9]+((__?|-+)[a-z0-9]+)*(/[a-z0-9]+((__?|-+)[a-z0-9]+)*)*)(:(?P<tag>\w[\w.-]{0,127}))?$")
        match = matcher.match(s)
        if match:
            return ImageName(registry_host=None,
                             registry_port=None,
                             components=trim_to_empty(match.group("components")).split("/"),
                             tag=match.group("tag"))

        # Registry present version
        matcher = re.compile(
            r"^((?P<host>[a-zA-Z0-9.-]+)(:(?P<port>\d+))?/)?(?P<components>[a-z0-9]+((__?|-+)[a-z0-9]+)*(/[a-z0-9]+((__?|-+)[a-z0-9]+)*)*)(:(?P<tag>\w[\w.-]{0,127}))?$")
        match = matcher.match(s)
        if match:
            return ImageName(registry_host=match.group("host"),
                             registry_port=parse_int_or(match.group("port"), None),
                             components=trim_to_empty(match.group("components")).split("/"),
                             tag=match.group("tag"))

        return None


def docker_create_client(
    registry: str,
    username: str,
    password: str,
) -> contextlib.AbstractContextManager[docker.DockerClient]:
    try:
        client = docker.DockerClient()
        client.login(registry=registry, username=username, password=password, reauth=True)
        return contextlib.closing(client)
    except docker.errors.APIError:
        logger.exception("Failed to login Docker server <%s>", registry)
        raise


def docker_build_image(
    client: docker.DockerClient,
    tag: str,
    path: str,
    dockerfile: str,
    build_args: dict[str, str],
) -> tuple[docker.models.images.Image, Iterator[dict[str, str]]]:
    try:
        return client.images.build(tag=tag,
                                   path=path,
                                   dockerfile=dockerfile,
                                   buildargs=build_args,
                                   rm=True,
                                   forcerm=True,
                                   nocache=True)

    except docker.errors.BuildError:
        logger.exception("Failed to build image <%s>", tag)
        raise
    except docker.errors.APIError:
        logger.exception("Docker server returns an error while building image <%s>", tag)
        raise
    except Exception:
        logger.exception("Unexpected error occurred while building image <%s>", tag)
        raise


def docker_get_image(
    client: docker.DockerClient,
    image: str,
) -> docker.models.images.Image:
    try:
        return client.images.get(image)
    except docker.errors.ImageNotFound:
        logger.exception("Image <%s> is not found from local repository", image)
        raise
    except docker.errors.APIError:
        logger.exception("Docker server returns an error while getting image <%s>", image)
        raise
    except Exception:
        logger.exception("Unexpected error occurred while getting image <%s>", image)
        raise


def docker_pull_image(
    client: docker.DockerClient,
    image: str,
    fallback_local: bool = False,
) -> docker.models.images.Image:
    try:
        return client.images.pull(image)
    except docker.errors.ImageNotFound:
        if not fallback_local:
            logger.exception("Image <%s> is not found from remote repository", image)
            raise
        logger.warning("Image <%s> is not found from remote repository, try local repository instead", image)
    except docker.errors.APIError:
        if not fallback_local:
            logger.exception("Docker server returns an error while pulling image <%s>", image)
            raise
        logger.warning("Docker server returns an error while pulling image <%s>, try local repository instead", image)
    except Exception:
        logger.exception("Unexpected error occurred while pulling image <%s>", image)
        raise

    return docker_get_image(client, image)


def docker_fetch_image(
    client: docker.DockerClient,
    image: str,
    force_pull: bool = False,
) -> docker.models.images.Image:
    if force_pull:
        return docker_pull_image(client, image, fallback_local=True)
    else:
        try:
            return docker_get_image(client, image)
        except Exception:
            return docker_pull_image(client, image, fallback_local=False)


def docker_run_detached(
    client: docker.DockerClient,
    image: str,
    name: str,
    command: str | list[str],
    volumes: dict[str, dict[str, str]],
    environment: dict[str, str],
    extra_hosts: dict[str, str],
    timeout: int,
    **kwargs,
) -> tuple[dict[str, Any], Any]:
    @contextlib.contextmanager
    def managed_docker_run(
        client: docker.DockerClient,
        **kwargs,
    ) -> Generator[docker.models.containers.Container, None, None]:
        container_model = None
        try:
            container_model = client.containers.run(**kwargs)
            yield container_model
        except docker.errors.DockerException:
            raise
        finally:
            if container_model is not None:
                try:
                    if container_model.status != "exited":
                        try:
                            container_model.stop()
                        except docker.errors.DockerException:
                            pass
                    container_model.wait()
                    try:
                        container_model.remove()
                    except docker.errors.DockerException:
                        pass
                except Exception:
                    raise

    try:
        run_args = kwargs.copy()
        run_args.update(dict(image=image,
                             name=name,
                             command=command,
                             volumes=volumes,
                             environment=environment,
                             extra_hosts=extra_hosts,
                             detach=True))

        with managed_docker_run(client, **run_args) as container_model:
            result = container_model.wait(timeout=timeout)
            logs = container_model.logs()

            return result, logs

    except requests.exceptions.ReadTimeout:
        logger.exception("Running container <%s> of image <%s> exceed the timeout", name, image)
        raise
    except docker.errors.ImageNotFound:
        logger.exception("Image <%s> is not found", image)
        raise
    except docker.errors.ContainerError:
        logger.exception("Failed to run container <%s> of image <%s>", name, image)
        raise
    except docker.errors.APIError:
        logger.exception("Docker server returns an error while running container <%s> of image <%s>", name, image)
        raise
    except Exception:
        logger.exception("Unexpected error occurred while running container <%s> of image <%s>", image)
        raise
