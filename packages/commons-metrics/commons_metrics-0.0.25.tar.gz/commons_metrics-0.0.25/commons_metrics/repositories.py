from typing import Optional

class ComponentRepository:
    """
    Repository class for component-specific database operations
    """
    def __init__(self, db_connection):
        self.db = db_connection

    def save_component(self, technical_name, functional_name, id_type, folder, class_name, status):
        cursor = None
        try:
            cursor = self.db.connection.cursor()

            insert_query = """
                INSERT INTO schmetrc.component(technical_name,functional_name, type_id, folder, class_name, status) 
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """

            cursor.execute(insert_query, (technical_name, functional_name, id_type, folder, class_name, status))
            component_id = cursor.fetchone()[0]
            self.db.commit_transaction()

            return component_id

        except Exception as e:
            self.db.rollback_transaction()
            raise Exception(f"Error saving component '{technical_name}': {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def query_components_by_type(self, id_type: int) -> list:
        """
        Consulta componentes de un tipo específico en la base de datos

        Args:
            id_type (int): ID del tipo de componente a consultar
        """
        cursor = None
        try:
            cursor = self.db.connection.cursor()

            query = """
            SELECT id, technical_name, type_id, status, functional_name, folder, class_name 
            FROM schmetrc.component 
            WHERE type_id = %s
            ORDER BY technical_name
            """

            cursor.execute(query, (id_type,))
            results = cursor.fetchall()

            components = []
            for row in results:
                component = {
                    'id': row[0],
                    'technical_name': row[1],
                    'type_id': row[2],
                    'status': row[3],
                    'functional_name': row[4],
                    'folder': row[5],
                    'class_name': row[6]
                }
                components.append(component)

            return components

        except Exception as e:
            raise Exception(f"Error querying components by type {id_type}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def query_versions_by_type(self, type_id: int) -> list:
        """
        Consulta versiones de un tipo específico (mobile o web) en la base de datos

        Args:
            type_id (int): ID del tipo (13 para mobile, 12 para web)
            
        Returns:
            list: Lista de versiones con sus IDs
        """
        cursor = None
        try:
            cursor = self.db.connection.cursor()
            query = """
            SELECT id, version, type_id, creation_date
            FROM schmetrc.general_version
            WHERE type_id = %s
            ORDER BY version DESC
            """
            cursor.execute(query, (type_id,))
            results = cursor.fetchall()
            
            # Get column names from cursor description
            column_names = [desc[0] for desc in cursor.description]

            versions = []
            for row in results:
                # Crear versión dinámicamente usando los nombres de columnas
                version = dict(zip(column_names, row))
                versions.append(version)

            return versions

        except Exception as e:
            raise RuntimeError(f"Error querying versions by type {type_id}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def save_adoption(self, version_id: int, component_id: int, application_code: str, count: int, date_id: int = None):
        """
        Inserta un registro de adopción en la tabla schmetrc.general_adoption
        
        Args:
            version_id (int): ID de la versión del sistema de diseño
            component_id (int): ID del componente
            application_code (str): Código de aplicación (ej: NU0296001)
            count (int): Cantidad de usos del componente
            date_id (int, optional): ID de la fecha en measurement_systems_history. Por defecto None
        """
        cursor = None
        try:
            cursor = self.db.connection.cursor()
            insert_query = """
                INSERT INTO schmetrc.general_adoption(version_id, component_id, application_code, count, date_id) 
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """
            
            cursor.execute(insert_query, (version_id, component_id, application_code, count, date_id))
            adoption_id = cursor.fetchone()[0]
            self.db.commit_transaction()
            return adoption_id
        except Exception as e:
            self.db.rollback_transaction()
            raise RuntimeError(f"Error saving adoption for component {component_id}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def get_or_create_current_month_date(self) -> int:
        """
        Obtiene el ID de la fecha del mes actual en measurement_systems_history.
        Si no existe, crea un registro con la fecha de hoy.
        
        Returns:
            int: ID del registro de fecha
        """
        cursor = None
        try:
            cursor = self.db.connection.cursor()
            
            # Buscar si existe un registro del mes actual
            query_select = """
            SELECT id
            FROM schmetrc.measurement_systems_history
            WHERE EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
              AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
            LIMIT 1
            """
            cursor.execute(query_select)
            result = cursor.fetchone()
            
            if result:
                # Ya existe un registro del mes actual
                date_id = result[0]
                print(f"   ℹ️ Usando fecha existente del mes actual (ID: {date_id})")
                return date_id
            else:
                # No existe, crear uno nuevo con la fecha de hoy
                query_insert = """
                INSERT INTO schmetrc.measurement_systems_history (date)
                VALUES (CURRENT_DATE)
                RETURNING id
                """
                cursor.execute(query_insert)
                date_id = cursor.fetchone()[0]
                self.db.commit_transaction()
                print(f"   ✅ Creado nuevo registro de fecha (ID: {date_id})")
                return date_id
            
        except Exception as e:
            self.db.rollback_transaction()
            raise RuntimeError(f"Error getting or creating current month date: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def delete_adoption_by_date_id(self, date_id: int, type_id: int = None) -> int:
        """
        Elimina todos los registros de adopción asociados a un date_id específico.
        Opcionalmente filtra por tipo de componente (mobile=13, web=12).
        Útil para limpiar datos del mes actual antes de una nueva inserción.
        
        Args:
            date_id (int): ID de la fecha cuyos registros se eliminarán (date_id)
            type_id (int, optional): ID del tipo de componente para filtrar. Si es None, elimina todos los tipos.
            
        Returns:
            int: Cantidad de registros eliminados
        """
        cursor = None
        try:
            cursor = self.db.connection.cursor()
            
            # Construir query con o sin filtro de tipo
            if type_id is not None:
                # Contar registros a eliminar (con filtro de tipo)
                count_query = """
                SELECT COUNT(*)
                FROM schmetrc.general_adoption ga
                INNER JOIN schmetrc.component c ON ga.component_id = c.id
                WHERE ga.date_id = %s AND c.type_id = %s
                """
                cursor.execute(count_query, (date_id, type_id))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # Eliminar los registros (con filtro de tipo)
                    delete_query = """
                    DELETE FROM schmetrc.general_adoption
                    WHERE id IN (
                        SELECT ga.id
                        FROM schmetrc.general_adoption ga
                        INNER JOIN schmetrc.component c ON ga.component_id = c.id
                        WHERE ga.date_id = %s AND c.type_id = %s
                    )
                    """
                    cursor.execute(delete_query, (date_id, type_id))
                    self.db.commit_transaction()
                    type_name = "mobile" if type_id == 13 else "web" if type_id == 12 else f"tipo {type_id}"
                    print(f"   🗑️ Eliminados {count} registros de adopción {type_name} del mes actual")
                else:
                    print("   ℹ️ No hay registros previos de adopción para eliminar")
            return count
            
        except Exception as e:
            self.db.rollback_transaction()
            raise RuntimeError(f"Error deleting adoption records for date_id {date_id}: {str(e)}")
        finally:
            if cursor:
                cursor.close()