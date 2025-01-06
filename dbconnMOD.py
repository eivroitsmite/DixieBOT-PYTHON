import mysql.connector
from mysql.connector import Error

# Database connection details
HOST = 'uk02-sql.pebblehost.com'
PORT = 3306
DATABASE = 'customer_829856_CCACModerationDB'
USER = 'customer_829856_CCACModerationDB'
PASSWORD = 'BlP^qL9Y!++eLygv2nlMcsXP'

_connection = None

def create_connection():
    """Creates or retrieves a global database connection."""
    global _connection
    try:
        if _connection is None or not _connection.is_connected():
            _connection = mysql.connector.connect(
                host=HOST,
                port=PORT,
                user=USER,
                password=PASSWORD,
                database=DATABASE
            )
        return _connection
    except Error as e:
        print("Error connecting to database:", e)
        return None

def create_table():
    """Creates the 'user_data' table if it does not already exist."""
    connection = create_connection()
    if connection is None:
        return
    try:
        cursor = connection.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS mod_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            moderator_id VARCHAR(100),
            action VARCHAR(50),
            user_id VARCHAR(100),
            reason TEXT,
            timestamp DATETIME
        );
        """
        cursor.execute(create_table_query)
        connection.commit()
    except Error as e:
        print("Error creating table:", e)
    finally:
        cursor.close()

def log_mod_action(moderator_id, action, user_id, reason, timestamp):
    """Logs a moderation action into the 'mod_logs' table."""
    connection = create_connection()
    if connection is None:
        return
    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO mod_logs (moderator_id, action, user_id, reason, timestamp)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (moderator_id, action, user_id, reason, timestamp))
        connection.commit()
    except Error as e:
        print("Error logging moderation action:", e)
    finally:
        cursor.close()

def get_user_by_id(user_id):
    """Retrieves a user record based on user_id."""
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        select_query = "SELECT * FROM mod_logs WHERE user_id = %s;"
        cursor.execute(select_query, (user_id,))
        result = cursor.fetchone()
        return result
    except Error as e:
        print("Error retrieving user:", e)
        return None
    finally:
        cursor.close()

def check_user_exists(user_id):
    """Checks if a user exists in the table based on user_id."""
    connection = create_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        select_query = "SELECT 1 FROM mod_logs WHERE user_id = %s;"
        cursor.execute(select_query, (user_id,))
        result = cursor.fetchone()
        return bool(result)
    except Error as e:
        print("Error checking if user exists:", e)
        return False
    finally:
        cursor.close()

def fetch_mod_logs():
    """Fetches all moderation logs from the 'mod_logs' table."""
    connection = create_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        select_query = "SELECT * FROM mod_logs ORDER BY timestamp DESC;"
        cursor.execute(select_query)
        return cursor.fetchall()
    except Error as e:
        print("Error fetching moderation logs:", e)
        return []
    finally:
        cursor.close()

# Exportable functions
__all__ = [
    "create_connection",
    "create_table",
    "add_user",
    "get_user_by_id",
    "get_password_by_user_id",
    "get_join_time_by_user_id",
    "check_user_exists",
    "delete_user_by_id"
]
