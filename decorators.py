from functools import update_wrapper


def decorator(decorator_fxn):
    """ The ultimate meta-decorator;
        Modifies the given decorator so that the original function it decorates retains it's __name__ and __doc__
    """
    def modified_decorator(original_fxn):
        return update_wrapper(decorator_fxn(original_fxn), original_fxn)
    return update_wrapper(modified_decorator, decorator_fxn)

def pipe(postprocessor):
    @decorator
    def _decorator(fxn):
        def _fxn(*args, **kwargs):
            return postprocessor(fxn(*args, **kwargs))
        return _fxn
    return _decorator
