from services.security import generate_uuid, generate_id
from werkzeug.security import generate_password_hash
from config import config
import services.database as database
from services.log import log


def check_account_roles():
    # fetch all account_roles from database
    account_roles_database = database.fetch_all('select * from account_roles;') 

    if not account_roles_database['success']:
        log.error("ROLES", f'> failed account roles initialization check, {account_roles_database['msg']}')
        return None
    
    log.inform("ROLES", f"> Found {len(account_roles_database['data'])} role/s")
    for i in account_roles_database['data']:
        print(f'\t- {i.get('name')} [{i.get('access_level')}]')


def check_accounts():
    account_database = database.fetch_all('select accounts.*, account_roles.name as role_name from accounts inner join account_roles on accounts.role_id = account_roles.id;')

    if not account_database['success']:
        log.error("ACCOUNT", '> failed account initialization check')
        return None
    
    log.inform("ACCOUNT", f"> Found {len(account_database['data'])} account/s")
    for i in account_database['data']:
        print(f'\t- {i.get('username')} [{i.get('role_name')}]')


# check and initialization of "ROOT" role
def initialize_root_role():
    root_admin_role = database.fetch_scalar("SELECT account_roles.id FROM account_roles WHERE account_roles.access_level = 0;")

    # role "ROOT" does not exist
    if root_admin_role['success'] and not root_admin_role['data']:
        log.warn("ROOT_ADMIN-ROLE", "Root admin role not found, attempting to add...")
        added_admin_role = database.execute_single(
            """
            INSERT INTO account_roles (name, access_level) 
            VALUES (%s, %s);
            """,
            ("Root", 0),
        )
        if not added_admin_role['success']:
            log.error("ROOT_ADMIN-ROLE", "Failed to add root admin role")
            return False

        log.inform("ROOT_ADMIN-ROLE", "Root admin role created")
        root_admin_role = database.fetch_scalar(
            "SELECT account_roles.id FROM account_roles WHERE account_roles.access_level = 0;"
        )
    elif root_admin_role['success'] and root_admin_role['data']:
        log.inform("ROOT_ADMIN-ROLE", "Root admin role already exists")
    else:
        log.inform("ROOT_ADMIN-ROLE", "Root admin check failed")


# check for accounts with ADMIN role
def initialize_root_account():
    root_admin_role = database.fetch_scalar("SELECT account_roles.id FROM account_roles WHERE account_roles.access_level = 0;")

    # INITIALIZE ROOT ADMIN ACCOUNT
    root_account = database.fetch_scalar(
        """
            SELECT
                a.id
            FROM accounts as a
            WHERE
                a.email = %s AND
                a.role_id = %s;
        """,
        (config.ROOT_ADMIN_EMAIL, root_admin_role['data']),
    )

    if root_account['success'] and not root_account['data']:
        log.warn("ROOT_ADMIN-ACCOUNT", "Root admin account not found, attempting to add...")

        # NEW ACCOUNT
        account_query = """
            INSERT INTO accounts
                (
                    accounts.id,
                    accounts.role_id,
                    accounts.first_name,
                    accounts.middle_name,
                    accounts.last_name,
                    accounts.email,
                    accounts.username,
                    accounts.password_hash
                )
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        account_params = (
            generate_uuid(),
            root_admin_role['data'],
            "walter",  
            "hartwell",
            "white",
            config.ROOT_ADMIN_EMAIL,
            "admin@system",
            generate_password_hash(config.ROOT_ADMIN_PASSWORD),
        )

        sakses = database.execute_single(account_query, account_params)

        if sakses['success']:
            log.inform("ROOT_ADMIN-ACCOUNT", "root admin account created")
        else:
            log.error("ROOT_ADMIN-ACCOUNT", "failed to create root admin account")
            return False


    else:
        log.inform("ROOT_ADMIN-ACCOUNT", "root admin account already exists")