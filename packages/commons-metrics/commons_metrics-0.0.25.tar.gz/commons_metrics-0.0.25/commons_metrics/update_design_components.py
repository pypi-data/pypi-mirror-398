
from contextlib import contextmanager
from psycopg2.extras import execute_values


class UpdateDesignSystemComponents:

# ---------------UTILITY FUNCTIONS---------------#
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def get_db_cursor(self):
        """
        Context manager para manejo automático de cursor
        """
        cursor = None
        try:
            cursor = self.connection.connection.cursor()
            yield cursor
        finally:
            if cursor:
                cursor.close()



    def create_new_components(self, components, identifier):
        """
        Crea nuevos componentes en la base de datos usando un solo query
        """
        if not components:
            return

        # Preparar los datos para la inserción masiva
        values_to_insert = []
        for comp in components:
            values_to_insert.append((
                comp['technical_name'],          # technical_name
                identifier,                      # type_id
                comp['folder'],                  # folder
                comp['class'],                   # class_name (array de clases)
                'ACTIVE',                        # status (ACTIVE | DEPRECATED)
            ))

        # Query de inserción masiva
        insert_query = """
            INSERT INTO schmetrc.component(technical_name, type_id, folder, class_name, status) 
            VALUES %s
            RETURNING id, technical_name;
        """

        try:
            with self.get_db_cursor() as cursor:
                # Ejecutar la inserción masiva
                result = execute_values(
                    cursor,
                    insert_query,
                    values_to_insert,
                    template=None,
                    page_size=100,
                    fetch=True
                )

                # Confirmar la transacción
                self.connection.connection.commit()

                print(f"✅ {len(values_to_insert)} componentes creados exitosamente en la base de datos:")
                for row in result:
                    print(f"   - ID: {row[0]}, Nombre: {row[1]}")

        except Exception as e:
            # Revertir en caso de error
            self.connection.connection.rollback()
            print(f"❌ Error al crear componentes: {e}")
            raise

    def deprecate_old_components(self, components):
        """
        Marca componentes antiguos como DEPRECATED en la base de datos
        """
        if not components:
            return

        # Preparar los nombres técnicos para la actualización
        technical_names = [comp['technical_name'] for comp in components]

        # Query de actualización masiva
        update_query = """
            UPDATE schmetrc.component
            SET status = 'DEPRECATED'
            WHERE technical_name = ANY(%s)
            RETURNING id, technical_name;
        """

        try:
            with self.get_db_cursor() as cursor:
                # Ejecutar la actualización masiva
                cursor.execute(update_query, (technical_names,))
                result = cursor.fetchall()

                # Confirmar la transacción
                self.connection.connection.commit()

                print(f"⚠️  {len(result)} componentes marcados como DEPRECATED en la base de datos:")
                for row in result:
                    print(f"   - ID: {row[0]}, Nombre: {row[1]}")

        except Exception as e:
            # Revertir en caso de error
            self.connection.connection.rollback()
            print(f"❌ Error al marcar componentes como DEPRECATED: {e}")
            raise

    def update_db_components_info(self, db_components, components_dict):
        """
        Actualiza la información de los componentes en la base de datos:
            - Si cambia el folder o las clases asociadas, se actualizan en la base de datos.
            - Si no hay cambios, no se hace nada.
        """

        # Preparar listas para actualizaciones
        components_to_update = []

        for db_comp in db_components:
            tech_name = db_comp['technical_name']
            if tech_name in components_dict:
                comp = components_dict[tech_name]
                # Verificar si hay cambios en folder o class_name
                if (db_comp['folder'] != comp['folder'] or
                    set(db_comp['class_name']) != set(comp['class'])):
                    components_to_update.append((
                        comp['folder'],
                        comp['class'],
                        tech_name,
                        "ACTIVE"
                    ))

        if not components_to_update:
            print("ℹ️  No hay componentes que actualizar en la base de datos.")
            return

        # Query de actualización masiva usando CTE
        update_query = """
            WITH updates(folder, class_name, technical_name, status) AS (
                VALUES %s
            )
            UPDATE schmetrc.component 
            SET folder = updates.folder,
                class_name = updates.class_name,
                status = updates.status
            FROM updates
            WHERE schmetrc.component.technical_name = updates.technical_name
            RETURNING schmetrc.component.id, schmetrc.component.technical_name;
        """

        try:
            with self.get_db_cursor() as cursor:
                # Ejecutar la actualización masiva
                result = execute_values(
                    cursor,
                    update_query,
                    components_to_update,
                    template=None,
                    page_size=100,
                    fetch=True
                )

                # Confirmar la transacción
                self.connection.connection.commit()

                print(f"✅ {len(result)} componentes actualizados en la base de datos:")
                for row in result:
                    print(f"🔄 Componente actualizado - ID: {row[0]}, Nombre: {row[1]}")

        except Exception as e:
            print(f"❌ Error al actualizar componentes en la base de datos: {e}")
            self.connection.connection.rollback()
            raise

    def update_db(self, db_components, all_components, identifier):
        """
        Actualiza la base de datos con los componentes actuales del proyecto 
        """
        # Comparar base de datos con componentes encontrados, y listar las diferencias, obtener los componentes completos
        db_components_dict = {comp['technical_name']: comp for comp in db_components}
        components_dict = {comp['technical_name']: comp for comp in all_components}

        # Obtener conjuntos de nombres para comparación
        db_component_names = set(db_components_dict.keys())
        component_names = set(components_dict.keys())

        # Componentes que están en el proyecto pero NO en la base de datos (nuevos)
        missing_in_db_names = component_names - db_component_names
        missing_in_db_components = [components_dict[name] for name in missing_in_db_names]
        self.create_new_components(missing_in_db_components, identifier)

        # Componentes que están en la base de datos pero NO en el proyecto
        missing_in_names = db_component_names - component_names
        missing_in_components = [db_components_dict[name] for name in missing_in_names]
        self.deprecate_old_components(missing_in_components)

        # Actualizar información de componentes comunes
        self.update_db_components_info(db_components, components_dict)
