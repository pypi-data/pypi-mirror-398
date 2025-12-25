import requests
import time
import json
import re
from typing import List, Dict, Optional
from requests.exceptions import HTTPError, Timeout, ConnectionError
import urllib3
from .commons_repos_client import CommonsReposClient

# Suprimir warnings de SSL para Azure DevOps con certificados corporativos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AzureDevOpsClient:
    """
    Cliente para interactuar con la API de Azure DevOps
    """
    
    def __init__(self, token: str, organization: str = "grupobancolombia", 
                 project_id: str = "b267af7c-3233-4ad1-97b3-91083943100d"):
        """
        Inicializa el cliente de Azure DevOps API
        
        Args:
            token: Bearer token de Azure DevOps
            organization: Nombre de la organización (default: 'grupobancolombia')
            project_id: ID del proyecto VSTI (default: ID de Vicepresidencia Servicios de Tecnología)
        """
        self.token = token
        self.organization = organization
        self.project_id = project_id
        
        # URLs de Azure DevOps
        self.base_url = f"https://{organization}.visualstudio.com/"
        self.search_url = f"https://{organization}.almsearch.visualstudio.com/"
        self.api_path = "_apis/"
        
        # Headers de autenticación
        self.headers = {
            "Accept": "application/json;api-version=5.0-preview.1",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Configuración
        self.max_results_per_page = 1000
        self.verify_ssl = False  # Desactivar para certificados corporativos
        self.excluded_repos = ["deprecated", "test", "prueba", "poc", "jubilado"]
    
    def _requests_with_retries(self, method: str, url: str, 
                               headers: Dict = None, params: Dict = None, 
                               json_body: Dict = None, timeout: tuple = (10, 300), 
                               retries: int = 5, backoff_factor: float = 0.5):
        """
        Realiza peticiones HTTP con reintentos automáticos
        
        Args:
            method: Método HTTP ('GET' o 'POST')
            url: URL a consultar
            headers: Headers de la petición
            params: Parámetros de la petición (para GET)
            json_body: Body JSON (para POST)
            timeout: Timeout de conexión y lectura
            retries: Número de reintentos
            backoff_factor: Factor de espera exponencial
            
        Returns:
            Response object
        """
        headers = headers or self.headers
        
        for attempt in range(retries):
            try:
                if method.upper() == 'GET':
                    response = requests.get(
                        url, 
                        headers=headers, 
                        params=params, 
                        timeout=timeout,
                        verify=self.verify_ssl
                    )
                elif method.upper() == 'POST':
                    response = requests.post(
                        url, 
                        headers=headers, 
                        json=json_body, 
                        timeout=timeout,
                        verify=self.verify_ssl
                    )
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")
                
                response.raise_for_status()
                return response
                
            except (Timeout, ConnectionError, HTTPError) as e:
                if isinstance(e, HTTPError) and e.response.status_code < 500:
                    raise e
                if attempt < retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    print(f"⚠️ Intento {attempt + 1}/{retries} fallido. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise ConnectionError(f"No se pudo conectar a {url} después de {retries} intentos.")
    
    def _search_repos_with_file(self, filename: str, 
                               project_filter: str = "Vicepresidencia Servicios de Tecnología") -> List[Dict]:
        """
        Busca repositorios que contengan un archivo específico
        
        Args:
            filename: Nombre del archivo a buscar (ej: 'pubspec.yaml', 'package.json')
            project_filter: Filtro de proyecto de Azure DevOps
            
        Returns:
            Lista de repositorios con nombre, ID y metadata
        """
        print(f"🔍 Buscando repositorios en Azure DevOps con archivo '{filename}'...")
        
        search_expression = f'file:{filename}'
        all_repo_info = set()
        skip_results = 0
        
        api_url = f"{self.search_url}{self.project_id}/{self.api_path}search/codeQueryResults"
        
        while True:
            json_body = {
                "searchText": search_expression,
                "skipResults": skip_results,
                "takeResults": self.max_results_per_page,
                "summarizedHitCountsNeeded": True,
                "searchFilters": {
                    "ProjectFilters": [project_filter]
                },
                "filters": [],
                "includeSuggestions": False,
                "sortOptions": []
            }
            
            try:
                response = self._requests_with_retries(
                    "POST", 
                    api_url, 
                    json_body=json_body
                )
                
                # Validar el status code antes de parsear
                if response.status_code != 200:
                    print(f"❌ Error HTTP {response.status_code}: {response.text[:500]}")
                    break
                
                # Intentar parsear el JSON
                try:
                    data = response.json()
                except json.JSONDecodeError as json_err:
                    print(f"❌ Error parseando respuesta JSON: {json_err}")
                    print(f"   Respuesta raw (primeros 500 caracteres): {response.text[:500]}")
                    break
                
                results_wrapper = data.get("results", {})
                
                # Manejar diferentes estructuras de respuesta
                if isinstance(results_wrapper, dict):
                    results = results_wrapper.get("values", [])
                elif isinstance(results_wrapper, list):
                    results = results_wrapper
                else:
                    results = []
                
                if not results:
                    break
                
                # Extraer información de repositorios y rutas de archivos
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    
                    repo_data = result.get("repository", {})
                    file_path = result.get("path", filename)  # Obtener la ruta completa del archivo
                    
                    if isinstance(repo_data, dict):
                        repo_name = repo_data.get("name")
                        repo_id = repo_data.get("id")
                    elif isinstance(repo_data, str):
                        repo_name = repo_data
                        repo_id = result.get("repositoryId")
                    else:
                        continue
                    
                    if repo_name and repo_id:
                        # Guardar repo_id, repo_name y file_path
                        all_repo_info.add((repo_name, repo_id, file_path))
                
                # Verificar si hay más páginas
                if len(results) < self.max_results_per_page:
                    break
                
                skip_results += len(results)
                
            except Exception as e:
                print(f"❌ Error en búsqueda de Azure: {e}")
                break
        
        # Filtrar repositorios excluidos
        filtered_repos = []
        for repo_name, repo_id, file_path in all_repo_info:
            repo_lower = repo_name.lower()
            should_exclude = any(word.lower() in repo_lower for word in self.excluded_repos)
            
            if not should_exclude:
                filtered_repos.append({
                    "name": repo_name,
                    "id": repo_id,
                    "file_path": file_path,  # Agregar la ruta del archivo encontrado
                    "source": "azure"
                })
        
        print(f"✅ Encontrados {len(filtered_repos)} repositorios en Azure DevOps")
        return sorted(filtered_repos, key=lambda r: r['name'])
    
    def get_repo_files(self, repo_id: str, extension: str = None, 
                      exclude_patterns: List[str] = None) -> List[Dict]:
        """
        Obtiene todos los archivos de un repositorio
        
        Args:
            repo_id: ID del repositorio en Azure DevOps
            extension: Extensión a filtrar (ej: '.dart', '.ts')
            exclude_patterns: Lista de patrones a excluir (ej: ['test', '.spec.'])
            
        Returns:
            Lista de archivos con path, objectId y metadata
        """
        exclude_patterns = exclude_patterns or []
        items_url = f"{self.base_url}{self.project_id}/{self.api_path}git/repositories/{repo_id}/items"
        params = {
            "recursionLevel": "full",
            "api-version": "7.1"
        }
        
        try:
            response = self._requests_with_retries(
                'GET',
                items_url,
                params=params,
                timeout=(10, 600)
            )
            
            all_items = response.json().get("value", [])
            filtered_files = []
            
            for item in all_items:
                # Solo archivos (blobs)
                if item.get("gitObjectType") != "blob":
                    continue
                
                path = item.get("path", "")
                path_lower = path.lower()
                
                # Filtrar por extensión si se especifica
                if extension and not path_lower.endswith(extension.lower()):
                    continue
                
                # Aplicar patrones de exclusión
                should_exclude = any(pattern.lower() in path_lower for pattern in exclude_patterns)
                if should_exclude:
                    continue
                
                filtered_files.append({
                    'name': path.split('/')[-1],
                    'path': path,
                    'objectId': item.get('objectId'),
                    'url': item.get('url', '')
                })
            
            return filtered_files
            
        except Exception as e:
            print(f"❌ Error obteniendo archivos del repo {repo_id}: {e}")
            return []
    
    def get_file_content(self, repo_id: str, blob_id: str) -> Optional[str]:
        """
        Obtiene el contenido de un archivo por su blob ID
        
        Args:
            repo_id: ID del repositorio
            blob_id: ID del blob (archivo)
            
        Returns:
            Contenido del archivo como string, o None si hay error
        """
        if not blob_id:
            return None
        
        content_url = f"{self.base_url}{self.project_id}/{self.api_path}git/repositories/{repo_id}/blobs/{blob_id}"
        params = {
            "api-version": "7.1",
            "$format": "octetstream"
        }
        
        try:
            response = self._requests_with_retries(
                'GET',
                content_url,
                params=params,
                timeout=(10, 180)
            )
            return response.text
            
        except Exception as e:
            print(f"⚠️ Error obteniendo contenido de archivo: {e}")
            return None
    
    def _get_file_content_by_path(self, repo_id: str, file_path: str) -> Optional[str]:
        """
        Obtiene el contenido de un archivo por su ruta
        
        Args:
            repo_id: ID del repositorio
            file_path: Ruta del archivo en el repositorio
            
        Returns:
            Contenido del archivo como string, o None si hay error
        """
        # Primero obtener el objectId del archivo
        items_url = f"{self.base_url}{self.project_id}/{self.api_path}git/repositories/{repo_id}/items"
        params = {
            "path": file_path,
            "api-version": "7.1"
        }
        
        try:
            response = self._requests_with_retries(
                'GET',
                items_url,
                params=params,
                timeout=(10, 60)
            )
            
            item_data = response.json()
            object_id = item_data.get('objectId')
            
            if object_id:
                return self.get_file_content(repo_id, object_id)
            
            return None
            
        except HTTPError as e:
            # Si es 404, el archivo no existe (es normal, no mostrar error)
            if e.response.status_code == 404:
                return None
            # Otros errores HTTP sí se muestran
            print(f"⚠️ Error HTTP {e.response.status_code} obteniendo {file_path}")
            return None
        except Exception as e:
            # Otros errores generales
            print(f"⚠️ Error obteniendo archivo por ruta: {e}")
            return None
    
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
            Lista de proyectos con información completa
            
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
        
        # Buscar repositorios con el archivo de configuración
        repos = self._search_repos_with_file(config_file)
        
        projects = []
        for idx, repo in enumerate(repos, 1):
            print(f"   📦 [{idx}/{len(repos)}] Verificando {repo['name']}...")
            
            # Usar la ruta del archivo encontrado por la búsqueda (puede estar en subcarpetas)
            file_path = repo.get('file_path', config_file)
            
            # Obtener contenido del archivo usando la ruta completa
            file_content = self._get_file_content_by_path(repo['id'], file_path)
            
            if not file_content:
                continue
            
            # Verificar si usa BDS
            if package_name not in file_content:
                continue
            
            # Extraer versión
            version = extract_version_method(file_content, package_name)
            
            project_info = {
                'name': repo['name'],
                'full_name': f"azure/{repo['name']}",
                'owner': 'azure',
                'repo_url': f"{self.base_url}{self.project_id}/_git/{repo['name']}",
                'file_path': file_path,
                'bds_version': version,
                'source': 'azure',
                'repo_id': repo['id']
            }
            
            projects.append(project_info)
        
        print(f"\n✅ Total proyectos {platform} con BDS en Azure: {len(projects)}")
        return projects
