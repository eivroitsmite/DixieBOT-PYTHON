from datetime import datetime
from uuid import uuid4

# Import functions from your module (replace `your_module` with the actual module name)
from dbconn import (
    create_table,
    add_user,
    get_user_by_id,
    get_password_by_user_id,
    get_join_time_by_user_id,
    check_user_exists
)

def test_create_table():
    """Test the table creation."""
    try:
        create_table()
        print("Table creation: SUCCESS")
    except Exception as e:
        print("Table creation: FAIL", e)

def test_add_user():
    """Test adding a user to the database."""
    try:
        user_id = str(uuid4())  # Generate a unique user ID
        join_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        password = "test_password"
        add_user(user_id, join_time, password)
        print(f"Add user (ID: {user_id}): SUCCESS")
        return user_id, join_time, password
    except Exception as e:
        print("Add user: FAIL", e)
        return None, None, None

def test_get_user_by_id(user_id):
    """Test retrieving a user by ID."""
    try:
        result = get_user_by_id(user_id)
        if result and result['user_id'] == user_id: # type: ignore
            print("Get user by ID: SUCCESS")
        else:
            print("Get user by ID: FAIL - User not found or data mismatch")
    except Exception as e:
        print("Get user by ID: FAIL", e)

def test_get_password_by_user_id(user_id, expected_password):
    """Test retrieving a password by user ID."""
    try:
        password = get_password_by_user_id(user_id)
        if password == expected_password:
            print("Get password by user ID: SUCCESS")
        else:
            print("Get password by user ID: FAIL - Incorrect password")
    except Exception as e:
        print("Get password by user ID: FAIL", e)

def test_get_join_time_by_user_id(user_id, expected_join_time):
    """Test retrieving join time by user ID."""
    try:
        join_time = get_join_time_by_user_id(user_id)
        
        # Convert join_time to datetime if it is a string
        if isinstance(join_time, str):
            join_time = datetime.strptime(join_time, '%Y-%m-%d %H:%M:%S')

        if join_time.strftime('%Y-%m-%d %H:%M:%S') == expected_join_time: # type: ignore
            print("Get join time by user ID: SUCCESS")
        else:
            print(f"Get join time by user ID: FAIL - Expected {expected_join_time}, got {join_time}")
    except Exception as e:
        print("Get join time by user ID: FAIL", e)

def test_check_user_exists(user_id, should_exist=True):
    """Test checking if a user exists by ID."""
    try:
        exists = check_user_exists(user_id)
        if exists == should_exist:
            print("Check user exists: SUCCESS")
        else:
            print(f"Check user exists: FAIL - Expected {should_exist}, got {exists}")
    except Exception as e:
        print("Check user exists: FAIL", e)

def run_tests():
    # """Run all tests."""
    # print("Testing create_table() function...")
    # test_create_table()
    
    # print("\nTesting add_user() function...")
    # user_id, join_time, password = test_add_user()
    # if user_id is None:
    #     print("Skipping remaining tests due to add_user failure.")
    #     return
    
    # print("\nTesting get_user_by_id() function...")
    # test_get_user_by_id(user_id)
    
    # print("\nTesting get_password_by_user_id() function...")
    # test_get_password_by_user_id(user_id, password)
    
    print("\nTesting get_join_time_by_user_id() function...")
    test_get_join_time_by_user_id("2256235e-14a8-4b2f-a6e1-f08eac57003e", "2024-11-11 19:46:02")
    
    # print("\nTesting check_user_exists() function...")
    # test_check_user_exists(user_id)
    
    # print("\nTesting check_user_exists() function for non-existent user...")
    # test_check_user_exists("non_existent_user_id", should_exist=False)

if __name__ == "__main__":
    run_tests()
