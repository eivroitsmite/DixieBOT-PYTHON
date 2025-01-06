from datetime import datetime
from uuid import uuid4

# Import functions from dbconnMod
from dbconnMOD import (
    create_table,
    log_mod_action,
    get_user_by_id,
    check_user_exists,
    fetch_mod_logs
)

def test_create_table():
    """Test the table creation."""
    try:
        create_table()
        print("Table creation: SUCCESS")
    except Exception as e:
        print("Table creation: FAIL", e)

def test_log_mod_action():
    """Test logging a moderation action."""
    try:
        moderator_id = "mod123"
        action = "warn"
        user_id = str(uuid4())
        reason = "Test reason for moderation"
        timestamp = datetime.now()

        log_mod_action(moderator_id, action, user_id, reason, timestamp)
        print(f"Log moderation action (User ID: {user_id}): SUCCESS")
        return user_id, moderator_id, action, reason, timestamp
    except Exception as e:
        print("Log moderation action: FAIL", e)
        return None, None, None, None, None

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

def test_fetch_mod_logs():
    """Test fetching all moderation logs."""
    try:
        logs = fetch_mod_logs()
        if logs:
            print("Fetch moderation logs: SUCCESS")
            for log in logs:
                print(log)
        else:
            print("Fetch moderation logs: SUCCESS - No logs found.")
    except Exception as e:
        print("Fetch moderation logs: FAIL", e)

def run_tests():
    """Run all tests."""
    print("Testing create_table() function...")
    test_create_table()

    print("\nTesting log_mod_action() function...")
    user_id, moderator_id, action, reason, timestamp = test_log_mod_action()
    if user_id is None:
        print("Skipping remaining tests due to log_mod_action failure.")
        return

    print("\nTesting get_user_by_id() function...")
    test_get_user_by_id(user_id)

    print("\nTesting check_user_exists() function...")
    test_check_user_exists(user_id)

    print("\nTesting fetch_mod_logs() function...")
    test_fetch_mod_logs()

if __name__ == "__main__":
    run_tests()
