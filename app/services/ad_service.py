# app/services/ad_service.py - Versión adaptativa con detección dinámica de atributos

from ldap3 import Server, Connection, ALL, SUBTREE, ALL_ATTRIBUTES
from typing import List, Dict, Optional, Tuple
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class ActiveDirectoryService:
    def __init__(self):
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Cargar y validar configuración
        self._load_config()
        
        # Cache para formato de credenciales exitoso
        self._successful_credential_format = None
        
        # Cache para atributos disponibles
        self._available_attributes = None
        self._tested_attributes = False
    
    def _load_config(self):
        """Cargar configuración desde variables de entorno"""
        self.server_host = os.getenv("AD_SERVER_HOST", "").strip()
        self.server_port = int(os.getenv("AD_SERVER_PORT", 389))
        self.use_ssl = os.getenv("AD_USE_SSL", "false").lower().strip() == "true"
        self.base_dn = os.getenv("AD_BASE_DN", "").strip()
        self.bind_user = os.getenv("AD_BIND_USER", "").strip()
        self.bind_password = os.getenv("AD_BIND_PASSWORD", "").strip()
        self.user_search_base = os.getenv("AD_USER_SEARCH_BASE", self.base_dn).strip()
        
        # Log de configuración (sin mostrar contraseña)
        self.logger.info(f"AD Config - Host: {self.server_host}, Port: {self.server_port}")
        self.logger.info(f"AD Config - Base DN: {self.base_dn}")
        self.logger.info(f"AD Config - Bind User: {self.bind_user}")
    
    def _validate_config(self):
        """Validar que toda la configuración requerida esté presente"""
        required_vars = {
            'AD_SERVER_HOST': self.server_host,
            'AD_BASE_DN': self.base_dn,
            'AD_BIND_USER': self.bind_user,
            'AD_BIND_PASSWORD': self.bind_password
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            error_msg = f"Missing required AD configuration variables: {', '.join(missing_vars)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _discover_available_attributes(self, conn: Connection) -> Dict[str, bool]:
        """Descubrir qué atributos están disponibles en este AD"""
        
        if self._available_attributes is not None:
            return self._available_attributes
        
        self.logger.info("Discovering available attributes in AD schema...")
        
        # Lista de atributos a probar
        attributes_to_test = [
            'cn', 'sAMAccountName', 'displayName', 'name', 'givenName', 'sn',
            'mail', 'userPrincipalName', 'distinguishedName', 
            'department', 'title', 'telephoneNumber', 'mobile',
            'physicalDeliveryOfficeName', 'company', 'manager',
            'employeeID', 'employeeNumber', 'whenCreated', 'lastLogon',
            'memberOf', 'objectClass', 'objectCategory'
        ]
        
        available = {}
        
        # Método 1: Probar cada atributo individualmente
        for attr in attributes_to_test:
            try:
                test_result = conn.search(
                    search_base=self.user_search_base,
                    search_filter="(&(objectClass=user)(objectCategory=person))",
                    search_scope=SUBTREE,
                    attributes=[attr],
                    size_limit=1
                )
                
                if test_result and conn.entries:
                    available[attr] = True
                    self.logger.debug(f"✅ Attribute available: {attr}")
                else:
                    available[attr] = False
                    self.logger.debug(f"❌ Attribute not available: {attr}")
                    
            except Exception as e:
                available[attr] = False
                self.logger.debug(f"❌ Attribute error {attr}: {str(e)}")
        
        # Método 2: Si el método 1 falla, usar ALL_ATTRIBUTES en una consulta
        if not any(available.values()):
            try:
                self.logger.info("Trying ALL_ATTRIBUTES discovery method...")
                test_result = conn.search(
                    search_base=self.user_search_base,
                    search_filter="(&(objectClass=user)(objectCategory=person))",
                    search_scope=SUBTREE,
                    attributes=ALL_ATTRIBUTES,
                    size_limit=1
                )
                
                if test_result and conn.entries:
                    entry = conn.entries[0]
                    actual_attributes = list(entry._attributes.keys())
                    self.logger.info(f"Discovered {len(actual_attributes)} attributes via ALL_ATTRIBUTES")
                    
                    # Marcar atributos encontrados como disponibles
                    for attr in attributes_to_test:
                        available[attr] = attr in actual_attributes
                        
            except Exception as e:
                self.logger.warning(f"ALL_ATTRIBUTES discovery failed: {e}")
        
        # Fallback: usar solo atributos absolutamente básicos
        if not any(available.values()):
            self.logger.warning("Could not discover attributes, using minimal fallback")
            available = {
                'cn': True,
                'distinguishedName': True,
                'objectClass': True
            }
        
        self._available_attributes = available
        self._tested_attributes = True
        
        # Log de atributos disponibles
        available_list = [attr for attr, avail in available.items() if avail]
        self.logger.info(f"Available attributes ({len(available_list)}): {available_list[:10]}...")
        
        return available
    
    def _get_safe_attributes(self, conn: Connection) -> List[str]:
        """Obtener lista de atributos seguros para usar en consultas"""
        
        if not self._tested_attributes:
            self._discover_available_attributes(conn)
        
        if not self._available_attributes:
            return ['cn', 'distinguishedName']
        
        # Retornar solo atributos que estén disponibles
        safe_attrs = [attr for attr, available in self._available_attributes.items() if available]
        
        if not safe_attrs:
            safe_attrs = ['cn', 'distinguishedName']
        
        return safe_attrs
    
    def _get_connection(self) -> Optional[Connection]:
        """Crear conexión a Active Directory"""
        try:
            # Validar configuración
            self._validate_config()
            
            self.logger.info(f"Connecting to AD: {self.server_host}:{self.server_port}")
            
            server = Server(
                self.server_host, 
                port=self.server_port, 
                use_ssl=self.use_ssl, 
                get_info=ALL
            )
            
            # Probar diferentes formatos de usuario si no tenemos uno exitoso
            if not self._successful_credential_format:
                self._successful_credential_format = self._find_working_credential()
            
            if not self._successful_credential_format:
                self.logger.error("No working credential format found")
                return None
            
            conn = Connection(
                server,
                user=self._successful_credential_format,
                password=self.bind_password,
                auto_bind=True
            )
            
            self.logger.info("Successfully connected to Active Directory")
            return conn
            
        except Exception as e:
            self.logger.error(f"Error connecting to AD: {str(e)}")
            return None
    
    def _find_working_credential(self) -> Optional[str]:
        """Encontrar formato de credencial que funcione"""
        
        original_user = self.bind_user
        base_dn = self.base_dn
        
        # Generar diferentes formatos
        formats_to_try = []
        
        if "@" in original_user:
            username_part = original_user.split("@")[0]
            domain_part = original_user.split("@")[1]
        else:
            username_part = original_user
            domain_part = "ikeasi.com"  # Actualizado con tu dominio
        
        # Extraer dominio del DN
        domain_parts = []
        for part in base_dn.split(","):
            if part.strip().upper().startswith("DC="):
                domain_parts.append(part.strip()[3:])
        
        domain_from_dn = ".".join(domain_parts) if domain_parts else domain_part
        
        # Formatos a probar (tu formato exitoso primero)
        formats_to_try = [
            f"{username_part}@{domain_from_dn}",  # Formato que ya funciona
            original_user,  # Formato original
            username_part.replace("su-", "") + f"@{domain_from_dn}",  # Sin prefijo su-
            f"IKEASI\\{username_part}",  # Formato Domain\User
            username_part,  # Solo username
            f"CN={username_part},CN=Users,{base_dn}",  # DN en Users
            f"CN={username_part},OU=Users,{base_dn}",  # DN en OU Users
        ]
        
        server = Server(self.server_host, port=self.server_port, use_ssl=self.use_ssl)
        
        for user_format in formats_to_try:
            if not user_format:
                continue
                
            self.logger.info(f"Trying credential format: {user_format}")
            
            try:
                test_conn = Connection(
                    server,
                    user=user_format,
                    password=self.bind_password,
                    auto_bind=True
                )
                test_conn.unbind()
                
                self.logger.info(f"SUCCESS: Working credential format: {user_format}")
                return user_format
                
            except Exception as e:
                self.logger.debug(f"Failed credential format {user_format}: {str(e)}")
                continue
        
        self.logger.error("No working credential format found")
        return None
    
    def search_users(self, search_term: str = "", max_results: int = 100) -> List[Dict]:
        """Buscar usuarios en Active Directory con detección automática de atributos"""
        try:
            self.logger.info(f"Searching users with term: '{search_term}'")
            
            conn = self._get_connection()
            if not conn:
                self.logger.error("Could not establish AD connection")
                return []
            
            try:
                # Descubrir atributos disponibles
                safe_attributes = self._get_safe_attributes(conn)
                self.logger.info(f"Using safe attributes: {safe_attributes[:5]}...")
                
                # Construir filtro de búsqueda adaptativo
                if search_term:
                    # Usar atributos disponibles para el filtro
                    filter_conditions = []
                    
                    if 'cn' in safe_attributes:
                        filter_conditions.append(f"(cn=*{search_term}*)")
                    if 'displayName' in safe_attributes:
                        filter_conditions.append(f"(displayName=*{search_term}*)")
                    if 'sAMAccountName' in safe_attributes:
                        filter_conditions.append(f"(sAMAccountName=*{search_term}*)")
                    if 'mail' in safe_attributes:
                        filter_conditions.append(f"(mail=*{search_term}*)")
                    if 'givenName' in safe_attributes:
                        filter_conditions.append(f"(givenName=*{search_term}*)")
                    
                    # Si no tenemos atributos de búsqueda, usar cn por defecto
                    if not filter_conditions:
                        filter_conditions = [f"(cn=*{search_term}*)"]
                    
                    search_filter = f"(&(objectClass=user)(objectCategory=person)(|{''.join(filter_conditions)}))"
                else:
                    search_filter = "(&(objectClass=user)(objectCategory=person))"
                
                self.logger.info(f"Searching in base: {self.user_search_base}")
                self.logger.info(f"Using filter: {search_filter}")
                
                search_result = conn.search(
                    search_base=self.user_search_base,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=safe_attributes,
                    size_limit=max_results
                )
                
                if not search_result:
                    self.logger.warning(f"Search returned no results. Response: {conn.result}")
                    return []
                
                users = []
                for entry in conn.entries:
                    try:
                        user_data = self._extract_user_data_adaptive(entry, safe_attributes)
                        if user_data:
                            users.append(user_data)
                    except Exception as e:
                        self.logger.warning(f"Error processing user entry: {e}")
                        continue
                
                self.logger.info(f"Successfully found {len(users)} users")
                return users
                
            finally:
                conn.unbind()
                
        except Exception as e:
            self.logger.error(f"Error searching users: {str(e)}")
            return []
    
    def _extract_user_data_adaptive(self, entry, available_attributes: List[str]) -> Optional[Dict]:
        """Extraer datos del usuario usando solo atributos disponibles"""
        try:
            def safe_get_attr(attr_name, default=""):
                """Obtener atributo de manera segura"""
                if attr_name not in available_attributes:
                    return default
                    
                try:
                    if hasattr(entry, attr_name):
                        attr_value = getattr(entry, attr_name)
                        if attr_value:
                            if hasattr(attr_value, 'value'):
                                return str(attr_value.value) if attr_value.value else default
                            else:
                                return str(attr_value) if attr_value else default
                    return default
                except:
                    return default
            
            # Determinar nombre de usuario con fallbacks
            username = (safe_get_attr('sAMAccountName') or 
                       safe_get_attr('cn') or 
                       safe_get_attr('name') or 
                       'unknown')
            
            # Determinar nombre para mostrar con fallbacks
            display_name = (safe_get_attr('displayName') or 
                           safe_get_attr('cn') or 
                           safe_get_attr('name') or 
                           username)
            
            # Determinar email con fallbacks
            email = (safe_get_attr('mail') or 
                    safe_get_attr('userPrincipalName') or 
                    '')
            
            # DN con fallback
            dn = safe_get_attr('distinguishedName') or str(entry.entry_dn)
            
            user_data = {
                'username': username,
                'display_name': display_name,
                'first_name': safe_get_attr('givenName'),
                'last_name': safe_get_attr('sn'),
                'email': email,
                'department': safe_get_attr('department'),
                'title': safe_get_attr('title'),
                'phone': safe_get_attr('telephoneNumber'),
                'mobile': safe_get_attr('mobile'),
                'office': safe_get_attr('physicalDeliveryOfficeName'),
                'company': safe_get_attr('company'),
                'manager': safe_get_attr('manager'),
                'employee_id': safe_get_attr('employeeID') or safe_get_attr('employeeNumber'),
                'created_date': None,
                'last_logon': None,
                'dn': dn
            }
            
            # Manejar fechas si están disponibles
            if 'whenCreated' in available_attributes:
                try:
                    if hasattr(entry, 'whenCreated') and entry.whenCreated:
                        user_data['created_date'] = entry.whenCreated.value
                except:
                    pass
                    
            if 'lastLogon' in available_attributes:
                try:
                    if hasattr(entry, 'lastLogon') and entry.lastLogon:
                        user_data['last_logon'] = entry.lastLogon.value
                except:
                    pass
            
            return user_data
            
        except Exception as e:
            self.logger.warning(f"Error extracting user data: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Obtener un usuario específico por username"""
        if not username or not username.strip():
            return None
            
        users = self.search_users(username.strip())
        for user in users:
            if user['username'].lower() == username.lower():
                return user
        return None
    
    def get_user_groups(self, username: str) -> List[str]:
        """Obtener grupos de un usuario"""
        if not username or not username.strip():
            return []
            
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            # Usar atributo de búsqueda disponible
            safe_attrs = self._get_safe_attributes(conn)
            
            if 'sAMAccountName' in safe_attrs:
                user_filter = f"(&(objectClass=user)(sAMAccountName={username.strip()}))"
            else:
                user_filter = f"(&(objectClass=user)(cn={username.strip()}))"
            
            conn.search(
                search_base=self.user_search_base,
                search_filter=user_filter,
                attributes=['memberOf'] if 'memberOf' in safe_attrs else []
            )
            
            if not conn.entries:
                return []
            
            groups = []
            user_entry = conn.entries[0]
            
            if hasattr(user_entry, 'memberOf') and user_entry.memberOf:
                for group_dn in user_entry.memberOf:
                    group_name = str(group_dn).split(',')[0].replace('CN=', '')
                    groups.append(group_name)
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Error getting user groups: {str(e)}")
            return []
        
        finally:
            conn.unbind()
    
    def test_connection(self) -> Dict:
        """Probar la conexión a Active Directory"""
        try:
            # Verificar configuración
            config_status = self.get_config_status()
            if config_status["status"] == "invalid":
                return {
                    "success": False,
                    "error": f"Configuration error: {config_status['error']}",
                    "details": config_status
                }
            
            # Intentar conexión
            conn = self._get_connection()
            if conn:
                # Descubrir atributos
                available_attrs = self._discover_available_attributes(conn)
                conn.unbind()
                
                available_count = sum(1 for avail in available_attrs.values() if avail)
                
                return {
                    "success": True,
                    "message": f"Connection successful using: {self._successful_credential_format}",
                    "working_credential": self._successful_credential_format,
                    "available_attributes": available_count,
                    "config": config_status
                }
            else:
                return {
                    "success": False,
                    "error": "Could not establish connection",
                    "config": config_status
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "config": self.get_config_status()
            }
    
    def get_config_status(self) -> Dict:
        """Obtener estado de la configuración"""
        try:
            self._validate_config()
            return {
                "status": "valid",
                "server_host": self.server_host,
                "server_port": self.server_port,
                "use_ssl": self.use_ssl,
                "base_dn": self.base_dn,
                "bind_user": self.bind_user,
                "user_search_base": self.user_search_base
            }
        except ValueError as e:
            return {
                "status": "invalid",
                "error": str(e)
            }