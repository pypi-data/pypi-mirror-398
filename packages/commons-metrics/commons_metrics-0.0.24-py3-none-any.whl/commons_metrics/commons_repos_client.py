"""
Módulo con funciones compartidas entre clientes de repositorios (GitHub, Azure DevOps)
"""
import re
import json
from typing import Optional, Dict


class CommonsReposClient:
    """Utilidades compartidas para clientes de repositorios"""
    
    @staticmethod
    def extract_package_version_from_pubspec(content: str, package_name: str) -> Optional[Dict]:
        """
        Extrae la versión de un paquete del contenido de pubspec.yaml
        
        Args:
            content: Contenido del archivo pubspec.yaml
            package_name: Nombre del paquete a buscar (ej: 'bds_mobile')
            
        Returns:
            Diccionario con versión completa y major, o None
        """
        if not content:
            return None
        
        # Patrones para diferentes formatos de versión (con posibles espacios antes)
        # IMPORTANTE: debe estar en sección dependencies: para evitar falsos positivos
        simple_patterns = [
            # Formato simple: bds_mobile: ^8.127.0 (en la misma línea)
            rf'^\s*{package_name}\s*:\s*\^?([0-9]+\.[0-9]+\.[0-9]+)',
            # Formato con >= o ~
            rf'^\s*{package_name}\s*:\s*>=([0-9]+\.[0-9]+\.[0-9]+)',
            rf'^\s*{package_name}\s*:\s*~>([0-9]+\.[0-9]+\.[0-9]+)',
        ]
        
        for pattern in simple_patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                version = match.group(1)
                major_version = version.split('.')[0]
                return {
                    'full_version': version,
                    'major_version': major_version
                }
        
        # Formato hosted con artifactory (múltiples variantes)
        hosted_patterns = [
            # Patrón 1: hosted simple (una línea)
            rf'^(\s*){package_name}\s*:\s*$\s*\1\s+hosted:\s*https?://.*?$\s*\1\s+version:\s*["\']?\^?([0-9]+\.[0-9]+\.[0-9]+)',
            # Patrón 2: hosted con name/url (multilínea)
            rf'^(\s*){package_name}\s*:\s*$\s*\1\s+hosted:\s*$.*?\s*\1\s+version:\s*["\']?\^?([0-9]+\.[0-9]+\.[0-9]+)',
        ]
        
        for hosted_pattern in hosted_patterns:
            hosted_match = re.search(hosted_pattern, content, re.MULTILINE | re.DOTALL)
            if hosted_match:
                # El último grupo siempre es la versión
                version = hosted_match.groups()[-1]
                major_version = version.split('.')[0]
                return {
                    'full_version': version,
                    'major_version': major_version
                }
        
        return None

    @staticmethod
    def extract_package_version_from_package_json(content: str, package_name: str) -> Optional[Dict]:
        """
        Extrae la versión de un paquete del contenido de package.json
        
        Args:
            content: Contenido del archivo package.json
            package_name: Nombre del paquete a buscar (ej: '@bancolombia/design-system-web')
            
        Returns:
            Diccionario con versión completa y major, o None
        """
        if not content:
            return None
        
        try:
            # Intentar parsear como JSON
            package_data = json.loads(content)
            
            # Buscar en dependencies y devDependencies
            for dep_key in ['dependencies', 'devDependencies']:
                if dep_key in package_data:
                    deps = package_data[dep_key]
                    if package_name in deps:
                        version_str = deps[package_name]
                        
                        # Extraer versión semántica (eliminar ^, ~, >=, etc.)
                        version_match = re.search(r'([0-9]+\.[0-9]+\.[0-9]+)', version_str)
                        if version_match:
                            version = version_match.group(1)
                            major_version = version.split('.')[0]
                            return {
                                'full_version': version,
                                'major_version': major_version
                            }
        except json.JSONDecodeError:
            # Si falla el parseo JSON, intentar con regex
            pass
        
        # Fallback: buscar con regex
        pattern = rf'"{re.escape(package_name)}"\s*:\s*"[\^~>=<]*([0-9]+\.[0-9]+\.[0-9]+)'
        match = re.search(pattern, content)
        if match:
            version = match.group(1)
            major_version = version.split('.')[0]
            return {
                'full_version': version,
                'major_version': major_version
            }
        
        return None
