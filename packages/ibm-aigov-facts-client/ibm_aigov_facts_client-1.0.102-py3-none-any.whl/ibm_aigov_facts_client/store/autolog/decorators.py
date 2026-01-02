from .autolog_utils import *
class clean_payload(object):
    def format_tags():
        def wrapper(func):
            def wrapped(*args, **kwargs):
                clean_tags(args[0].current_data.tags, args[0].run_id)
                changed_tags = rename_tags(args[0].current_data.tags)
                args[0].current_data.tags.clear()
                args[0].current_data.tags.update(changed_tags)
                # set_guid_tag(args[0].run_id)
                return func(*args, **kwargs)
            return wrapped
        return wrapper

def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper