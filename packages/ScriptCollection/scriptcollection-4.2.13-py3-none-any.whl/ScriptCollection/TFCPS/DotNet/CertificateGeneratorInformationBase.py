from abc import ABC, abstractmethod


class CertificateGeneratorInformationBase(ABC):
    
    @abstractmethod
    def generate_certificate(self)->bool:
        raise ValueError("Method is abstract")
