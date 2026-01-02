from functools import wraps

# The main difference from Exception is that we provide a suggested fix
class BreesyError(Exception):
    def __init__(self, message: str, suggested_fix: str | None = None):
        super().__init__(message)
        self.suggested_fix = suggested_fix

    def __str__(self):
        if self.suggested_fix:
            return f"\n ⚠️ {super().__str__()} \n 💡 SUGGESTED FIX: {self.suggested_fix}"
        return super().__str__()


# In case a library throws and we didn't anticipate it, we want to protect the user from a scary message
class BreesyLibraryError(BreesyError):
    def __init__(self, library_name: str, ex: Exception | None = None):
        super().__init__(
            f"Oh no, a library that Breesy is using threw an error! Please show this error to Breesy developers! "
            f"Error with library named '{library_name}', error message: '{ex}'",
            f"Google or ask an AI the library name and the error message, you will probably find some useful advice. "
            f"Try other ways of achieving your goal with Breesy, ask colleagues or the lecturer for help. "
            f"Example query to Google/AI: 'explain fix {library_name} exception {ex}'")


# Breesy error specifically for cases where the user is not at fault
class BreesyInternalError(BreesyError):
    def __init__(self, message: str, ex: Exception | None = None):
        super().__init__(
            "Oh no, something unexpected went wrong! Please show this error to Breesy developers (your lecturer)!"
            f"Error message: '{message}';"
            f"Internal error: '{ex}'",
            "Try other ways of achieving your goal with Breesy, ask colleagues or the lecturer for help.")


# Decorator to protect the user from library errors
def protect_from_lib_error(library_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                raise BreesyLibraryError(library_name, ex)

        return wrapper

    return decorator
