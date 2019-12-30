class TaskContext:

    redis = None
    tasks = None

    def __init__(self):
        self.tasks = []


def task(f):
    tasks.append(f.__name__)

    # Inject redis parameter
    redis_param_index = f.__code__.co_varnames.index('redis')

    @wraps(f)
    def wrapper(*args, **kwds):
        return f(*args, **kwds)

    return wrapper
