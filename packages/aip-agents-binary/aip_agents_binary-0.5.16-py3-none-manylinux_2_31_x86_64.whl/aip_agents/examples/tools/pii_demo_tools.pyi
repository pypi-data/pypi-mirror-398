from _typeshed import Incomplete
from aip_agents.utils.logger import LoggerManager as LoggerManager
from pydantic import BaseModel

logger: Incomplete

class CustomerIdSchema(BaseModel):
    """Schema for customer ID input."""
    customer_id: str

class EmployeeIdSchema(BaseModel):
    """Schema for employee ID input."""
    employee_id: str

class UserIdSchema(BaseModel):
    """Schema for user ID input."""
    user_id: str

def get_customer_info(customer_id: str) -> str:
    """Gets customer information including email and phone number.

    This tool demonstrates PII handling by returning sensitive customer data
    that will be automatically anonymized by the PII handler.

    Args:
        customer_id: The ID of the customer to retrieve information for.

    Returns:
        A string containing customer information with PII.
    """
def get_employee_data(employee_id: str) -> str:
    """Gets employee data including name, email, and salary information.

    This tool demonstrates PII handling with employee-specific data that includes
    sensitive information like salary and personal email addresses.

    Args:
        employee_id: The ID of the employee to retrieve data for.

    Returns:
        A string containing employee information with PII.
    """
def get_user_profile(user_id: str) -> str:
    """Gets user profile information with personal details.

    This tool demonstrates PII handling with user profile data that includes
    personal information like email, phone, and date of birth.

    Args:
        user_id: The ID of the user to retrieve profile for.

    Returns:
        A string containing user profile information with PII.
    """
