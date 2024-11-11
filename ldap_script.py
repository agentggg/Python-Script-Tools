import logging
import sys
from typing import List

import ldap

logging.basicConfig(
    level=logging.INFO, 
    format="{levelname} - {asctime} - Function name: {funcName} - Line number:{lineno} - {message}", 
    style="{", 
    datefmt="%m-%d-%Y - %H:%M"
    )

class LdapConnectivity():
    def __init__(self):
        pass

    def initailize_connection(self):    
        try:
            self.conn = ldap.initialize("ldap://localhost")
            self.conn.set_option(ldap.OPT_REFERRALS, 0)
            username = 'cn=admin,dc=bt,dc=com'
            password = 'adminpassword'
            self.conn.simple_bind_s(username, password)
            return(True)
        except ldap.INVALID_CREDENTIALS:
            logging.warning('Invalid credentials provided')
            return(False)

    def get_all_user_account(self, group_name: str):
        """
        Takes the group name as an argument
        Creates the DN with the group_name concat
        Makes the call to the AD server for all the memberUid that is apart of that group
        Python ldap server returns the result in an encoded byte string. The data should be converted to a regular (unicode) string data type
        The unicode string is then appended to the result list and returned
        """
        try:
            result = []
            group_dn = f"cn={group_name},ou=groups,dc=bt,dc=com"
            response = self.conn.search_s(group_dn, ldap.SCOPE_SUBTREE, "(memberUid=*)")
            all_accounts = response[0][1]['memberUid']
            for each_account in all_accounts:
                if isinstance(each_account, bytes):
                    each_account = each_account.decode('utf-8')
                    result.append(each_account)
                else:
                    result.append(each_account)
            return result
        except ldap.INVALID_DN_SYNTAX:
            return('Invalid DN')
        except ldap.NO_SUCH_OBJECT:
            return('Invalid AD Group Name')
        

    def main(self, action: List['str']):
        establish_connection = self.initailize_connection()
        if establish_connection == False:
            logging.error('Failed to Authenticate')
            exit(1)
        if action[1] == 'allUserAccountByGroupName':
            if len(action) != 3:
                logging.error('AD Group Name Parameter Required')
                exit(1)
            user_account_by_group_name = self.get_all_user_account(action[2])
            return user_account_by_group_name
        
if __name__ == "__main__":
    try:
        instantiate = LdapConnectivity()
        connect = instantiate.main(sys.argv)
        logging.info(f"==>> connect: {connect}")
    except TypeError:
        logging.critical('Missing parameter')
    
