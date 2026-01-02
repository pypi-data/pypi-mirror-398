import time
from retrying import retry

def execute_until_success(func, delay_type, delay, max_retries=None, retry_exceptions=None, *args, **kwargs):
    """
    This function executes a given function until it succeeds and no exceptions are thrown.
    
    Parameters:
    func (function): The function to be executed.
    delay_type (str): The type of delay between attempts. Can be 'constant' or 'exponential'.
    delay (int): The delay in seconds.
    max_retries (int, optional): The maximum number of retries. If not set, it will keep trying until the function succeeds.
    retry_exceptions (tuple, optional): The exceptions on which to retry. If not provided, retry will be attempted for any exception.
    *args: Variable length argument list for the function.
    **kwargs: Arbitrary keyword arguments for the function.

    Returns:
    The return value of the function, if it succeeds.
    """

    def retry_on_exception(exc):
        """This function will be used to determine whether to retry if the function raises an exception."""
        if retry_exceptions is None or isinstance(exc, tuple(retry_exceptions)):
            return True  # Retry for specified exceptions or any exception
        return False

    def wait_strategy(attempt_number, delay_since_first_attempt_ms):
        """This function determines the delay between retries."""
        if delay_type == 'constant':
            return delay  # Constant delay
        elif delay_type == 'exponential':
            return 2 ** attempt_number  # Exponential backoff

    @retry(retry_on_exception=retry_on_exception, wait_func=wait_strategy, stop_max_attempt_number=max_retries)
    def func_with_retry(*args, **kwargs):
        return func(*args, **kwargs)

    return func_with_retry(*args, **kwargs)
