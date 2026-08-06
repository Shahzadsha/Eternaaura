"""
Test datasets and input constants for Playwright automated testing.
"""

TEST_USERS = {
    "customer": {
        "username": "qa_customer@eternaaura.com",
        "email": "qa_customer@eternaaura.com",
        "password": "CustomerSecurePass123!",
        "first_name": "QA",
        "last_name": "Customer",
        "phone_number": "+919876543210",
    },
    "staff": {
        "username": "qa_staff@eternaaura.com",
        "email": "qa_staff@eternaaura.com",
        "password": "StaffSecurePass123!",
        "first_name": "QA",
        "last_name": "Staff",
        "phone_number": "+919876543211",
        "is_staff": True,
    },
    "superadmin": {
        "username": "qa_admin@eternaaura.com",
        "email": "qa_admin@eternaaura.com",
        "password": "AdminSecurePass123!",
        "first_name": "QA",
        "last_name": "SuperAdmin",
        "is_staff": True,
        "is_superuser": True,
    },
}

TEST_ADDRESS = {
    "full_name": "Automation Tester",
    "phone_number": "+919876543210",
    "line1": "100 Automation Street",
    "line2": "Suite 400",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "country": "India",
}

TEST_REVIEW = {
    "rating": 5,
    "title": "Exquisite Craftsmanship & Quality",
    "body": "The finish is remarkable and the packaging was super elegant. Highly recommended!",
}

TEST_COUPON = {
    "code": "QAWELCOME10",
    "discount_type": "percent",
    "discount_value": 10.0,
    "min_order_value": 500.0,
}
