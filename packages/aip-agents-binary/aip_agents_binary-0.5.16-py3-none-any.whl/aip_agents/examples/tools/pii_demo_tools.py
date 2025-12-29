"""Mock tools for demonstrating PII handling in parallel tool execution.

This module provides tools that return personally identifiable information (PII)
to demonstrate how the PII handler automatically anonymizes and deanonymizes data
during tool execution.

Tools included:
- get_customer_info: Returns customer information including email and phone
- get_employee_data: Returns employee data including name and salary
- get_user_profile: Returns user profile with personal details

Authors:
    Cascade AI Assistant
"""

from langchain_core.tools import tool
from pydantic import BaseModel

from aip_agents.utils.logger import LoggerManager

logger = LoggerManager().get_logger(__name__)


class CustomerIdSchema(BaseModel):
    """Schema for customer ID input."""

    customer_id: str


class EmployeeIdSchema(BaseModel):
    """Schema for employee ID input."""

    employee_id: str


class UserIdSchema(BaseModel):
    """Schema for user ID input."""

    user_id: str


@tool(args_schema=CustomerIdSchema)
def get_customer_info(customer_id: str) -> str:
    """Gets customer information including email and phone number.

    This tool demonstrates PII handling by returning sensitive customer data
    that will be automatically anonymized by the PII handler.

    Args:
        customer_id: The ID of the customer to retrieve information for.

    Returns:
        A string containing customer information with PII.
    """
    customer_data = {
        "C001": {
            "name": "John Smith",
            "email": "john.smith@example.com",
            "phone": "+1-555-0101",
            "address": "123 Main St, New York, NY 10001",
        },
        "C002": {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1-555-0102",
            "address": "456 Oak Ave, Los Angeles, CA 90001",
        },
        "C003": {
            "name": "Bob Williams",
            "email": "bob.williams@example.com",
            "phone": "+1-555-0103",
            "address": "789 Pine Rd, Chicago, IL 60601",
        },
    }

    customer = customer_data.get(customer_id.upper())
    if customer:
        logger.info(f"Retrieved customer info for {customer_id}")
        return (
            f"Customer {customer_id}: Name: {customer['name']}, "
            f"Email: {customer['email']}, Phone: {customer['phone']}, "
            f"Address: {customer['address']}"
        )
    else:
        message = f"Customer {customer_id} not found"
        logger.warning(message)
        return message


@tool(args_schema=EmployeeIdSchema)
def get_employee_data(employee_id: str) -> str:
    """Gets employee data including name, email, and salary information.

    This tool demonstrates PII handling with employee-specific data that includes
    sensitive information like salary and personal email addresses.

    Args:
        employee_id: The ID of the employee to retrieve data for.

    Returns:
        A string containing employee information with PII.
    """
    employee_data = {
        "E001": {
            "name": "Carol Davis",
            "email": "carol.davis@company.com",
            "phone": "+1-555-0201",
            "salary": "$85,000",
            "department": "Engineering",
        },
        "E002": {
            "name": "David Miller",
            "email": "david.miller@company.com",
            "phone": "+1-555-0202",
            "salary": "$92,000",
            "department": "Product",
        },
        "E003": {
            "name": "Emma Wilson",
            "email": "emma.wilson@company.com",
            "phone": "+1-555-0203",
            "salary": "$78,000",
            "department": "Marketing",
        },
    }

    employee = employee_data.get(employee_id.upper())
    if employee:
        logger.info(f"Retrieved employee data for {employee_id}")
        return (
            f"Employee {employee_id}: Name: {employee['name']}, "
            f"Email: {employee['email']}, Phone: {employee['phone']}, "
            f"Salary: {employee['salary']}, Department: {employee['department']}"
        )
    else:
        message = f"Employee {employee_id} not found"
        logger.warning(message)
        return message


@tool(args_schema=UserIdSchema)
def get_user_profile(user_id: str) -> str:
    """Gets user profile information with personal details.

    This tool demonstrates PII handling with user profile data that includes
    personal information like email, phone, and date of birth.

    Args:
        user_id: The ID of the user to retrieve profile for.

    Returns:
        A string containing user profile information with PII.
    """
    user_data = {
        "U001": {
            "username": "john_doe",
            "email": "john.doe@personal.com",
            "phone": "+1-555-0301",
            "dob": "1990-05-15",
            "city": "Seattle, WA",
        },
        "U002": {
            "username": "jane_smith",
            "email": "jane.smith@personal.com",
            "phone": "+1-555-0302",
            "dob": "1992-08-22",
            "city": "Portland, OR",
        },
        "U003": {
            "username": "bob_jones",
            "email": "bob.jones@personal.com",
            "phone": "+1-555-0303",
            "dob": "1988-03-10",
            "city": "San Francisco, CA",
        },
    }

    user = user_data.get(user_id.upper())
    if user:
        logger.info(f"Retrieved user profile for {user_id}")
        return (
            f"User {user_id}: Username: {user['username']}, "
            f"Email: {user['email']}, Phone: {user['phone']}, "
            f"DOB: {user['dob']}, City: {user['city']}"
        )
    else:
        message = f"User {user_id} not found"
        logger.warning(message)
        return message
