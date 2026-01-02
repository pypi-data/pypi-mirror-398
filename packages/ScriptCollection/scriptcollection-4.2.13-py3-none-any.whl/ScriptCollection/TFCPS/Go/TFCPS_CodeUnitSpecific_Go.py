import os
from lxml import etree
from ...GeneralUtilities import GeneralUtilities
from ...ScriptCollectionCore import ScriptCollectionCore
from ...SCLog import  LogLevel
from ..TFCPS_CodeUnitSpecific_Base import TFCPS_CodeUnitSpecific_Base,TFCPS_CodeUnitSpecific_Base_CLI

class TFCPS_CodeUnitSpecific_Go_Functions(TFCPS_CodeUnitSpecific_Base):

    def __init__(self,current_file:str,verbosity:LogLevel,targetenvironmenttype:str,use_cache:bool,is_pre_merge:bool):
        super().__init__(current_file, verbosity,targetenvironmenttype,use_cache,is_pre_merge)

    @GeneralUtilities.check_arguments
    def build(self) -> None:
        #TODO
        self.__generate_sbom_for_go_image()

    @GeneralUtilities.check_arguments
    def __generate_sbom_for_go_image(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def linting(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def __update_coverage_file(self,coverage_file:str) -> None:
        tree = etree.parse(coverage_file)
        root = tree.getroot()
        for package in root.findall(".//package"):
            package.set("name",self.get_codeunit_name())
        for cls in root.findall(".//class"):
            filename = cls.get("filename")
            if filename:
                cls.set("filename", f"./{filename}")
            cls.set("name",str(filename).rsplit("/", 1)[-1])
        tree.write(coverage_file, encoding="utf-8", xml_declaration=True, pretty_print=True)

    @GeneralUtilities.check_arguments
    def run_testcases(self) -> None:
        test_coverage_folder = os.path.join(self.get_codeunit_folder(), "Other", "Artifacts", "TestCoverage").replace("\\", "/")
        GeneralUtilities.ensure_directory_exists(test_coverage_folder)
        src_folder = GeneralUtilities.resolve_relative_path(self.get_codeunit_name(), self.get_codeunit_folder())
        sc: ScriptCollectionCore = ScriptCollectionCore()
        sc.run_program_argsasarray("go", ["install", "github.com/t-yuki/gocover-cobertura@latest"], src_folder)
        sc.run_program_argsasarray("go", ["test", "-coverprofile=coverage.out", "./..."], src_folder)
        coverage_file:str=f"{test_coverage_folder}/TestCoverage.xml"
        sc.run_program_argsasarray("sh", ["-c", f"gocover-cobertura < coverage.out > {coverage_file}"], src_folder)
        self.__update_coverage_file(coverage_file)
        self.run_testcases_common_post_task(self.get_repository_folder(),self.get_codeunit_name(),True,self.get_type_environment_type())

    def get_dependencies(self)->dict[str,set[str]]:
        return dict[str,set[str]]()#TODO
    
    @GeneralUtilities.check_arguments
    def get_available_versions(self,dependencyname:str)->list[str]:
        return []#TODO
    
    @GeneralUtilities.check_arguments
    def set_dependency_version(self,name:str,new_version:str)->None:
        raise ValueError(f"Operation is not implemented.")
    
class TFCPS_CodeUnitSpecific_Go_CLI:

    @staticmethod
    @GeneralUtilities.check_arguments
    def parse(file:str)->TFCPS_CodeUnitSpecific_Go_Functions:
        parser=TFCPS_CodeUnitSpecific_Base_CLI.get_base_parser()
        #add custom parameter if desired
        args=parser.parse_args()
        result:TFCPS_CodeUnitSpecific_Go_Functions=TFCPS_CodeUnitSpecific_Go_Functions(file,LogLevel(int(args.verbosity)),args.targetenvironmenttype,not args.nocache,args.ispremerge)
        return result
