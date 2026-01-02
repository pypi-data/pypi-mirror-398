import os
import re
from lxml import etree
from ...GeneralUtilities import GeneralUtilities
from ...SCLog import  LogLevel
from ..TFCPS_CodeUnitSpecific_Base import TFCPS_CodeUnitSpecific_Base,TFCPS_CodeUnitSpecific_Base_CLI

class TFCPS_CodeUnitSpecific_NodeJS_Functions(TFCPS_CodeUnitSpecific_Base):


    def __init__(self,current_file:str,verbosity:LogLevel,targetenvironmenttype:str,use_cache:bool,is_pre_merge:bool):
        super().__init__(current_file, verbosity,targetenvironmenttype,use_cache,is_pre_merge)


    @GeneralUtilities.check_arguments
    def build(self) -> None:
        self._protected_sc.run_with_epew("npm", "run build", self.get_codeunit_folder(),print_live_output=self._protected_sc.log.loglevel==LogLevel.Diagnostic,encode_argument_in_base64=True)
        self.standardized_tasks_build_bom_for_node_project()
        self.copy_source_files_to_output_directory()

    @GeneralUtilities.check_arguments
    def linting(self) -> None:
        self._protected_sc.run_with_epew("npm", "run lint", self.get_codeunit_folder(),print_live_output=self._protected_sc.log.loglevel==LogLevel.Diagnostic,encode_argument_in_base64=True)

    @GeneralUtilities.check_arguments
    def do_common_tasks(self,current_codeunit_version:str)-> None:
        codeunit_version = current_codeunit_version
        codeunit_folder = self.get_codeunit_folder()
        self.do_common_tasks_base(current_codeunit_version)
        self.tfcps_Tools_General.replace_version_in_packagejson_file(GeneralUtilities.resolve_relative_path("./package.json", codeunit_folder), codeunit_version)
        self.tfcps_Tools_General.do_npm_install(codeunit_folder, True,self.use_cache())
        #if generateAPIClientBase.generate_api_client():
        #    generateAPIClientGenerate:GenerateAPIClientGenerate=generateAPIClientBase
        #    self.tfcps_Tools_General.generate_api_client_from_dependent_codeunit_in_angular(codeunit_folder, generateAPIClientGenerate.name_of_api_providing_codeunit,generateAPIClientGenerate.generate_api_client)
  
    @GeneralUtilities.check_arguments
    def generate_reference(self) -> None:
        self.generate_reference_using_docfx()

    
    @GeneralUtilities.check_arguments
    def run_testcases(self) -> None:
        # prepare
        codeunit_name: str =self.get_codeunit_name()
        
        codeunit_folder =self.get_codeunit_folder()
        repository_folder = os.path.dirname(codeunit_folder)

        # run testcases
        self._protected_sc.run_with_epew("npm", f"run test-{self.get_target_environment_type()}", self.get_codeunit_folder(),print_live_output=self._protected_sc.log.loglevel==LogLevel.Diagnostic,encode_argument_in_base64=True)

        # rename file
        coverage_folder = os.path.join(codeunit_folder, "Other", "Artifacts", "TestCoverage")
        target_file = os.path.join(coverage_folder, "TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(target_file)
        os.rename(os.path.join(coverage_folder, "cobertura-coverage.xml"), target_file)
        self.__rename_packagename_in_coverage_file(target_file, codeunit_name)

        # adapt backslashs to slashs
        content = GeneralUtilities.read_text_from_file(target_file)
        content = re.sub('\\\\', '/', content)
        GeneralUtilities.write_text_to_file(target_file, content)

        # aggregate packages in testcoverage-file
        roottree: etree._ElementTree = etree.parse(target_file)
        existing_classes = list(roottree.xpath('//coverage/packages/package/classes/class'))

        old_packages_list = roottree.xpath('//coverage/packages/package')
        for package in old_packages_list:
            package.getparent().remove(package)

        root = roottree.getroot()
        packages_element = root.find("packages")
        package_element = etree.SubElement(packages_element, "package")
        package_element.attrib['name'] = codeunit_name
        package_element.attrib['lines-valid'] = root.attrib["lines-valid"]
        package_element.attrib['lines-covered'] = root.attrib["lines-covered"]
        package_element.attrib['line-rate'] = root.attrib["line-rate"]
        package_element.attrib['branches-valid'] = root.attrib["branches-valid"]
        package_element.attrib['branches-covered'] = root.attrib["branches-covered"]
        package_element.attrib['branch-rate'] = root.attrib["branch-rate"]
        package_element.attrib['timestamp'] = root.attrib["timestamp"]
        package_element.attrib['complexity'] = root.attrib["complexity"]

        classes_element = etree.SubElement(package_element, "classes")

        for existing_class in existing_classes:
            classes_element.append(existing_class)

        result = etree.tostring(roottree, pretty_print=True).decode("utf-8")
        GeneralUtilities.write_text_to_file(target_file, result)

        # post tasks
        self.run_testcases_common_post_task(repository_folder, codeunit_name, True, self.get_target_environment_type())

    @GeneralUtilities.check_arguments
    def __rename_packagename_in_coverage_file(self, file: str, codeunit_name: str) -> None:
        root: etree._ElementTree = etree.parse(file)
        packages = root.xpath('//coverage/packages/package')
        for package in packages:
            package.attrib['name'] = codeunit_name
        result = etree.tostring(root).decode("utf-8")
        GeneralUtilities.write_text_to_file(file, result)


    @GeneralUtilities.check_arguments 
    def standardized_tasks_build_bom_for_node_project(self) -> None:
        relative_path_to_bom_file = f"Other/Artifacts/BOM/{os.path.basename(self.get_codeunit_folder())}.{self.tfcps_Tools_General.get_version_of_codeunit(self.get_codeunit_file())}.sbom.xml"
        self._protected_sc.run_with_epew("cyclonedx-npm", f"--output-format xml --output-file {relative_path_to_bom_file}", self.get_codeunit_folder(),print_live_output=self._protected_sc.log.loglevel==LogLevel.Diagnostic,encode_argument_in_base64=True)
        self._protected_sc.format_xml_file(self.get_codeunit_folder()+"/"+relative_path_to_bom_file)

    
    def get_dependencies(self)->dict[str,set[str]]:
        return dict[str,set[str]]()#TODO
    
    @GeneralUtilities.check_arguments
    def get_available_versions(self,dependencyname:str)->list[str]:
        return []#TODO
    
    @GeneralUtilities.check_arguments
    def set_dependency_version(self,name:str,new_version:str)->None:
        raise ValueError(f"Operation is not implemented.")
    
class TFCPS_CodeUnitSpecific_NodeJS_CLI:
 
    @staticmethod
    @GeneralUtilities.check_arguments
    def parse(file:str)->TFCPS_CodeUnitSpecific_NodeJS_Functions:
        parser=TFCPS_CodeUnitSpecific_Base_CLI.get_base_parser()
        #add custom parameter if desired
        args=parser.parse_args()
        result:TFCPS_CodeUnitSpecific_NodeJS_Functions=TFCPS_CodeUnitSpecific_NodeJS_Functions(file,LogLevel(int(args.verbosity)),args.targetenvironmenttype,not args.nocache,args.ispremerge)
        return result
