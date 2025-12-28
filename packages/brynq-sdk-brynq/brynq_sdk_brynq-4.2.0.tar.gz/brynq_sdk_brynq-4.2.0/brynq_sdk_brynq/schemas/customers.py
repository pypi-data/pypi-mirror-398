from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Union, List, Dict, Any, Tuple, Type
from datetime import date
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated


def parse_date(value: Union[str, None]) -> Optional[date]:
    """Convert string date to date object or return None"""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def convert_to_str(value: Union[str, int]) -> str:
    """Convert integer or string value to string"""
    return str(value)


DateField = Annotated[Union[date, None], BeforeValidator(parse_date)]
StringOrInt = Annotated[str, BeforeValidator(convert_to_str)]


def validate_data(data: List[Dict[str, Any]], schema: Type[BaseModel], debug: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate a list of dictionaries using a Pydantic schema and separate valid and invalid data.
    
    Args:
        data (List[Dict[str, Any]]): List of dictionaries to validate
        schema (Type[BaseModel]): Pydantic schema class to use for validation
        debug (bool, optional): Whether to print debug information. Defaults to False.
    
    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: Tuple of (valid_data, invalid_data)
            - valid_data: List of validated dictionaries that conform to the schema
            - invalid_data: List of dictionaries that failed validation, with error details
    """
    valid_data = []
    invalid_data = []
    
    for idx, item in enumerate(data):
        try:
            validated = schema(**item).model_dump()
            valid_data.append(validated)
        except ValidationError as e:
            if debug:
                print(f"Validation error at index {idx}:")
                print(e.json(indent=2))
            
            # Add error information to the invalid item
            invalid_item = item.copy()
            invalid_item['_validation_errors'] = [
                {
                    'loc': ' -> '.join(str(loc) for loc in error['loc']),
                    'msg': error['msg'],
                    'type': error['type']
                }
                for error in e.errors()
            ]
            invalid_data.append(invalid_item)
    
    return valid_data, invalid_data


class CustomerSchema(BaseModel):
    """Schema for basic customer data validation"""
    name: str = Field(..., description="Name of the customer")
    domain: str = Field(..., description="Domain identifier for the customer")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class CustomerUsers(BaseModel):
    """Schema for customer users counts"""
    global_: StringOrInt = Field(..., alias="global", description="Number of global users")
    qlik_analyzer: StringOrInt = Field(..., alias="qlikAnalyzer", description="Number of Qlik Analyzer users")
    qlik_pro: StringOrInt = Field(..., alias="qlikPro", description="Number of Qlik Pro users")
    jira: int = Field(..., description="Number of Jira users")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class CustomerContractDetailsSchema(BaseModel):
    """Schema for customer contract details"""
    id: int = Field(..., description="Unique identifier for the customer", gt=0)
    name: str = Field(..., description="Name of the customer")
    profit_subscription: Optional[str] = Field(None, alias="profitSubscription", description="Profit subscription identifier")
    subscription_cost: float = Field(..., alias="subscriptionCost", description="Cost of the subscription")
    subscription_cost_mutation: Optional[float] = Field(None, alias="subscriptionCostMutation", description="Change in subscription cost")
    effective_date: DateField = Field(..., alias="effectiveDate", description="Start date of the contract")
    expiration_date: DateField = Field(None, alias="expirationDate", description="End date of the contract")
    payment_term: str = Field(..., alias="paymentTerm", description="Payment term (e.g., annual)")
    subscription_type: str = Field(..., alias="subscriptionType", description="Type of subscription")
    referred_by: Optional[str] = Field(None, alias="referredBy", description="Referral source")
    users: CustomerUsers = Field(..., description="User counts by type")
    apps: int = Field(..., description="Number of apps")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True
