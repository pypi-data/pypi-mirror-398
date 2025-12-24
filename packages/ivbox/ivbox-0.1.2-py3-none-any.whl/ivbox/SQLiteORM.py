import sqlite3 as sql
import threading
from typing import Union, List, Tuple, Optional
import numpy as np
import os
import re
import sys
import time
from .helpers.utils import *
import datetime, decimal, uuid, json

# Auxiliar classes
from .helpers.QueryResults import QueryResults
from .helpers.SchemaValidator import SchemaValidator

class TypeData(Exception):

    pass

__all__ = [

    "SQLiteORM",
    
    "integer", "text", "obj", "floating", "real", "numeric", "varchar", "boolean","enum"

]

SQLITE_FUNCS = ["CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP"]

def _build_type_declaration(base_type: str, **kwargs) -> Union[str, bool]:

    pk             = kwargs.get("pk", False)

    autoincrement  = kwargs.get("autoincrement", False)

    not_null       = kwargs.get("not_null", False)

    default        = kwargs.get("default", None)

    enum_values    = kwargs.get("enum_values", None)

    size           = kwargs.get("size", None)

    unique         = kwargs.get("unique", False)

    fk             = kwargs.get("fk", None)

    def add_common_options(options: list):

        nonlocal default

        if not_null:      options.append("NOT_NULL")

        if pk:            options.append("PRIMARY_KEY")

        if autoincrement:

            if not pk:

                options.append("PRIMARY_KEY")

            if base_type.upper() != "INTEGER":

                print("⚠️ AUTOINCREMENT only works with INTEGER PRIMARY KEY")

                return options

            options.append("AUTOINCREMENT")

        if unique:        options.append("UNIQUE")

        if default is not None:

            # Clone value to avoid mutating original
            default_value = default

            # Check if it's a TEXT literal and not a SQLite function
            if isinstance(default_value, str) and not default_value.upper() in SQLITE_FUNCS:

                default_value = f"'{default_value}'"

            options.append(f"DEFAULT({default_value})")

        return options

    # ============================================
    # 4. Validación para tipos numéricos
    # ============================================
    def validate_numeric(type_):

        if size is not None:

            raise ValueError(json.dumps({

                "message": f"SQLite {type_} type does NOT support size.",

                "value": size,

                "base_type": type_

            }))

        if default is not None:

            # INTEGER cannot accept float or str
            if type_ == "INTEGER" and isinstance(default, (str, float)):

                raise ValueError(json.dumps({

                    "message": "SQLite INTEGER cannot use string or float as DEFAULT",

                    "value": default,

                    "base_type": type_

                }))

            # REAL must not accept strings
            if type_ == "REAL" and isinstance(default, str):

                raise ValueError(json.dumps({

                    "message": "SQLite REAL cannot use string as DEFAULT",

                    "value": default,

                    "base_type": type_

                }))

    # ============================================
    # 5. Validación para TEXT / DATE
    # ============================================
    def validate_text_date(type_):

        if size is not None:

            raise ValueError(json.dumps({

                "message": f"SQLite {type_} does NOT support size",

                "value": size,

                "base_type": type_

            }))
    
    def validate_varchar(type_):

        nonlocal size, default

        if size is None:

            raise ValueError(json.dumps({

                "message": "SQLite VARCHAR requires a size parameter",

                "value": size,

                "base_type": type_

            }))

        if not isinstance(size, int) or size <= 0:

            raise ValueError(json.dumps({

                "message": "SQLite VARCHAR size must be a positive integer",

                "value": size,

                "base_type": type_

            }))
        
        if default is not None:

            if isinstance(default, str) and default.upper() in SQLITE_FUNCS:

                return  # es una función válida de SQLite
            
            if isinstance( default , str ):

                clean_default = default.strip("'").strip('"')

                if len(clean_default) > size:

                    raise ValueError(json.dumps({

                        "message": f"SQLite VARCHAR default value exceeds defined size of {size}",

                        "value": default,

                        "base_type": type_

                    }))
    
    def validate_boolean(type_):

        if size is not None:

            raise ValueError(json.dumps({

                "message": f"SQLite BOOLEAN does NOT support size",

                "value": size,

                "base_type": type_

            }))

        if default is not None:

            if not isinstance(default, int) or default not in (0, 1):

                raise ValueError(json.dumps({

                    "message": "SQLite BOOLEAN default must be 0 or 1",

                    "value": default,

                    "base_type": type_

                }))
    
    def validate_enum(type_):

        nonlocal enum_values

        if default is not None and default not in enum_values:

            raise ValueError(json.dumps({

                "message": f"SQLite ENUM default must be among that values {", ".join(enum_values)}",

                "value": default,

                "base_type": type_

            }))

    options = [base_type]

    if base_type in ("INTEGER", "REAL", "NUMERIC"):

        validate_numeric(base_type)

        options = add_common_options(options)

    elif base_type in ("TEXT", "DATE", "JSON"):

        validate_text_date(base_type)

        options = add_common_options(options)
    
    elif base_type == "VARCHAR":

        validate_varchar(base_type)

        # Optain position varchar
        pos_varchar = options.index("VARCHAR")

        options[pos_varchar] = f"VARCHAR({size})"

        options = add_common_options(options)
    
    elif base_type == "BOOLEAN":

        # SQLite does not have a separate BOOLEAN type, use INTEGER
        base_type = "INTEGER"

        validate_boolean(base_type)

        options = add_common_options(options)
    
    elif base_type == "ENUM":

        if enum_values:

            cleaned = []

            for val in enum_values:

                if isinstance(val, str):

                    cleaned.append(f"'{val}'")

                else:

                    cleaned.append(str(val))
            
            check_sql = f"CHECK( IN ({', '.join(cleaned)}))"

            options.append(check_sql)

            validate_enum(base_type)

            options = add_common_options(options)

    else:

        raise TypeError(f"Unsupported SQLite type: {base_type}")

    # ============================================
    # 7. Reordenar opciones limpia y correctamente
    # ============================================
    protected = []

    for opt in options:

        if opt.startswith("DEFAULT("):

            protected.append(opt)  # lo dejamos intacto

        else:

            protected.append(opt.replace("_", " "))

    options = protected

    # ============================================
    # 8. Formatear salida
    # ============================================
    formatted = " ".join(options)

    return formatted

def build_type(type_name: str, **kwargs):

    try:

        return _build_type_declaration(type_name, **kwargs)

    except ValueError as ve:

        data = json.loads(str(ve))

        msg = data.get("message", "")

        val = data.get("value", "")

        bt  = data.get("base_type", type_name)

        print(f"⚠️ {msg} Given: {val} for base type: {bt}")

        if bt in ("ENUM"):

            raise Exception(f"⚠️ {msg} Given: {val} for base type: {bt}")

        # formatear salida final
        if isinstance(bt, str):

            return bt.replace("_", " ").strip()

        return str(bt)

    except TypeData as e:

        print(f"⚠️ Unexpected error: {e}")

        return type_name
    
    except Exception as e:

        print( e )

def boolean(**kwargs):

    # SQLite does not have a separate BOOLEAN type, use INTEGER as numeric type
    return numeric(**kwargs)

def integer(**kwargs):

    return { "__col_type__":int, "_callback_": build_type("INTEGER", **kwargs) }

def floating(**kwargs):

    return { "__col_type__":float, "_callback_": build_type("REAL", **kwargs) }

def real(**kwargs):

    return floating(**kwargs)

def text(**kwargs):

    return { "__col_type__":str, "_callback_": build_type("TEXT", **kwargs) }

def obj(**kwargs):

    return { "__col_type__":str, "_callback_": build_type("JSON", **kwargs) }

def varchar(**kwargs):

    return { "__col_type__":str, "_callback_": build_type("VARCHAR", **kwargs) }

def numeric(**kwargs):

    base_type = "NUMERIC"

    base_instance = int

    if "default" in kwargs:

        default = kwargs["default"]

        regex_int = r"^-?\d+$"

        regex_float = r"^-?\d+\.\d+$"

        regex_cientific = r"^-?\d+(\.\d+)?[eE][-+]?\d+$"

        regex_date = r"^\d{4}-\d{2}-\d{2}$"

        # Comprobación del default
        if default is None:

            type_ = "NUMERIC"

        elif re.match(regex_int, str(default)):

            type_ = "INTEGER"

        elif re.match(regex_float, str(default)) or re.match(regex_cientific, str(default)):

            type_ = "REAL"

            base_instance = float
        
        elif re.match(regex_date, str(default)):
            
            type_ = "DATE"  # SQLite almacena fechas como texto

            base_instance = str

        else:

            type_ = "TEXT"

            base_instance = str
    
    base_type = type_

    return { "__col_type__":base_instance, "_callback_": build_type(base_type, **kwargs) }

def enum(**kwargs):

    enum_values = kwargs.get("enum_values", None)

    type_ = str

    if not isinstance(enum_values, (list, tuple)) or len(enum_values) == 0:

        raise ValueError("ENUM requires a non-empty list of values")

    if any( isinstance( item, int ) for item in enum_values ):

        type_ = int

    if any( isinstance( item, ( bool, float ) ) for item in enum_values ):

        type_ = item.__name__

    # Guardar los valores para validación

    return { "__col_type__":type_, "_callback_": build_type("ENUM", **kwargs) }

class SQLiteORM:

    def __init__(self, db_path: str):

        self.db_path = db_path
        
        self.db_name = db_path
        
        self.conn = None
        
        self.cursor = None
        
        self.query = None
        
        self.deleted_rows = 0
        
        self.stream_mode = False
    
    """

        DATABASE CONNECTION FUNCTIONS: close_connection, connect_DB, connect_stream_DB, close_connection_stream_DB
        DESCRIPTION: These methods handle the connection to the SQLite database, including standard and eStream modes.
        
    """

    def close_connection(self) -> None:

        self.conn.close()

    def connect_DB(self) -> Union[sql.Connection, None]:

        try:
            
            self.conn = sql.connect(self.db_path, check_same_thread=False)

            self.conn.row_factory = sql.Row

            self.cursor = self.conn.cursor()

            self.cursor.execute("PRAGMA journal_mode=WAL;") # multi threading to avoid blocks of database

            print("✅ Connection success to database:", self.db_name.split('.')[-1])

            return self.conn

        except sql.Error as e:

            print(f"❌ Database error: {e}")

            return None

    def connect_stream_DB(self) -> Union[sql.Connection, None]:
        
        try:

            self.conn = sql.connect(self.db_path, check_same_thread=False)
            
            self.conn.row_factory = sql.Row
            
            self.cursor = self.conn.cursor()

            print(f"Connecting to database {self.db_name} in eStream mode...")
            
            self.cursor.execute("PRAGMA synchronous = OFF;")
            
            self.cursor.execute("PRAGMA journal_mode = MEMORY;")
            
            self.cursor.execute("PRAGMA temp_store = MEMORY;")
            
            self.cursor.execute("PRAGMA locking_mode = EXCLUSIVE;")
            
            self.cursor.execute("PRAGMA foreign_keys = OFF;")
            
            self.cursor.execute("PRAGMA cache_size = -2000000;")
            
            self.cursor.execute("PRAGMA automatic_index = OFF;")
            
            self.cursor.execute("PRAGMA cache_spill = OFF;")

            print("⚡ eStream mode active! Ultra-fast performance enabled.")

            self.stream_mode = True

            return self.conn

        except sql.Error as e:

            print(f"❌ eStream connection error: {e}")

            return None

    def close_connection_stream_DB(self):
        
        try:

            print("Closing eStream connection and restoring normal mode...")

            self.cursor.execute("PRAGMA foreign_keys = ON;")

            self.cursor.execute("PRAGMA journal_mode = WAL;")

            self.cursor.execute("PRAGMA synchronous = NORMAL;")

            self.cursor.execute("PRAGMA locking_mode = NORMAL;")

            self.cursor.execute("PRAGMA automatic_index = ON;")

            self.cursor.execute("PRAGMA cache_spill = ON;")

            print(f"Database {self.db_name} closed and returned to stable normal mode.")

            self.conn.close()

            self.stream_mode = False

            return True

        except sql.Error as e:

            print(f"❌ Error restoring normal mode: {e}")

            return False

    """

        DATABASE DML FUNCTIONS: insert, insert_many, select_all, select_one, select_where, 
            select_columns, select_by_id, select_like, select_in, update_all, update, delete_all, delete
        DESCRIPTION: These methods provide basic CRUD operations for interacting with the SQLite database.

    """

    # ===============================
    # INSERT ORM ( insert both single values and many values)
    # ===============================
    def insert_many(self, table_name: str, items: list):

        try:

            if not items:

                raise Exception("items is empty, there are not rows to insert.")

            # ==========================
            # 1. TABLE COLUMNS
            # ==========================
            columns = self.check_columns(table_name)

            if not columns:

                raise Exception(f"It could not be obtained columns from {table_name}")

            # ==========================
            # 2. PRIMARY KEY
            # ==========================
            info = self.get_object_columns(table_name)

            if not info:

                raise Exception(f"It could not be obtained table_info PRAGMA from '{table_name}'")

            # TODO check primary keys provided that they are autoincrement
            primary_keys = self.get_autoincrement_pks( table_name )

            cols_to_insert = [c for c in columns if c]

            if not cols_to_insert:

                raise Exception(

                    f"'{table_name}' table does not have recorded columns (Only for a primary key)."

                )

            # ==========================
            # 3. VALIDATE ROWS LENGTH
            # ==========================
            expected_cols = len(cols_to_insert) - len(primary_keys)

            for row in items:

                if len(row) != expected_cols:

                    raise Exception(

                        f"Row {row} has {len(row)} values but awaited for {expected_cols}: {cols_to_insert}"

                    )

            # ==========================
            # 4. PREPARED QUERY
            # ==========================
            placeholders = ", ".join(["?"] * expected_cols)

            base_query = (

                f"INSERT OR IGNORE INTO {table_name} ({', '.join(cols_to_insert)}) "

                f"VALUES ({placeholders})"

            )

            # ==========================
            # 5. PRAGMA TURBO
            # ==========================
            self.activate_stream()

            # ==========================
            # 6. CHUNK SIZE INTELLIGENT
            # ==========================
            chunk_size = auto_chunk_size(items, mode="sqlite")

            total = len(items)

            print(f"INSERT MANY INIT ({total} rows)…")

            print(f"✔ Recorded columns: {cols_to_insert}")

            print(f"✔ Chunk size: {chunk_size:,}")

            # ==========================
            # 7. INSERT BY CHUNKS
            # ==========================
            for start in range(0, total, chunk_size):

                chunk = items[start : start + chunk_size]

                self.execute_query(base_query, chunk)

                print(f"   → Recorded {start + len(chunk)}/{total}")

            # ==========================
            # 8. RESTAURE PRAGMAS
            # ==========================
            self.desactivate_stream()

            print("✅ INSERT MANY DONE")

            return True

        except Exception as e:

            print("❌ insert_many error:", e)

            return False

    def insert(self, table_name: str, data: Union[tuple, list] )-> bool:

        try:

            if isinstance(data, (list, tuple)) and not any(isinstance(row, (list, tuple)) for row in data):

                columns_name_db =  self.check_columns( table_name )

                columns_type_db = [

                    (self.execute_query(f"SELECT typeof({col}) as type from {table_name} limit 1").json)[0]["type"]

                    for col in columns_name_db

                ]

                if len(data) != len(columns_name_db):

                    raise ValueError("Data length does not match number of columns in the table.")

                # Detect primary keys because they might be autoincrement amd it is not necessary to provide a value
                info = self.execute_query(f"PRAGMA table_info({table_name})")

                # TODO primary keys only for autoincrement
                primary_keys = self.get_autoincrement_pks( table_name )

                placeholders = ", ".join(["?"] * ( len(data) - len(primary_keys) ))
                
                # Build insert or ignore into query
                query = f"INSERT OR IGNORE INTO {table_name} ({', '.join([col for col in columns_name_db if col not in primary_keys])}) VALUES ({placeholders})"

                print(f"Query: {query}")

                print(f"Placeholders: {placeholders}")

                args = tuple(

                    val for i, val in enumerate(data)

                    if columns_name_db[i] not in primary_keys

                )
                
                self.execute_query(query, args)

                print("✅ Insert successful")

                return True

            else:
                
                raise ValueError("Data must be a tuple/list for single insert or list of tuples/lists for multiple inserts.")
                
        except sql.Error as e:

            print(f"⚠️ Insert error: {e}")

            return False

    # ===============================
    # SELECT ORM ( select both by clasical and criterial)
    # ===============================
    def select_all(self, table: str):

        query = f"SELECT * FROM {table}"

        return self.execute_query(query)

    def select_one(self, table: str, **conditions):

        if not conditions:

            raise ValueError("select_one requires at least one condition.")

        conditions_list = [f"{col} = ?" for col in conditions]

        where = " AND ".join(conditions_list)

        params = tuple(conditions.values())

        query = f"SELECT * FROM {table} WHERE {where} LIMIT 1"

        result = self.execute_query(query, params)
        
        return result[0] if result else None

    def select_where(self, table: str, **conditions):

        conditions_list = [f"{col} = ?" for col in conditions]

        where = " AND ".join(conditions_list)

        params = tuple(conditions.values())

        query = f"SELECT * FROM {table} WHERE {where}"

        return self.execute_query(query, params)

    def select_columns(self, table: str, columns: list):

        cols = ", ".join(columns)

        query = f"SELECT {cols} FROM {table}"

        return self.execute_query(query)

    def select_by_id(self, table: str, id_column: str, id_value):

        query = f"SELECT * FROM {table} WHERE {id_column} = ? LIMIT 1"

        result = self.execute_query(query, (id_value,))

        return result[0] if result else None

    def select_like(self, table: str, column: str, pattern: str):

        query = f"SELECT * FROM {table} WHERE {column} LIKE ?"

        return self.execute_query(query, (pattern,))

    def select_in(self, table: str, column: str, values: list):
        
        placeholders = ", ".join("?" for _ in values)

        query = f"SELECT * FROM {table} WHERE {column} IN ({placeholders})"

        return self.execute_query(query, values)

    # ========================
    # UPDATE ALL RECORDS
    # ========================
    def update_all(self, set_values: dict, table_name: str) -> bool:
        
        return self.update(set_values=set_values, table_name=table_name)
        
    # ========================
    # UPDATE RECORDS
    # ========================
    def update(self, set_values=dict, data: Union[str,list, int] = None, table_name: str = "") -> bool:

        try:

            self.activate_stream()

            # Validate table
            if not self.check_table(table_name):

                raise Exception(f"Table '{table_name}' does not exist")

            # Build WHERE clause
            where, params, row_count = list(self._build_where_clause(data=data, table=table_name).values())

            print( f"{where} {params} {row_count} ")

            # check if keys of set values are valid columns
            valid_columns = self.check_columns(table_name)

            for col in set_values.keys():

                if col not in valid_columns:

                    raise Exception(f"Column '{col}' does not exist in table '{table_name}'")

            query = f"UPDATE {table_name} SET {self._build_set_clause(set_values)}{where}"

            self.query = query

            print(f"Executing update: {self.formatted_query()} with params {tuple(set_values.values()) + params}")
            
            self.execute_query(query, tuple(set_values.values()) + params)

            print("✅ Update successful")

            return True

        except Exception as e:

            print(f"Error: {e}")
            
            return False

    # ========================
    # DELETE ALL RECORDS
    # ========================
    def delete_all(self, table_name: str) -> bool:

        return self.delete(table_name=table_name)

    # ========================
    # DELETE RECORDS
    # ========================
    def delete(self, data: Union[list, int] = None, table_name: str = "") -> bool:

        try:

            self.activate_stream()

            # Validate table
            if not self.check_table(table_name):

                raise Exception(f"Table '{table_name}' does not exist")

            # Build WHERE clause
            where, params, row_count = list(self._build_where_clause(data=data, table=table_name).values())

            if row_count == 0:

                print("No rows found to delete with the provided criteria.")

                return False

            query = f"DELETE FROM {table_name}{where}"

            self.query = query

            print(f"Executing delete: {self.formatted_query()} with params {params}")
    
            self.execute_query(query, params)

            print("✅ Delete successful")

            self.desactivate_stream()

            print(f"Rows deleted: {row_count if isinstance(data, list) else 1}")

            if row_count > 50000:

                print("🛠️  Performing VACUUM to optimize database after large delete...")
                
                self.execute_query("VACUUM;")

                print("✅ VACUUM completed.")

            return True

        except Exception as e:

            print(f"Error: {e}")

            return False
    
    """

        DEFINITION DATA LANGUAGE FUNCTIONS: create_table, create_tables, drop_table, drop_tables, rename_table, rename_tables, alter_table, alter_tables
        DESCRIPTION: These methods handle DDL operations for managing database schema.
        
        # ======================== EXAMPLE USAGE ========================
        db.create_table(
            "productos",
            columns={
                "id": integer(pk=True, autoincrement=True),
                "nombre": text(not_null=True),
                "precio": real(default=0),
                "activo": boolean(default=1),
                "id_marca": integer(fk=("marcas", "id"))
            }
        )

    """
    def create_table(self, table_name: str, columns: dict= None, foreign_keys: dict= None , multiple = False, validation = 'standard' ) -> bool:

        try:

            found_table_destination = True

            found_primary_keys = True

            found_primary_keys_destinations = True

            _checked_fk_types = True

            _checked_fk_types_error = ""

            _table_destination = ""

            _fields_destination = []

            if not multiple:

                data = {

                    table_name: [

                        columns,

                        foreign_keys

                    ]

                }

                sv = SchemaValidator( data , 'create_table' )   # validate dictionary

                sv._validateSchema()

            if self.check_table(table_name):

                raise Exception(f"⚠️ Table {table_name} already exists")

            col_defs = []

            col_names = []

            for col_name, opts in columns.items():

                opts_ = opts.get("_callback_")

                col_def = col_name + " " + opts_

                if "CHECK(" in opts_ and "ENUM" in opts_:

                    col_def = col_def.replace("CHECK(", f"CHECK({col_name} ", 1)

                col_defs.append(col_def)

                if foreign_keys:

                    col_names.append( col_name )

            header_create_table = f"CREATE TABLE IF NOT EXISTS {table_name}"

            body_options_create_table = f"{",\n".join(col_defs)}"

            relations_foreign_keys = ""

            # --- Check foreign_keys ---
            if len(col_names) != 0:

                # Obtain database tables
                database_tables = [table.get("name") for table in self.get_db_tables()]

                def __check_table_destination(table_destination: str) -> bool:

                    return table_destination in database_tables
                     
                # Obtain primary_keys of each table    { table: [ primary keys  ] , .....  }
                primary_keys = {}

                def __get_table_destination_foreign_keys( table: str ) -> Union[ list, bool ]:

                    try:
                        if not isinstance( table, str ):

                            raise Exception("")

                        # 3. Obtain PKs of destination table
                        fks = primary_keys.get(table, [])

                        fk_names = [fk.get("name") for fk in fks]

                        fk_types = [fk.get("type") for fk in fks]  # list of types if composite PKs

                        return fk_names , fk_types
                    
                    except Exception: 

                        return False , False
                
                def __check_pk_destinations( fk_n , fd ):

                    return fd in fk_n

                def __check_pk_types( fd ):
                    # 5. Extract the type of source field
                    #    Your method is kept but fixed to extract only type
                    field_source_type = False

                    for col in col_defs:

                        if col.startswith(f"{field_source} "):

                            field_source_type = col.split()[1].upper()   # INTEGER, TEXT, REAL…

                            break
                    
                    if not isinstance(field_source_type, str) and field_source_type == False:

                        return False, f"Not found field source type for field destination {fd}"
 
                    # 6. Extract matching PK type from destination
                    index_dest = fk_names.index(fd)

                    field_destination_type = fk_types[index_dest].upper()

                    # 7. Compare types
                    if field_destination_type != field_source_type:

                        return False, (

                            f"Invalid such a field destination {fd} from table {table_destination} "

                            f"due to mismatched types: {field_source_type} != {field_destination_type}"

                        )
                    
                    return True , ""

                for table in database_tables:

                    primary_keys[table] = [pk for pk in self.get_pk(table)]

 
                # First loop represent possible foreign keys
                for constraint, (field_source, table_destination, field_destination) in foreign_keys.items():

                    if isinstance( field_source, str ) and isinstance( field_destination, str ): 

                        print( field_destination )

                        # 1. Check that source field exists in the new table definition
                        if field_source not in col_names:

                            raise Exception(

                                f"Invalid field_source '{field_source}'. It does not exist in table '{table_name}'"
                                
                            )

                        # 2. Check that destination table exists
                        found_table_destination = __check_table_destination(table_destination)

                        _table_destination = table_destination

                        if validation == 'strict' and not found_table_destination: break

                        # 3. Obtain PKs of destination table
                        fk_names , fk_types = __get_table_destination_foreign_keys( _table_destination )
                        
                        found_primary_keys = fk_names

                        if isinstance( found_primary_keys, bool ): break

                        # 4. Check that destination field is a primary key
                        found_primary_keys_destinations = __check_pk_destinations( fk_names, field_destination )

                        _fields_destination.append( field_destination )

                        if found_primary_keys_destinations == False: break

                        checked_fk_types , error = __check_pk_types( field_destination )

                        _checked_fk_types = checked_fk_types

                        _checked_fk_types_error = error

                        if _checked_fk_types == False and _checked_fk_types_error != "": break

                        # 8. Build foreign key SQL
                        relations_foreign_keys += f",\nCONSTRAINT {constraint} FOREIGN KEY ({field_source}) REFERENCES {table_destination}({field_destination})"

                        print(f"Foreign key str")

                    elif isinstance( field_source, tuple ) and isinstance( field_destination, tuple ):

                        if len(field_source) != len(field_destination):

                            raise ValueError(

                                f"Foreign key '{constraint}' must have same number both of source and destination columns"

                            )

                        # 1. Check both source fields exist in the new table definition
                        not_found_cols = []

                        for col in field_source:

                            if col not in col_names and col not in not_found_cols:

                                not_found_cols.append(col)

                        if len(not_found_cols) != 0:
                            
                            raise ValueError(f"Unable to bind foreign key. Not found column{singularOrPlural( not_found_cols )} {",".join(not_found_cols)}")
                        
                        # 2. Check that destination table exists
                        found_table_destination = __check_table_destination(table_destination)

                        _table_destination = table_destination

                        if validation == 'strict' and not found_table_destination: break

                        relations_foreign_keys += f",\nCONSTRAINT {constraint} FOREIGN KEY ({",".join(field_source)}) REFERENCES {table_destination}({",".join(field_destination)})"
                        
                        print(f"Foreign key tuple")

                    else:

                        continue

            if validation == 'strict' and found_primary_keys == False: 

                raise Exception(

                    f"Not found primary keys for '{_table_destination}'"

                )

            if validation == 'strict':
            
                if found_table_destination == False: 

                    raise Exception(

                        f"Invalid table_destination '{_table_destination}'. Table does not exist"

                    )

                if _fields_destination and found_primary_keys_destinations == False:

                    raise Exception(

                        f"Invalid field{singularOrPlural( _fields_destination )}_destination '{",".join(_fields_destination)}'. "

                        f"It is not a primary key of table '{_table_destination}'"

                    )

            if _checked_fk_types == False and _checked_fk_types_error != "":

                raise Exception( _checked_fk_types_error )

            query = f"{header_create_table} ({body_options_create_table}{relations_foreign_keys});" 

            semicolon = query.find(";")

            if len( query ) - 1 == semicolon:

                print(f"Ready to execute query create table.... {table_name}")

                if ( self.execute_query( query ) ):

                    print( f"✅ Successfully migrated table {table_name} to database {self.db_name}" )

            return True

        except sql.Error as e:

            print(f"⚠️ Create table error: {e}")

            return False
        
        except ValueError as ve:

            print(f"⚠️ Value error: {ve}")

            return False
        
        except Exception as e:

            print(e)

            return False
    
    def create_tables( self, datatables , checking_foreign_keys = 'standard' ):

        try:

            if not isinstance( datatables, dict ):

                raise Exception("❌ Unable to init tables, not allowed arguments. Must be an object")
            
            sv = SchemaValidator( datatables , 'create_table' )

            sv._validateSchema()

            for table, dataset in datatables.items():

                # dataset siempre debe ser lista, pero puede tener 1 o 2 elementos
                if not isinstance(dataset, list):

                    raise Exception(f"❌ Table '{table}' must contain a list [columns, (optional) foreign_keys]")

                if len(dataset) == 0:

                    raise Exception(f"❌ Table '{table}' cannot have an empty list")

                columns = dataset[0]

                foreign_keys = dataset[1] if len(dataset) > 1 else None

                time.sleep(0.1)

                self.create_table( table_name=table, columns=columns, foreign_keys=foreign_keys, multiple=True , validation=checking_foreign_keys )

        except Exception as e:

            print(e)

            return False
    
    def drop_table( self, table_name: str ) -> bool:

        try:

            if not isinstance(table_name, str) or table_name == "":

                raise ValueError("Invalid table name for DROP TABLE")

            if self.check_table( table_name ) == False:

                print(f"⚠️ Table '{table_name}' does not exist")

                return True

            query = f"DROP TABLE IF EXISTS {table_name};"

            if self.execute_query(query):

                print(f"✅ Table '{table_name}' dropped successfully")

                return True

            return False

        except sql.Error as e:

            print(f"⚠️ Drop table SQL error: {e}")

            return False

        except Exception as e:

            print(e)

            return False
    
    def drop_tables( self, tables: list ) -> bool:
        
        try:
            
            sv = SchemaValidator( tables , "drop_table" )

            sv._validateSchema()

            for table in tables:

                self.drop_table( table )

            return True

        except Exception as e:

            print(e)

            return False

    def drop_all_tables( self ):

        try:
            
            database_tables = [table.get("name") for table in self.get_db_tables()]

            autoincrement_tables = [table.get("name") for table in self.get_db_tables(autoincrement=True)]

            tables_to_drop = list( set( database_tables) - set( autoincrement_tables ) )

            self.drop_tables( tables_to_drop )

        except Exception as e:

            print(e)

            return False
        
    def rename_table( self, current_table:str, new_table: str ) -> bool:

        try:

            if  current_table == "":

                raise ValueError(f"Must not be empty current table for RENAME TABLE")

            if  new_table == "":

                raise ValueError(f"Must not be empty new table for RENAME TABLE")

            if ( not isinstance(current_table, str) or current_table == "" ):

                raise ValueError(f"Invalid current table {current_table} for RENAME TABLE")
                
            if ( not isinstance(new_table, str) or new_table == "" ):

                raise ValueError(f"Invalid new table {new_table} for RENAME TABLE")

            if self.check_table( current_table ) == False:

                print(f"⚠️ Table '{current_table}' does not exist")

                return True
            
            if self.check_table( new_table ) == True:

                print(f"⚠️ There is already table named {new_table}")

                return True

            if current_table == new_table: 

                print(f"⚠️ Unable to rename table. Both tables are named on the same")

                return True

            query = f"ALTER TABLE {current_table} RENAME TO {new_table};"

            if self.execute_query(query):

                print(f"✅ Table '{current_table}' renamed to '{new_table}' successfully")

                return True

            return False

        except sql.Error as e:

            print(f"⚠️ Raname table SQL error: {e}")

            return False

        except Exception as e:

            print(e)

            return False
    
    def rename_tables( self, tables: dict ) -> bool:
        
        try:

            if not isinstance( tables, dict ):

                raise Exception("❌ Unable to init tables, not allowed arguments. Must be an object")
            
            sv = SchemaValidator( tables , "rename_table" )

            sv._validateSchema()

            for current_table, new_table in tables.items():

                self.rename_table( current_table, new_table )

            return True

        except Exception as e:

            print(e)

            return False

    """

        Estructure args: 
        (
            table_name = table,
            [
                ( "edit", <field> , <format> ),
                ( "add", <field> , <format>, optional[ after=<field> | before=<field> ] ),
                ( "drop", <field> ),
            ]
        )

    """

    def alter_table(self, table_name: str, operations: list) -> bool:

        try:
            self.activate_stream()

            if not isinstance(table_name, str):

                raise Exception(f"❌ Invalid table name {table_name}. Must be string")

            if not isinstance(operations, list):

                raise Exception(f"❌ Unable to init operations for table {table_name}")

            # Validate schema
            sv = SchemaValidator(operations, "alter_table")

            sv._validateSchema()

            # Get table info
            columns, fks, sql_create = self.get_table_info(table_name)

            cols = [col.get('name') for col in columns]

            data_types_cols = []

            constraints = self.get_constraints(table_name)

            body_constraint = ""

            fk_constraints = []

            for key,values in constraints.items():

                if values["type"] != "FOREIGN KEY":

                    continue

                constraint = key
                
                columns_     = ",".join(values.get("columns"))        # lista

                ref_table    = values.get("ref_table")      # string

                ref_columns  = ",".join(values.get("ref_columns"))    # lista

                on_delete    = values.get("on_delete")      # string

                on_update    = values.get("on_update")      # string
                
                fk_constraints.append( f"CONSTRAINT {constraint} FOREIGN KEY ({columns_}) REFERENCES {ref_table}({ref_columns})" )
            
            body_constraint = ",\n".join(fk_constraints)

            for col in columns:

                data_type = col["name"]

                # TYPE
                if col.get("type") == "ENUM":
                    
                    # Buscar CHECK ENUM en el SQL original
                    pattern = rf"{col['name']}\s+ENUM\s+CHECK\s*\(\s*{col['name']}\s+IN\s*\((.*?)\)\)"

                    match = re.search(pattern, sql_create)

                    if match:

                        enum_raw = match.group(1).replace(" ", "")

                        data_type += f" ENUM CHECK({col['name']} IN ({enum_raw}))"

                    else:

                        data_type += " ENUM"   # fallback

                else:

                    data_type += f" {col['type']}"

                # NOT NULL
                if col.get("notnull") == 1:

                    data_type += " NOT NULL"

                # PK & AUTOINCREMENT
                if col.get("pk") == 1:

                    data_type += " PRIMARY KEY"

                    if col.get("type") == "INTEGER":

                        data_type += " AUTOINCREMENT"

                # DEFAULT
                if col.get("dflt_value") is not None:

                    data_type += f" DEFAULT({col.get('dflt_value')})"

                data_types_cols.append(data_type)

            # -----------------------------------------------------------------
            # Helper para reconstrucción en EDIT / ADD WITH POSITION
            # -----------------------------------------------------------------
            def __build_create_table(new_sql):

                try:
    
                    match = re.search(r'CREATE TABLE\s+["\']?(\w+)["\']?\s*\(', sql_create)

                    if match:

                        real_table_name = match.group(1)

                    else:

                        raise Exception("❌ Unable to detect table name in CREATE TABLE")

                    new_sql = re.sub(

                        rf'CREATE TABLE\s+["\']?{real_table_name}["\']?\s*\(',

                        f'CREATE TABLE IF NOT EXISTS temp_{real_table_name} (',

                        sql_create

                    )

                    self.execute_query(new_sql)

                    # Copiar datos
                    self.execute_query(

                        f"INSERT OR IGNORE INTO temp_{table_name} SELECT * FROM {table_name};"

                    )

                    # Reemplazar tablas
                    self.drop_table(table_name)

                    self.rename_table(f"temp_{table_name}", table_name)

                    return True

                except Exception:

                    return False

            # -----------------------------------------------------------------
            # PROCESS OPERATIONS
            # -----------------------------------------------------------------
            for op in operations:

                # ==============================================================
                # EDIT
                # ==============================================================
                if op[0] == "edit":

                    table_field = op[1]

                    new_callback = op[2].get("_callback_")

                    new_data_type = f"{table_field} {new_callback}"

                    if table_field not in cols:

                        raise Exception(f"❌ Column '{table_field}' not found in {table_name}")

                    # Buscar línea actual de esa columna
                    current_data_type = next(

                        (c for c in data_types_cols if c.startswith(table_field)),

                        None

                    )

                    if current_data_type is None:

                        raise Exception(f"❌ Could not locate column definition for {table_field}")

                    # Reemplazar
                    new_sql = sql_create.replace(current_data_type, new_data_type)

                    if not __build_create_table(new_sql):

                        raise Exception("❌ Failed executing EDIT alter table")

                # ==============================================================
                # ADD NORMAL / ADD WITH POSITION
                # ==============================================================
                elif op[0] == "add":

                    table_field = op[1]

                    callback = op[2].get("_callback_")

                    position = op[3] if len(op) == 4 else None

                    new_data_type = f"{table_field} {callback}"

                    # --------------------------
                    # ADD NORMAL
                    # --------------------------
                    if position is None:

                        sql = (

                            f"ALTER TABLE {table_name}\n"

                            f"    ADD COLUMN {new_data_type};"

                        )

                        self.execute_query(sql)

                        print(f"✅ Added new column '{table_field}' to {table_name} successfully")

                        continue

                    # --------------------------
                    # ADD WITH POSITION
                    # --------------------------
                    try:
                        # Validar syntax
                        if not (position.startswith("after=") or position.startswith("before=")):

                            raise Exception(

                                f"❌ Position must be after=<col> or before=<col> → {position}"

                            )

                        parts = position.split("=")

                        if len(parts) != 2:

                            raise Exception(

                                f"❌ Invalid assignment '{position}'. Use after=<col> or before=<col>"

                            )

                        col_position = parts[1]

                        if col_position not in cols:

                            raise Exception(

                                f"❌ Column '{col_position}' not found in table '{table_name}'"

                            )
                
                        pattern = rf"^\s*{col_position}\b[\s\S]*?(?=^\s*\w+\b|\)$)"

                        match = re.search(pattern, sql_create, flags=re.MULTILINE)

                        if match:
                        
                            match_ = match.group()

                            col_name_from_match = match_.strip().split()[0]

                            result = list(filter(

                                lambda col_def: col_def.startswith(col_name_from_match + " "),

                                data_types_cols

                            ))

                            index = None

                            if result:

                                index = data_types_cols.index(result[0])

                            if index is not None:

                                if position.startswith("after="):

                                    data_types_cols.insert( index + 1 , new_data_type )
                                
                                else: 

                                    data_types_cols.insert( index , new_data_type )

                            else:

                                data_types_cols.append( new_data_type )
                        
                        else:

                            data_types_cols.append( new_data_type )

                        # Replace from create table sql
                        new_body_create_table = ",\n".join( data_types_cols )

                    except Exception as e:

                        print(e)

                        continue

                # end for operations

            self.desactivate_stream()

            return True

        except Exception as e:

            print(e)

            return False

   
    """

        ADDITIONAL METHODS: fetch_all, fetch_one, fetch_many, date, time, datetime, format_table, formatted_query, 
            format_results, processing_stream, _build_placeholders, _build_set_clause, _build_where_clause, execute_query, 
            reset_autoincrement, reset_autoincrements, activate_stream, desactivate_stream, is_text_column, get_database, 
            get_sqlite_type, get_pk, get_query, get_object_columns, check_columns, check_table, get_db_tables
        
        DESCRIPTION: These methods provide additional functionalities for fetching results, formatting outputs,
            building SQL clauses, executing queries, managing autoincrement values, and checking database schema.
            
    """
    # =======================
    # ADDITIONAL METHODS
    # =======================  
    def fetch_all(self) -> list[dict]:

        rows = self.cursor.fetchall()

        results = [dict(row) for row in rows]

        return results

    def fetch_one(self) -> Union[dict, None]:

        row = self.cursor.fetchone()

        if row:

            return dict(row)

        return None
    
    def fetch_many(self, size: int) -> list[dict]:

        rows = self.cursor.fetchmany(size)

        results = [dict(row) for row in rows]

        return results

    def date(self) -> str:

        # Return current date in YYYY-MM-DD format
        return SQLITE_FUNCS[0]
    
    def time(self) -> str:

        # Return current time in HH:MM:SS format
        return SQLITE_FUNCS[1]
    
    def datetime(self) -> str:

        # Return current date and time in YYYY-MM-DD HH:MM:SS format
        return SQLITE_FUNCS[2]

    def format_table(self, data: list) -> str:

        if not data:

            return "No data available."

        headers = [f"Col{i+1}" for i in range(len(data[0]))]

        table = " | ".join(headers) + "\n"

        table += "-" * len(table) + "\n"

        for row in data:

            formatted_values = [str(value) for value in row]

            table += " | ".join(formatted_values) + "\n"

        return table

    def formatted_query(self) -> str:

        return self.query.strip().replace("\n", " ").replace("  ", " ")
    
    def format_results(self, rows: list[dict]) -> str:

        if not rows:

            return "No results found."

        headers = rows[0].keys()

        table = " | ".join(headers) + "\n"

        table += "-" * len(table) + "\n"

        for row in rows:
            
            formatted_values = []

            for h in headers:

                value = row[h]

                if value is None and isinstance(value, str):

                    formatted = ""

                elif isinstance(value, (int, float)) and value is None:

                    formatted = str(value)

                else:

                    formatted = str(value)

                formatted_values.append(formatted)

            table += " | ".join(formatted_values) + "\n"

        return table

    def processing_stream(self, **statements) -> int:

        table_name, column, operator, value = list(statements.values())

        ids = self.execute_query(f"SELECT {column} FROM {table_name} WHERE {column} {operator} ?", (value,)).json

        print(f"   → Found {len(ids)} rows to process.")

        total_ids = len(ids)

        percentage_step = max(total_ids // 10, 1)

        for idx in range(total_ids):

            if (idx + 1) % percentage_step == 0 or (idx + 1) == total_ids:

                percent_complete = ((idx + 1) / total_ids) * 100

                print(f"   → Processed {idx + 1}/{total_ids} ({percent_complete:.1f}%)")

                time.sleep(0.04)  # Simulate processing time

        return total_ids

    def _build_placeholders(self, length: int) -> str:

        return ", ".join(["?"] * length)

    def _build_set_clause(self, set_values: dict) -> str:

        set_clauses = [f"{col} = ?" for col in set_values.keys()]

        return ", ".join(set_clauses)

    def _build_where_clause(self, **args) -> dict[str, Union[str, int, list, tuple]]:

        # Obtain primary key
        print( f"Building WHERE clause with args: {args} " )

        data, table_name = list(args.values())

        primary_keys = self.get_pk(table_name)

        where = ""

        params = ()

        row_count = 0

        if len(primary_keys) == 0:

            raise Exception("Table has no primary key — cannot perform delete by ID.")

        if len(primary_keys) > 1:

            raise Exception( f"Table has multiple primary keys. Choose one: {', '.join(pk['name'] for pk in primary_keys)}")

        name_primary_key = primary_keys[0]["name"]

        type_primary_key = primary_keys[0]["type"]

        if data is not None:
            # =============================
            # CASE: data as only ID
            # =============================
            if isinstance(data, int):

                placeholders = "?"

                where = f" WHERE {name_primary_key} IN ({placeholders})"

                params = (data,)

            # =============================
            # CASE: data as a list of IDs
            # =============================
            elif (
                isinstance(data, list)
                and len(data) == 3
                and isinstance(data[0], str)
                and data[1].upper() in ("=", ">", "<", "<>", "!=", ">=", "<=")
                and isinstance(data[2], (int, float, str))
            ):
                column, op, value = data

                where = f" WHERE {column} {op} ?"

                params = (value,)

                row_count = self.processing_stream(table=table_name, column=column, operator=op, value=value)

            # --- LIKE ---
            elif (
                isinstance(data, list)
                and len(data) == 3
                and isinstance(data[0], str)
                and data[1].upper() == "LIKE"
                and isinstance(data[2], str)
            ):
                column, op, value = data

                op = op.upper()

                type_value = self.get_sqlite_type(value)

                if type_value.upper() not in ("TEXT", "VARCHAR", "CHAR"):

                    raise Exception(f"Column '{column}' is type '{type_value}', cannot use {op}")

                if not self.is_text_column(table_name, column):

                    raise Exception(f"Cannot use {op} on non-text column '{column}' (type: {type_value})")
                    
                where = f" WHERE {column} {op} ?"

                params = (value,)

            # --- BETWEEN ---
            elif (
                isinstance(data, list)
                and len(data) == 3
                and isinstance(data[0], str)
                and data[1].upper() == "BETWEEN"
                and isinstance(data[2], (list,tuple))
                and len(data[2]) == 2
            ):
                column, op, (v1, v2) = data[0], data[1], data[2]

                where = f" WHERE {column} {op.upper()} ? AND ?"

                params = (v1, v2)
            
            elif (
                isinstance(data, list)
                and len(data) == 3
                and isinstance(data[0], str)
                and data[1].upper() == "IN"
                and isinstance(data[2], (list,tuple))
            ):
                column, op, values = data[0], data[1], data[2]

                where = f" WHERE {column} {op.upper()} ({', '.join(['?'] * len(values))})"

                params = tuple(values)

            elif isinstance(data, list) and len(data) > 0:

                # Validar tipos
                wrong_ids = []

                # Stream delete
                for item in data:

                    print(f"Processing id ({item})")

                    if self.get_sqlite_type(item) != type_primary_key:

                        print(f"Error processing id {item}")

                        wrong_ids.append(item)

                if wrong_ids:

                    raise Exception(

                        f"IDs {', '.join(map(str, wrong_ids))} do not match primary key type '{type_primary_key}' in table '{table_name}'"

                    )

                # Crear placeholders seguros
                placeholders = ", ".join(["?"] * len(data))

                where = f" WHERE {name_primary_key} IN ({placeholders})"

                params = tuple(data)

            else:

                raise Exception("You must provide an integer ID or a list of IDs for deletion.")
        
        return {"where": where, "params": params , "row_count": row_count }
    
    def execute_query(self, query: str, params: Union[tuple, list, None]=None) -> Union[list, bool]:

        try:

            # Check if all tables over query exist
            if params is None:

                result = self.cursor.execute(query)

            elif isinstance(params, list):
                
                if all(isinstance(p, (list, tuple)) for p in params):

                    result = self.cursor.executemany(query, params)

                else:

                    raise ValueError("Params must be a list of tuples or lists for executemany().")

            else:

                result = self.cursor.execute(query, params)

            self.conn.commit()

            cmd = query.lstrip().split()[0].upper()

            if cmd in ("SELECT", "PRAGMA", "WITH"):

                rows = result.fetchall()

                return QueryResults(rows, formatter=self.format_results)

            return True

        except sql.Error as e:

            print(f"⚠️ Query error: {e}")

            return False

    def reset_autoincrement(self, table_name: str) -> bool:

        """
        Reset AUTOINCREMENT counter for a specific table.

        """
        try:

            self.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")

            self.conn.commit()

            print(f"✅ AUTOINCREMENT reset for table '{table_name}'")

            return True

        except sql.Error as e:

            print(f"⚠️ Error resetting autoincrement for table '{table_name}': {e}")

            return False
            
    def reset_autoincrements(self) -> bool:

        """
        Reset AUTOINCREMENT counter for all tables.

        """
        try:

            self.cursor.execute("DELETE FROM sqlite_sequence;")
            
            self.conn.commit()

            print(f"✅ AUTOINCREMENT reset for all tables")

            return True

        except sql.Error as e:

            print(f"⚠️ Error resetting autoincrement for all tables: {e}")
            
            return False

    def activate_stream(self) -> None:

        if self.stream_mode:

            print("eStream mode is already active.")

            self.cursor.execute("PRAGMA synchronous = OFF;")

            self.cursor.execute("PRAGMA journal_mode = MEMORY;")

            self.cursor.execute("PRAGMA temp_store = MEMORY;")

            self.cursor.execute("PRAGMA locking_mode = EXCLUSIVE;")

            self.cursor.execute("PRAGMA foreign_keys = OFF;")

            self.cursor.execute("PRAGMA cache_size = -2000000;")
    
    def desactivate_stream(self) -> None:

        if self.stream_mode:

            print("eStream mode is already deactivated.")

            self.cursor.execute("PRAGMA foreign_keys = ON;")

            self.cursor.execute("PRAGMA journal_mode = WAL;")

            self.cursor.execute("PRAGMA synchronous = NORMAL;")

    def is_text_column(self, table_name, column):

        info = self.execute_query(f"PRAGMA table_info({table_name})").json

        for col in info:

            if col["name"] == column:

                ctype = col["type"].upper()

                if any(t in ctype for t in ("CHAR", "TEXT", "CLOB", "VARCHAR")):

                    return True

                return False

        raise Exception(f"Column '{column}' not found in table '{table_name}'")

    def get_database(self) -> str:

        if "db" in self.db_path: 
            
            return self.db_path

        return self.db_name

    def get_sqlite_type(self, value) -> str:

        if value is None:

            return "NULL"

        if isinstance(value, bool):

            return "INTEGER"

        if isinstance(value, int):

            return "INTEGER"

        if isinstance(value, float):

            return "REAL"

        if isinstance(value, str):

            return "TEXT"

        if isinstance(value, bytes):

            return "BLOB"

        if isinstance(value, (datetime.date, datetime.datetime)):

            return "TEXT"  # ISO format recommended

        if isinstance(value, decimal.Decimal):

            return "NUMERIC"

        if isinstance(value, uuid.UUID):

            return "TEXT"

        if isinstance(value, (list, dict)):

            return "TEXT"  # Save as JSON

        # Every other kind: save as text
        return "TEXT"

    def get_pk(self, table_name: str) -> list:

        primary_keys = [ { "name": field.get("name") , "type": field.get("type") } for field in self.get_object_columns( table_name ) if field.get("pk") == 1]

        return list( primary_keys )

    def get_fk( self, table_name: str ) -> dict:

        return self.execute_query( f"PRAGMA foreign_key_list({table_name})" )

    def get_query(self) -> str:
        
        return self.query

    def get_object_columns(self, table_name: str) -> Union[dict, None]:

        try:

            columns = self.execute_query(f"PRAGMA table_info({table_name});").json

            return columns

        except sql.Error as e:

            print(f"⚠️ Error fetching columns for {table_name}: {e}")

            return None

    def check_columns(self, table_name: str) -> Union[list, None]:

        try:
            
            self.cursor.execute(f"PRAGMA table_info({table_name});")

            columns_info = self.cursor.fetchall()

            columns = [col['name'] for col in columns_info]

            return columns

        except sql.Error as e:

            print(f"⚠️ Error fetching columns for {table_name}: {e}")

            return None

    def check_table(self, table_name: str) -> bool:
        
        try:
        
            data = self.execute_query("""

                SELECT name FROM sqlite_master WHERE type='table' AND name = ?

            """, (table_name,)).count

            if data == 0:

                return False
            
            return True
    
        except Exception as e:

            print(f"Error: {e}")

            return False
    
    def get_db_tables( self, **args ) -> Union[list, bool]:

        try:

            autoincrement = args.get("autoincrement", False)

            return self.execute_query( f"""

                SELECT name FROM sqlite_master WHERE type='table' { "AND name LIKE 'sqlite_%' AND sql NOT LIKE '%AUTOINCREMENT%'" if autoincrement else "" }

            """ ).json

        except Exception as e:

            print(f"Error: {e}")

            return False

    def get_constraints(self, table_name: str) -> dict:
        """
        Extract all constraints (FOREIGN KEY, CHECK, UNIQUE) from a table.
        Output format is a single dict:
        
        {
            "constraint_name": {
                "type": "FOREIGN KEY" | "CHECK" | "UNIQUE",
                ...data...
            }
        }
        """

        constraints = {}

        # -------------------------------------------------------
        # 1. Read raw CREATE TABLE source
        # -------------------------------------------------------
        sql_res = self.execute_query(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        ).json

        if not sql_res or not sql_res[0]["sql"]:
            return {}

        sql = sql_res[0]["sql"]

        # -------------------------------------------------------
        # 2. Extract constraint names + type via regex
        # -------------------------------------------------------

        pattern = r"CONSTRAINT\s+(\w+)\s+(FOREIGN KEY|CHECK|UNIQUE)"
        named_constraints = re.findall(pattern, sql)

        # Pre-fill dictionary with basic structure
        for name, ctype in named_constraints:
            constraints[name] = {"type": ctype}

        # -------------------------------------------------------
        # 3. FOREIGN KEY definitions (must merge with PRAGMA)
        # -------------------------------------------------------
        fk_list = self.execute_query(
            f"PRAGMA foreign_key_list({table_name})"
        ).json

        # SQLite groups FK constraints by their sequential id
        fk_counter = 0

        for fk in fk_list:

            # Find matching constraint name (in order)
            fk_name = None
            counter = 0

            for cname, cdata in constraints.items():
                if cdata["type"] == "FOREIGN KEY":
                    if counter == fk["id"]:
                        fk_name = cname
                        break
                    counter += 1

            # If FK is unnamed (rare), skip
            if not fk_name:
                continue

            # Fill constraint detail
            constraints[fk_name].update({
                "columns":      [fk["from"]],
                "ref_table":    fk["table"],
                "ref_columns":  [fk["to"]],
                "on_delete":    fk["on_delete"],
                "on_update":    fk["on_update"],
            })

        # -------------------------------------------------------
        # 4. CHECK constraints – extract full expression
        # -------------------------------------------------------
        check_pattern = r"CONSTRAINT\s+(\w+)\s+CHECK\s*\((.*?)\)"
        check_matches = re.findall(check_pattern, sql, flags=re.DOTALL)

        for name, expression in check_matches:
            if name in constraints and constraints[name]["type"] == "CHECK":
                constraints[name]["expression"] = expression.strip()

        # -------------------------------------------------------
        # 5. UNIQUE constraints – extract columns
        # -------------------------------------------------------
        unique_pattern = r"CONSTRAINT\s+(\w+)\s+UNIQUE\s*\((.*?)\)"
        unique_matches = re.findall(unique_pattern, sql)

        for name, cols in unique_matches:
            if name in constraints and constraints[name]["type"] == "UNIQUE":
                constraints[name]["columns"] = [
                    c.strip() for c in cols.split(",")
                ]

        return constraints


    def get_autoincrement_pks(self, table_name:str) -> list:
        # Paso 1: obtener PKs
        pk_cols = [ pk.get("name") for pk in self.get_pk( table_name ) ]
        # Paso 2: leer SQL original
        _,_,sql = self.get_table_info(table_name)

        sql_upper = sql.upper()

        # Paso 3: solo devolver PKs con AUTOINCREMENT
        autoinc_pks = []
        for col in pk_cols:
            pattern = rf'["\[]?{col.upper()}["\]]?\s+INTEGER\s+PRIMARY\s+KEY(?:\s+NOT\s+NULL)?\s+AUTOINCREMENT'
            if re.search(pattern, sql_upper):
                autoinc_pks.append(col)

        return autoinc_pks


    def get_table_info( self, table_name ):

        data = {

            "columns": self.execute_query(f"PRAGMA table_info({table_name})").json,

            "foreign_keys": self.execute_query(f"PRAGMA foreign_key_list({table_name})").json,

            "sql": (self.execute_query(

                f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"

            ).json)[0]["sql"]

        }

        return data.get("columns", False) , data.get("foreign_keys", False) , data.get("sql", False)