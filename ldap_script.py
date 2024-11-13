import logging
import sys
from typing import List

import ldap
from ldap import MOD_REPLACE, MOD_ADD, MOD_DELETE

logging.basicConfig(
    level=logging.ERROR, 
    format="{levelname} - {asctime} - Function name: {funcName} - Line number:{lineno} - {message}", 
    style="{", 
    datefmt="%m-%d-%Y - %H:%M"
    )

class LdapConnectivity():
    def __init__(self):
        pass

    def initialize_connection(self):    
        """
        Initializes an LDAP connection and performs a simple bind.

        This method establishes a connection to the LDAP server, sets necessary options,
        and attempts to bind using provided admin credentials. If the connection or
        authentication fails, it handles the errors and logs appropriate messages.

        Returns:
            bool: True if the connection and binding are successful, False otherwise.

        Raises:
            ldap.INVALID_CREDENTIALS: If the provided credentials are incorrect.
            ldap.SERVER_DOWN: If the LDAP server is unreachable.

        Logging:
            - Logs an error message for invalid credentials.
            - Logs an error message if the server is down.

        Example:
            success = self.initialize_connection()
            if success:
                print("LDAP connection established successfully.")
            else:
                print("Failed to initialize LDAP connection.")
        """
        try:
            self.conn = ldap.initialize("ldap://10.0.0.120")
            self.conn.set_option(ldap.OPT_REFERRALS, 0)
            username = 'cn=admin,dc=bt,dc=com'
            password = 'adminpassword'
            self.conn.simple_bind_s(username, password)
            return(True)
        except ldap.INVALID_CREDENTIALS:
            logging.error('Invalid credentials provided')
            return(False)
        except ldap.SERVER_DOWN:
            logging.error('Connection to server failed')
            return(False)

    def get_all_user_account(self, group_name: str):
        """
        Retrieves all user accounts (memberUid) for a specified LDAP group.

        This method takes the name of an LDAP group as input, constructs the Distinguished Name (DN)
        for the search query, and performs a subtree search to retrieve all users (memberUid) belonging
        to the specified group. The method decodes the returned byte strings to Unicode strings and
        returns a list of user accounts.

        Args:
            group_name (str): The name of the LDAP group to query (e.g., 'no_access').

        Returns:
            list: A list of usernames (str) belonging to the specified group.
            str: 'Invalid DN' if the DN syntax is incorrect.
            str: 'Invalid AD Group Name' if the specified group does not exist.
            bool: False if any other exception occurs.

        Raises:
            ldap.INVALID_DN_SYNTAX: If the constructed DN has an invalid syntax.
            ldap.NO_SUCH_OBJECT: If the specified LDAP group does not exist.

        Example:
            user_accounts = self.get_all_user_account('no_access')
            if user_accounts:
                print(f"User accounts in 'no_access': {user_accounts}")
            else:
                print("Failed to retrieve user accounts.")

        Workflow:
            1. Constructs the DN using the provided group name.
            2. Performs a subtree search with the filter '(memberUid=*)'.
            3. Decodes each memberUid from byte string to Unicode string.
            4. Appends the decoded usernames to the response list.
            5. Returns the list of usernames or an error message if an exception occurs.

        Logging:
            Logs any unexpected exceptions with the error message.
        """
        try:
            response = []
            dn = f"cn={group_name},ou=groups,dc=bt,dc=com"
            result = self.conn.search_s(dn, ldap.SCOPE_SUBTREE, "(memberUid=*)")
            all_accounts = result[0][1]['memberUid']
            for each_account in all_accounts:
                if isinstance(each_account, bytes):
                    each_account = each_account.decode('utf-8')
                    response.append(each_account)
                else:
                    response.append(each_account)
            return response
        except ldap.INVALID_DN_SYNTAX:
            return('Invalid DN')
        except ldap.NO_SUCH_OBJECT:
            return('Invalid AD Group Name')      
        except Exception as err:
            logging.error(f"==>> err: {err}")
            return(False)

    def get_user_account(self, username: str):
        """
        Retrieves the account details for a specified user from the LDAP directory.

        This method accepts a username, constructs a Distinguished Name (DN) for searching,
        and queries the LDAP directory for the user’s account information. It removes sensitive
        attributes, decodes the byte strings to Unicode, and retrieves the group name associated
        with the user's `gidNumber`. The resulting user account data is returned as a dictionary.

        Args:
            username (str): The UID of the user to query (e.g., 'Dana').

        Returns:
            dict: A dictionary containing the user account details with decoded Unicode strings.
                The dictionary includes the following keys:
                    - All user attributes except 'objectClass' and 'userPassword'.
                    - 'gName': The name of the Active Directory group (AD group) the user belongs to.
            str: 'Invalid User Account' if the user account is not found.
            str: 'Failed to Retrieve the User Account' if an unexpected error occurs.

        Raises:
            IndexError: If the search result does not contain the expected user information.
            Exception: For any other unexpected errors.

        Example:
            user_account = self.get_user_account('Dana')
            if user_account:
                print("User Account Details:", user_account)
            else:
                print("User account retrieval failed.")

        Workflow:
            1. Constructs the base DN for searching the LDAP directory.
            2. Performs a subtree search using the username filter `(uId={username})`.
            3. Removes sensitive attributes ('objectClass' and 'userPassword') from the response.
            4. Decodes all byte string attributes to Unicode strings.
            5. Retrieves the AD group name based on the user's `gidNumber`.
            6. Updates the user account dictionary with the group name ('gName').
            7. Returns the processed user account information.

        Logging:
            - Logs any unexpected exceptions with the error message (if applicable).

        Notes:
            - This method removes sensitive data like 'userPassword' from the returned dictionary.
            - The method converts all byte strings to Unicode strings for ease of use.
        """
        try:
            dn = "dc=bt, dc=com"
            response = self.conn.search_s(dn, ldap.SCOPE_SUBTREE, f"(uId={username})")[0][1]
            del response['objectClass'] 
            del response['userPassword'] 
            for each_response_key, each_response_value in response.items():
                response[each_response_key] = each_response_value[0].decode('utf-8')
            group_response = self.conn.search_s(dn, ldap.SCOPE_SUBTREE, f"(gidNumber={response['gidNumber']})", ['cn'])
            ad_group_name = group_response[-1][1]['cn'][0].decode('utf-8')
            response['gName'] = ad_group_name
            return response
        except IndexError:
            return("Invalid User Account")
        except Exception as err:
            logging.error(f"==>> err: {err}")
            return("Failed to Retrieve the User Account")
        
    def update_user_and_add_to_group(self, username, target_group):
        """
        Updates the gidNumber of a user and manages their group membership in an LDAP directory.

        This function retrieves the user's account information, updates the user's gidNumber based
        on the specified target group, removes the user from their current group (if different),
        and adds the user to the target group by modifying the 'memberUid' attribute.

        Args:
            username (str): The UID of the user to be updated (e.g., 'bob').
            target_group (str): The target group to move the user to (e.g., 'admin_access', 'no_access').

        Group Mapping:
            gNumber (dict): A mapping of group names to their corresponding gidNumbers:
                - "admin_access": 500
                - "no_access": 502

        Workflow:
            1. Retrieve the user's account information using `get_user_account`.
            2. Construct the user's DN (Distinguished Name) and the target group's DN.
            3. Determine the user's current group based on their gidNumber.
            4. Update the user's gidNumber to match the target group.
            5. If the user's current group differs from the target group:
                - Remove the user from the current group's 'memberUid' attribute.
            6. Add the user to the target group's 'memberUid' attribute.
            7. If any step fails, rollback the changes to maintain consistency.

        Raises:
            ldap.ALREADY_EXISTS: If the user is already a member of the target group.
            ldap.LDAPError: For any other LDAP-related errors during the update process.

        Returns:
            None
        """
        gNumber = {
            "admin_access": 500,
            "no_access": 502
        }

        account_info = self.get_user_account(username)
        if not account_info:
            return("User not found.")

        user_dn = f"cn={account_info['cn']},dc=bt,dc=com"
        target_group_dn = f"cn={target_group},ou=Groups,dc=bt,dc=com"

        current_gid_number = int(account_info['gidNumber'])
        current_group = None
        for group, gid in gNumber.items():
            if gid == current_gid_number:
                current_group = group
                break

        if not current_group:
            return("Current group not found for the user.")

        current_group_dn = f"cn={current_group},ou=Groups,dc=bt,dc=com"

        new_gid_number = str(gNumber[target_group]).encode()
        current_gid_number_bytes = str(current_gid_number).encode()
        mod_list_gid = [(MOD_REPLACE, 'gidNumber', new_gid_number)]
        mod_add_username = [(MOD_ADD, 'memberUid', username.encode())]
        mod_remove_username = [(MOD_DELETE, 'memberUid', username.encode())]

        try:
            self.conn.modify_s(user_dn, mod_list_gid)
            if current_group != target_group:
                try:
                    self.conn.modify_s(current_group_dn, mod_remove_username)
                    return("successfully moved the user")
                except ldap.LDAPError as e:
                    self.conn.modify_s(user_dn, [(MOD_REPLACE, 'gidNumber', current_gid_number_bytes)])
                    raise e

            try:
                self.conn.modify_s(target_group_dn, mod_add_username)
                return("successfully moved the user")
            except ldap.LDAPError as e:
                self.conn.modify_s(user_dn, [(MOD_REPLACE, 'gidNumber', current_gid_number_bytes)])
                if current_group != target_group:
                    self.conn.modify_s(current_group_dn, mod_add_username)
                raise e
        except ldap.LDAPError:
            return(f"User '{username}' is already a member of the group '{target_group}'.")
        except Exception as e:
            return(f"LDAP Error: {e}")

    def main(self, action: List['str']):
        try:
            establish_connection = self.initialize_connection() 
            if establish_connection == False:
                logging.error('Failed to Authenticate')
                exit(0)

            if action[1] == 'allUserAccountByGroupName':
                if (len(action) == 3) and (action[2] not in ['access', 'admin_access']):
                    logging.error('Correct AD Group Name Parameter Required')
                    exit(0)
                response = self.get_all_user_account(action[2])    
            elif action[1] == 'userAccount':
                if len(action) != 3:
                    logging.error('Only Username Parameter Required')
                    exit(0)
                response = self.get_user_account(action[2])
            elif action[1] == 'moveUser':
                response = self.update_user_and_add_to_group(action[2], action[3])
        except Exception as e:
            logging.error(f"==>> e: {e}")
            return('Check the Required Parameters for the Endpoint')
        return response
 
if __name__ == "__main__":
    try:
        instantiate = LdapConnectivity()
        response = instantiate.main(sys.argv)
        print(response)
    except TypeError:
        logging.critical('Missing parameter')
