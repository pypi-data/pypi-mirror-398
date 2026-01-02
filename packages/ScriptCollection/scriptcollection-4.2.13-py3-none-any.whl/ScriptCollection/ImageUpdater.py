from abc import abstractmethod
import json
import re
from urllib.parse import quote
import yaml
import requests
from packaging import version as ve
from packaging.version import Version
from .GeneralUtilities import GeneralUtilities,VersionEcholon


class ImageUpdaterHelper:

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_filter_for_major_and_minor_versions(versions: list[Version], major: int, minor: int) -> Version:
        return [v for v in versions if v.major == major and v.minor == minor]

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_filter_for_major_versions(versions: list[Version], major: int) -> Version:
        return [v for v in versions if v.major == major]

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_get_latest_patch_version(newer_versions: list[Version], current_version: Version) -> Version:
        candidates = ImageUpdaterHelper._internal_filter_for_major_and_minor_versions(newer_versions, current_version.major, current_version.minor)
        if len(candidates) == 0:
            return current_version
        result = ImageUpdaterHelper.get_latest_version(candidates)
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_get_latest_patch_or_latest_minor_version(newer_versions: list[Version], current_version: Version) -> Version:
        candidates = ImageUpdaterHelper._internal_filter_for_major_versions(newer_versions, current_version.major)
        if len(candidates) == 0:
            return current_version
        result = ImageUpdaterHelper.get_latest_version(candidates)
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_get_latest_patch_or_latest_minor_or_next_major_version(newer_versions: list[Version], current_version: Version) -> Version:
        candidates = ImageUpdaterHelper._internal_filter_for_major_versions(newer_versions, current_version.major+1)
        if 0 < len(candidates):
            result = ImageUpdaterHelper.get_latest_version(candidates)
            return result
        else:
            candidates = ImageUpdaterHelper._internal_filter_for_major_versions(newer_versions, current_version.major)
            if len(candidates) == 0:
                return current_version
            result = ImageUpdaterHelper.get_latest_version(candidates)
            return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def filter_considering_echolon(newer_versions: list[Version], current_version: Version, version_echolon: VersionEcholon) -> Version:
        if version_echolon == VersionEcholon.LatestPatch:
            return ImageUpdaterHelper._internal_get_latest_patch_version(newer_versions, current_version)
        elif version_echolon == VersionEcholon.LatestPatchOrLatestMinor:
            return ImageUpdaterHelper._internal_get_latest_patch_or_latest_minor_version(newer_versions, current_version)
        elif version_echolon == VersionEcholon.LatestPatchOrLatestMinorOrNextMajor:
            return ImageUpdaterHelper._internal_get_latest_patch_or_latest_minor_or_next_major_version(newer_versions, current_version)
        elif version_echolon == VersionEcholon.LatestVersion: 
            return ImageUpdaterHelper.get_latest_version(newer_versions)
        else:
            raise ValueError(f"Unknown version-echolon")

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_latest_version(versions: list[Version]) -> Version:
        result = max(versions)
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_latest_version_from_versiontrings(version_strings: list[str]) -> str:
        parsed = [ve.parse(v) for v in version_strings]
        result = max(parsed)
        return str(result)

    @staticmethod
    @GeneralUtilities.check_arguments
    def filter_for_newer_versions(comparison_version: Version, versions_to_filter: list[Version]) -> list[Version]:
        result = [v for v in versions_to_filter if comparison_version < v]
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_versions_in_docker_hub(image: str, search_string: str, filter_regex: str, maximal_amount_of_items_to_load: int = 250) -> list[Version]:#TODO add option to specify image source url
        if "/" not in image:
            image = f"library/{image}"
        response = requests.get(f"https://hub.docker.com/v2/repositories/{quote(image)}/tags?name={quote(search_string)}&ordering=last_updated&page=1&page_size={str(maximal_amount_of_items_to_load)}", timeout=20, headers={'Cache-Control': 'no-cache'})
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch data for image {image} from Docker Hub: {response.status_code}")
        response_text = response.text
        data = json.loads(response_text)
        tags: list[str] = [tag["name"] for tag in data["results"] if re.match(filter_regex, tag["name"])]
        versions = [tag.split("-")[0] for tag in tags]
        result = [ve.parse(v) for v in versions]
        return result


class ConcreteImageUpdater:

    @abstractmethod
    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        raise NotImplementedError


class ConcreteImageUpdaterForNginx(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["nginx"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "Nginx"


class ConcreteImageUpdaterForWordpress(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["wordpress"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "Wordpress"


class ConcreteImageUpdaterForGitLab(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}-ce.0"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["gitlab/gitlab-ce", "gitlab/gitlab-ee"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "GitLab"


class ConcreteImageUpdaterForRegistry(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["registry"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "Registry"


class ConcreteImageUpdaterForPrometheus(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["prom/prometheus"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "Prometheus"


class ConcreteImageUpdaterForPrometheusBlackboxExporter(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["prom/blackbox-exporter"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "PrometheusBlackboxExporter"


class ConcreteImageUpdaterForPrometheusNginxExporter(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["prom/nginx-prometheus-exporter"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "NginxPrometheusExporter"


class ConcreteImageUpdaterForPrometheusNodeExporter(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["prom/node-exporter"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "PrometheusNodeExporter"


class ConcreteImageUpdaterForKeycloak(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return []  # TODO

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "KeyCloak"


class ConcreteImageUpdaterForMariaDB(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["mariadb"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "MariaDB"


class ConcreteImageUpdaterForPostgreSQL(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["postgres"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag+".0")

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "PostgreSQL"


class ConcreteImageUpdaterForAdminer(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["adminer"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "Adminer"


class ConcreteImageUpdaterForGeneric(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return [".*"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "Generic"


class ConcreteImageUpdaterForGenericV(ConcreteImageUpdater):

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions = ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return [".*"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self, image: str, tag: str) -> str:
        return "GenericV"


class ImageUpdater:

    updater: list[ConcreteImageUpdater] = None

    def __init__(self):
        self.updater = list[ConcreteImageUpdater]()

    def add_default_mapper(self) -> None:
        self.updater.append(ConcreteImageUpdaterForNginx())
        self.updater.append(ConcreteImageUpdaterForWordpress())
        self.updater.append(ConcreteImageUpdaterForGitLab())
        self.updater.append(ConcreteImageUpdaterForRegistry())
        self.updater.append(ConcreteImageUpdaterForPrometheus())
        self.updater.append(ConcreteImageUpdaterForPrometheusBlackboxExporter())
        self.updater.append(ConcreteImageUpdaterForPrometheusNginxExporter())
        self.updater.append(ConcreteImageUpdaterForPrometheusNodeExporter())
        self.updater.append(ConcreteImageUpdaterForKeycloak())
        self.updater.append(ConcreteImageUpdaterForMariaDB())
        self.updater.append(ConcreteImageUpdaterForPostgreSQL())
        self.updater.append(ConcreteImageUpdaterForAdminer())

    @GeneralUtilities.check_arguments
    def check_service_for_newest_version(self, dockercompose_file: str, service_name: str) -> bool:
        imagename, existing_tag, existing_version = self.get_current_version_of_service_from_docker_compose_file(dockercompose_file, service_name)  # pylint:disable=unused-variable
        newest_version, newest_tag = self.get_latest_version_of_image(imagename, VersionEcholon.LatestVersion, existing_version)  # pylint:disable=unused-variable
        if existing_version < newest_version:
            GeneralUtilities.write_message_to_stdout(f"Service {service_name} with image {imagename} uses tag {existing_version}. The newest available version of this image is {newest_version}.")
            return True
        else:
            return False

    @GeneralUtilities.check_arguments
    def check_for_newest_version(self, dockercompose_file: str, excluded_services: list[str] = []) -> bool:
        all_services = self.get_services_from_docker_compose_file(dockercompose_file)
        services_to_check = [service for service in all_services if service not in all_services]
        newer_version_available: bool = False
        for service_to_check in services_to_check:
            if self.check_service_for_newest_version(dockercompose_file, service_to_check):
                newer_version_available = True
        return newer_version_available

    @GeneralUtilities.check_arguments
    def update_all_services_in_docker_compose_file(self, dockercompose_file: str, version_echolon: VersionEcholon, except_services: list[str] = [], updatertype: str = None):
        all_services = self.get_services_from_docker_compose_file(dockercompose_file)
        services_to_update = [service for service in all_services if service not in except_services]
        self.update_services_in_docker_compose_file(dockercompose_file, services_to_update, version_echolon, updatertype)

    @GeneralUtilities.check_arguments
    def update_services_in_docker_compose_file(self, dockercompose_file: str, service_names: list[str], version_echolon: VersionEcholon, updatertype: str = None):
        for service_name in service_names:
            if self.service_has_image_information(dockercompose_file, service_name):
                self.update_service_in_docker_compose_file(dockercompose_file, service_name, version_echolon, updatertype)

    @GeneralUtilities.check_arguments
    def service_has_image_information(self, dockercompose_file: str, service_name: str) -> bool:
        with open(dockercompose_file, 'r', encoding="utf-8") as file:
            compose_data = yaml.safe_load(file)
            service = compose_data.get('services', {}).get(service_name, {})
            image = service.get('image', None)
            return image is not None

    @GeneralUtilities.check_arguments
    def update_service_in_docker_compose_file(self, dockercompose_file: str, service_name: str, version_echolon: VersionEcholon, updatertype: str = None):
        imagename, existing_tag, existing_version = self.get_current_version_of_service_from_docker_compose_file(dockercompose_file, service_name)  # pylint:disable=unused-variable
        result = self.get_latest_version_of_image(imagename, version_echolon, existing_version, updatertype)
        newest_version = result[0]
        newest_tag = result[1]
        # TODO write info to console if there is a newwer version available if versionecoholon==latest would have been chosen
        if existing_version < newest_version:

            with open(dockercompose_file, 'r', encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            services = compose_data.get("services", {})
            if service_name not in services:
                raise ValueError(f"Service '{service_name}' not found.")

            image = services[service_name].get("image")
            if not image:
                raise ValueError(f"Service '{service_name}' does not have an image-field.")

            imagename = image.split(":")[0]
            services[service_name]["image"] = imagename+":"+newest_tag

            with open(dockercompose_file, 'w', encoding="utf-8") as f:
                yaml.dump(compose_data, f, default_flow_style=False)

    @GeneralUtilities.check_arguments
    def get_current_version_of_service_from_docker_compose_file(self, dockercompose_file: str, service_name: str) -> tuple[str, str, Version]:  # returns (image,existing_tag,existing_version)
        with open(dockercompose_file, 'r', encoding="utf-8") as file:
            compose_data = yaml.safe_load(file)
            service = compose_data.get('services', {}).get(service_name, {})
            image = str(service.get('image', None))
            if image:
                if ':' in image:
                    name, tag = image.rsplit(':', 1)
                else:
                    name, tag = image, 'latest'
                return name, tag, self.get_docker_version_from_tag(name, tag)
            else:
                raise ValueError(f"Service '{service_name}' in '{dockercompose_file}'")

    @GeneralUtilities.check_arguments
    def __get_updater_for_image(self,  image: str) -> ConcreteImageUpdater:
        for updater in self.updater:
            for supported_image_regex in updater.get_supported_images():
                r = re.compile("^"+supported_image_regex+"$")
                if r.match(supported_image_regex):
                    return updater
        raise ValueError(f"No updater available for image '{image}'")

    @GeneralUtilities.check_arguments
    def __get_updater_by_name(self,  updater_name: str) -> ConcreteImageUpdater:
        for updater in self.updater:
            if updater.get_name() == updater_name:
                return updater
        raise ValueError(f"No updater available with name '{updater_name}'")

    @GeneralUtilities.check_arguments
    def get_docker_version_from_tag(self,  image: str, tag: str) -> Version:
        updater: ConcreteImageUpdater = self.__get_updater_for_image(image)
        return updater.get_version_from_tag(image, tag)

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self, image: str, version_echolon: VersionEcholon, current_version: Version, updatertype: str = None) -> tuple[Version, str]:

        updater: ConcreteImageUpdater = None
        if updatertype is None:
            updater=self.__get_updater_for_image(image)
        else:
            updater=self.__get_updater_by_name(updatertype)

        newest_version: Version = updater.get_latest_version_of_image(image, version_echolon, current_version)
        newest_tag: str = updater.version_to_tag(newest_version)
        return (newest_version, newest_tag)

    @GeneralUtilities.check_arguments
    def get_services_from_docker_compose_file(self, dockercompose_file: str) -> list[str]:
        with open(dockercompose_file, 'r', encoding="utf-8") as f:
            compose_data = yaml.safe_load(f)
            services = compose_data.get('services', {})
            result = list(services.keys())
            return result
