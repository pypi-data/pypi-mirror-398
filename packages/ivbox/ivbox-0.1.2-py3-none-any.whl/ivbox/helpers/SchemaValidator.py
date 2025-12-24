from typing import Union
from .utils import singularOrPlural

class SchemaError(Exception):
    pass

class SchemaValidator:

    def __init__(self, schema: Union[dict, list], type_: str):
        self.schema = schema
        self.type_ = type_
        self.type_schemas = { 
            "create_table": self._validate_schema_create_table, 
            "drop_table": self._validate_schema_drop_table, 
            "rename_table": self._validate_schema_rename_table, 
            "alter_table": self._validate_schema_alter_table 
        }

    def _validate_schema_create_table( self ):
        # Validate keys of main schema
        for key in self.schema.keys():

            if not isinstance(key, str):
                raise SchemaError(f"❌ Table name must be a string → {key}")

        # Validate each table
        for table, dataset in self.schema.items():

            if not isinstance(dataset, list):
                raise SchemaError(f"❌ {table}: must be a list [columns, (optional) foreign_keys]")

            if len(dataset) < 1:
                raise SchemaError(f"❌ {table}: must contain at least 1 element: columns")

            if len(dataset) > 2:
                raise SchemaError(f"❌ {table}: must contain at most 2 elements: [columns, foreign_keys]")

            columns = dataset[0]
            foreign_keys = dataset[1] if len(dataset) == 2 else None

            # Validate columns dict
            if not isinstance(columns, dict):
                raise SchemaError(f"❌ {table}: first element must be a dictionary of columns")

            col_errors = ""
            for col_name, options in columns.items():

                if not isinstance(col_name, str):
                    col_errors += f"Column name must be a string → {col_name}\n"

                if not isinstance(options, dict) or "__col_type__" not in options:
                    col_errors += f"{col_name}: must be a column function such as integer(), text(), enum(), etc.\n"

            if col_errors:
                raise SchemaError(f"❌ Errors in columns of {table}:\n{col_errors}")

            # Validate foreign keys block
            if foreign_keys is not None:

                if not isinstance(foreign_keys, dict):
                    raise SchemaError(f"❌ {table}: second element must be a dictionary of foreign keys")

                if len(foreign_keys) == 0:
                    raise SchemaError(f"❌ {table}: foreign key block cannot be empty")

                fk_errors = ""

                for cons, tpl in foreign_keys.items():

                    if not isinstance(cons, str):
                        fk_errors += f"FK key must be a string → {cons}\n"

                    if not isinstance(tpl, tuple):
                        fk_errors += f"{cons}: must be a tuple\n"
                        continue

                    if len(tpl) != 3:
                        fk_errors += f"{cons}: must contain (column_src, table_dest, column_dest)\n"

                if fk_errors:
                    raise SchemaError(f"❌ Errors in foreign keys of {table}:\n{fk_errors}")
    
    def _validate_schema_drop_table( self ):

        if not isinstance(self.schema, list):

            raise SchemaError("❌ Must be a list of tables for DROP TABLE")

        invalid_tables = []

        for table in self.schema:

            if not isinstance( table , str ):

                invalid_tables.append( table )

        if len(invalid_tables) > 0:

            raise SchemaError( f"⚠️ Invalid table{singularOrPlural( invalid_tables )} for drop table {",".join(invalid_tables)}" )

    def _validate_schema_rename_table( self ):
        
        errors = ""

        for current_table, new_table in self.schema.items():

            if not isinstance(current_table, str):

                errors += f"""
                    must be string ----->{repr(current_table)}: .....\n
                """

            if not isinstance(new_table, str):

                errors += f"""
                    {current_table}: {repr(new_table)} <------- must be string\n
                """
        
        if errors != "":

            raise SchemaError(f"❌ Following dict must contains string tables → \n{str(errors)}")
    
    def _validate_schema_alter_table(self):

        """
        Structure:
        [
            ("edit", "field", type_function),
            ("add", "field", type_function, "after=<field>" | "before=<field>"),
            ("drop", "field"),
        ]
        """

        valid_ops = {"edit": (3,), "add": (3,4), "drop": (2,)}
        
        functions_msg = "must be a column function such as integer(), text(), enum(), etc."

        # Schema must be a list
        if not isinstance(self.schema, list):

            raise SchemaError("❌ Alter table schema must be a list of tuples")

        if len(self.schema) == 0:

            raise SchemaError("❌ No operations provided for alter_table()")

        errors = ""

        for t in self.schema:

            # Validate tuple
            if not isinstance(t, tuple):

                errors += f"❌ Operation must be tuple → {t}\n"

                continue

            if len(t) < 2:

                errors += f"❌ Operation {t} must have at least 2 elements\n"

                continue

            op = t[0]

            # Validate operator
            if not isinstance(op, str):

                errors += f"❌ Operator {op} must be string\n"

                continue

            if op not in valid_ops:

                errors += f"❌ Invalid operator '{op}'. Allowed: {', '.join(valid_ops)}\n"

                continue

            # Validate tuple length
            if len(t) not in valid_ops[op]:

                errors += f"❌ Operator '{op}' must have {valid_ops[op]} arguments → {t}\n"

                continue

            # Validate second argument: field name
            field = t[1]

            if not isinstance(field, str):

                errors += f"❌ Field name must be string in operation → {t}\n"

                continue

            # Validate third argument for edit/add
            if op in ("edit", "add"):

                typ = t[2]

                if not isinstance(typ, dict) or "__col_type__" not in typ:

                    errors += f"❌ Third element for '{op}' {functions_msg} → {t}\n"

                    continue

            # Validate fourth argument for add
            if op == "add" and len(t) == 4:

                position = t[3]

                if not isinstance(position, str) or not (position.startswith("after=") or position.startswith("before=")):

                    errors += f"❌ Fourth element must be 'after=<field>' or 'before=<field>' → {t}\n"

        if errors:

            raise SchemaError(f"❌ Errors in alter_table schema:\n{errors}")

    def _validateSchema( self ):

        if self.type_ not in self.type_schemas:

            raise SchemaError( f"❌ Not found type schema" )
            
        self.type_schemas.get( self.type_ )()