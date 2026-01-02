import inspect
from plexflow.core.context.partial_context import PartialContext
import logging
import os
import json

def plexflow(task_func):
    def wrapper(*args, **kwargs):
        task_mode = os.getenv("TASK_MODE", "default")
        default_ttl = int(os.getenv("DEFAULT_CONTEXT_TTL", 3600 * 24 * 7 * 2)) # 2 weeks

        if task_mode == "k8s":
            dag_run_id = os.getenv("AIRFLOW_RUN_ID", None)
            # setup logging level
            logging.basicConfig(level=logging.INFO)
            
            # Loop over environment variables and look for
            # variables that start with ARG_ or KW_ARG_
            # These are the extra arguments and keyword arguments
            # that are passed to the task
            # The ARG_ variables are passed as positional arguments
            # and must be sorted from ARG_0 to ARG_N
            # The KW_ARG_ variables are passed as keyword arguments
            # and are ordered arbitrarily
            extra_args = []
            extra_kwargs = {}
            # lets first sort the env variables by the name of the variable
            sorted_env = sorted(os.environ.items(), key=lambda x: x[0])
            logging.info(f"Sorted env: {sorted_env}")
            
            for key, value in sorted_env:
                if key.startswith("ARG_"):
                    extra_args.append(value)
                elif key.startswith("KW_ARG_"):
                    arg = json.loads(value)
                    extra_kwargs[arg["key"]] = arg["value"]
            
            logging.info(f"Extra args: {extra_args}")
            logging.info(f"Extra kwargs: {extra_kwargs}")
            
            # Now lets update the args and kwargs with the extra arguments
            args = list(args) + extra_args
            kwargs.update(extra_kwargs)
        else:
            context = kwargs.get('ti', None)
            dag_run_id = context.run_id

        context_id = PartialContext.create_universal_id(dag_run_id)

        logging.info(f"Task mode: {task_mode}")
        logging.info(f"Context id: {context_id}")
        logging.info(f"Dag run id: {dag_run_id}")
        logging.info(f"Default TTL: {default_ttl}")
        logging.info(f"Universal id: {context_id}") 
        
        sig = inspect.signature(task_func)
        logging.info(f"Function signature: {sig.parameters}")
        
        func_kwargs = {}
        pos_arg_index = 0

        for param_name, param in sig.parameters.items():
            arg_type = param.annotation
            
            if param_name in kwargs:
                func_kwargs[param_name] = kwargs[param_name]
            elif issubclass(arg_type, PartialContext):
                # check if arg_type is subclass of PartialContext
                # Create an instance of the class
                func_kwargs[param_name] = arg_type(context_id=context_id, dag_run_id=dag_run_id, default_ttl=default_ttl)
            else:
                func_kwargs[param_name] = args[pos_arg_index]
                pos_arg_index += 1

        result = task_func(**func_kwargs)

        return result
    return wrapper
