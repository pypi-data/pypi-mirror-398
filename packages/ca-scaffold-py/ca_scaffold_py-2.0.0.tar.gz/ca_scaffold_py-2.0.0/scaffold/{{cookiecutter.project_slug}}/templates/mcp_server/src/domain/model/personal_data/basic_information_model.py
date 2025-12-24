from typing import Optional
from pydantic import BaseModel


class Customer(BaseModel):
    """Customer Model."""
    uniqueCustomerKey: str
    identification: object
    generalInformation: object
    naturalPersonInformation: Optional[object] = None


class BasicInformation(BaseModel):
    """Basic Information Model."""
    customer: Customer
