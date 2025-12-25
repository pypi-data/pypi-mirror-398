# SarvClient API Interaction Module

## Overview

The **SarvClient** module provides a Python interface for interacting with the SarvCRM API. It simplifies authentication, CRUD operations, and module-specific functionalities for seamless integration with SarvCRM.

[SarvCRM API Documents](https://app.sarvcrm.com/webservice/)

## Features
- **Authentication**: Log in and manage sessions with the SarvCRM API.
- **CRUD Operations**: Perform Create, Read, Update, and Delete transactions via simple methods.
- **Context Manager Support**: Automatically handle login and logout within `with` statements.
- **Localization**: Supports specifying the desired language for API interactions.
- **Utility Methods**: Format dates, times, and other helper functionalities compliant with SarvCRM standards.
- **ENVMod Support**: You can use the SarvClient with the ENVMod module for more rubost and flexible env management.
---

## Installation

1. Ensure you have `Python 3.9+` installed.
2. Make sure `pip` is installed
4. Install the package
   ```bash
   pip install py-sarvcrm-api
   ```
---

## Quick Start

#### **CRUD**

```python
from sarvcrm_api import SarvClient

# Initialize the client
client = SarvClient(
    utype="your_utype",
    username="your_username",
    password="your_password",
    language="en_US",
    is_password_md5=True, # if your password is already md5
    #url=https://example.com/API.php  # if you use local server
    #frontend_url=https://example.com/  # if you use local server
)


# Use as a context manager for clean execution
with client:
    # Create new item in Accounts
    uid = client.Accounts.create(type='Corporate', name='RadinSystem', numbers=['02145885000'])
    print(f'New Account Created: {uid}')
    
    # Read one item record
    record = clinet.Accounts.read_record(uid)
    print(f'Single Account record: {record}')

    # Use query and selected_fields to read item
    opportunity = client.Opportunities.read_list(query="opportunities.id='<UID>'", selected_fields=['fullname'])
    print(f'Opportunity: {opportunity}')

    # Read List of items
    records = client.Accounts.read_list(order_by='accounts.name')
    print('Accounts list:')
    for account in Accounts:
        print(f' - {account}')

    # Update an item
    updated_item = client.Accounts.update(uid, name='Radin-System')
    print(f'Updated item id: {updated_item}')

    # Search for data by phone number
    result = client.search_by_number(number="02145885000", module=client.Accounts)  # module is optional
    print(f'Search by number result: {result}')

    # Delete Item
    deleted_item = client.Accounts.delete(uid)
    print(f'Deleted item: {deleted_item}')
```

#### **Get me**

This method on `Users` module will give the logged in user details.

```python
my_user = client.Users.get_me()
```

Also you can use `user_id` property of client to get current users `id`

```pyton
print(client.user_id)
```

#### **Get current user items**

Use `read_user_created` or `read_user_assigned` to get items created or assigned to the current user.

```python
created_items = client.Leads.read_user_created(limit=10)
assigned_items = client.Tasks.read_user_assigned(limit=2)
```

### Initiate client with `ENVMod`
You can load the client with environment variables using `ENVMod` class. This is useful for development
and testing purposes.

```python
from classmods import ENVMod
from sarvcrm_api import SarvClient

sarv_client = SarvClient(**ENVMod.load_args(SarvClient.__init__))
```

If you have environment variables set up, you can use them directly in your code. For example, read
example file [env example](.env_example)

## Additional Features

- **Error Handling**: This module raises `requests.HTTPError` and `SarvException` for API errors.
- **Secure Defaults**: Passwords are hashed with `MD5` unless explicitly provided as pre-hashed.
- **Easy Intraction**: Added all modules and methods for easy intraction.

---

## Developers
   - **Contribute**: Feel free to fork this repo and send pull request.

### Testing
  - **Pytest Support**: create the `.env` file from `.env_example` and use pytest to start testing.
  - **Test Cases**: For now simple test methods are used and more test cases will be added soon.

## License

This module is licensed for Radin System. For details, see the [LICENSE](LICENSE) file.
