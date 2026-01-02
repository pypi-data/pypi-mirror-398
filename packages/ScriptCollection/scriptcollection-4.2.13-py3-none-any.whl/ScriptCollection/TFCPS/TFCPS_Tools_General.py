from datetime import datetime,timezone
from graphlib import TopologicalSorter
import os
from pathlib import Path
import shutil
import zipfile
import tarfile
import time
import re
import sys
import json
import tempfile 
import uuid
import urllib.request
from packaging import version
import requests
from lxml import etree
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import  LogLevel
from ..ImageUpdater import ImageUpdater, VersionEcholon

class TFCPS_Tools_General:

    __sc:ScriptCollectionCore=ScriptCollectionCore()

    def __init__(self,sc:ScriptCollectionCore):
        self.__sc=sc


    @GeneralUtilities.check_arguments
    def codeunit_is_enabled(self, codeunit_file: str) -> bool:
        root: etree._ElementTree = etree.parse(codeunit_file)
        return GeneralUtilities.string_to_boolean(str(root.xpath('//cps:codeunit/@enabled', namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'})[0]))

    @GeneralUtilities.check_arguments
    def ensure_cyclonedxcli_is_available(self, target_folder: str,enforce_update:bool) -> str:
        local_filename = "cyclonedx-cli"
        filename_on_github: str
        if GeneralUtilities.current_system_is_windows():
            filename_on_github = "cyclonedx-win-x64.exe"
            local_filename = local_filename+".exe"
        else:
            filename_on_github = "cyclonedx-linux-x64"
        return self.ensure_file_from_github_assets_is_available_with_retry(target_folder, "CycloneDX", "cyclonedx-cli", "CycloneDXCLI", local_filename, lambda latest_version: filename_on_github,enforce_update=False)
    
    @GeneralUtilities.check_arguments
    def ensure_file_from_github_assets_is_available_with_retry(self, target_folder: str, githubuser: str, githubprojectname: str, resource_name: str, local_filename: str, get_filename_on_github, amount_of_attempts: int = 5,enforce_update:bool=False) -> str:
        return GeneralUtilities.retry_action(lambda: self.ensure_file_from_github_assets_is_available(target_folder, githubuser, githubprojectname, resource_name, local_filename, get_filename_on_github,enforce_update), amount_of_attempts)

    @GeneralUtilities.check_arguments
    def ensure_file_from_github_assets_is_available(self, target_folder: str, githubuser: str, githubprojectname: str, resource_name: str, local_filename: str, get_filename_on_github,enforce_update:bool) -> str:
        #TODO use or remove target_folder-parameter
        resource_folder =os.path.join( self.__sc.get_global_cache_folder(),"Tools",resource_name)
        file = f"{resource_folder}/{local_filename}"
        file_exists = os.path.isfile(file)
        if not file_exists:
            self.__sc.log.log(f"Download Asset \"{githubuser}/{githubprojectname}: {resource_name}\" from GitHub to global cache...", LogLevel.Information)
            GeneralUtilities.ensure_folder_exists_and_is_empty(resource_folder)
            headers = { 'User-Agent': 'Mozilla/5.0'}
            self.__add_github_api_key_if_available(headers)
            url = f"https://api.github.com/repos/{githubuser}/{githubprojectname}/releases/latest"
            self.__sc.log.log(f"Download \"{url}\"...", LogLevel.Debug)
            time.sleep(2)
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=(10, 10))
            response_json=response.json()
            latest_version = response_json["tag_name"]
            filename_on_github = get_filename_on_github(latest_version)
            link = f"https://github.com/{githubuser}/{githubprojectname}/releases/download/{latest_version}/{filename_on_github}"
            time.sleep(2)
            with requests.get(link, headers=headers, stream=True, allow_redirects=True,  timeout=(5, 600)) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                with open(file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        show_progress: bool = False
                        if show_progress:
                            downloaded += len(chunk)
                            if total_size:
                                percent = downloaded / total_size * 100
                                sys.stdout.write(f"\rDownload: {percent:.2f}%")
                                sys.stdout.flush()
            self.__sc.log.log(f"Downloaded \"{url}\".", LogLevel.Diagnostic)
        GeneralUtilities.assert_file_exists(file)
        return file

    def __add_github_api_key_if_available(self, headers: dict):
        token = os.getenv("GITHUB_TOKEN")
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        else:
            user_folder = str(Path.home())
            github_token_file: str = str(os.path.join(user_folder, ".github", "token.txt"))
            if os.path.isfile(github_token_file):
                token = GeneralUtilities.read_text_from_file(github_token_file)
                headers["Authorization"] = f"Bearer {token}"
        return headers

    
    @GeneralUtilities.check_arguments
    def is_codeunit_folder(self, codeunit_folder: str) -> bool:
        repo_folder = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        if not self.__sc.is_git_repository(repo_folder):
            return False
        codeunit_name = os.path.basename(codeunit_folder)
        codeunit_file: str = os.path.join(codeunit_folder, f"{codeunit_name}.codeunit.xml")
        if not os.path.isfile(codeunit_file):
            return False
        return True

    @GeneralUtilities.check_arguments
    def assert_is_codeunit_folder(self, codeunit_folder: str) -> str:
        repo_folder = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        if not self.__sc.is_git_repository(repo_folder):
            raise ValueError(f"'{codeunit_folder}' can not be a valid codeunit-folder because '{repo_folder}' is not a git-repository.")
        codeunit_name = os.path.basename(codeunit_folder)
        codeunit_file: str = os.path.join(codeunit_folder, f"{codeunit_name}.codeunit.xml")
        if not os.path.isfile(codeunit_file):
            raise ValueError(f"'{codeunit_folder}' is no codeunit-folder because '{codeunit_file}' does not exist.")

    @GeneralUtilities.check_arguments
    def get_codeunits(self, repository_folder: str, ignore_disabled_codeunits: bool = True) -> list[str]:
        codeunits_with_dependent_codeunits: dict[str, set[str]] = dict[str, set[str]]()
        subfolders = GeneralUtilities.get_direct_folders_of_folder(repository_folder)
        for subfolder in subfolders:
            codeunit_name: str = os.path.basename(subfolder)
            codeunit_file = os.path.join(subfolder, f"{codeunit_name}.codeunit.xml")
            if os.path.exists(codeunit_file):
                if ignore_disabled_codeunits and not self.codeunit_is_enabled(codeunit_file):
                    continue
                codeunits_with_dependent_codeunits[codeunit_name] = self.get_dependent_code_units(codeunit_file)
        sorted_codeunits = self._internal_get_sorted_codeunits_by_dict(codeunits_with_dependent_codeunits)
        #TODO show warning somehow for enabled codeunits which depends on ignored codeunits
        return sorted_codeunits

    @GeneralUtilities.check_arguments
    def repository_has_codeunits(self, repository: str, ignore_disabled_codeunits: bool = True) -> bool:
        return 0<len(self.get_codeunits(repository, ignore_disabled_codeunits))

    @GeneralUtilities.check_arguments
    def get_dependent_code_units(self, codeunit_file: str) -> list[str]:
        root: etree._ElementTree = etree.parse(codeunit_file)
        result = set(root.xpath('//cps:dependentcodeunit/text()', namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'}))
        result = sorted(result)
        return result

    @GeneralUtilities.check_arguments
    def _internal_get_sorted_codeunits_by_dict(self, codeunits: dict[str, set[str]]) -> list[str]:
        sorted_codeunits = {
            node: sorted(codeunits[node])
            for node in sorted(codeunits)
        }

        ts = TopologicalSorter()
        for node, deps in sorted_codeunits.items():
            ts.add(node, *deps)

        result_typed = list(ts.static_order())
        result = [str(item) for item in result_typed]
        return result

    @GeneralUtilities.check_arguments
    def get_unsupported_versions(self, repository_folder: str, moment: datetime) -> list[tuple[str, datetime, datetime]]:
        self.__sc.assert_is_git_repository(repository_folder)
        result: list[tuple[str, datetime, datetime]] = list[tuple[str, datetime, datetime]]()
        for entry in self.get_versions(repository_folder):
            if not (entry[1] <= moment and moment <= entry[2]):
                result.append(entry)
        return result


    @GeneralUtilities.check_arguments
    def get_versions(self, repository_folder: str) -> list[tuple[str, datetime, datetime]]:
        self.__sc.assert_is_git_repository(repository_folder)
        folder = os.path.join(repository_folder, "Other", "Resources", "Support")
        file = os.path.join(folder, "InformationAboutSupportedVersions.csv")
        result: list[(str, datetime, datetime)] = list[(str, datetime, datetime)]()
        if not os.path.isfile(file):
            return result
        entries = GeneralUtilities.read_csv_file(file, True)
        for entry in entries:
            d1 = GeneralUtilities.string_to_datetime(entry[1])
            if d1.tzinfo is None: 
                d1 = d1.replace(tzinfo=timezone.utc)
            d2 = GeneralUtilities.string_to_datetime(entry[2])
            if d2.tzinfo is None:
                d2 = d2.replace(tzinfo=timezone.utc)
            result.append((entry[0], d1, d2))
        return result
    
    @GeneralUtilities.check_arguments
    def dependent_codeunit_exists(self, repository: str, codeunit: str) -> None:
        codeunit_file = f"{repository}/{codeunit}/{codeunit}.codeunit.xml"
        return os.path.isfile(codeunit_file)

    @GeneralUtilities.check_arguments
    def get_all_authors_and_committers_of_repository(self, repository_folder: str, subfolder: str = None) -> list[tuple[str, str]]:
        self.__sc.is_git_or_bare_git_repository(repository_folder)
        space_character = "_"
        if subfolder is None:
            subfolder_argument = GeneralUtilities.empty_string
        else:
            subfolder_argument = f" -- {subfolder}"
        log_result = self.__sc.run_program("git", f'log --pretty=%aN{space_character}%aE%n%cN{space_character}%cE HEAD{subfolder_argument}', repository_folder)
        plain_content: list[str] = list(
            set([line for line in log_result[1].split("\n") if len(line) > 0]))
        result: list[tuple[str, str]] = []
        for item in plain_content:
            if len(re.findall(space_character, item)) == 1:
                splitted = item.split(space_character)
                result.append((splitted[0], splitted[1]))
            else:
                raise ValueError(f'Unexpected author: "{item}"')
        return result

    @GeneralUtilities.check_arguments
    def copy_artifacts_from_dependent_code_units(self, repo_folder: str, codeunit_name: str) -> None:
        codeunit_file = os.path.join(repo_folder, codeunit_name, codeunit_name + ".codeunit.xml")
        dependent_codeunits = self.get_dependent_code_units(codeunit_file)
        if len(dependent_codeunits) > 0:
            self.__sc.log.log(f"Get dependent artifacts for codeunit {codeunit_name}.")
        dependent_codeunits_folder = os.path.join(repo_folder, codeunit_name, "Other", "Resources", "DependentCodeUnits")
        GeneralUtilities.ensure_directory_does_not_exist(dependent_codeunits_folder)
        for dependent_codeunit in dependent_codeunits:
            target_folder = os.path.join(dependent_codeunits_folder, dependent_codeunit)
            GeneralUtilities.ensure_directory_does_not_exist(target_folder)
            other_folder = os.path.join(repo_folder, dependent_codeunit, "Other")
            artifacts_folder = os.path.join(other_folder, "Artifacts")
            shutil.copytree(artifacts_folder, target_folder)


    @GeneralUtilities.check_arguments
    def write_version_to_codeunit_file(self, codeunit_file: str, current_version: str) -> None:
        versionregex = "\\d+\\.\\d+\\.\\d+"
        versiononlyregex = f"^{versionregex}$"
        pattern = re.compile(versiononlyregex)
        if pattern.match(current_version):
            GeneralUtilities.write_text_to_file(codeunit_file, re.sub(f"<cps:version>{versionregex}<\\/cps:version>", f"<cps:version>{current_version}</cps:version>", GeneralUtilities.read_text_from_file(codeunit_file)))
        else:
            raise ValueError(f"Version '{current_version}' does not match version-regex '{versiononlyregex}'.")

    @GeneralUtilities.check_arguments
    def set_default_constants(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        self.set_constant_for_curenttimestamp(codeunit_folder)
        self.set_constant_for_commitid(codeunit_folder)
        self.set_constant_for_commitdate(codeunit_folder)
        self.set_constant_for_codeunitname(codeunit_folder)
        self.set_constant_for_codeunitversion(codeunit_folder)
        self.set_constant_for_codeunitmajorversion(codeunit_folder)
        self.set_constant_for_description(codeunit_folder)

    @GeneralUtilities.check_arguments
    def set_constant_for_curenttimestamp(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        timestamp = GeneralUtilities.datetime_to_string_for_logfile_entry(GeneralUtilities.get_now().astimezone(timezone.utc))
        self.set_constant(codeunit_folder, "CurrentTimestamp", timestamp)

    @GeneralUtilities.check_arguments
    def set_constant_for_commitid(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        repository = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        commit_id = self.__sc.git_get_commit_id(repository)
        self.set_constant(codeunit_folder, "CommitId", commit_id)

    @GeneralUtilities.check_arguments
    def set_constant_for_commitdate(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        repository = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        commit_date: datetime = self.__sc.git_get_commit_date(repository)
        self.set_constant(codeunit_folder, "CommitDate", GeneralUtilities.datetime_to_string(commit_date))

    @GeneralUtilities.check_arguments
    def set_constant_for_codeunitname(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        codeunit_name: str = os.path.basename(codeunit_folder)
        self.set_constant(codeunit_folder, "CodeUnitName", codeunit_name) 

    @GeneralUtilities.check_arguments
    def set_constant_for_codeunitversion(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        codeunit_version: str = self.get_version_of_codeunit(os.path.join(codeunit_folder,f"{os.path.basename(codeunit_folder)}.codeunit.xml"))
        self.set_constant(codeunit_folder, "CodeUnitVersion", codeunit_version)

    @GeneralUtilities.check_arguments
    def set_constant_for_codeunitmajorversion(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        major_version = int(self.get_version_of_codeunit(os.path.join(codeunit_folder,f"{os.path.basename(codeunit_folder)}.codeunit.xml")).split(".")[0])
        self.set_constant(codeunit_folder, "CodeUnitMajorVersion", str(major_version))


    @GeneralUtilities.check_arguments
    def get_version_of_codeunit(self,codeunit_file:str) -> None:
        codeunit_file_content:str=GeneralUtilities.read_text_from_file(codeunit_file)
        return self.get_version_of_codeunit_filecontent(codeunit_file_content)
    
    @GeneralUtilities.check_arguments
    def get_version_of_codeunit_filecontent(self,file_content:str) -> None:
        root: etree._ElementTree = etree.fromstring(file_content.encode("utf-8"))
        result = str(root.xpath('//cps:version/text()',  namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'})[0])
        return result
    
    @GeneralUtilities.check_arguments
    def set_constant_for_description(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        codeunit_file:str=os.path.join(codeunit_folder,f"{os.path.basename(codeunit_folder)}.codeunit.xml")
        codeunit_description: str = self.get_codeunit_description(codeunit_file)
        self.set_constant(codeunit_folder, "CodeUnitDescription", codeunit_description)

    @GeneralUtilities.check_arguments
    def get_codeunit_description(self,codeunit_file:str) -> bool:
        root: etree._ElementTree = etree.parse(codeunit_file)
        return str(root.xpath('//cps:properties/@description', namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'})[0])

    @GeneralUtilities.check_arguments
    def set_constant(self, codeunit_folder: str, constantname: str, constant_value: str, documentationsummary: str = None, constants_valuefile: str = None) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        if documentationsummary is None:
            documentationsummary = GeneralUtilities.empty_string
        constants_folder = os.path.join(codeunit_folder, "Other", "Resources", "Constants")
        GeneralUtilities.ensure_directory_exists(constants_folder)
        constants_metafile = os.path.join(constants_folder, f"{constantname}.constant.xml")
        if constants_valuefile is None:
            constants_valuefile_folder = constants_folder
            constants_valuefile_name = f"{constantname}.value.txt"
            constants_valuefiler_reference = f"./{constants_valuefile_name}"
        else:
            constants_valuefile_folder = os.path.dirname(constants_valuefile)
            constants_valuefile_name = os.path.basename(constants_valuefile)
            constants_valuefiler_reference = os.path.join(constants_valuefile_folder, constants_valuefile_name)

        # TODO implement usage of self.reference_latest_version_of_xsd_when_generating_xml
        GeneralUtilities.write_text_to_file(constants_metafile, f"""<?xml version="1.0" encoding="UTF-8" ?>
<cps:constant xmlns:cps="https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure" constantspecificationversion="1.1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/raw/main/Conventions/RepositoryStructure/CommonProjectStructure/constant.xsd">
    <cps:name>{constantname}</cps:name>
    <cps:documentationsummary>{documentationsummary}</cps:documentationsummary>
    <cps:path>{constants_valuefiler_reference}</cps:path>
</cps:constant>""")
        # TODO validate generated xml against xsd
        GeneralUtilities.write_text_to_file(os.path.join(constants_valuefile_folder, constants_valuefile_name), constant_value)

    @GeneralUtilities.check_arguments
    def get_constant_value(self, source_codeunit_folder: str, constant_name: str) -> str:
        self.assert_is_codeunit_folder(source_codeunit_folder)
        value_file_relative = self.__get_constant_helper(source_codeunit_folder, constant_name, "path")
        value_file = GeneralUtilities.resolve_relative_path(value_file_relative, os.path.join(source_codeunit_folder, "Other", "Resources", "Constants"))
        return GeneralUtilities.read_text_from_file(value_file)

    @GeneralUtilities.check_arguments
    def get_constant_documentation(self, source_codeunit_folder: str, constant_name: str) -> str:
        self.assert_is_codeunit_folder(source_codeunit_folder)
        return self.__get_constant_helper(source_codeunit_folder, constant_name, "documentationsummary")

    @GeneralUtilities.check_arguments
    def __get_constant_helper(self, source_codeunit_folder: str, constant_name: str, propertyname: str) -> str:
        self.assert_is_codeunit_folder(source_codeunit_folder)
        root: etree._ElementTree = etree.parse(os.path.join(source_codeunit_folder, "Other", "Resources", "Constants", f"{constant_name}.constant.xml"))
        results = root.xpath(f'//cps:{propertyname}/text()', namespaces={
            'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'
        })
        length = len(results)
        if (length == 0):
            return ""
        elif length == 1:
            return results[0]
        else:
            raise ValueError("Too many results found.")

    @GeneralUtilities.check_arguments
    def copy_licence_file(self, codeunit_folder: str) -> None:
        folder_of_current_file = os.path.join(codeunit_folder,"Other")
        license_file = GeneralUtilities.resolve_relative_path("../../License.txt", folder_of_current_file)
        target_folder = GeneralUtilities.resolve_relative_path("Artifacts/License", folder_of_current_file)
        GeneralUtilities.ensure_directory_exists(target_folder)
        shutil.copy(license_file, target_folder)

    @GeneralUtilities.check_arguments
    def generate_diff_report(self, repository_folder: str, codeunit_name: str, current_version: str) -> None:
        self.__sc.assert_is_git_repository(repository_folder)
        codeunit_folder = os.path.join(repository_folder, codeunit_name)
        target_folder = GeneralUtilities.resolve_relative_path("Other/Artifacts/DiffReport", codeunit_folder)
        GeneralUtilities.ensure_directory_does_not_exist(target_folder)
        GeneralUtilities.ensure_directory_exists(target_folder)
        target_file_light = os.path.join(target_folder, "DiffReport.html").replace("\\", "/")
        target_file_dark = os.path.join(target_folder, "DiffReportDark.html").replace("\\", "/")
        src = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # hash/id of empty git-tree
        src_prefix = "Begin"
        if self.__sc.get_current_git_branch_has_tag(repository_folder):
            latest_tag = self.__sc.get_latest_git_tag(repository_folder)
            src = self.__sc.git_get_commitid_of_tag(repository_folder, latest_tag)
            src_prefix = latest_tag
        dst = "HEAD"
        dst_prefix = f"v{current_version}"

        temp_file = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        try:
            GeneralUtilities.ensure_file_does_not_exist(temp_file)
            GeneralUtilities.write_text_to_file(temp_file, self.__sc.run_program("git", f'--no-pager diff --src-prefix={src_prefix}/ --dst-prefix={dst_prefix}/ {src} {dst} -- {codeunit_name}', repository_folder)[1])
            styles:dict[str,str]={
                "default":target_file_light,
                "github-dark":target_file_dark
            }
            for style,target_file in styles.items():
                self.__sc.run_program_argsasarray("pygmentize", ['-l', 'diff', '-f', 'html', '-O', 'full', '-o', target_file, '-P', f'style={style}', temp_file], repository_folder)
        finally:
            GeneralUtilities.ensure_file_does_not_exist(temp_file)

    @GeneralUtilities.check_arguments
    def get_version_of_project(self,repositoryfolder:str) -> str:
        self.__sc.assert_is_git_repository(repositoryfolder)
        return self.__sc.get_semver_version_from_gitversion(repositoryfolder)

    @GeneralUtilities.check_arguments
    def create_changelog_entry(self, repositoryfolder: str, message: str, commit: bool, force: bool):
        self.__sc.assert_is_git_repository(repositoryfolder)
        random_file = os.path.join(repositoryfolder, str(uuid.uuid4()))
        try:
            if force and not self.__sc.git_repository_has_uncommitted_changes(repositoryfolder):
                GeneralUtilities.ensure_file_exists(random_file)
            current_version = self.get_version_of_project(repositoryfolder)
            changelog_file = os.path.join(repositoryfolder, "Other", "Resources", "Changelog", f"v{current_version}.md")
            if os.path.isfile(changelog_file):
                self.__sc.log.log(f"Changelog-file '{changelog_file}' already exists.")
            else:
                GeneralUtilities.ensure_file_exists(changelog_file)
                GeneralUtilities.write_text_to_file(changelog_file, f"""# Release notes

## Changes

- {message}
""")
        finally:
            GeneralUtilities.ensure_file_does_not_exist(random_file)
        if commit:
            self.__sc.git_commit(repositoryfolder, f"Added changelog-file for v{current_version}.")
 
    @GeneralUtilities.check_arguments
    def merge_sbom_file_from_dependent_codeunit_into_this(self,codeunit_folder: str, codeunitname:str,dependent_codeunit_name: str,use_cache:bool) -> None:
        repository_folder = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        dependent_codeunit_folder = os.path.join(repository_folder, dependent_codeunit_name).replace("\\", "/")
        codeunit_file:str=os.path.join(codeunit_folder,f"{codeunitname}.codeunit.xml")
        dependent_codeunit_file:str=os.path.join(dependent_codeunit_folder,f"{dependent_codeunit_name}.codeunit.xml")
        sbom_file = f"{repository_folder}/{codeunitname}/Other/Artifacts/BOM/{codeunitname}.{self.get_version_of_codeunit(codeunit_file)}.sbom.xml"
        dependent_sbom_file = f"{repository_folder}/{dependent_codeunit_name}/Other/Artifacts/BOM/{dependent_codeunit_name}.{self.get_version_of_codeunit(dependent_codeunit_file)}.sbom.xml"
        self.merge_sbom_file(repository_folder, dependent_sbom_file, sbom_file,use_cache)

    @GeneralUtilities.check_arguments
    def merge_sbom_file(self, repository_folder: str, source_sbom_file_relative: str, target_sbom_file_relative: str,use_cache:bool) -> None:
        GeneralUtilities.assert_file_exists(os.path.join(repository_folder, source_sbom_file_relative))
        GeneralUtilities.assert_file_exists(os.path.join(repository_folder, target_sbom_file_relative))
        target_original_sbom_file_relative = os.path.dirname(target_sbom_file_relative)+"/"+os.path.basename(target_sbom_file_relative)+".original.xml"
        os.rename(os.path.join(repository_folder, target_sbom_file_relative), os.path.join(repository_folder, target_original_sbom_file_relative))

        cyclonedx_exe:str=self.ensure_cyclonedxcli_is_available(repository_folder,not use_cache)
        self.__sc.run_program(cyclonedx_exe, f"merge --input-files {source_sbom_file_relative} {target_original_sbom_file_relative} --output-file {target_sbom_file_relative}", repository_folder)
        GeneralUtilities.ensure_file_does_not_exist(os.path.join(repository_folder, target_original_sbom_file_relative))
        self.__sc.format_xml_file(os.path.join(repository_folder, target_sbom_file_relative))

    @GeneralUtilities.check_arguments
    def codeunit_has_testable_sourcecode(self,codeunit_file:str) -> bool:
        self.assert_is_codeunit_folder(os.path.dirname(codeunit_file))
        root: etree._ElementTree = etree.parse(codeunit_file)
        return GeneralUtilities.string_to_boolean(str(root.xpath('//cps:properties/@codeunithastestablesourcecode', namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'})[0]))

    @GeneralUtilities.check_arguments
    def codeunit_has_updatable_dependencies(self,codeunit_file:str) -> bool:
        self.assert_is_codeunit_folder(os.path.dirname(codeunit_file))
        root: etree._ElementTree = etree.parse(codeunit_file)
        return GeneralUtilities.string_to_boolean(str(root.xpath('//cps:properties/@codeunithasupdatabledependencies', namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'})[0]))

    @GeneralUtilities.check_arguments
    def get_codeunit_owner_emailaddress(self,codeunit_file:str) -> None:
        self.assert_is_codeunit_folder(os.path.dirname(codeunit_file))
        namespaces = {'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        root: etree._ElementTree = etree.parse(codeunit_file)
        result = root.xpath('//cps:codeunit/cps:codeunitowneremailaddress/text()', namespaces=namespaces)[0]
        return result

    @GeneralUtilities.check_arguments
    def get_codeunit_owner_name(self,codeunit_file:str) -> None:
        self.assert_is_codeunit_folder(os.path.dirname(codeunit_file))
        namespaces = {'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure',  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        root: etree._ElementTree = etree.parse(codeunit_file)
        result = root.xpath('//cps:codeunit/cps:codeunitownername/text()', namespaces=namespaces)[0]
        return result

    @GeneralUtilities.check_arguments
    def generate_svg_files_from_plantuml_files_for_repository(self, repository_folder: str,use_cache:bool) -> None:
        self.__sc.log.log("Generate svg-files from plantuml-files...")
        self.__sc.assert_is_git_repository(repository_folder)
        plantuml_jar_file=self.ensure_plantuml_is_available(repository_folder,not use_cache)
        target_folder = os.path.join(repository_folder, "Other",  "Reference")
        self.__generate_svg_files_from_plantuml(target_folder, plantuml_jar_file)

    @GeneralUtilities.check_arguments
    def generate_svg_files_from_plantuml_files_for_codeunit(self, codeunit_folder: str,use_cache:bool) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        repository_folder = os.path.dirname(codeunit_folder)
        plantuml_jar_file=self.ensure_plantuml_is_available(repository_folder,not use_cache)
        target_folder = os.path.join(codeunit_folder, "Other", "Reference")
        self.__generate_svg_files_from_plantuml(target_folder, plantuml_jar_file)

    @GeneralUtilities.check_arguments
    def ensure_plantuml_is_available(self, target_folder: str,enforce_update:bool) -> str:
        return self.ensure_file_from_github_assets_is_available_with_retry(target_folder, "plantuml", "plantuml", "PlantUML", "plantuml.jar", lambda latest_version: "plantuml.jar",enforce_update=enforce_update)

    @GeneralUtilities.check_arguments
    def __generate_svg_files_from_plantuml(self, diagrams_files_folder: str, plantuml_jar_file: str) -> None:
        for file in GeneralUtilities.get_all_files_of_folder(diagrams_files_folder):
            if file.endswith(".plantuml"):
                output_filename = self.get_output_filename_for_plantuml_filename(file)
                argument = ['-jar',plantuml_jar_file, '-tsvg', os.path.basename(file)]
                folder = os.path.dirname(file)
                self.__sc.run_program_argsasarray("java", argument, folder)
                result_file = folder+"/" + output_filename
                GeneralUtilities.assert_file_exists(result_file)
                self.__sc.format_xml_file(result_file)

    @GeneralUtilities.check_arguments
    def get_output_filename_for_plantuml_filename(self, plantuml_file: str) -> str:
        for line in GeneralUtilities.read_lines_from_file(plantuml_file):
            prefix = "@startuml "
            if line.startswith(prefix):
                title = line[len(prefix):]
                return title+".svg"
        return Path(plantuml_file).stem+".svg"

    @GeneralUtilities.check_arguments
    def generate_codeunits_overview_diagram(self, repository_folder: str) -> None:
        self.__sc.log.log("Generate Codeunits-overview-diagram...")
        self.__sc.assert_is_git_repository(repository_folder)
        project_name: str = os.path.basename(repository_folder)
        target_folder = os.path.join(repository_folder, "Other", "Reference", "Technical", "Diagrams")
        GeneralUtilities.ensure_directory_exists(target_folder)
        target_file = os.path.join(target_folder, "CodeUnits-Overview.plantuml")
        lines = ["@startuml CodeUnits-Overview"]
        lines.append(f"title CodeUnits of {project_name}")

        codeunits = self.get_codeunits(repository_folder)
        for codeunitname in codeunits:
            codeunit_file: str = os.path.join(repository_folder, codeunitname, f"{codeunitname}.codeunit.xml")

            description = self.get_codeunit_description(codeunit_file)

            lines.append(GeneralUtilities.empty_string)
            lines.append(f"[{codeunitname}]")
            lines.append(f"note as {codeunitname}Note")
            lines.append(f"  {description}")
            lines.append(f"end note")
            lines.append(f"{codeunitname} .. {codeunitname}Note")

        lines.append(GeneralUtilities.empty_string)
        for codeunitname in codeunits:
            codeunit_file: str = os.path.join(repository_folder, codeunitname, f"{codeunitname}.codeunit.xml")
            dependent_codeunits = self.get_dependent_code_units(codeunit_file)
            for dependent_codeunit in dependent_codeunits:
                lines.append(f"{codeunitname} --> {dependent_codeunit}")

        lines.append(GeneralUtilities.empty_string)
        lines.append("@enduml")

        GeneralUtilities.write_lines_to_file(target_file, lines)
        
    @GeneralUtilities.check_arguments
    def ensure_trufflehog_is_available(self,enforce_update:bool=False) -> dict[str,str]:
        def download_and_extract(osname: str, osname_in_github_asset: str, extension: str):
            resource_name: str = f"TruffleHog_{osname}"
            zip_filename: str = f"{resource_name}.{extension}"
            target_folder_unextracted = os.path.join(self.__sc.get_global_cache_folder(),"Tools",resource_name+"_Unextracted")
            target_folder_extracted = os.path.join(self.__sc.get_global_cache_folder(),"Tools",resource_name)
            update:bool=not os.path.isdir(target_folder_extracted) or GeneralUtilities.folder_is_empty(target_folder_extracted) or enforce_update
            if update:
                downloaded_file=self.ensure_file_from_github_assets_is_available_with_retry(target_folder_unextracted, "trufflesecurity", "trufflehog", resource_name+"_Unextracted", zip_filename, lambda latest_version: f"trufflehog_{latest_version[1:]}_{osname_in_github_asset}_amd64.tar.gz",enforce_update=enforce_update)
                #TODO add option to also download arm-version
                local_zip_file: str = downloaded_file
                GeneralUtilities.ensure_folder_exists_and_is_empty(target_folder_extracted)
                if extension == "zip":
                    with zipfile.ZipFile(local_zip_file, 'r') as zip_ref:
                        zip_ref.extractall(target_folder_extracted)
                elif extension == "tar.gz": 
                    with tarfile.open(local_zip_file, "r:gz") as tar:
                        tar.extractall(path=target_folder_extracted)
                else:
                    raise ValueError(f"Unknown extension: \"{extension}\"")
                GeneralUtilities.ensure_directory_does_not_exist(target_folder_unextracted)
            GeneralUtilities.assert_folder_exists(target_folder_extracted)
            executable=[f for f in GeneralUtilities.get_all_files_of_folder(target_folder_extracted) if os.path.basename(f).startswith("trufflehog")][0]
            return executable

        result=dict[str,str]()
        result["Windows"]=download_and_extract("Windows", "windows", "tar.gz")
        result["Linux"]=download_and_extract("Linux", "linux", "tar.gz")
        result["MacOS"]=download_and_extract("MacOS", "darwin", "tar.gz")
        return result

    @GeneralUtilities.check_arguments
    def generate_tasksfile_from_workspace_file(self, repository_folder: str, append_cli_args_at_end: bool = False) -> None:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.__sc.program_runner.will_be_executed_locally():  # works only locally, but much more performant than always running an external program
            self.__sc.log.log("Generate taskfile from code-workspace-file...")
            self.__sc.assert_is_git_repository(repository_folder)
            workspace_file: str = self.__sc.find_file_by_extension(repository_folder, "code-workspace")
            task_file: str = repository_folder + "/Taskfile.yml"
            lines: list[str] = ["version: '3'", GeneralUtilities.empty_string, "tasks:", GeneralUtilities.empty_string]
            workspace_file_content: str = self.__sc.get_file_content(workspace_file)
            jsoncontent = json.loads(workspace_file_content)
            tasks = jsoncontent["tasks"]["tasks"]
            tasks.sort(key=lambda x: x["label"].split("/")[-1], reverse=False)  # sort by the label of the task
            for task in tasks:
                if task["type"] == "shell":

                    description: str = task["label"]
                    name: str = GeneralUtilities.to_pascal_case(description)
                    command = task["command"]
                    relative_script_file = task["command"]

                    relative_script_file = "."
                    cwd: str = None
                    if "options" in task:
                        options = task["options"]
                        if "cwd" in options:
                            cwd = options["cwd"]
                            cwd = cwd.replace("${workspaceFolder}", ".")
                            cwd = cwd.replace("\\", "\\\\").replace('"', '\\"')  # escape backslashes and double quotes for YAML
                            relative_script_file = cwd
                    if len(relative_script_file) == 0:
                        relative_script_file = "."

                    command_with_args = command
                    if "args" in task:
                        args = task["args"]
                        if len(args) > 1:
                            command_with_args = f"{command_with_args} {' '.join(args)}"

                    if "description" in task:
                        additional_description = task["description"]
                        description = f"{description} ({additional_description})"

                    if append_cli_args_at_end:
                        command_with_args = f"{command_with_args} {{{{.CLI_ARGS}}}}"

                    description_literal = description.replace("\\", "\\\\").replace('"', '\\"')  # escape backslashes and double quotes for YAML
                    command_with_args = command_with_args.replace("\\", "\\\\").replace('"', '\\"')  # escape backslashes and double quotes for YAML

                    lines.append(f"  {name}:")
                    lines.append(f'    desc: "{description_literal}"')
                    lines.append('    silent: true')
                    if cwd is not None:
                        lines.append(f'    dir: "{cwd}"')
                    lines.append("    cmds:")
                    lines.append(f'      - "{command_with_args}"')
                    lines.append('    aliases:')
                    lines.append(f'      - {name.lower()}')
                    if "aliases" in task:
                        aliases = task["aliases"]
                        for alias in aliases:
                            lines.append(f'      - {alias}')
                    lines.append(GeneralUtilities.empty_string)

            self.__sc.set_file_content(task_file, "\n".join(lines))
        else:
            self.__sc.run_program("scgeneratetasksfilefromworkspacefile", f"--repositoryfolder {repository_folder}")

    @GeneralUtilities.check_arguments
    def ensure_androidappbundletool_is_available(self, target_folder: str,enforce_update:bool) -> str:
        return self.ensure_file_from_github_assets_is_available_with_retry(target_folder, "google", "bundletool", "AndroidAppBundleTool", "bundletool.jar", lambda latest_version: f"bundletool-all-{latest_version}.jar",enforce_update=enforce_update)

    @GeneralUtilities.check_arguments
    def ensure_mediamtx_is_available(self, target_folder: str,enforce_update:bool) -> None:
        def download_and_extract(osname: str, osname_in_github_asset: str, extension: str):
            resource_name: str = f"MediaMTX_{osname}"
            zip_filename: str = f"{resource_name}.{extension}"
            resource_folder: str = os.path.join(target_folder, "Other", "Resources", resource_name)
            target_folder_extracted = os.path.join(resource_folder, "MediaMTX")
            update:bool=not os.path.isdir(target_folder_extracted) or GeneralUtilities.folder_is_empty(target_folder_extracted) or enforce_update
            if update:
                self.ensure_file_from_github_assets_is_available_with_retry(target_folder, "bluenviron", "mediamtx", resource_name, zip_filename, lambda latest_version: f"mediamtx_{latest_version}_{osname_in_github_asset}_amd64.{extension}",enforce_update=enforce_update)
                local_zip_file: str = os.path.join(resource_folder, f"{resource_name}.{extension}")
                GeneralUtilities.ensure_folder_exists_and_is_empty(target_folder_extracted)
                if extension == "zip":
                    with zipfile.ZipFile(local_zip_file, 'r') as zip_ref:
                        zip_ref.extractall(target_folder_extracted)
                elif extension == "tar.gz": 
                    with tarfile.open(local_zip_file, "r:gz") as tar:
                        tar.extractall(path=target_folder_extracted)
                else:
                    raise ValueError(f"Unknown extension: \"{extension}\"")
                GeneralUtilities.ensure_file_does_not_exist(local_zip_file)

        download_and_extract("Windows", "windows", "zip")
        download_and_extract("Linux", "linux", "tar.gz")
        download_and_extract("MacOS", "darwin", "tar.gz")
 
    @GeneralUtilities.check_arguments
    def clone_repository_as_resource(self, local_repository_folder: str, remote_repository_link: str, resource_name: str, repository_subname: str = None,use_cache:bool=True) -> None:
        self.__sc.log.log(f'Clone resource {resource_name}...')
        resrepo_commit_id_folder: str = os.path.join(local_repository_folder, "Other", "Resources", f"{resource_name}Version")
        resrepo_commit_id_file: str = os.path.join(resrepo_commit_id_folder, f"{resource_name}Version.txt")
        latest_version: str = GeneralUtilities.read_text_from_file(resrepo_commit_id_file)
        resrepo_data_folder: str = os.path.join(local_repository_folder, "Other", "Resources", resource_name).replace("\\", "/")
        current_version: str = None
        resrepo_data_version: str = os.path.join(resrepo_data_folder, f"{resource_name}Version.txt")
        if os.path.isdir(resrepo_data_folder):
            if os.path.isfile(resrepo_data_version):
                current_version = GeneralUtilities.read_text_from_file(resrepo_data_version)
        if (current_version is None) or (current_version != latest_version):
            target_folder: str = resrepo_data_folder
            if repository_subname is not None:
                target_folder = f"{resrepo_data_folder}/{repository_subname}"
            
            update:bool=not os.path.isdir(target_folder) or GeneralUtilities.folder_is_empty(target_folder) or not use_cache
            if update:
                self.__sc.log.log(f"Clone {remote_repository_link} as resource...", LogLevel.Information)
                GeneralUtilities.ensure_folder_exists_and_is_empty(target_folder)
                self.__sc.run_program("git", f"clone --recurse-submodules {remote_repository_link} {target_folder}")
                self.__sc.run_program("git", f"checkout {latest_version}", target_folder)
                GeneralUtilities.write_text_to_file(resrepo_data_version, latest_version)

                git_folders: list[str] = []
                git_files: list[str] = []
                for dirpath, dirnames, filenames in os.walk(target_folder):
                    for dirname in dirnames:
                        if dirname == ".git":
                            full_path = os.path.join(dirpath, dirname)
                            git_folders.append(full_path)
                    for filename in filenames:
                        if filename == ".git":
                            full_path = os.path.join(dirpath, filename)
                            git_files.append(full_path)
                for git_folder in git_folders:
                    if os.path.isdir(git_folder):
                        GeneralUtilities.ensure_directory_does_not_exist(git_folder)
                for git_file in git_files:
                    if os.path.isdir(git_file):
                        GeneralUtilities.ensure_file_does_not_exist(git_file)

    @GeneralUtilities.check_arguments
    def ensure_certificate_authority_for_development_purposes_is_generated(self, product_folder: str):
        product_name: str = os.path.basename(product_folder)
        now = GeneralUtilities.get_now()
        ca_name = f"{product_name}CA_{now.year:04}{now.month:02}{now.day:02}{now.hour:02}{now.min:02}{now.second:02}"
        ca_folder = os.path.join(product_folder, "Other", "Resources", "CA")
        generate_certificate = True
        if os.path.isdir(ca_folder):
            ca_files = [file for file in GeneralUtilities.get_direct_files_of_folder(ca_folder) if file.endswith(".crt")]
            if len(ca_files) > 0:
                ca_file = ca_files[-1]  # pylint:disable=unused-variable
                certificate_is_valid = True  # TODO check if certificate is really valid
                generate_certificate = not certificate_is_valid
        if generate_certificate:
            self.__sc.generate_certificate_authority(ca_folder, ca_name, "DE", "SubjST", "SubjL", "SubjO", "SubjOU")
        # TODO add switch to auto-install the script if desired
        # for windows: powershell Import-Certificate -FilePath ConSurvCA_20241121000236.crt -CertStoreLocation 'Cert:\CurrentUser\Root'
        # for linux: (TODO)

    @GeneralUtilities.check_arguments
    def generate_certificate_for_development_purposes_for_product(self, repository_folder: str):
        self.__sc.assert_is_git_repository(repository_folder)
        product_name = os.path.basename(repository_folder)
        ca_folder: str = os.path.join(repository_folder, "Other", "Resources", "CA")
        self.__generate_certificate_for_development_purposes(product_name, os.path.join(repository_folder, "Other", "Resources"), ca_folder, None)

    @GeneralUtilities.check_arguments
    def __generate_certificate_for_development_purposes(self, service_name: str, resources_folder: str, ca_folder: str, domain: str = None):
        if domain is None:
            domain = f"{service_name}.test.local"
        domain = domain.lower()
        resource_name: str = "DevelopmentCertificate"
        certificate_folder: str = os.path.join(resources_folder, resource_name)

        resource_content_filename: str = service_name+resource_name
        certificate_file = os.path.join(certificate_folder, f"{domain}.crt")
        unsignedcertificate_file = os.path.join(certificate_folder, f"{domain}.unsigned.crt")
        certificate_exists = os.path.exists(certificate_file)
        if certificate_exists:
            certificate_expired = GeneralUtilities.certificate_is_expired(certificate_file)
            generate_new_certificate = certificate_expired
        else:
            generate_new_certificate = True
        if generate_new_certificate:
            GeneralUtilities.ensure_directory_does_not_exist(certificate_folder)
            GeneralUtilities.ensure_directory_exists(certificate_folder)
            self.__sc.log.log("Generate TLS-certificate for development-purposes...")
            self.__sc.generate_certificate(certificate_folder, domain, resource_content_filename, "DE", "SubjST", "SubjL", "SubjO", "SubjOU")
            self.__sc.generate_certificate_sign_request(certificate_folder, domain, resource_content_filename, "DE", "SubjST", "SubjL", "SubjO", "SubjOU")
            ca_name = os.path.basename(self.__sc.find_last_file_by_extension(ca_folder, "crt"))[:-4]
            self.__sc.sign_certificate(certificate_folder, ca_folder, ca_name, domain, resource_content_filename)
            GeneralUtilities.ensure_file_does_not_exist(unsignedcertificate_file)
            self.__sc.log.log("Finished generating TLS-certificate for development-purposes...",LogLevel.Debug)

 
    @GeneralUtilities.check_arguments
    def do_npm_install(self, package_json_folder: str, npm_force: bool,use_cache:bool) -> None:
        target_folder:str=os.path.join(package_json_folder,"node_modules")
        update:bool=not os.path.isdir(target_folder) or GeneralUtilities.folder_is_empty(target_folder) or not use_cache
        if update:
            self.__sc.log.log("Do npm-install...")
            argument1 = "install"
            if npm_force:
                argument1 = f"{argument1} --force"
            self.__sc.run_with_epew("npm", argument1, package_json_folder)

            argument2 = "install --package-lock-only"
            if npm_force:
                argument2 = f"{argument2} --force"
            self.__sc.run_with_epew("npm", argument2, package_json_folder)

            argument3 = "clean-install"
            if npm_force:
                argument3 = f"{argument3} --force"
            self.__sc.run_with_epew("npm", argument3, package_json_folder)

    @staticmethod
    @GeneralUtilities.check_arguments
    def sort_reference_folder(folder1: str, folder2: str) -> int:
        """Returns a value greater than 0 if and only if folder1 has a base-folder-name with a with a higher version than the base-folder-name of folder2.
        Returns a value lower than 0 if and only if folder1 has a base-folder-name with a with a lower version than the base-folder-name of folder2.
        Returns 0 if both values are equal."""
        if (folder1 == folder2):
            return 0

        version_identifier_1 = os.path.basename(folder1)
        if version_identifier_1 == "Latest":
            return -1
        version_identifier_1 = version_identifier_1[1:]

        version_identifier_2 = os.path.basename(folder2)
        if version_identifier_2 == "Latest":
            return 1
        version_identifier_2 = version_identifier_2[1:]

        if version.parse(version_identifier_1) < version.parse(version_identifier_2):
            return -1
        elif version.parse(version_identifier_1) > version.parse(version_identifier_2):
            return 1
        else:
            return 0

    @GeneralUtilities.check_arguments
    def t4_transform(self, codeunit_folder: str, ignore_git_ignored_files: bool ,use_cache:bool):
        grylib_dll:str=self.__ensure_grylibrary_is_available(use_cache)
        repository_folder: str = os.path.dirname(codeunit_folder)
        codeunitname: str = os.path.basename(codeunit_folder)
        codeunit_folder = os.path.join(repository_folder, codeunitname)
        for search_result in Path(codeunit_folder).glob('**/*.tt'):
            tt_file = str(search_result)
            relative_path_to_tt_file_from_repository = str(Path(tt_file).relative_to(repository_folder))
            if (not ignore_git_ignored_files) or (ignore_git_ignored_files and not self.__sc.file_is_git_ignored(relative_path_to_tt_file_from_repository, repository_folder)):
                relative_path_to_tt_file_from_codeunit_file = str(Path(tt_file).relative_to(codeunit_folder))
                argument = [f"--parameter=repositoryFolder={repository_folder}", f"--parameter=codeUnitName={codeunitname}", f"--parameter=gryLibraryDLLFile={grylib_dll}", relative_path_to_tt_file_from_codeunit_file]
                self.__sc.run_program_argsasarray("t4", argument, codeunit_folder)

    @GeneralUtilities.check_arguments
    def __ensure_grylibrary_is_available(self, use_cache:bool) -> None:
        grylibrary_folder =os.path.join( self.__sc.get_global_cache_folder(),"Tools","GRYLibrary")
        grylibrary_dll_file = os.path.join(grylibrary_folder, "BuildResult_DotNet_win-x64", "GRYLibrary.dll")
        grylibrary_dll_file_exists = os.path.isfile(grylibrary_dll_file)
        if not os.path.isfile(grylibrary_dll_file):
            self.__sc.log.log("Download GRYLibrary to global cache...",LogLevel.Information)
            grylibrary_latest_codeunit_file = "https://raw.githubusercontent.com/anionDev/GRYLibrary/stable/GRYLibrary/GRYLibrary.codeunit.xml"
            with urllib.request.urlopen(grylibrary_latest_codeunit_file) as url_result:
                grylibrary_latest_version = self.get_version_of_codeunit_filecontent(url_result.read().decode("utf-8"))
            if grylibrary_dll_file_exists:
                grylibrary_existing_codeunit_file = os.path.join(grylibrary_folder, "SourceCode", "GRYLibrary.codeunit.xml")
                grylibrary_existing_codeunit_version = self.get_version_of_codeunit(grylibrary_existing_codeunit_file)
                if grylibrary_existing_codeunit_version != grylibrary_latest_version:
                    GeneralUtilities.ensure_directory_does_not_exist(grylibrary_folder)
            GeneralUtilities.ensure_directory_does_not_exist(grylibrary_folder)
            GeneralUtilities.ensure_directory_exists(grylibrary_folder)
            archive_name = f"GRYLibrary.v{grylibrary_latest_version}.Artifacts.zip"
            archive_download_link = f"https://github.com/anionDev/GRYLibrary/releases/download/v{grylibrary_latest_version}/{archive_name}"
            archive_file = os.path.join(grylibrary_folder, archive_name)
            urllib.request.urlretrieve(archive_download_link, archive_file)
            with zipfile.ZipFile(archive_file, 'r') as zip_ref:
                zip_ref.extractall(grylibrary_folder)
            GeneralUtilities.ensure_file_does_not_exist(archive_file)
            GeneralUtilities.assert_file_exists(grylibrary_dll_file)
        return grylibrary_dll_file
    
    @GeneralUtilities.check_arguments
    def ensure_ffmpeg_is_available(self, codeunit_folder: str,use_cache:bool) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        ffmpeg_folder = os.path.join(codeunit_folder, "Other", "Resources", "FFMPEG")
        internet_connection_is_available = GeneralUtilities.internet_connection_is_available()
        exe_file = f"{ffmpeg_folder}/ffmpeg.exe"
        exe_file_exists = os.path.isfile(exe_file)
        update:bool=(not exe_file_exists) or (not use_cache)
        if update:
            if internet_connection_is_available:  # Load/Update
                GeneralUtilities.ensure_directory_does_not_exist(ffmpeg_folder)
                GeneralUtilities.ensure_directory_exists(ffmpeg_folder)
                ffmpeg_temp_folder = ffmpeg_folder+"Temp"
                GeneralUtilities.ensure_directory_does_not_exist(ffmpeg_temp_folder)
                GeneralUtilities.ensure_directory_exists(ffmpeg_temp_folder)
                zip_file_on_disk = os.path.join(ffmpeg_temp_folder, "ffmpeg.zip")
                original_zip_filename = "ffmpeg-master-latest-win64-gpl-shared"
                zip_link = f"https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/{original_zip_filename}.zip"
                urllib.request.urlretrieve(zip_link, zip_file_on_disk)
                shutil.unpack_archive(zip_file_on_disk, ffmpeg_temp_folder)
                bin_folder_source = os.path.join(ffmpeg_temp_folder, "ffmpeg-master-latest-win64-gpl-shared/bin")
                bin_folder_target = ffmpeg_folder
                GeneralUtilities.copy_content_of_folder(bin_folder_source, bin_folder_target)
                GeneralUtilities.ensure_directory_does_not_exist(ffmpeg_temp_folder)
            else:
                if exe_file_exists:
                    self.__sc.log.log("Can not check for updates of FFMPEG due to missing internet-connection.")
                else:
                    raise ValueError("Can not download FFMPEG.")

    @GeneralUtilities.check_arguments
    def set_constants_for_certificate_private_information(self, codeunit_folder: str) -> None:
        """Expects a certificate-resource and generates a constant for its sensitive information in hex-format"""
        self.assert_is_codeunit_folder(codeunit_folder)
        repo_name:str=os.path.basename(GeneralUtilities.resolve_relative_path("..",codeunit_folder))
        resource_name: str = "DevelopmentCertificate"
        filename: str = repo_name+"DevelopmentCertificate"
        self.generate_constant_from_resource_by_filename(codeunit_folder, resource_name, f"{filename}.pfx", "PFX")
        self.generate_constant_from_resource_by_filename(codeunit_folder, resource_name, f"{filename}.password", "Password")

    @GeneralUtilities.check_arguments
    def generate_constant_from_resource_by_filename(self, codeunit_folder: str, resource_name: str, filename: str, constant_name: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        certificate_resource_folder = GeneralUtilities.resolve_relative_path(f"Other/Resources/{resource_name}", codeunit_folder)
        resource_file = os.path.join(certificate_resource_folder, filename)
        resource_file_content = GeneralUtilities.read_binary_from_file(resource_file)
        resource_file_as_hex = resource_file_content.hex()
        self.set_constant(codeunit_folder, f"{resource_name}{constant_name}Hex", resource_file_as_hex)

    @GeneralUtilities.check_arguments
    def get_resource_from_global_resource(self, codeunit_folder: str, resource_name: str):
        repository_folder: str = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        source_folder: str = os.path.join(repository_folder, "Other", "Resources", resource_name)
        target_folder: str = os.path.join(codeunit_folder, "Other", "Resources", resource_name)
        GeneralUtilities.ensure_folder_exists_and_is_empty(target_folder)
        GeneralUtilities.copy_content_of_folder(source_folder, target_folder)


    @GeneralUtilities.check_arguments
    def merge_packages(self,coverage_file:str,package_name:str) -> None:
        tree = etree.parse(coverage_file) 
        root = tree.getroot()
        packages = root.findall("./packages/package")
        all_classes = []
        for pkg in packages:
            pkg_name:str=pkg.get("name")
            if len(packages)==1 or ( pkg_name==package_name or pkg_name.startswith(f"{package_name}.")):
                classes = pkg.find("classes")
                if classes is not None:
                    all_classes.extend(classes.findall("class"))
        new_package = etree.Element("package", name=package_name)
        new_classes = etree.SubElement(new_package, "classes")
        for cls in all_classes:
            new_classes.append(cls)
        packages_node = root.find("./packages")
        packages_node.clear()
        packages_node.append(new_package)
        tree.write(coverage_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        self.calculate_entire_line_rate(coverage_file)

    
    @GeneralUtilities.check_arguments
    def calculate_entire_line_rate(self,coverage_file:str) -> None:
        tree = etree.parse(coverage_file)
        root = tree.getroot()
        package = root.find("./packages/package")
        if package is None:
            raise RuntimeError("No <package>-Element found")

        line_elements = package.findall(".//line")

        amount_of_lines = 0
        amount_of_hited_lines = 0

        for line in line_elements:
            amount_of_lines += 1
            hits = int(line.get("hits", "0"))
            if hits > 0:
                amount_of_hited_lines += 1
        line_rate = amount_of_hited_lines / amount_of_lines if amount_of_lines > 0 else 0.0
        package.set("line-rate", str(line_rate))
        tree.write(coverage_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")


    @GeneralUtilities.check_arguments
    def generate_api_client_from_dependent_codeunit_with_default_properties(self, codeunit_folder:str, name_of_api_providing_codeunit: str, target_subfolder_in_codeunit: str,language:str,use_cache:bool) -> None:
        self.generate_api_client_from_dependent_codeunit(codeunit_folder,name_of_api_providing_codeunit,target_subfolder_in_codeunit,language,use_cache,["models","apis"])

    @GeneralUtilities.check_arguments
    def generate_api_client_from_dependent_codeunit(self, codeunit_folder:str, name_of_api_providing_codeunit: str, target_subfolder_in_codeunit: str,language:str,use_cache:bool,properties:list[str]) -> None:
        openapigenerator_jar_file = self.ensure_openapigenerator_is_available(use_cache)
        openapi_spec_file = os.path.join(codeunit_folder, "Other", "Resources", "DependentCodeUnits", name_of_api_providing_codeunit, "APISpecification", f"{name_of_api_providing_codeunit}.latest.api.json")
        target_folder = os.path.join(codeunit_folder, target_subfolder_in_codeunit)
        GeneralUtilities.ensure_folder_exists_and_is_empty(target_folder)
        argument=f'-jar {openapigenerator_jar_file} generate -i {openapi_spec_file} -g {language} -o {target_folder}'
        for property_value in properties:
            argument=f"{argument} --global-property {property_value}"
        self.__sc.run_program("java",argument , codeunit_folder)

    @GeneralUtilities.check_arguments
    def replace_version_in_packagejson_file(self, packagejson_file: str, codeunit_version: str) -> None:
        encoding = "utf-8"
        with open(packagejson_file, encoding=encoding) as f:
            data = json.load(f)
        data['version'] = codeunit_version
        with open(packagejson_file, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=2)
        GeneralUtilities.write_text_to_file(packagejson_file, GeneralUtilities.read_text_from_file(packagejson_file).replace("\r", ""))

    @GeneralUtilities.check_arguments
    def ensure_openapigenerator_is_available(self,use_cache:bool) -> None:
        openapigenerator_folder = os.path.join(self.__sc.get_global_cache_folder(), "Tools", "OpenAPIGenerator")
        filename = "open-api-generator.jar"
        jar_file = f"{openapigenerator_folder}/{filename}"
        jar_file_exists = os.path.isfile(jar_file)
        update:bool=not jar_file_exists or not use_cache
        if update:
            self.__sc.log.log("Download OpenAPIGeneratorCLI...",LogLevel.Debug)
            used_version ="7.16.0"#TODO retrieve latest version
            download_link = f"https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/{used_version}/openapi-generator-cli-{used_version}.jar"
            GeneralUtilities.ensure_directory_does_not_exist(openapigenerator_folder)
            GeneralUtilities.ensure_directory_exists(openapigenerator_folder)
            urllib.request.urlretrieve(download_link, jar_file)
        GeneralUtilities.assert_file_exists(jar_file)
        return jar_file

    @GeneralUtilities.check_arguments
    def standardized_tasks_update_version_in_docker_examples(self, codeunit_folder:str, codeunit_version:str) -> None:
        codeunit_name = os.path.basename(codeunit_folder)
        codeunit_name_lower = codeunit_name.lower()
        examples_folder = GeneralUtilities.resolve_relative_path("Other/Reference/ReferenceContent/Examples", codeunit_folder)
        for example_folder in GeneralUtilities.get_direct_folders_of_folder(examples_folder):
            docker_compose_file = os.path.join(example_folder, "docker-compose.yml")
            if os.path.isfile(docker_compose_file):
                filecontent = GeneralUtilities.read_text_from_file(docker_compose_file)
                replaced = re.sub(f'image:\\s+{codeunit_name_lower}:\\d+\\.\\d+\\.\\d+', f"image: {codeunit_name_lower}:{codeunit_version}", filecontent)
                GeneralUtilities.write_text_to_file(docker_compose_file, replaced)

    @GeneralUtilities.check_arguments
    def set_version_of_openapigenerator(self, codeunit_folder: str, used_version: str = None) -> None:
        target_folder: str = os.path.join(codeunit_folder, "Other", "Resources", "Dependencies", "OpenAPIGenerator")
        version_file = os.path.join(target_folder, "Version.txt")
        GeneralUtilities.ensure_directory_exists(target_folder)
        GeneralUtilities.ensure_file_exists(version_file)
        GeneralUtilities.write_text_to_file(version_file, used_version)

    @GeneralUtilities.check_arguments
    def get_latest_version_of_openapigenerator(self) -> None:
        headers = {'Cache-Control': 'no-cache'}
        self.__add_github_api_key_if_available(headers)
        response = requests.get(f"https://api.github.com/repos/OpenAPITools/openapi-generator/releases", headers=headers, timeout=(10, 10))
        latest_version = response.json()["tag_name"]
        return latest_version

    @GeneralUtilities.check_arguments
    def update_images_in_example(self, codeunit_folder: str):
        iu = ImageUpdater()
        iu.add_default_mapper()
        dockercomposefile: str = f"{codeunit_folder}\\Other\\Reference\\ReferenceContent\\Examples\\MinimalDockerComposeFile\\docker-compose.yml"
        excluded = ["opendms"]
        iu.update_all_services_in_docker_compose_file(dockercomposefile, VersionEcholon.LatestPatchOrLatestMinor, excluded)
        iu.check_for_newest_version(dockercomposefile, excluded)

    @GeneralUtilities.check_arguments
    def push_wheel_build_artifact(self, push_build_artifacts_file,  codeunitname, repository: str, apikey: str, gpg_identity: str, repository_folder_name: str,verbosity:LogLevel) -> None:
        folder_of_this_file = os.path.dirname(push_build_artifacts_file)
        repository_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}../Submodules{os.path.sep}{repository_folder_name}", folder_of_this_file)
        wheel_file = self.get_wheel_file(repository_folder, codeunitname)
        self.__standardized_tasks_push_wheel_file_to_registry(wheel_file, apikey, repository, gpg_identity,verbosity)

    @GeneralUtilities.check_arguments
    def get_wheel_file(self, repository_folder: str, codeunit_name: str) -> str:
        self.__sc.assert_is_git_repository(repository_folder)
        return self.__sc.find_file_by_extension(os.path.join(repository_folder, codeunit_name,"Other","Artifacts", "BuildResult_Wheel"), "whl")

    @GeneralUtilities.check_arguments
    def __standardized_tasks_push_wheel_file_to_registry(self, wheel_file: str, api_key: str, repository: str, gpg_identity: str,verbosity:LogLevel) -> None:
        # repository-value when PyPi should be used: "pypi"
        # gpg_identity-value when wheel-file should not be signed: None
        folder = os.path.dirname(wheel_file)
        filename = os.path.basename(wheel_file)

        if gpg_identity is None:
            gpg_identity_argument = GeneralUtilities.empty_string
        else:
            gpg_identity_argument = GeneralUtilities.empty_string  # f" --sign --identity {gpg_identity}"
            # disabled due to https://blog.pypi.org/posts/2023-05-23-removing-pgp/

        if int(LogLevel.Information)<int(verbosity):
            verbose_argument = " --verbose"
        else:
            verbose_argument = GeneralUtilities.empty_string

        twine_argument = f"upload{gpg_identity_argument} --repository {repository} --non-interactive {filename} --disable-progress-bar"
        twine_argument = f"{twine_argument} --username __token__ --password {api_key}{verbose_argument}"
        self.__sc.run_program("twine", twine_argument, folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def push_nuget_build_artifact(self, push_script_file: str, repository_folder_name: str,  codeunitname: str, registry_address: str,api_key: str):
        build_artifact_folder = GeneralUtilities.resolve_relative_path(f"../../Submodules/{repository_folder_name}/{codeunitname}/Other/Artifacts/BuildResult_NuGet", os.path.dirname(push_script_file))
        self.__sc.push_nuget_build_artifact(self.__sc.find_file_by_extension(build_artifact_folder, "nupkg"), registry_address, api_key)

    @GeneralUtilities.check_arguments
    def suport_information_exists(self, repository_folder: str, version_of_product: str) -> bool:
        self.__sc.assert_is_git_repository(repository_folder)
        folder = os.path.join(repository_folder, "Other", "Resources", "Support")
        file = os.path.join(folder, "InformationAboutSupportedVersions.csv")
        if not os.path.isfile(file):
            return False
        entries = GeneralUtilities.read_csv_file(file, True)
        for entry in entries:
            if entry[0] == version_of_product:
                return True
        return False
    
    @GeneralUtilities.check_arguments
    def mark_current_version_as_supported(self, repository_folder: str, version_of_product: str, supported_from: datetime, supported_until: datetime):
        self.__sc.assert_is_git_repository(repository_folder)
        if self.suport_information_exists(repository_folder, version_of_product):
            raise ValueError(f"Version-support for v{version_of_product} already defined.")
        folder = os.path.join(repository_folder, "Other", "Resources", "Support")
        GeneralUtilities.ensure_directory_exists(folder)
        file = os.path.join(folder, "InformationAboutSupportedVersions.csv")
        if not os.path.isfile(file):
            GeneralUtilities.ensure_file_exists(file)
            GeneralUtilities.append_line_to_file(file, "Version;SupportBegin;SupportEnd")
        GeneralUtilities.append_line_to_file(file, f"{version_of_product};{GeneralUtilities.datetime_to_string(supported_from)};{GeneralUtilities.datetime_to_string(supported_until)}")


    @GeneralUtilities.check_arguments
    def add_github_release(self, productname: str, projectversion: str, build_artifacts_folder: str, github_username: str, repository_folder: str, additional_attached_files: list[str]) -> None:
        self.__sc.assert_is_git_repository(repository_folder)
        self.__sc.log.log(f"Create GitHub-release for {productname}...")
        github_repo = f"{github_username}/{productname}"
        artifact_files = []
        codeunits = self.get_codeunits(repository_folder)
        for codeunit in codeunits:
            artifact_files.append(self.__sc.find_file_by_extension(f"{build_artifacts_folder}/{productname}/{projectversion}/{codeunit}", "Artifacts.zip"))
        if additional_attached_files is not None:
            for additional_attached_file in additional_attached_files:
                artifact_files.append(additional_attached_file)
        changelog_file = os.path.join(repository_folder, "Other", "Resources", "Changelog", f"v{projectversion}.md")
        self.__sc.run_program_argsasarray("gh", ["release", "create", f"v{projectversion}", "--repo",  github_repo, "--notes-file", changelog_file, "--title", f"Release v{projectversion}"]+artifact_files)

    @GeneralUtilities.check_arguments
    def update_dependency_in_resources_folder(self, update_dependencies_file, dependency_name: str, latest_version_function: str) -> None:
        dependency_folder = GeneralUtilities.resolve_relative_path(f"../Resources/Dependencies/{dependency_name}", update_dependencies_file)
        version_file = os.path.join(dependency_folder, "Version.txt")
        version_file_exists = os.path.isfile(version_file)
        write_to_file = False
        if version_file_exists:
            current_version = GeneralUtilities.read_text_from_file(version_file)
            if current_version != latest_version_function:
                write_to_file = True
        else:
            GeneralUtilities.ensure_directory_exists(dependency_folder)
            GeneralUtilities.ensure_file_exists(version_file)
            write_to_file = True
        if write_to_file:
            GeneralUtilities.write_text_to_file(version_file, latest_version_function)


    @GeneralUtilities.check_arguments
    def push_docker_build_artifact(self, push_artifacts_file: str, registry: str, push_readme: bool, repository_folder_name: str, remote_image_name: str = None) -> None:
        folder_of_this_file = os.path.dirname(push_artifacts_file)
        filename = os.path.basename(push_artifacts_file)
        codeunitname_regex: str = "([a-zA-Z0-9]+)"
        filename_regex: str = f"PushArtifacts\\.{codeunitname_regex}\\.py"
        if match := re.search(filename_regex, filename, re.IGNORECASE):
            codeunitname = match.group(1)
        else:
            raise ValueError(f"Expected push-artifacts-file to match the regex \"{filename_regex}\" where \"{codeunitname_regex}\" represents the codeunit-name.")
        
        repository_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}..{os.path.sep}Submodules{os.path.sep}{repository_folder_name}", folder_of_this_file)
        codeunit_folder = os.path.join(repository_folder, codeunitname)
        artifacts_folder = os.path.join(repository_folder,codeunitname, "Other", "Artifacts")
        applicationimage_folder = os.path.join(artifacts_folder, "BuildResult_OCIImage")
        image_file = self.__sc.find_file_by_extension(applicationimage_folder, "tar")
        image_filename = os.path.basename(image_file)
        codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunitname}.codeunit.xml"))
        if remote_image_name is None:
            remote_image_name = codeunitname
        remote_image_name = remote_image_name.lower()
        local_image_name = codeunitname.lower()
        remote_repo = f"{registry}/{remote_image_name}"
        remote_image_latest = f"{remote_repo}:latest"
        remote_image_version = f"{remote_repo}:{codeunit_version}"
        self.__sc.log.log("Load image...")
        self.__sc.run_program("docker", f"load --input {image_filename}", applicationimage_folder)
        self.__sc.log.log("Tag image...")
        self.__sc.run_program_with_retry("docker", f"tag {local_image_name}:{codeunit_version} {remote_image_latest}")
        self.__sc.run_program_with_retry("docker", f"tag {local_image_name}:{codeunit_version} {remote_image_version}")
        self.__sc.log.log("Push image...")
        self.__sc.run_program_with_retry("docker", f"push {remote_image_latest}")
        self.__sc.run_program_with_retry("docker", f"push {remote_image_version}")
        if push_readme:
            self.__sc.run_program_with_retry("docker-pushrm", f"{remote_repo}", codeunit_folder)

    def prepare_building_codeunits(self,repository_folder:str,use_cache:bool,generate_development_certificate:bool):        
        if generate_development_certificate:
            self.ensure_certificate_authority_for_development_purposes_is_generated(repository_folder)
            self.generate_certificate_for_development_purposes_for_product(repository_folder)
        self.generate_tasksfile_from_workspace_file(repository_folder)
        self.generate_codeunits_overview_diagram(repository_folder)
        self.generate_svg_files_from_plantuml_files_for_repository(repository_folder,use_cache)

    @GeneralUtilities.check_arguments
    def copy_product_resource_to_codeunit_resource_folder(self, codeunit_folder: str, resourcename: str) -> None:
        repository_folder = GeneralUtilities.resolve_relative_path(f"..", codeunit_folder)
        self.__sc.assert_is_git_repository(repository_folder)
        src_folder = GeneralUtilities.resolve_relative_path(f"Other/Resources/{resourcename}", repository_folder)
        GeneralUtilities.assert_condition(os.path.isdir(src_folder), f"Required product-resource {resourcename} does not exist. Expected folder: {src_folder}")
        trg_folder = GeneralUtilities.resolve_relative_path(f"Other/Resources/{resourcename}", codeunit_folder)
        GeneralUtilities.ensure_directory_does_not_exist(trg_folder)
        GeneralUtilities.ensure_directory_exists(trg_folder)
        GeneralUtilities.copy_content_of_folder(src_folder, trg_folder)
        
    @GeneralUtilities.check_arguments
    def ensure_containers_are_not_running(self, container_names_to_remove:list[str]) -> None:
        for container_name in container_names_to_remove:
            self.__sc.log.log(f"Ensure container {container_name} does not exist...")
            self.__sc.run_program("docker", f"container rm -f {container_name}", throw_exception_if_exitcode_is_not_zero=False)
        
    @GeneralUtilities.check_arguments
    def load_docker_image(self, oci_image_artifacts_folder:str) -> None:
        image_filename = os.path.basename(self.__sc.find_file_by_extension(oci_image_artifacts_folder, "tar"))
        self.__sc.log.log("Load docker-image...")
        self.__sc.run_program("docker", f"load -i {image_filename}", oci_image_artifacts_folder)

    @GeneralUtilities.check_arguments
    def start_dockerfile_example(self, current_file: str,remove_old_container: bool, remove_volumes_folder: bool, env_file: str) -> None:
        container_names_to_remove:list[str]=[]
        folder_of_current_file = os.path.dirname(current_file)
        if remove_old_container:
            docker_compose_file = f"{folder_of_current_file}/docker-compose.yml"
            lines = GeneralUtilities.read_lines_from_file(docker_compose_file)
            for line in lines:
                if match := re.search("container_name:\\s*'?([^']+)'?", line):
                    container_names_to_remove.append(match.group(1))
            self.__sc.log.log(f"Ensure container of {docker_compose_file} do not exist...")
        oci_image_artifacts_folder = GeneralUtilities.resolve_relative_path("../../../../Artifacts/BuildResult_OCIImage", folder_of_current_file)
        self.ensure_containers_are_not_running(container_names_to_remove)
        self.load_docker_image(oci_image_artifacts_folder)
        example_name = os.path.basename(folder_of_current_file)
        codeunit_name = os.path.basename(GeneralUtilities.resolve_relative_path("../../../../..", folder_of_current_file))
        if remove_volumes_folder:
            volumes_folder = os.path.join(folder_of_current_file, "Volumes")
            self.__sc.log.log(f"Ensure volumes-folder '{volumes_folder}' does not exist...")
            GeneralUtilities.ensure_directory_does_not_exist(volumes_folder)
            GeneralUtilities.ensure_directory_exists(volumes_folder)
        docker_project_name = f"{codeunit_name}_{example_name}".lower()
        self.__sc.log.log("Start docker-container...")
        argument = f"compose --project-name {docker_project_name}"
        if env_file is not None:
            argument = f"{argument} --env-file {env_file}"
        argument = f"{argument} up --detach"
        self.__sc.run_program("docker", argument, folder_of_current_file)

    @GeneralUtilities.check_arguments
    def ensure_env_file_is_generated(self, current_file: str, env_file_name: str, env_values: dict[str, str]):
        folder = os.path.dirname(current_file)
        env_file = os.path.join(folder, env_file_name)
        if not os.path.isfile(env_file):
            lines = []
            for key, value in env_values.items():
                lines.append(f"{key}={value}")
            GeneralUtilities.write_lines_to_file(env_file, lines)

    @GeneralUtilities.check_arguments
    def stop_dockerfile_example(self, current_file: str, remove_old_container: bool, remove_volumes_folder: bool) -> None:
        folder = os.path.dirname(current_file)
        example_name = os.path.basename(folder)
        codeunit_name = os.path.basename(GeneralUtilities.resolve_relative_path("../../../../..", folder))
        docker_project_name = f"{codeunit_name}_{example_name}".lower()
        self.__sc.log.log("Stop docker-container...")
        self.__sc.run_program("docker", f"compose --project-name {docker_project_name} down", folder)
        if  remove_old_container:
            pass#TODO
        if  remove_volumes_folder:
            pass#TODO

    @GeneralUtilities.check_arguments
    def update_submodule(self, repository_folder: str, submodule_name: str, local_branch: str = "main", remote_branch: str = "main", remote: str = "origin"):
        submodule_folder = GeneralUtilities.resolve_relative_path("Other/Resources/Submodules/"+submodule_name, repository_folder)
        self.__sc.git_fetch(submodule_folder, remote)
        self.__sc.git_checkout(submodule_folder, local_branch)
        self.__sc.git_pull(submodule_folder, remote, local_branch, remote_branch, True)
        current_version = self.__sc.get_semver_version_from_gitversion(repository_folder)
        changelog_file = os.path.join(repository_folder, "Other", "Resources", "Changelog", f"v{current_version}.md")
        if (not os.path.isfile(changelog_file)):
            GeneralUtilities.ensure_file_exists(changelog_file)
            GeneralUtilities.write_text_to_file(changelog_file, """# Release notes

## Changes

- Updated geo-ip-database.
""")

    def set_latest_version_for_clone_repository_as_resource(self,repository_folder:str, resourcename: str, github_link: str, branch: str = "main"):

        resrepo_commit_id_folder: str = os.path.join(repository_folder, "Other", "Resources", f"{resourcename}Version")
        resrepo_commit_id_file: str = os.path.join(resrepo_commit_id_folder, f"{resourcename}Version.txt")
        current_version: str = GeneralUtilities.read_text_from_file(resrepo_commit_id_file)

        stdOut = [l.split("\t") for l in GeneralUtilities.string_to_lines(self.__sc.run_program("git", f"ls-remote {github_link}")[1])]
        stdOut = [l for l in stdOut if l[1] == f"refs/heads/{branch}"]
        GeneralUtilities.assert_condition(len(stdOut) == 1)
        latest_version: str = stdOut[0][0]
        if current_version != latest_version:
            GeneralUtilities.write_text_to_file(resrepo_commit_id_file, latest_version)

    @GeneralUtilities.check_arguments
    def get_dependencies_which_are_ignored_from_updates(self, codeunit_folder: str) -> list[str]:
        self.assert_is_codeunit_folder(codeunit_folder)
        namespaces = {'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        codeunit_name = os.path.basename(codeunit_folder)
        codeunit_file = os.path.join(codeunit_folder, f"{codeunit_name}.codeunit.xml")
        root: etree._ElementTree = etree.parse(codeunit_file)
        ignoreddependencies = root.xpath('//cps:codeunit/cps:properties/cps:updatesettings/cps:ignoreddependencies/cps:ignoreddependency', namespaces=namespaces)
        result = [x.text.replace("\\n", GeneralUtilities.empty_string).replace("\\r", GeneralUtilities.empty_string).replace("\n", GeneralUtilities.empty_string).replace("\r", GeneralUtilities.empty_string).strip() for x in ignoreddependencies]
        return result
    
    @GeneralUtilities.check_arguments
    def update_dependencies_of_package_json(self, folder_of_package_json: str) -> None:#TODO this should probably be implemented in TFCPS_CodeUnitSpecific_NodeJS_Functions
        #TODO move this to TFCPS_CodeUnitSpecific_NodeJS_Functions
        if self.is_codeunit_folder(folder_of_package_json):
            ignored_dependencies = self.get_dependencies_which_are_ignored_from_updates(folder_of_package_json)
        else:
            ignored_dependencies = []
        # TODO consider ignored_dependencies
        result = self.__sc.run_with_epew("npm", "outdated", folder_of_package_json, throw_exception_if_exitcode_is_not_zero=False)
        if result[0] == 0:
            return  # all dependencies up to date
        elif result[0] == 1:
            package_json_content = None
            package_json_file = f"{folder_of_package_json}/package.json"
            with open(package_json_file, "r", encoding="utf-8") as package_json_file_object:
                package_json_content = json.load(package_json_file_object)
                lines = GeneralUtilities.string_to_lines(result[1])[1:][:-1]
                for line in lines:
                    normalized_line_splitted = ' '.join(line.split()).split(" ")
                    package = normalized_line_splitted[0]
                    latest_version = normalized_line_splitted[3]
                    if package in package_json_content["dependencies"]:
                        package_json_content["dependencies"][package] = latest_version
                    if package in package_json_content["devDependencies"]:
                        package_json_content["devDependencies"][package] = latest_version
            with open(package_json_file, "w", encoding="utf-8") as package_json_file_object:
                json.dump(package_json_content, package_json_file_object, indent=4)
            GeneralUtilities.write_text_to_file(package_json_file, GeneralUtilities.read_text_from_file(package_json_file).replace("\r", ""))
            self.do_npm_install(folder_of_package_json, True,True)#TODO use_cache might be dangerous here
        else:
            self.__sc.log.log("Update dependencies resulted in an error.", LogLevel.Error)


    @GeneralUtilities.check_arguments
    def get_resource_from_submodule_with_default_ignore_pattern(self,codeunit_folder:str,submodule_name:str,resource_name:str):
        self.get_resource_from_submodule(codeunit_folder,submodule_name,resource_name,["**.git","**.gitmodules"])
        
    @GeneralUtilities.check_arguments
    def get_resource_from_submodule(self,codeunit_folder:str,submodule_name:str,resource_name:str,ignore_patterns:list[str]):
        self.assert_is_codeunit_folder(codeunit_folder)
        repository=os.path.dirname(codeunit_folder)
        source_folder=os.path.join(repository,"Other","Resources","Submodules",submodule_name)
        GeneralUtilities.assert_folder_exists(source_folder)
        target_folder=os.path.join(codeunit_folder,"Other","Resources",resource_name)
        GeneralUtilities.ensure_folder_exists_and_is_empty(target_folder)
        GeneralUtilities.copy_content_of_folder(source_folder,target_folder,True,ignore_patterns)


    @GeneralUtilities.check_arguments
    def pull_images_of_test_services(self,repository_folder:str,env_variables:dict[str,str],fallback_registries:dict[str,str]):
        if env_variables is None:
            env_variables={}
        if fallback_registries is None:
            fallback_registries={}
        for image,fallback_registry in fallback_registries.items():
            env_variables[f"image_{image}"]=self.__sc.get_image_with_registry_for_docker_image(image,None,fallback_registry)
        test_services=GeneralUtilities.get_direct_folders_of_folder(os.path.join(repository_folder,"Other","Resources","LocalTestServices"))
        if 0<len(test_services):
            self.__sc.log.log("Pull images for local test-services...")
        for test_service_folder in test_services:
            test_service_name=os.path.basename(test_service_folder)
            self.__sc.log.log(f"Pull images for test-service {test_service_name}...")
            arguments=f"compose -f docker-compose.yml"
            if env_variables:
                env_variables_file=os.path.join(test_service_folder,"Parameters.env")
                GeneralUtilities.ensure_file_exists(env_variables_file)
                lines=[]
                for k,v in env_variables.items():
                    lines=lines+[f"{k}={v}"]
                GeneralUtilities.write_lines_to_file(env_variables_file,lines)
                arguments=arguments+" --env-file Parameters.env"
            else:
                GeneralUtilities.ensure_file_does_not_exist(env_variables_file)
            arguments=arguments+" pull --quiet"
            self.__sc.run_program("docker",arguments,test_service_folder,print_live_output=self.__sc.log.loglevel==LogLevel.Debug)
