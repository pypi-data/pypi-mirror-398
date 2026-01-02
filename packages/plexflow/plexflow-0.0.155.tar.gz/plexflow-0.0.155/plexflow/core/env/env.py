import os
from airflow.models import Variable
from airflow.exceptions import AirflowException

def get_var(var_name: str) -> str:
    """
    Function to retrieve a variable from Airflow or OS environment.

    This function first attempts to retrieve the variable from Airflow's variables.
    If the variable is not found in Airflow or an error occurs, it then attempts to retrieve it from the OS environment.

    Args:
        var_name (str): The name of the variable to retrieve.

    Returns:
        str: The value of the variable. If the variable is not found, returns None.

    Examples:
        >>> get_var('HOME')
        '/home/user'
        >>> get_var('UNKNOWN_VAR')
        None
    """
    try:
        # Try to get the variable from Airflow
        var_value = Variable.get(var_name)
    except AirflowException:
        # If it fails, get the variable from os environment
        var_value = os.getenv(var_name)

    return var_value
