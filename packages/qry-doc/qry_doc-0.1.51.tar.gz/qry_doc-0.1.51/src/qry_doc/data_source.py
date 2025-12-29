"""
Data source loading utilities for qry-doc.

This module provides functionality to load data from various sources
including CSV files, pandas DataFrames, and SQL connections.
"""
import re
from pathlib import Path
from typing import Union

import pandas as pd

from qry_doc.exceptions import DataSourceError


class DataSourceLoader:
    """
    Loads data from various sources into pandas DataFrames.
    
    Supports:
    - CSV file paths
    - pandas DataFrames (passthrough)
    - SQL connection strings (future)
    """
    
    # Supported CSV extensions
    CSV_EXTENSIONS = {".csv", ".tsv", ".txt"}
    
    # SQL connection string patterns
    SQL_PATTERNS = [
        re.compile(r"^(postgresql|postgres)://", re.IGNORECASE),
        re.compile(r"^mysql://", re.IGNORECASE),
        re.compile(r"^sqlite://", re.IGNORECASE),
        re.compile(r"^mssql://", re.IGNORECASE),
        re.compile(r"^oracle://", re.IGNORECASE),
    ]
    
    @classmethod
    def load(cls, source: Union[str, Path, pd.DataFrame]) -> pd.DataFrame:
        """
        Load data from the given source into a DataFrame.
        
        Args:
            source: Can be:
                - A path to a CSV file (str or Path)
                - A pandas DataFrame (returned as-is)
                - A SQL connection string (future support)
        
        Returns:
            A pandas DataFrame containing the loaded data.
            
        Raises:
            DataSourceError: If the source format is not supported or loading fails.
        """
        # Handle DataFrame passthrough
        if isinstance(source, pd.DataFrame):
            return source
        
        # Handle Path objects
        if isinstance(source, Path):
            source = str(source)
        
        # Must be a string at this point
        if not isinstance(source, str):
            raise DataSourceError(
                user_message=(
                    f"Formato de datos no soportado (tipo: {type(source).__name__}). "
                    "Use: ruta a archivo CSV, DataFrame de pandas, o cadena de conexión SQL."
                )
            )
        
        # Check if it's a CSV path
        if cls.is_csv_path(source):
            return cls._load_csv(source)
        
        # Check if it's a SQL connection
        if cls.is_sql_connection(source):
            return cls._load_sql(source)
        
        # Unknown format
        raise DataSourceError(
            user_message=(
                f"Formato de datos no reconocido: '{source[:50]}{'...' if len(source) > 50 else ''}'. "
                "Use: ruta a archivo CSV (.csv, .tsv), DataFrame de pandas, "
                "o cadena de conexión SQL (postgresql://, mysql://, sqlite://)."
            )
        )
    
    @classmethod
    def is_csv_path(cls, source: str) -> bool:
        """
        Check if the source string looks like a CSV file path.
        
        Args:
            source: The string to check.
            
        Returns:
            True if it appears to be a CSV path.
        """
        if not source:
            return False
        
        path = Path(source)
        
        # Check extension
        if path.suffix.lower() in cls.CSV_EXTENSIONS:
            return True
        
        # Check if file exists and has CSV-like extension
        if path.exists() and path.is_file():
            return path.suffix.lower() in cls.CSV_EXTENSIONS
        
        return False
    
    @classmethod
    def is_sql_connection(cls, source: str) -> bool:
        """
        Check if the source string looks like a SQL connection string.
        
        Args:
            source: The string to check.
            
        Returns:
            True if it appears to be a SQL connection string.
        """
        if not source:
            return False
        
        for pattern in cls.SQL_PATTERNS:
            if pattern.match(source):
                return True
        
        return False
    
    @classmethod
    def _load_csv(cls, path: str) -> pd.DataFrame:
        """
        Load a CSV file into a DataFrame.
        
        Args:
            path: Path to the CSV file.
            
        Returns:
            DataFrame with the CSV contents.
            
        Raises:
            DataSourceError: If the file cannot be read.
        """
        file_path = Path(path)
        
        if not file_path.exists():
            raise DataSourceError(
                user_message=f"El archivo no existe: {file_path.name}"
            )
        
        if not file_path.is_file():
            raise DataSourceError(
                user_message=f"La ruta no es un archivo: {file_path.name}"
            )
        
        try:
            # Detect separator based on extension
            sep = "\t" if file_path.suffix.lower() == ".tsv" else ","
            
            # Try to read with UTF-8 first, then fallback to latin-1
            try:
                df = pd.read_csv(file_path, sep=sep, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, sep=sep, encoding="latin-1")
            
            return df
            
        except pd.errors.EmptyDataError:
            raise DataSourceError(
                user_message=f"El archivo está vacío: {file_path.name}"
            )
        except pd.errors.ParserError as e:
            raise DataSourceError(
                user_message=f"Error al parsear el archivo CSV: {file_path.name}",
                internal_error=e
            )
        except PermissionError:
            raise DataSourceError(
                user_message=f"Sin permisos para leer el archivo: {file_path.name}"
            )
        except Exception as e:
            raise DataSourceError(
                user_message=f"Error al cargar el archivo: {file_path.name}",
                internal_error=e
            )
    
    @classmethod
    def _load_sql(cls, connection_string: str) -> pd.DataFrame:
        """
        Load data from a SQL database.
        
        Automatically explores the database and loads the most suitable table/view.
        
        Args:
            connection_string: SQL connection string (e.g., postgresql://user:pass@host/db).
            
        Returns:
            DataFrame with the query results.
            
        Raises:
            DataSourceError: If connection or query fails.
        """
        try:
            from sqlalchemy import create_engine, text, inspect
        except ImportError:
            raise DataSourceError(
                user_message=(
                    "Para usar conexiones SQL, instale sqlalchemy: "
                    "pip install sqlalchemy psycopg2-binary"
                )
            )
        
        try:
            # Create engine
            engine = create_engine(connection_string)
            
            # Get inspector to explore database
            inspector = inspect(engine)
            
            # Get all tables and views
            views = inspector.get_view_names()
            tables = inspector.get_table_names()
            
            print(f"📊 Explorando base de datos...")
            print(f"   Tablas encontradas: {len(tables)}")
            print(f"   Vistas encontradas: {len(views)}")
            
            # Analyze all tables to find the best one
            table_info = []
            
            for table in tables:
                try:
                    with engine.connect() as conn:
                        # Get row count
                        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                        row_count = result.scalar() or 0
                        
                        # Get column count
                        columns = inspector.get_columns(table)
                        col_count = len(columns)
                        
                        table_info.append({
                            'name': table,
                            'type': 'table',
                            'rows': row_count,
                            'cols': col_count,
                            'score': row_count * col_count  # Simple scoring
                        })
                except Exception:
                    continue
            
            # Analyze views (usually better for analysis)
            for view in views:
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text(f'SELECT COUNT(*) FROM "{view}"'))
                        row_count = result.scalar() or 0
                        
                        # Get columns from view
                        result = conn.execute(text(f'SELECT * FROM "{view}" LIMIT 1'))
                        col_count = len(result.keys())
                        
                        table_info.append({
                            'name': view,
                            'type': 'view',
                            'rows': row_count,
                            'cols': col_count,
                            'score': row_count * col_count * 1.5  # Prefer views
                        })
                except Exception:
                    continue
            
            if not table_info:
                raise DataSourceError(
                    user_message="No se encontraron tablas o vistas accesibles en la base de datos."
                )
            
            # Sort by score and select best
            table_info.sort(key=lambda x: x['score'], reverse=True)
            
            # Print exploration results
            print(f"\n📋 Tablas/Vistas disponibles:")
            for info in table_info[:10]:  # Show top 10
                print(f"   - {info['name']} ({info['type']}): {info['rows']} filas, {info['cols']} columnas")
            
            # Select the best table
            best = table_info[0]
            print(f"\n✅ Seleccionada: {best['name']} ({best['rows']} filas, {best['cols']} columnas)")
            
            # Load data
            df = pd.read_sql_table(best['name'], engine)
            
            if df.empty:
                # Try next best if empty
                for info in table_info[1:]:
                    df = pd.read_sql_table(info['name'], engine)
                    if not df.empty:
                        print(f"   (Cambiado a {info['name']} porque {best['name']} estaba vacía)")
                        break
            
            if df.empty:
                raise DataSourceError(
                    user_message="Todas las tablas encontradas están vacías."
                )
            
            return df
            
        except DataSourceError:
            raise
        except ImportError as e:
            driver_msg = ""
            if "psycopg2" in str(e):
                driver_msg = "pip install psycopg2-binary"
            elif "pymysql" in str(e):
                driver_msg = "pip install pymysql"
            
            raise DataSourceError(
                user_message=f"Falta el driver de base de datos. Instale: {driver_msg}",
                internal_error=e
            )
        except Exception as e:
            error_str = str(e).lower()
            
            if "connection refused" in error_str or "could not connect" in error_str:
                raise DataSourceError(
                    user_message=(
                        "No se pudo conectar a la base de datos. "
                        "Verifique que el servidor esté corriendo y los datos de conexión sean correctos."
                    ),
                    internal_error=e
                )
            elif "authentication" in error_str or "password" in error_str:
                raise DataSourceError(
                    user_message="Error de autenticación. Verifique usuario y contraseña.",
                    internal_error=e
                )
            elif "does not exist" in error_str:
                raise DataSourceError(
                    user_message="La base de datos especificada no existe.",
                    internal_error=e
                )
            else:
                raise DataSourceError(
                    user_message=f"Error al conectar a la base de datos: {str(e)[:100]}",
                    internal_error=e
                )
    
    @classmethod
    def load_sql_table(
        cls, 
        connection_string: str, 
        table_name: str
    ) -> pd.DataFrame:
        """
        Load a specific table from a SQL database.
        
        Args:
            connection_string: SQL connection string.
            table_name: Name of the table to load.
            
        Returns:
            DataFrame with the table contents.
        """
        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise DataSourceError(
                user_message="Instale sqlalchemy: pip install sqlalchemy psycopg2-binary"
            )
        
        try:
            engine = create_engine(connection_string)
            df = pd.read_sql_table(table_name, engine)
            return df
        except Exception as e:
            raise DataSourceError(
                user_message=f"Error al cargar tabla '{table_name}': {str(e)[:100]}",
                internal_error=e
            )
    
    @classmethod
    def load_sql_query(
        cls, 
        connection_string: str, 
        query: str
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.
        
        Args:
            connection_string: SQL connection string.
            query: SQL query to execute.
            
        Returns:
            DataFrame with query results.
        """
        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise DataSourceError(
                user_message="Instale sqlalchemy: pip install sqlalchemy psycopg2-binary"
            )
        
        try:
            engine = create_engine(connection_string)
            df = pd.read_sql_query(query, engine)
            return df
        except Exception as e:
            raise DataSourceError(
                user_message=f"Error al ejecutar query: {str(e)[:100]}",
                internal_error=e
            )
    
    @classmethod
    def explore_database(cls, connection_string: str) -> dict:
        """
        Explore a database and return information about all tables/views.
        
        Args:
            connection_string: SQL connection string.
            
        Returns:
            Dict with database structure information.
        """
        try:
            from sqlalchemy import create_engine, text, inspect
        except ImportError:
            raise DataSourceError(
                user_message="Instale sqlalchemy: pip install sqlalchemy psycopg2-binary"
            )
        
        try:
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            
            result = {
                'tables': {},
                'views': {}
            }
            
            # Explore tables
            for table in inspector.get_table_names():
                try:
                    columns = inspector.get_columns(table)
                    with engine.connect() as conn:
                        count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                        row_count = count_result.scalar() or 0
                    
                    result['tables'][table] = {
                        'columns': [{'name': c['name'], 'type': str(c['type'])} for c in columns],
                        'row_count': row_count
                    }
                except Exception:
                    continue
            
            # Explore views
            for view in inspector.get_view_names():
                try:
                    with engine.connect() as conn:
                        count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{view}"'))
                        row_count = count_result.scalar() or 0
                        
                        sample = conn.execute(text(f'SELECT * FROM "{view}" LIMIT 1'))
                        columns = list(sample.keys())
                    
                    result['views'][view] = {
                        'columns': columns,
                        'row_count': row_count
                    }
                except Exception:
                    continue
            
            return result
            
        except Exception as e:
            raise DataSourceError(
                user_message=f"Error al explorar base de datos: {str(e)[:100]}",
                internal_error=e
            )
