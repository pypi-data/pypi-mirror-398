def get_var_name(var, globals):
    for name, value in globals.items():
        if value is var:
            return name
    return None
