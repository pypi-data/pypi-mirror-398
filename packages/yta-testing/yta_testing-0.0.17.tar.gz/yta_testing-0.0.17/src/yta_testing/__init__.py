"""
The Youtube Autonomous Testing Module.
"""
from typing import Union
from dotenv import load_dotenv
from functools import wraps

import functools
import os
import pytest


TEST_FILES_PATH = 'test_files'
"""
The relative path to the test files
folder. This is the one we should use
in all our projects.
"""

def assert_exception_is_raised(
    function: callable,
    exception_type: Union[Exception, str, None] = None,
    message: Union[str, None] = None
):
    """
    Call this method providing some code defined
    as a function to validate that it is raising
    an exception when called (send the function,
    not the call).

    The 'exception_type' can be an Exception, a
    TypeError, a ValueError, a string including
    the name of the exception type to expect, or
    None if the type is not important and must 
    not be checked.

    The 'message' can be the string we expect to
    be received as the exception message, or None
    if we don't care about the message. We will
    look for the provided 'message' text inside
    the exception message, it can be a part of 
    the message and not the exact one.

    Here is an example:
    ```
    assert_exception_is_raised(
        function = lambda: ParameterValidator.validate_tuple('tuple', 3),
        exception_type = None,
        message = 'The provided "tuple" parameter is not a tuple.'
    )
    ```
    """
    with pytest.raises(
        expected_exception = BaseException,
        #match = message
    ) as exception:
        function()

    # Any exception is subclass of 'Exception'
    # so we avoid checking it
    if isinstance(exception_type, str):
        if exception.type.__name__ != exception_type:
            raise Exception(f'Expected exception of type "{exception_type}" but obtained "{exception.type.__name__}" exception.')
        #assert exception.type.__name__ == exception_type
    elif exception_type is not None:
        if exception.type != exception_type:
            raise Exception(f'Expected exception of type "{exception_type.__name__}" but obtained "{exception.type.__name__}".')
        #assert exception.type == exception_type

    """
    The 'match' expects a regular expression and we
    send long texts sometimes, so I'm avoiding using
    it by now.
    """
    if message is not None:
        # Uncomment to see the message to copy it :)
        # print(str(exception.value))
        if message not in str(exception.value):
            raise Exception(f'The "{message}" provided is not in the exception message "{str(exception.value)}".')
        #assert message in str(exception.value)

    assert True

def assert_optional_library_is_missing(
    function: callable,
    library_name: str,
):
    """
    This method will check if the 'function'
    provided raises an exception telling us
    that the optional library is not installed
    only if that library is not actually
    installed, and will do nothing if it is
    installed.

    This is to test the OptionalClass we use
    from 'yta_programming'.
    """
    import importlib
    
    is_library_installed = importlib.util.find_spec(library_name) is None

    if not is_library_installed:
        assert_exception_is_raised(
            function = function,
            # message = f'The class "yta_youtube_api.YoutubeAPI" needs the "{library_name}" installed. You can install it with this command: pip install yta_youtube[{library_name}]'
            message = f'needs the "{library_name}" installed. You can install it with this command: pip install'
        )
        
    assert True

def is_dependency_installed(
    dependency_name: str
) -> bool:
    """
    Check if the dependency `dependency_name` is installed
    or not.

    The `dependency_name` is the name to import it and 
    use in the code, not the name in pypi:
    - `PIL` must be used and not `pillow`
    - `cv2` must be used and not `opencv-python`

    Note for developer: This method is duplicated in the
    `yta_programming` library but copied here to avoid
    imports as this library is just for testing and we
    don't want dependencies.
    """
    import importlib

    return importlib.util.find_spec(dependency_name) is not None

def execute_if_dependency_installed(
    dependency_name: str
) -> Union[any, bool]:
    """
    *Decorator*

    Decorator to execute the code only if the dependency
    with the given `dependency_name` is installed in this
    project, returning True in case it was not installed.

    The `dependency_name` is the name to import it and 
    use in the code, not the name in pypi:
    - `PIL` must be used and not `pillow`
    - `cv2` must be used and not `opencv-python`

    Note for developer: This method is duplicated in the
    `yta_programming` library but copied here to avoid
    imports as this library is just for testing and we
    don't want dependencies.
    """
    def decorator(
        func
    ):
        @wraps(
            func
        )
        def wrapper(
            *args,
            **kwargs
        ):
            return (
                func(*args, **kwargs)
                if is_dependency_installed(dependency_name) else
                True
            )
        return wrapper
    
    return decorator

def float_approx_to_compare(float):
    """
    Compare float values with 
    approximation due to the decimal
    differences we can have.

    Then, you can compare floats by
    using:

    - `assert fa == float_approx_to_compare(fb)`
    """
    return pytest.approx(float, rel = 1e-5, abs = 1e-8)


def skip_pytest(
    env_var: str = 'SKIP_TESTS'
):
    """
    *Decorator*

    Decorator to skip the pytest if the env
    variable 'env_var' is set and has a valid
    value ('1', 'true', 'yes', ''). This is
    useful when we have some tests we want to
    execute only in local, so we can set the
    variable in remote environments to avoid
    them of being executed.
    """
    def decorator(
        function
    ):
        @functools.wraps(function)
        def wrapper(
            *args,
            **kwargs
        ):
            path = os.getcwd().replace('\\', '/')
            load_dotenv(f'{path}/.env')
            env_var_value = os.getenv(env_var, '').lower()

            if env_var_value in ('1', 'true', 'yes', ''):
                pytest.skip(f'Skipping test "{function.__name__}": file-related tests are disabled by configuration ("{env_var_value}" environment variable).')

            return function(*args, **kwargs)
        
        return wrapper
    
    return decorator

class TestFilesHandler:
    """
    Class to easily handle the files we
    create when testing the projects.
    
    This class must be instantiated before
    the tests are executed, and the 
    '.delete_new_files()' method must be
    called when all the tests have finished.
    """

    __test__ = False
    """
    Attribute to be ignored by pytest.
    """

    @property
    def files(
        self
    ) -> list[str]:
        """
        The files that are currently in the
        'test_files' folder.
        """
        return set(os.listdir(self._test_files_path))

    def __init__(
        self,
        test_files_path: str = TEST_FILES_PATH
    ):
        self._test_files_path: str = test_files_path
        """
        The relative path to the test files
        folder.
        """
        self._initial_files: list[str] = self.files
        """
        The files that were available when the
        class was instantiated (before executing
        the tests).
        """

    def delete_new_files(
        self
    ) -> list[str]:
        """
        Delete all the new files found and return
        a list containing the names of the files
        that have been deleted.
        """
        files_removed = []

        for f in self.files - self._initial_files:
            path = os.path.join(self._test_files_path, f)
            if os.path.isfile(path):
                os.remove(path)
                files_removed.append(path)

        return files_removed