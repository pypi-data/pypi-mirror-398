import os
from urllib import request
import time
import ssl
from datetime import timedelta,datetime
from ...GeneralUtilities import GeneralUtilities
from ...SCLog import  LogLevel
from ..TFCPS_CodeUnitSpecific_Base import TFCPS_CodeUnitSpecific_Base,TFCPS_CodeUnitSpecific_Base_CLI

class TFCPS_CodeUnitSpecific_Docker_Functions(TFCPS_CodeUnitSpecific_Base):

    def __init__(self,current_file:str,verbosity:LogLevel,targetenvironmenttype:str,use_cache:bool,is_pre_merge:bool):
        super().__init__(current_file, verbosity,targetenvironmenttype,use_cache,is_pre_merge)

    @GeneralUtilities.check_arguments
    def build(self,custom_arguments:dict[str,str],fallback_registries:dict[str,str]) -> None:

        codeunitname: str =self.get_codeunit_name()
        codeunit_folder =self.get_codeunit_folder() 
        codeunitname_lower = codeunitname.lower()
        codeunit_file =self.get_codeunit_file()
        codeunitversion = self.tfcps_Tools_General.get_version_of_codeunit(codeunit_file)
        args = ["image", "build", "--pull", "--force-rm", "--progress=plain", "--build-arg", f"TargetEnvironmentType={self.get_target_environment_type()}", "--build-arg", f"CodeUnitName={codeunitname}", "--build-arg", f"CodeUnitVersion={codeunitversion}", "--build-arg", f"CodeUnitOwnerName={self.tfcps_Tools_General.get_codeunit_owner_name(self.get_codeunit_file())}", "--build-arg", f"CodeUnitOwnerEMailAddress={self.tfcps_Tools_General.get_codeunit_owner_emailaddress(self.get_codeunit_file())}"]
        docker_file=os.path.join(self.get_codeunit_folder(),codeunitname,"Dockerfile")
        args=args+self._protected_sc.get_docker_build_args_for_base_images(docker_file,fallback_registries)
        if custom_arguments is None:
            custom_arguments=dict[str,str]()
        for custom_argument_key, custom_argument_value in custom_arguments.items():
            args.append("--build-arg")
            args.append(f"{custom_argument_key}={custom_argument_value}")
        args = args+["--tag", f"{codeunitname_lower}:latest", "--tag", f"{codeunitname_lower}:{codeunitversion}", "--file", f"{codeunitname}/Dockerfile"]
        if not self.use_cache():
            args.append("--no-cache")
        args.append(".")
        codeunit_content_folder = os.path.join(codeunit_folder)
        self._protected_sc.run_program_argsasarray("docker", args, codeunit_content_folder, print_errors_as_information=True)
        artifacts_folder = GeneralUtilities.resolve_relative_path("Other/Artifacts", codeunit_folder)
        app_artifacts_folder = os.path.join(artifacts_folder, "BuildResult_OCIImage")
        GeneralUtilities.ensure_directory_does_not_exist(app_artifacts_folder)
        GeneralUtilities.ensure_directory_exists(app_artifacts_folder)
        self._protected_sc.run_program_argsasarray("docker", ["save", "--output", f"{codeunitname}_v{codeunitversion}.tar", f"{codeunitname_lower}:{codeunitversion}"], app_artifacts_folder, print_errors_as_information=True)
        self.copy_source_files_to_output_directory()
        self.__generate_sbom_for_docker_image()


    @GeneralUtilities.check_arguments
    def __generate_sbom_for_docker_image(self) -> None:
        codeunitname=self.get_codeunit_name()
        codeunit_folder =self.get_codeunit_folder()
        artifacts_folder = GeneralUtilities.resolve_relative_path("Other/Artifacts", codeunit_folder)
        codeunitname_lower = codeunitname.lower()
        sbom_folder = os.path.join(artifacts_folder, "BOM")
        codeunitversion = self.tfcps_Tools_General.get_version_of_codeunit(self.get_codeunit_file())
        GeneralUtilities.ensure_directory_exists(sbom_folder)
        #TODO ensure syft-image-tag will be updated by update-dependencies-script.
        self._protected_sc.run_program_argsasarray("docker", ["run","--rm","-v","/var/run/docker.sock:/var/run/docker.sock","-v","./BOM:/BOM",self._protected_sc.get_image_with_registry_for_docker_image("syft","v1.39.0","docker.io/anchore/syft"),f"{codeunitname_lower}:{codeunitversion}","-o",f"cyclonedx-xml=/BOM/{codeunitname}.{codeunitversion}.sbom.xml"], artifacts_folder, print_errors_as_information=True)
        self._protected_sc.format_xml_file(sbom_folder+f"/{codeunitname}.{codeunitversion}.sbom.xml")
 
    @GeneralUtilities.check_arguments
    def linting(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def do_common_tasks(self,current_codeunit_version:str )-> None:
        codeunitname =self.get_codeunit_name()
        codeunit_folder = self.get_codeunit_folder()
        codeunit_version = current_codeunit_version
        self._protected_sc.replace_version_in_dockerfile_file(GeneralUtilities.resolve_relative_path(f"./{codeunitname}/Dockerfile", codeunit_folder), codeunit_version)
        self.do_common_tasks_base(current_codeunit_version)
        self.tfcps_Tools_General.standardized_tasks_update_version_in_docker_examples(codeunit_folder,codeunit_version)
 
    @GeneralUtilities.check_arguments
    def generate_reference(self) -> None:
        self.generate_reference_using_docfx()
    
    @GeneralUtilities.check_arguments
    def run_testcases(self) -> None:
        pass#TODO
    
    @GeneralUtilities.check_arguments
    def get_dependencies(self)->dict[str,set[str]]:
        return dict[str,set[str]]()#TODO
    
    @GeneralUtilities.check_arguments
    def get_available_versions(self,dependencyname:str)->list[str]:
        return []#TODO

    @GeneralUtilities.check_arguments
    def set_dependency_version(self,name:str,new_version:str)->None:
        raise ValueError(f"Operation is not implemented.")

    @GeneralUtilities.check_arguments
    def image_is_working(self,timeout:timedelta,environment_variables:dict[str,str],test_port:int,http_test_route:str,use_https_for_test:bool)->tuple[bool,str]:
        if timeout is None:
            timeout=timedelta(seconds=120)
        if environment_variables is None:
            environment_variables={}
        oci_image_artifacts_folder :str= GeneralUtilities.resolve_relative_path("Other/Artifacts/BuildResult_OCIImage", self.get_codeunit_folder())
        container_name:str=f"{self.get_codeunit_name()}finaltest".lower()
        self.tfcps_Tools_General.ensure_containers_are_not_running([container_name])
        self.tfcps_Tools_General.load_docker_image(oci_image_artifacts_folder)
        codeunit_file:str=os.path.join(self.get_codeunit_folder(),f"{self.get_codeunit_name()}.codeunit.xml")
        image=f"{self.get_codeunit_name()}:{self.tfcps_Tools_General.get_version_of_codeunit(codeunit_file)}".lower()
        argument=f"run -d --name {container_name} -p {test_port}:{test_port}"
        for k,v in environment_variables.items():
            argument=f"{argument} -e {k}={v}"#TODO switch to argument-array to also allow values with white-space
        argument=f"{argument} {image}"
        GeneralUtilities.assert_condition(http_test_route is None or http_test_route.startswith("/"),"If a test-route is given then it must start with \"/\".")
        try:
            last_exception:Exception=None
            self._protected_sc.run_program("docker",argument)
            start:datetime=GeneralUtilities.get_now()
            end:datetime=start+timeout
            while GeneralUtilities.get_now()<end:
                time.sleep(1)
                try:
                    if not self._protected_sc.container_is_running_and_healthy(container_name):
                        raise ValueError("Container is not running and healthy.")
                    if http_test_route is not None:
                        url="http"
                        if use_https_for_test:
                            url=url+"s"
                        url=url+"://localhost"
                        if test_port is not None:
                            url=url+":"+str(test_port)
                        url=url+http_test_route
                        ctx = ssl.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE
                        with request.urlopen(url, context=ctx) as response:
                            status = response.status
                            if status < 200 or 300 <= status:
                                raise ValueError(f"Test-call \"GET {url}\" had response-statuscode {status}.")
                    return (True,None)
                except Exception as e:
                    last_exception=e
            exception_message=""
            if last_exception is not None:
                exception_message=exception_message+"\nLast exception: "+GeneralUtilities.exception_to_str(last_exception)
            if not self._protected_sc.container_is_exists(container_name):
                return (False,f"Container \"{container_name}\" does not exist.{exception_message}")
            if not self._protected_sc.container_is_running(container_name):
                return (False,f"Container \"{container_name}\" is not running.{exception_message}")
            if not self._protected_sc.container_is_healthy(container_name):
                container_output=self._protected_sc.get_output_of_container(container_name)
                return (False,f"Container \"{container_name}\" is not healthy. Container-output:\n{container_output}{exception_message}")
            return (False,f"Container \"{container_name}\" is not working properly.{exception_message}")
        finally:
            self.tfcps_Tools_General.ensure_containers_are_not_running([container_name])

    @GeneralUtilities.check_arguments
    def verify_image_is_working(self,timeout:timedelta,environment_variables:dict[str,str],test_port:int,http_test_route:str,use_https_for_test:bool):
        check_result:tuple[bool,str]= self.image_is_working(timeout,environment_variables,test_port,http_test_route,use_https_for_test)
        if not check_result[0]:
            raise ValueError("Image not working: "+check_result[1])

class TFCPS_CodeUnitSpecific_Docker_CLI:

    @staticmethod
    @GeneralUtilities.check_arguments
    def parse(file:str)->TFCPS_CodeUnitSpecific_Docker_Functions:
        parser=TFCPS_CodeUnitSpecific_Base_CLI.get_base_parser()
        #add custom parameter if desired
        args=parser.parse_args()
        result:TFCPS_CodeUnitSpecific_Docker_Functions=TFCPS_CodeUnitSpecific_Docker_Functions(file,LogLevel(int(args.verbosity)),args.targetenvironmenttype,not args.nocache,args.ispremerge)
        return result
