import json

def get_service_information():
    with open('service_information.json', 'r') as f:
        data_as_dict = json.load(f)
        return data_as_dict


# system startup check
def system_check() -> bool:
    from services.core import get_db_connection, get_mail_server
    from services.log import log

    log.inform("SYSTEM-CHECK", f"\n{'/'*25}  System Check  {25*'/'}\n")
    log.inform("SYSTEM-CHECK", "Starting system check...")

    # DATABASE CONNECTION
    if get_db_connection():
        log.inform("SYSTEM-CHECK", "Database connection established")
    else:
        log.error("SYSTEM-CHECK", "Failed to connect to database")
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


    from services.initialize import check_account_roles, check_accounts, initialize_root_role, initialize_root_account

    initialize_root_role()
    initialize_root_account()

    check_account_roles()
    check_accounts()

    log.inform("DATABASE-CHECK", "database checks completed")
    log.inform("DATABASE-CHECK", f"\n{'\\'*25}  Database Initialization End  {25*'\\'}\n")
