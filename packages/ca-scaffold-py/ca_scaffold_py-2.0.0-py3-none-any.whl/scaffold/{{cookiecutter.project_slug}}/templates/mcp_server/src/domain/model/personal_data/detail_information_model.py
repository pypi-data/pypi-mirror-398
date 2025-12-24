from typing import Optional
from pydantic import BaseModel


class Customer(BaseModel):
    """Customer Model."""
    uniqueCustomerKey: str
    identification: Optional[object] = None
    naturalPersonInformation: Optional[object] = None
    legalPersonInformation: Optional[object] = None
    nationalityInformation: Optional[object] = None
    detailedInformation: Optional[object] = None


class DetailInformation(BaseModel):
    """Basic Information Model."""
    customer: Customer
