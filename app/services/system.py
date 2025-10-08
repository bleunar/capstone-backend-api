import json, os

def get_service_information():
    base = os.path.dirname(__file__)
    path = os.path.join(base, "..", "service_information.json")
    with open(path, 'r') as f:
        return json.load(f)


# system startup check
def system_check() -> bool:
    from .core import get_db_connection, get_mail_server, initialize_database_with_retry
    from .log import log

    log.inform("SYSTEM-CHECK", f"\n{'/'*25}  System Check  {25*'/'}\n")
    log.inform("SYSTEM-CHECK", "Starting system check...")

    # DATABASE CONNECTION
    log.inform("SYSTEM-CHECK", "Initializing database connection with retry mechanism...")
    if not initialize_database_with_retry(max_attempts=20, total_duration_minutes=5):
        log.error("SYSTEM-CHECK", "Failed to establish database connection after all retry attempts")
        return False
    
    # Verify connection works with database operations
    from .database import test_database_connection
    db_test_result = test_database_connection()
    if db_test_result["success"]:
        log.inform("SYSTEM-CHECK", "Database connection established and verified with test query")
    else:
        log.error("SYSTEM-CHECK", f"Database connection verification failed: {db_test_result.get('msg', 'Unknown error')}")
        return False


    # MAIL SERVER
    if get_mail_server():
        log.inform("SYSTEM-CHECK", "Mail server connection established")
    else:
        log.error("SYSTEM-CHECK", "Failed to connect to mail server")
        return False
    

    log.inform("SYSTEM-CHECK", "critical checks completed")
    log.inform("SYSTEM-CHECK", f"\n{'\\'*25}  System Check End  {25*'\\'}\n")

    # initialization 

    log.inform("DATABASE-CHECK", f"\n{'/'*25}  Database Initialization  {25*'/'}\n")
    log.inform("DATABASE-CHECK", "Starting database check...")


    from .initialize import check_account_roles, check_accounts, initialize_root_role, initialize_root_account

    initialize_root_role()
    initialize_root_account()

    check_account_roles()
    check_accounts()

    log.inform("DATABASE-CHECK", "database checks completed")
    log.inform("DATABASE-CHECK", f"\n{'\\'*25}  Database Initialization End  {25*'\\'}\n")
