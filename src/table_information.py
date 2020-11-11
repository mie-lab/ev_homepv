from psycopg2 import sql

schema = 'ev_homepv'

home_table_info = {
    'home_table_name': sql.Identifier(schema, 'ecar_homes'),
    'schema_single': schema,
    'home_table_name_single': 'ecar_homes',
}

ecar_table_info = {
    'ecar_table_name': sql.Identifier(schema, 'ecar_data'),
    'schema_single': schema,
    'ecar_table_name_single': 'ecar_data',
}

ecarid_athome_table_info = {
    'ecarid_athome_table_name': sql.Identifier(schema, 'ecarid_is_athome'),
    'schema_single': schema,
    'ecarid_athome_table_name_single': 'ecarid_is_athome',
}
