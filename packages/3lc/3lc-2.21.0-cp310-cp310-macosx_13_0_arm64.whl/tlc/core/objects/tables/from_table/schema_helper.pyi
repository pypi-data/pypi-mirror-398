from tlc.core.builtins.constants.string_roles import STRING_ROLE_TABLE_URL as STRING_ROLE_TABLE_URL
from tlc.core.schema import Schema as Schema, StringValue as StringValue

def input_table_schema(display_name: str = 'Input table', description: str = 'A reference to the input table') -> Schema: ...
