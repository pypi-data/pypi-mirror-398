import inspect
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
def get_inputs(cls, *args, **kwargs):
    """
    Dynamically construct a dataclass instance from args and kwargs,
    filling missing values from defaults in the dataclass.
    """
    fields = list(cls.__annotations__.keys())
    values = {}

    args = list(args)
    for field in fields:
        if field in kwargs:
            values[field] = kwargs[field]
        elif args:
            values[field] = args.pop(0)
        else:
            values[field] = getattr(cls(), field)  # default from dataclass

    return cls(**values)


def prune_inputs(func, *args, **kwargs):
    """
    Adapt the provided args/kwargs to fit the signature of func.
    Returns (args, kwargs) suitable for calling func.
    """
    sig = inspect.signature(func)
    params = sig.parameters

    # Handle positional arguments
    new_args = []
    args_iter = iter(args)
    for name, param in params.items():
        if param.kind in (inspect.Parameter.POSITIONAL_ONLY,
                          inspect.Parameter.POSITIONAL_OR_KEYWORD):
            try:
                new_args.append(next(args_iter))
            except StopIteration:
                break
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            # collect all remaining args
            new_args.extend(args_iter)
            break
        else:
            break

    # Handle keyword arguments
    new_kwargs = {}
    for name, param in params.items():
        if name in kwargs:
            new_kwargs[name] = kwargs[name]
        elif param.default is inspect.Parameter.empty and param.kind == inspect.Parameter.KEYWORD_ONLY:
            # Required keyword not provided
            raise TypeError(f"Missing required keyword argument: {name}")

    # Only include keywords func accepts
    accepted_names = {
        name for name, p in params.items()
        if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                      inspect.Parameter.KEYWORD_ONLY)
    }
    new_kwargs = {k: v for k, v in new_kwargs.items() if k in accepted_names}

    return tuple(new_args), new_kwargs
def run_pruned_func(func, *args, **kwargs):
   args,kwargs = prune_inputs(func, *args, **kwargs)
   return func(*args, **kwargs)
