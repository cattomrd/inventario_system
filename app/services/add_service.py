# app/services/ad_service.py
from ldap3 import Server, Connection, ALL, SUBTREE
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class ActiveDirectoryService:
    def __init__(self):
        self.server_host = os.getenv("AD_SERVER_HOST")
        self.server_port = int(os.getenv("AD_SERVER_PORT", 389))
        self.use_ssl = os.getenv("AD_USE_SSL", "false").lower() == "true"
        self.base_dn = os.getenv("AD_BASE_DN")
        self.bind_user = os.getenv("AD_BIND_USER")
        self.bind_password = os.getenv("AD_BIND_PASSWORD")
        self.user_search_base = os.getenv("AD_USER_SEARCH_BASE", self.base_dn)
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _get_connection(self) -> Optional[Connection]:
        """Crear conexión a Active Directory"""
        try:
            server = Server(
                self.server_host, 
                port=self.server_port, 
                use_ssl=self.use_ssl, 
                get_info=ALL
            )
            
            conn = Connection(
                server,
                user=self.bind_user,
                password=self.bind_password,
                auto_bind=True
            )
            
            return conn
            
        except Exception as e:
            self.logger.error(f"Error connecting to AD: {str(e)}")
            return None
    
    def search_users(self, search_term: str = "", max_results: int = 100) -> List[Dict]:
        """Buscar usuarios en Active Directory"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            # Construir filtro de búsqueda
            if search_term:
                search_filter = f"""(&(objectClass=user)(objectCategory=person)
                    (!(userAccountControl:1.2.840.113556.1.4.803:=2))
                    (|
                        (displayName=*{search_term}*)
                        (sAMAccountName=*{search_term}*)
                        (mail=*{search_term}*)
                        (givenName=*{search_term}*)
                        (sn=*{search_term}*)
                    ))"""
            else:
                search_filter = """(&(objectClass=user)(objectCategory=person)
                    (!(userAccountControl:1.2.840.113556.1.4.803:=2)))"""
            
            # Atributos a obtener
            attributes = [
                'sAMAccountName', 'displayName', 'givenName', 'sn', 
                'mail', 'department', 'title', 'telephoneNumber',
                'mobile', 'physicalDeliveryOfficeName', 'company',
                'manager', 'employeeID', 'whenCreated', 'lastLogon'
            ]
            
            conn.search(
                search_base=self.user_search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes,
                size_limit=max_results
            )
            
            users = []
            for entry in conn.entries:
                user_data = {
                    'username': str(entry.sAMAccountName) if entry.sAMAccountName else '',
                    'display_name': str(entry.displayName) if entry.displayName else '',
                    'first_name': str(entry.givenName) if entry.givenName else '',
                    'last_name': str(entry.sn) if entry.sn else '',
                    'email': str(entry.mail) if entry.mail else '',
                    'department': str(entry.department) if entry.department else '',
                    'title': str(entry.title) if entry.title else '',
                    'phone': str(entry.telephoneNumber) if entry.telephoneNumber else '',
                    'mobile': str(entry.mobile) if entry.mobile else '',
                    'office': str(entry.physicalDeliveryOfficeName) if entry.physicalDeliveryOfficeName else '',
                    'company': str(entry.company) if entry.company else '',
                    'manager': str(entry.manager) if entry.manager else '',
                    'employee_id': str(entry.employeeID) if entry.employeeID else '',
                    'created_date': entry.whenCreated.value if entry.whenCreated else None,
                    'last_logon': entry.lastLogon.value if entry.lastLogon else None,
                    'dn': entry.entry_dn
                }
                users.append(user_data)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Error searching users: {str(e)}")
            return []
        
        finally:
            conn.unbind()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Obtener un usuario específico por username"""
        users = self.search_users(username)
        for user in users:
            if user['username'].lower() == username.lower():
                return user
        return None
    
    def get_user_groups(self, username: str) -> List[str]:
        """Obtener grupos de un usuario"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            # Buscar el usuario
            user_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
            conn.search(
                search_base=self.user_search_base,
                search_filter=user_filter,
                attributes=['memberOf']
            )
            
            if not conn.entries:
                return []
            
            groups = []
            user_entry = conn.entries[0]
            
            if user_entry.memberOf:
                for group_dn in user_entry.memberOf:
                    # Extraer el nombre del grupo del DN
                    group_name = str(group_dn).split(',')[0].replace('CN=', '')
                    groups.append(group_name)
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Error getting user groups: {str(e)}")
            return []
        
        finally:
            conn.unbind()
    
    def test_connection(self) -> bool:
        """Probar la conexión a Active Directory"""
        conn = self._get_connection()
        if conn:
            conn.unbind()
            return True
        return False