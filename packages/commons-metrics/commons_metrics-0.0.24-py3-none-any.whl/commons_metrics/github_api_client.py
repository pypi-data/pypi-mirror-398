import requests
import base64
import time
from threading import Lock
from typing import List, Dict, Optional
import os
from .commons_repos_client import CommonsReposClient


class RateLimiter:
    """
    Controla el rate limiting para respetar los límites de API de GitHub.
    GitHub permite 5000 requests/hora autenticados = ~1.4 TPS.
    Usamos 720ms entre requests (1.39 TPS) para estar seguros.
    """
    def __init__(self, delay: float = 0.72):
        self.delay = delay
        self.last_request_time = 0
        self.lock = Lock()
    
    def wait(self):
        """Espera el tiempo necesario antes de hacer el siguiente request"""
        with self.lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            if time_since_last_request < self.delay:
                sleep_time = self.delay - time_since_last_request
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()


class GitHubAPIClient:
    """
    Cliente para interactuar con la API de GitHub con rate limiting integrado.
    Controla automáticamente el TPS para no exceder los límites de GitHub (5000 req/hora).
    """
    
    # Rate limiter compartido entre todas las instancias
    _rate_limiter = RateLimiter(delay=0.72)  # 720ms entre requests = 1.39 TPS
    
    def __init__(self, token: str, owner: str = None, repo: str = None, enable_rate_limit: bool = True):
        """
        Inicializa el cliente de GitHub API
        
        Args:
            token: Personal Access Token de GitHub
            owner: Dueño del repositorio (ej: 'grupobancolombia-innersource') - Opcional
            repo: Nombre del repositorio (ej: 'NU0066001_BDS_MOBILE_Lib') - Opcional
            enable_rate_limit: Si True, aplica rate limiting automático (por defecto True)
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.enable_rate_limit = enable_rate_limit
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}" if owner and repo else "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_directory_contents(self, path: str = "") -> List[Dict]:
        """
        Obtiene el contenido de un directorio en el repositorio
        
        Args:
            path: Ruta del directorio (ej: 'lib/atoms')
            
        Returns:
            Lista de diccionarios con información de archivos/carpetas
        """
        if self.enable_rate_limit:
            self._rate_limiter.wait()
        
        url = f"{self.base_url}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return []
        else:
            raise Exception(f"Error getting directory contents: {response.status_code} - {response.text}")
    
    def get_file_content(self, path: str) -> Optional[str]:
        """
        Obtiene el contenido de un archivo
        
        Args:
            path: Ruta del archivo en el repositorio
            
        Returns:
            Contenido del archivo como string, o None si no existe
        """
        if self.enable_rate_limit:
            self._rate_limiter.wait()
        
        url = f"{self.base_url}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            content = response.json()
            if content.get('encoding') == 'base64':
                decoded_content = base64.b64decode(content['content']).decode('utf-8')
                return decoded_content
            return None
        elif response.status_code == 404:
            return None
        else:
            raise Exception(f"Error getting file content: {response.status_code} - {response.text}")
    
    def list_folders_in_directory(self, path: str) -> List[str]:
        """
        Lista solo las carpetas dentro de un directorio
        
        Args:
            path: Ruta del directorio
            
        Returns:
            Lista de nombres de carpetas
        """
        contents = self.get_directory_contents(path)
        folders = [
            item['name'] 
            for item in contents 
            if item['type'] == 'dir'
        ]
        return folders
    
    def walk_directory(self, path: str = "", extension: str = None, exclude_patterns: List[str] = None) -> List[Dict]:
        """
        Recorre recursivamente un directorio y retorna todos los archivos
        
        Args:
            path: Ruta del directorio inicial
            extension: Extensión a filtrar (ej: '.ts', '.dart')
            exclude_patterns: Lista de patrones a excluir (ej: ['.spec.', '.test.', '.d.ts'])
            
        Returns:
            Lista de diccionarios con información de archivos encontrados
        """
        all_files = []
        exclude_patterns = exclude_patterns or []
        
        def should_exclude(filename: str) -> bool:
            return any(pattern in filename for pattern in exclude_patterns)
        
        def recurse_directory(current_path: str):
            contents = self.get_directory_contents(current_path)
            
            for item in contents:
                item_path = f"{current_path}/{item['name']}" if current_path else item['name']
                
                if item['type'] == 'file':
                    # Aplicar filtros de extensión y exclusión
                    if extension and not item['name'].endswith(extension):
                        continue
                    if should_exclude(item['name']):
                        continue
                    
                    all_files.append({
                        'name': item['name'],
                        'path': item_path,
                        'url': item.get('url', ''),
                        'download_url': item.get('download_url', '')
                    })
                    
                elif item['type'] == 'dir':
                    # Excluir directorios comunes que no contienen componentes
                    if item['name'] not in ['node_modules', 'dist', 'build', '.git', 'test', 'tests', '__pycache__']:
                        recurse_directory(item_path)
        
        recurse_directory(path)
        return all_files
    
    def search_code(self, query: str, per_page: int = 100) -> List[Dict]:
        """
        Busca código en GitHub usando la API de búsqueda
        
        Args:
            query: Query de búsqueda (ej: '"bds_mobile" in:file filename:pubspec.yaml')
            per_page: Número de resultados por página (máximo 100)
            
        Returns:
            Lista de diccionarios con información de archivos encontrados
        """
        all_results = []
        page = 1
        
        while True:
            if self.enable_rate_limit:
                self._rate_limiter.wait()
            
            url = "https://api.github.com/search/code"
            params = {
                'q': query,
                'per_page': per_page,
                'page': page
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                all_results.extend(items)
                
                # Si hay menos items que per_page, es la última página
                if len(items) < per_page:
                    break
                    
                page += 1
            elif response.status_code == 403:
                # Rate limit alcanzado
                print(f"⚠️ Rate limit alcanzado. Resultados obtenidos: {len(all_results)}")
                break
            else:
                raise Exception(f"Error searching code: {response.status_code} - {response.text}")
        
        return all_results
    
    def search_projects_with_bds(self, platform: str, design_system_name: str = None) -> List[Dict]:
        """
        Busca proyectos que usan el sistema de diseño BDS (mobile o web)
        
        Args:
            platform: 'mobile' o 'web'
            design_system_name: Nombre del paquete del sistema de diseño
                               Si no se proporciona, usa valores por defecto:
                               - mobile: "bds_mobile"
                               - web: "@bancolombia/design-system-web"
            
        Returns:
            Lista de proyectos con información del repositorio incluyendo la versión
        
        Raises:
            ValueError: Si platform no es 'mobile' o 'web'
        """
        # Validar plataforma
        if platform not in ['mobile', 'web']:
            raise ValueError(f"Platform debe ser 'mobile' o 'web', se recibió: {platform}")
        
        # Configurar valores según la plataforma
        if platform == 'mobile':
            config_file = 'pubspec.yaml'
            default_package_name = 'bds_mobile'
            extract_version_method = CommonsReposClient.extract_package_version_from_pubspec
        else:  # web
            config_file = 'package.json'
            default_package_name = '@bancolombia/design-system-web'
            extract_version_method = CommonsReposClient.extract_package_version_from_package_json
        
        # Usar nombre de paquete por defecto si no se proporciona
        package_name = design_system_name or default_package_name
        
        # Agregar filtro de organización si self.owner está definido
        org_filter = f" org:{self.owner}" if self.owner else ""
        query = f'"{package_name}" in:file filename:{config_file}{org_filter}'
        results = self.search_code(query)
        
        projects = []
        for item in results:
            # Obtener contenido del archivo de configuración para extraer la versión
            file_content = self._get_file_content_from_url(item['url'])
            version = extract_version_method(file_content, package_name)
            
            project_info = {
                'name': item['repository']['name'],
                'full_name': item['repository']['full_name'],
                'owner': item['repository']['owner']['login'],
                'repo_url': item['repository']['html_url'],
                'file_path': item['path'],
                'bds_version': version
            }
            projects.append(project_info)
        
        return projects
    
    def search_repositories(self, query: str, per_page: int = 100) -> List[Dict]:
        """
        Busca repositorios en GitHub usando la API de búsqueda
        
        Args:
            query: Query de búsqueda (ej: 'NU0296001 mobile in:name org:grupobancolombia-innersource')
            per_page: Número de resultados por página (máximo 100)
            
        Returns:
            Lista de diccionarios con información de repositorios encontrados
        """
        all_results = []
        page = 1
        search_url = "https://api.github.com/search/repositories"
        
        while True:
            if self.enable_rate_limit:
                self._rate_limiter.wait()
            
            params = {
                'q': query,
                'per_page': per_page,
                'page': page
            }
            
            response = requests.get(search_url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"Error searching repositories: {response.status_code}")
                print(f"Response: {response.text}")
                break
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
            
            all_results.extend(items)
            
            # Verificar si hay más páginas
            if len(items) < per_page:
                break
            
            page += 1
            
        return all_results
    
    def _get_file_content_from_url(self, api_url: str) -> Optional[str]:
        """
        Obtiene el contenido de un archivo desde una URL de la API de GitHub
        
        Args:
            api_url: URL de la API de GitHub para el archivo
            
        Returns:
            Contenido del archivo como string, o None si no existe
        """
        if self.enable_rate_limit:
            self._rate_limiter.wait()
        
        response = requests.get(api_url, headers=self.headers)
        
        if response.status_code == 200:
            content = response.json()
            if content.get('encoding') == 'base64':
                decoded_content = base64.b64decode(content['content']).decode('utf-8')
                return decoded_content
            return None
        return None