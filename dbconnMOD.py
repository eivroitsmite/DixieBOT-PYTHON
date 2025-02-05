import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Database connection details for the user verification database
MOD_HOST = 'uk02-sql.pebblehost.com'
MOD_PORT = 3306
MOD_DATABASE = 'customer_829856_CCACModerationDB'
MOD_USER = 'customer_829856_CCACModerationDB'
MOD_PASSWORD = 'BlP^qL9Y!++eLygv2nlMcsXP'

# Global connection variable for the verification database
_connection = None

def create_connection():
    """Creates or retrieves a global connection to the verification database."""
    global _connection
    try:
        if _connection is None or not _connection.is_connected():
            _connection = mysql.connector.connect(
                host=MOD_HOST,
                port=MOD_PORT,
                user=MOD_USER,
                password=MOD_PASSWORD,
                database=MOD_DATABASE
            )
        return _connection
    except Error as e:
        print("Error connecting to verification database:", e)
        return None

def create_mod_log_table():
    """Creates the 'mod_logs' table if it does not already exist."""
    connection = create_connection()
    if connection is None:
        return
    try:
        cursor = connection.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS mod_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            reason TEXT NOT NULL,
            moderator_id VARCHAR(100) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        connection.commit()
    except Error as e:
        print("Error creating mod_logs table:", e)
    finally:
        cursor.close()
        connection.close()


def add_mod_log(user_id, reason, moderator_id):
    """Adds a new moderation log to the 'mod_logs' table."""
    connection = create_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO mod_logs (user_id, reason, moderator_id)
        VALUES (%s, %s, %s);
        """
        cursor.execute(insert_query, (user_id, reason, moderator_id))
        connection.commit()
        return True
    except Error as e:
        print("Error inserting moderation log:", e)
        return False
    finally:
        cursor.close()
        connection.close()

def get_mod_logs_by_user(user_id):
    """Retrieves all moderation logs for a specific user."""
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        select_query = "SELECT * FROM mod_logs WHERE user_id = %s ORDER BY timestamp DESC;"
        cursor.execute(select_query, (user_id,))
        result = cursor.fetchall()
        return result
    except Error as e:
        print("Error retrieving mod logs:", e)
        return None
    finally:
        cursor.close()
        connection.close()

def get_mod_logs_by_moderator(moderator_id):
    """Retrieves all moderation logs issued by a specific moderator."""
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        select_query = "SELECT * FROM mod_logs WHERE moderator_id = %s ORDER BY timestamp DESC;"
        cursor.execute(select_query, (moderator_id,))
        result = cursor.fetchall()
        return result
    except Error as e:
        print("Error retrieving logs by moderator:", e)
        return None
    finally:
        cursor.close()
        connection.close()

def check_log_exists(log_id):
    """Checks if a specific moderation log exists based on log_id."""
    connection = create_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        select_query = "SELECT 1 FROM mod_logs WHERE log_id = %s;"
        cursor.execute(select_query, (log_id,))
        result = cursor.fetchone()
        return bool(result)
    except Error as e:
        print("Error checking if log exists:", e)
        return False
    finally:
        cursor.close()
        connection.close()

def delete_mod_log_by_id(log_id):
    """Deletes a moderation log from the database based on log_id."""
    connection = create_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        delete_query = "DELETE FROM mod_logs WHERE log_id = %s;"
        cursor.execute(delete_query, (log_id,))
        connection.commit()
        print(f"Log with ID {log_id} deleted successfully.")
        return cursor.rowcount > 0
    except Error as e:
        print(f"Error deleting log with ID {log_id}: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

# Exportable functions
__all__ = [
    "create_connection",
    "create_mod_log_table",
    "add_mod_log",
    "get_mod_logs_by_user",
    "get_mod_logs_by_moderator",
    "check_log_exists",
    "delete_mod_log_by_id"
]
