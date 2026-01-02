from .CertificateGeneratorInformationBase import CertificateGeneratorInformationBase


class CertificateGeneratorInformationNoGenerate(CertificateGeneratorInformationBase):
    
    def generate_certificate(self)->bool:
        return False
