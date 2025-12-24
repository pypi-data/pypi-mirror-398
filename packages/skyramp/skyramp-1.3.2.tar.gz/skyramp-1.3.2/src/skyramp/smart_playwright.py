#pylint: disable=too-many-lines
"""
Intelligent Playwright wrapper with LLM-powered selector improvement.

This module provides a drop-in replacement for Playwright page objects that automatically
attempts to improve failing selectors using LLM when the original selector fails.

Usage:
    from skyramp.smart_playwright import wrap_playwright_page
    
    # Wrap your existing Playwright page
    smart_page = wrap_playwright_page(page)
    
    # Use it exactly like a normal Playwright page
    smart_page.get_by_role("button", name="Submit").click()
    # If the selector fails, it will automatically try LLM-improved alternatives
"""

import ast
import ctypes
import json
import logging
import os
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urlunparse
from playwright.sync_api import expect as playwright_expect
from playwright.sync_api import Error as PlaywrightError

from skyramp.utils import _library, check_for_update

logger = logging.getLogger(__name__)

DEFAULT_WAIT_FOR_TIMEOUT = 1500

def has_javascript(content):
    """Returns if webpage has javascript"""
    func = _library.hasJavascript

    func.argtypes = [ctypes.c_char_p]
    func.restype = ctypes.c_bool

    arg = [content.encode()]

    ret = func(*arg)

    return ret


def debug(args):
    """ helper function to print log messages per env var"""
    if os.environ.get('SKYRAMP_DEBUG', 'false') == 'true':
        print(args)

def is_running_in_docker():
    """
    Detect if we're running inside a Docker container.

    Checks the SKYRAMP_IN_DOCKER environment variable

    Returns:
        bool: True if running in Docker, False otherwise
    """
    return os.environ.get('SKYRAMP_IN_DOCKER', '').lower() in ('true', '1', 'yes')

def transform_url_for_docker(url):
    """
    Transform localhost URLs to host.docker.internal when running in Docker.

    This helper function automatically detects if we're running inside a Docker
    container and transforms localhost URLs to use host.docker.internal, which
    allows containers to access services running on the host machine.

    Args:
        url: The URL to potentially transform

    Returns:
        The transformed URL if in Docker and URL contains localhost, otherwise the original URL
    """
    if not url:
        return url

    # Auto-detect if we're running in Docker
    if not is_running_in_docker():
        return url

    # Use proper URL parsing to only replace the hostname component
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        # Only transform if hostname is exactly 'localhost' or '127.0.0.1'
        if hostname in ('localhost', '127.0.0.1'):
            # Reconstruct netloc properly to handle username, password, and port
            # netloc format: [user[:password]@]host[:port]
            new_netloc = 'host.docker.internal'

            # Preserve port if present
            if parsed.port:
                new_netloc = f'{new_netloc}:{parsed.port}'

            # Preserve username and password if present
            if parsed.username:
                userpass = parsed.username
                if parsed.password:
                    userpass = f'{userpass}:{parsed.password}'
                new_netloc = f'{userpass}@{new_netloc}'

            transformed = urlunparse((
                parsed.scheme,
                new_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            debug(f"Transformed URL: {url} -> {transformed}")
            return transformed
    except (ValueError, AttributeError):
        pass

    return url

class SkyrampException(Exception):
    """ Wrapper for playwright exception """
    def __init__(self, playwright_exception, new_message):
        self.message = new_message
        self.stack = playwright_exception.stack
        self.name = playwright_exception.name

        self.playwright_exception = playwright_exception

    def __getattr__(self, name):
        """Forward other method calls to the original exception."""
        return getattr(self.playwright_exception, name)

    def __str__(self):
        return self.message

def wrap_exception(skyramp_locator, msg, error):
    """ Wrap playwright error with Skyramp Exception """
    new_msg = msg + "\n"
    if skyramp_locator.skyramp_page.has_llm_choices():
        new_msg += skyramp_locator.generate_llm_errors()

    new_msg = error.message + "\n" + new_msg

    return SkyrampException(error, new_msg)


class SelectorCache:
    """Simple in-memory cache for successful selector improvements."""

    def __init__(self):
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    def get(self, original_selector: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached suggestions for a selector."""
        return self._cache.get(original_selector)

    def put(self, original_selector: str, suggestions: List[Dict[str, Any]]) -> None:
        """Cache suggestions for a selector."""
        self._cache[original_selector] = suggestions

    def clear(self) -> None:
        """Clear all cached suggestions."""
        self._cache.clear()


# Global cache instance
_selector_cache = SelectorCache()


# pylint: disable=too-many-locals
def improve_selector_with_llm(
    original_selector: str,
    error_message: str,
    dom_context: str = "",
    page_title: str = "",
    page_url: str = ""
) -> Optional[List[Dict[str, Any]]]:
    """
    Call the Go library to improve a failing Playwright selector using LLM.
    
    Args:
        original_selector: The failing selector
        error_message: The error message from Playwright
        dom_context: Relevant DOM context
        page_title: Page title for context
        page_url: Page URL for context
    
    Returns:
        List of selector suggestions or None if failed
    """
    # Check cache first
    cached_suggestions = _selector_cache.get(original_selector)
    if cached_suggestions:
        logger.info("Using cached suggestions for selector: %s", original_selector)
        return cached_suggestions

    try:
        request_data = {
            "original_selector": original_selector,
            "error_message": error_message,
            "dom_context": dom_context,
            "page_title": page_title,
            "page_url": page_url,
            "language": "python",
        }

        request_json = json.dumps(request_data).encode('utf-8')

        func = _library.improvePlywrightSelectorWrapper

        class ResponseWrapper(ctypes.Structure):
            """The response structure matching Go's C.struct_response_wrapper"""
            _fields_ = [
                ("response", ctypes.c_char_p),
                ("error", ctypes.c_char_p),
            ]

        func.argtypes = [ctypes.c_char_p]
        func.restype = ResponseWrapper

        response_wrapper = func(request_json)

        if response_wrapper.error:
            #pylint: disable=no-member  # check this later
            error_msg = ctypes.c_char_p(response_wrapper.error).value.decode('utf-8')
            logger.error("LLM selector improvement failed: %s", error_msg)
            return None

        if response_wrapper.response:
            #pylint: disable=no-member  # check this later
            response_json = ctypes.c_char_p(response_wrapper.response).value.decode('utf-8')
            response_data = json.loads(response_json)

            suggestions = response_data.get("suggestions", [])
            if suggestions:
                # Cache successful suggestions
                _selector_cache.put(original_selector, suggestions)
                logger.info("Got %d selector suggestions from LLM", len(suggestions))
                return suggestions

        return None
    #pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("Failed to call LLM for selector improvement: %s", e)
        return None

def parse_error_stack(stack):
    """parse error stack to find the line that is replaced by llm"""
    stack_lines = stack.split('\n')

    prev = ""
    is_file_path = True
    for l in stack_lines:
        if not is_file_path:
            is_file_path = True
            continue

        is_file_path = False
        if "src/skyramp" in l:
            break

        prev = l

    return prev


#pylint: disable=too-many-branches,too-many-statements
def retry_with_llm(skyramp_locator, error):
    """ retry with llm"""
    if os.environ.get("API_KEY", "") == "":
        return None, error

    error_message = error.message
    error_type = type(error)

    if not isinstance(skyramp_locator, SkyrampPlaywrightLocator):
        return None, error

    if not skyramp_locator.should_attempt_improvement(error_message, error_type):
        debug(f'cannot improve {error_type}')
        return None, error

    debug(f'  try to get suggestions from LLM for {skyramp_locator}')

    page_title = skyramp_locator.page.title()
    page_url = skyramp_locator.page.url

    new_msg = f'{error_message} (while using selector: {skyramp_locator}'
    page_content = skyramp_locator.page.content()

    suggestions = improve_selector_with_llm(
        original_selector=str(skyramp_locator.playwright_locator),
        error_message=new_msg,
        dom_context=page_content,
        page_title=page_title,
        page_url=page_url
    )

    if suggestions is None or len(suggestions) == 0:
        debug('No LLM suggestions available, failing with origina lerror')
        return None, error

    sorted_suggestions = sorted(suggestions,
                                key=lambda x: x.get('confidence', 0),
                                reverse=True)

    debug("")
    for idx, s in enumerate(sorted_suggestions, 1):
        debug(f"suggestion {idx}")
        debug(f'  selector: {s.get("selector", "")}')
        debug(f'  confidence: {s.get("confidence", 0.0)}')
        debug(f'  reasoning: {s.get("reasoning", "")}')

    for suggestion in sorted_suggestions:
        debug("")
        try:
            suggested_selector = suggestion.get('selector', '')
            #debug(f'trying {suggested_selector}')
            new_locator = None
            try:
                new_locator = skyramp_locator.create_locator_from_suggestion(suggested_selector)
            #pylint: disable=broad-exception-caught
            except Exception as e:
                debug(f"  failed to process {suggested_selector} {e}")

            if new_locator is None:
                debug(f' failed to create a locator {suggested_selector}')
                continue

            locator_count = new_locator.count()

            #pylint: disable=line-too-long
            debug(f'  trying new locator {suggested_selector} {locator_count} instead of {skyramp_locator}')

            if locator_count == 1:
                param = skyramp_locator.exec_param
                args = skyramp_locator.exec_args
                fname = skyramp_locator.exec_fname

                try:
                    result = None
                    if param is None and len(args) == 0:
                        result = getattr(new_locator, fname)()
                    elif param is None and len(args) != 0:
                        result = getattr(new_locator, fname)(**args)
                    elif param is not None and len(args) == 0:
                        result = getattr(new_locator, fname)(param)
                    else:
                        result = getattr(new_locator, fname)(param, **args)

                    print(f'✅ SUCCESS! Used selector: {suggested_selector} instead of {skyramp_locator}')
                    print(f'  {parse_error_stack(error.stack)}')

                    skyramp_locator.llm_locator = new_locator
                    skyramp_locator.set_locator_count(1)
                    skyramp_locator.skyramp_page.add_llm_choices(skyramp_locator.playwright_locator,
                                                                  suggested_selector, error.stack)
                    return result, None
                #pylint: disable=broad-exception-caught
                except Exception:
                    debug(f'retrying with LLM failed at {skyramp_locator}' +
                          f'replaced by {suggested_selector} {str(error)}')

        #pylint: disable=broad-exception-caught
        except Exception:
            continue

    # wrap with new error message
    message = f'Failed to find a good alternative for {skyramp_locator} with LLM.\n' + \
              'Please add "data-testid" attribute for a more stable locator\n'
    return None, wrap_exception(skyramp_locator, message, error)


def parse_function_chain(chain_str):
    """ parse function chain returned by llm to list of func names and args """
    # Remove any object prefix like "page."
    chain_str = re.sub(r'^[a-zA-Z_][a-zA-Z0-9_]*\.', '', chain_str)

    # Match function calls: funcName(args)
    regex = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)')
    result = []
    for match in regex.finditer(chain_str):
        func_name = match.group(1)
        args_str = match.group(2).strip()
        args = []
        if args_str:
            arg_matches = []
            depth = 0
            current = ''
            in_string = []
            i = 0
            while i < len(args_str):
                c = args_str[i]
                if c in ["'", '"']:
                    current += c
                    if len(in_string) >0 and c == in_string[-1]:
                        in_string.pop()
                    else:
                        in_string.append(c)
                elif len(in_string) == 0:
                    if c in ['{','[']:
                        depth += 1
                        current += c
                    elif c in ['}',']']:
                        depth -= 1
                        current += c
                    elif c == ',' and depth == 0:
                        arg_matches.append(current.strip())
                        current = ''
                    else:
                        current += c
                else:
                    current += c
                i += 1
            if current.strip():
                arg_matches.append(current.strip())
            args = arg_matches
        result.append({'function': func_name, 'arguments': args})
    return result


# pylint: disable=too-many-public-methods
class SkyrampPlaywrightLocator:
    """
    Intelligent wrapper for Playwright Locator with LLM-powered selector improvement.
    """

    def __init__(self, skyramp_page, locator, prev_locator, selector_info=None):
        self._skyramp_page = skyramp_page
        self._locator = locator
        self._previous_locator = prev_locator
        self._selector_info = selector_info or {}
        self._current_selector = self._build_selector_string()

        # for future use
        self._exec_fname = None
        self._exec_param = None
        self._exec_args = None
        self._locator_count = 0
        self._llm_selector = False

    @property
    def selector_str(self):
        """ returns selector in string """
        return self._current_selector

    def __str__(self):
        ret = self._current_selector

        cur = self
        while cur is not None:
            parent = cur._selector_info.get("parent", None) \
                if cur._selector_info is not None else None

            if parent is None:
                break

            ret = parent.selector_str + "." + ret

            cur = parent

        return ret

    #pylint: disable=too-many-return-statements
    def _build_selector_string(self):
        """Build a readable selector string from selector info for LLM context."""
        if not self._selector_info:
            return str(self._locator) if hasattr(self._locator, '__str__') else ""

        method = self._selector_info.get('method', 'locator')
        args = self._selector_info.get('args', [])
        kwargs = self._selector_info.get('kwargs', {})

        ret = f'{method}('
        ret_args = []
        if len(args) != 0:
            ret_args += [str(arg) for arg in args]

        if len(kwargs) != 0:
            for k, v in kwargs.items():
                ret_args += [f'{k}="{v}"']

        if len(ret_args) != 0:
            ret += ', '.join(ret_args)

        ret += ")"
        return ret

    @property
    def selector_info(self):
        """return selector_info """
        return self._selector_info

    @property
    def locator_count(self):
        """return current locator's count in the page"""
        return self._locator_count

    def set_locator_count(self, count):
        """ Set locator count"""
        self._locator_count = count

    @property
    def playwright_locator(self):
        """return playwright locator"""
        return self._locator

    @property
    def exec_fname(self):
        """return action func name"""
        return self._exec_fname

    @property
    def exec_param(self):
        """return param for action func"""
        return self._exec_param

    @property
    def exec_args(self):
        """return additional params for action func"""
        return self._exec_args

    @property
    def skyramp_page(self):
        """return skyramp page"""
        return self._skyramp_page

    @property
    def current_selector(self):
        """ return current selector in string """
        return self._current_selector

    @property
    def llm_selector(self):
        """ reutn if this is llm selector"""
        return self._llm_selector

    def should_attempt_improvement(self, error_message: str, error_type=None) -> bool:
        """Determine if an error is worth trying LLM improvement."""
        improvement_keywords = [
            "timeout",
            "not found",
            "no element",
            "not visible",
            "not attached",
            "selector resolved to hidden",
            "element is not enabled",
        ]

        # Check for specific Playwright error types
        if error_type:
            playwright_error_types = [
                "TimeoutError",
                "Error",
                "LocatorAssertionError"
            ]
            if any(error_type.__name__.endswith(err_type) for err_type in playwright_error_types):
                return True

        error_lower = error_message.lower()
        return any(keyword in error_lower for keyword in improvement_keywords)

    def create_locator_from_suggestion(self, suggestion):
        """Create a new locator based on suggestion"""
        suggestion = suggestion.strip()
        if suggestion.startswith("page."):
            suggestion = suggestion[5:]

        chains = parse_function_chain(suggestion)

        def str_to_literal(s):
            try:
                return ast.literal_eval(s)
            except (ValueError, SyntaxError):
                return s  # Return as-is if not a literal

        cur = self.page
        for chain in chains:
            f = getattr(cur, chain["function"])

            if chain["function"] in ["first", "last"]:
                cur = f
                continue

            args = []
            kwargs = {}

            if len(chain["arguments"]) == 0:
                cur = f()
                continue

            for a in chain["arguments"]:
                if a[0] in ["'", '"']:
                    new_a = str_to_literal(a)
                    args.append(new_a)
                    continue

                if "=" in a:
                    fields = a.split('=')
                    kwargs[fields[0]] = str_to_literal(fields[1])
                else:
                    args.append(str_to_literal(a))
            try:
                if len(kwargs) == 0:
                    cur = f(*args)
                elif len(args) == 0:
                    cur = f(**kwargs)
                else:
                    cur = f(*args, **kwargs)
            #pylint: disable=broad-exception-caught
            except Exception as e:
                debug(f'    failed to construct locator {e}')
                return None

        return cur

    def _is_selector_method(self, method_name: str) -> bool:
        """Check if a method uses selectors that can be improved."""
        selector_methods = [
            'click', 'fill', 'type', 'press', 'check', 'uncheck', 'select_option',
            'hover', 'focus', 'blur', 'scroll_into_view_if_needed', 'screenshot',
            'text_content', 'inner_text', 'inner_html', 'get_attribute', 'is_visible',
            'is_enabled', 'is_checked', 'is_disabled', 'is_editable', 'is_hidden'
        ]
        return method_name in selector_methods

    def _test_locator_exists(self, locator):
        """Test if a locator can find an element without performing actions."""
        try:
            # Use count() to check existence without throwing an error
            # This doesn't perform any actions, just checks if element exists
            count = locator.count()
            return count > 0
        #pylint: disable=broad-exception-caught
        except Exception:
            return False

    def execute(self):
        """execute actions associated with the locator"""
        debug(f'    execute { self._exec_fname} { self } ' +
              f'with { self._exec_param } {self._exec_args}')

        f = getattr(self._locator, self._exec_fname)
        try:
            if self._exec_param is None:
                return f(**self._exec_args), None

            return f(self._exec_param, **self._exec_args), None
        except PlaywrightError as e:
            return None, e
        #pylint: disable=broad-exception-caught
        except Exception as e:
            return None, e

    def generate_llm_errors(self):
        """ generate llm error messages """
        ret = 'List of dynamic selectors that could be relevant to error:\n'

        choices = self._skyramp_page.get_llm_choices()
        if len(choices) == 0:
            return ""

        i = 1
        for choice in choices:
            ret += f'{ i }. original locator: {choice["original"]}\n'
            ret += f'  selected locator: {choice["new"]}\n'
            ret += f'  at: {choice["stack"].strip()}\n'
            i += 1

        return ret

    @property
    def wrong_selector_error_msg(self):
        """return wrong_selector_error msg"""
        # pylint: disable=line-too-long
        return 'Potentially a wrong selector. Please add "data-testid" attrbitue for a more stable locator.'

    def new_prev_hydration_error_msg(self):
        """return prev locator hydration error msg"""
        # pylint: disable=line-too-long
        msg = f'Cannot find locator {self} and likely a hydration issue on {self._previous_locator}.\n'
        msg += f'Please add enough wait_for_timeout() on {self._previous_locator}'
        return msg

    def new_multi_locator_error_msg(self):
        """return multi locator error msg"""
        # pylint: disable=line-too-long
        return f'{self} found {self._locator_count} locators. Please add "data-testid" attribute for a more stable locator'

    def _retry_with_llm(self, error, msg):
        api_key = os.environ.get("API_KEY", "")

        if api_key == "":
            raise wrap_exception(self, msg, error)

        ret, new_error = retry_with_llm(self, error)

        if new_error is not None:
            raise new_error

        self._llm_selector = True
        return ret

    # pylint: disable=too-many-return-statements,too-many-branches,too-many-statements
    def _smart_retry_with_fallback(self, fname, param, **kwargs):
        self._exec_fname = fname
        self._exec_param = param
        self._exec_args = kwargs

        locator_count = self._locator.count()
        current_url = self._skyramp_page.page.url
        debug(f'handling { self}.{ fname}, count = { locator_count }, {current_url }')
        self._locator_count = locator_count

        if locator_count == 1:
            debug(f'  single locator for { self} identified, { current_url}')

            first_result, first_error = self.execute()
            if first_error is None:
                # normal execution, check url changes
                return self._skyramp_page.check_navigation(current_url, first_result)

            if isinstance(first_error, PlaywrightError):
                debug(f'  first attempt of { self} failed, {first_error.name}')
                if first_error.name == "TimeoutError":
                    #pylint: disable=line-too-long
                    debug(f'  locator {self} exists, but execution failed, wait a bit and try again')
                    self.wait()

                    second_result, second_error = self.execute()
                    if second_error is None:
                        return self._skyramp_page.check_navigation(current_url, second_result)

                    #pylint: disable=line-too-long
                    debug(f'  failed second time and execute previous locator {self._previous_locator} again')
                    _, previous_error = self._previous_locator.execute()
                    #pylint: disable=broad-exception-caught
                    if previous_error is not None:
                        #pylint: disable=line-too-long
                        debug(f'  failed to execute previous locator {self._previous_locator} again, continue')
                    else:
                        third_result, third_error = self.execute()
                        if third_error is None:
                            return self._skyramp_page.check_navigation(current_url, third_result)

                    if second_error.name == "TimeoutError":
                        return self._retry_with_llm(second_error, self.hydration_error_msg)
                    if "strict mode violation" in second_error.message:
                        return self._retry_with_llm(second_error, self.new_multi_locator_error_msg())

                if "strict mode violation" in first_error.message:
                    return self._retry_with_llm(first_error, self.new_multi_locator_error_msg())

                if "Unknown key" in first_error.message:
                    msg = first_error.message.split('\n')[0]
                    print(f'{ msg }, continue without execution')
                    return None

            raise first_error

        if locator_count > 0:
            #pylint: disable=line-too-long
            debug(f'  multiple {locator_count} locators for {self} identified, {current_url}')

            self.wait()
            locator_count = self._locator.count()

            if locator_count > 5:
                #pylint: disable=line-too-long
                raise Exception(f'{locator_count} locators detected for {self}. Please add "data-test-id" attribute for a more stable locator')

            result, error = self.execute()
            if error is None:
                return self._skyramp_page.check_navigation(current_url, result)

            if isinstance(error, PlaywrightError):
                return self._retry_with_llm(error, self.new_multi_locator_error_msg())

            raise error

        if locator_count == 0:
            # if locator does not exist, we need to consider two cases
            # one is if any actions that required hydration did not work
            # second, if locator id is not correct
            # check if last step has potential hydration
            if self._previous_locator is not None and \
                self._previous_locator.locator_count == 0:
                #pylint: disable=line-too-long
                debug(f'  previous action {str(self._previous_locator)} is potentially associated with hydration, {current_url}')
                self.wait()
                previous_count = self._previous_locator.count()
                #pylint: disable=line-too-long
                debug(f'  re-execute the previous one {str(self._previous_locator)}, new locator count = {previous_count}, {current_url})')
                _, previous_error = self._previous_locator.execute()
                if previous_error is not None:
                    #pylint: disable=line-too-long
                    debug(f'  failed to execute previous locator {str(self._previous_locator)} again, continue')

                first_result, first_error = self.execute()
                if first_error is None:
                    return self._skyramp_page.check_navigation(current_url, first_result)

                if not isinstance(first_error, PlaywrightError):
                    raise first_error

                if first_error.name == "TimeoutError":
                    debug(f'  {self} failed at first try. attempting again with some timeout')
                    self.wait()
                    second_result, second_error = self.execute()
                    if second_error is None:
                        return self._skyramp_page.check_navigation(current_url, second_result)

                    return self._retry_with_llm(second_error, self.new_prev_hydration_error_msg())

                if "strict mode violation" in first_error.message:
                    debug(f'  a rare case when multiple locators are detected on {self}')
                    return self._retry_with_llm(first_error, self.new_multi_locator_error_msg())

                raise first_error

            if self._previous_locator is not None and self._previous_locator.llm_selector:
                #pylint: disable=line-too-long
                debug(f'  {self} locator count is zero, but previous locator was selected by LLM')
            else:
                #pylint: disable=line-too-long
                debug(f'  {self} locator count is zero, but previous locator seems not related to hydration')

            # previous action may not be associated with hydration
            # then we just try current locator. could be a locator with a wrong id
            # wait for a short time just in case
            self.wait()

            self._locator_count = self._locator.count()
            debug(f'  after waiting locator {self} count = {self.locator_count}, {current_url}')

            first_result, first_error = self.execute()
            if first_error is None:
                return self._skyramp_page.check_navigation(current_url, first_result)

            if first_error.name == "TimeoutError":
                debug(f'{self} failed at first try. attempting again with some timeout')
                self.wait()

                second_result, second_error = self.execute()
                if second_error is None:
                    return self._skyramp_page.check_navigation(current_url, second_result)

                if not isinstance(second_error, PlaywrightError):
                    raise second_error

                if second_error.name == "TimeoutError":
                    return self._retry_with_llm(second_error, self.wrong_selector_error_msg)
                if "strict mode violation" in second_error.message:
                    return self._retry_with_llm(second_error, self.new_multi_locator_error_msg())

                raise second_error

            if self.locator_count > 1 or "strict mode violation" in first_error.message:
                return self._retry_with_llm(first_error, self.new_multi_locator_error_msg())

            raise first_error

        result, _ = self.execute()
        return result

    def click(self, **kwargs):
        """Wrap click"""
        return self._smart_retry_with_fallback("click", None, **kwargs)

    def fill(self, text, **kwargs):
        """Wrap fill"""
        return self._smart_retry_with_fallback("fill", text, **kwargs)

    def type(self, text, **kwargs):
        """Wrap type"""
        return self._smart_retry_with_fallback("type", text, **kwargs)

    def press(self, key, **kwargs):
        """Wrap press"""
        return self._smart_retry_with_fallback("press", key, **kwargs)

    def check(self, **kwargs):
        """Wrap check"""
        return self._smart_retry_with_fallback("check", None, **kwargs)

    def uncheck(self, **kwargs):
        """Wrap uncheck"""
        return self._smart_retry_with_fallback("uncheck", None, **kwargs)

    def select_option(self, value=None, **kwargs):
        """Wrap select_option"""
        return self._smart_retry_with_fallback("select_option", value, **kwargs)

    def hover(self, **kwargs):
        """Wrap hover"""
        return self._smart_retry_with_fallback("hover", None, **kwargs)

    def text_content(self, **kwargs):
        """Wrap text_content"""
        return self._smart_retry_with_fallback("text_content", None, **kwargs)

    def is_visible(self, **kwargs):
        """Wrap is_visible"""
        return self._smart_retry_with_fallback("is_visible", None, **kwargs)

    def filter(self, **kwargs):
        """Wrap filter"""
        new_locator = self._locator.filter(**kwargs)
        selector_info = {
            'method': 'filter',
            'args': [],
            'kwargs': kwargs,
            'parent': self
        }

        return self._skyramp_page.new_skyramp_playwright_locator(new_locator, selector_info)

    def locator(self, selector, **kwargs):
        """Wrap locator"""
        new_locator = self._locator.locator(selector, **kwargs)
        selector_info = {
            'method': 'locator',
            'args': [selector],
            'kwargs': kwargs,
            'parent': self
        }

        return self._skyramp_page.new_skyramp_playwright_locator(new_locator, selector_info)

    def get_by_role(self, role, **kwargs):
        """Create a smart locator by role with LLM fallback."""
        original_locator = self._locator.get_by_role(role, **kwargs)
        selector_info = {
            'method': 'get_by_role',
            'args': [role],
            'kwargs': kwargs,
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_text(self, text, **kwargs):
        """Create a smart locator by text with LLM fallback."""
        original_locator = self._locator.get_by_text(text, **kwargs)
        selector_info = {
            'method': 'get_by_text',
            'args': [text],
            'kwargs': kwargs,
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_label(self, label,**kwargs):
        """Create a smart locator by label with LLM fallback."""
        original_locator = self._locator.get_by_label(label, **kwargs)
        selector_info = {
            'method': 'get_by_label',
            'args': [label],
            'kwargs': kwargs,
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_test_id(self, test_id):
        """Create a smart locator by test ID with LLM fallback."""
        original_locator = self._locator.get_by_test_id(test_id)
        selector_info = {
            'method': 'get_by_test_id',
            'args': [test_id],
            'kwargs': {},
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_title(self, title, **kwargs):
        """Create a smart locator by title with LLM fallback."""
        original_locator = self._locator.get_by_title(title, **kwargs)
        selector_info = {
            'method': 'get_by_title',
            'args': [title],
            'kwargs': kwargs,
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_placeholder(self, placeholder, **kwargs):
        """Create a smart locator by placeholder with LLM fallback."""
        original_locator = self._locator.get_by_placeholder(placeholder, **kwargs)
        selector_info = {
            'method': 'get_by_placeholder',
            'args': [placeholder],
            'kwargs': kwargs,
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_alt_text(self, alt, **kwargs):
        """Create a smart locator by alt text with LLM fallback."""
        original_locator = self._locator.get_by_alt_text(alt, **kwargs)
        selector_info = {
            'method': 'get_by_alt_text',
            'args': [alt],
            'kwargs': kwargs,
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    def nth(self, index):
        """Wrap nth and return a new locator"""
        original_locator = self._locator.nth(index)
        selector_info = {
            'method': 'nth',
            'args': [index],
            'kwargs': {},
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    @property
    def first(self):
        """Wrap first and return a new locator"""
        original_locator = self._locator.first
        selector_info = {
            'method': 'first',
            'args': [],
            'kwargs': {},
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    @property
    def last(self):
        """Wrap first and return a new locator"""
        original_locator = self._locator.last
        selector_info = {
            'method': 'last',
            'args': [],
            'kwargs': {},
            'parent': self
        }
        return self._skyramp_page.new_skyramp_playwright_locator(original_locator, selector_info)

    def unwrap(self):
        """Return original playwright locator"""
        return self._locator

    @property
    def page(self):
        """Return underlying playwright page"""
        return self._skyramp_page.page

    def wait(self, t=DEFAULT_WAIT_FOR_TIMEOUT):
        """Helper for page.wait_for_timeout"""
        debug(f'    wait for {t}')
        return self._skyramp_page.page.wait_for_timeout(t)

    def __getattr__(self, name):
        """Forward other method calls to the original locator."""
        return getattr(self._locator, name)


class SkyrampPlaywrightPage:
    """
    Intelligent wrapper for Playwright Page with LLM-powered selector improvement.
    """
    def __init__(self, page):
        self._page = page
        self._locators = []
        self._llm_choices = []

        check_for_update("python")

    def unwrap(self):
        """Return original playwright page"""
        return self._page

    @property
    def page(self):
        """ return original playwright page """
        return self._page

    def _push_locator(self, locator):
        self._locators.append(locator)

    def _get_last_locator(self):
        if len(self._locators) == 0:
            return None

        return self._locators[-1]

    def new_skyramp_playwright_locator(self, original_locator, selector_info):
        """ create a skyramp locator that wraps playwright locator """
        prev_locator = self._get_last_locator()
        new_locator = SkyrampPlaywrightLocator(self, original_locator,
                                               prev_locator, selector_info)
        if selector_info.get("parent", None) is not None:
            self._push_locator(new_locator)
        return new_locator

    def locator(self, selector: str, **kwargs) -> SkyrampPlaywrightLocator:
        """Create a smart locator with LLM fallback."""
        original_locator = self._page.locator(selector, **kwargs)
        selector_info = {
            'method': 'locator',
            'args': [selector],
            'kwargs': kwargs
        }
        return self.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_role(self, role: str, **kwargs) -> SkyrampPlaywrightLocator:
        """Create a smart locator by role with LLM fallback."""
        original_locator = self._page.get_by_role(role, **kwargs)
        selector_info = {
            'method': 'get_by_role',
            'args': [role],
            'kwargs': kwargs
        }
        return self.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_text(self, text: str, **kwargs) -> SkyrampPlaywrightLocator:
        """Create a smart locator by text with LLM fallback."""
        original_locator = self._page.get_by_text(text, **kwargs)
        selector_info = {
            'method': 'get_by_text',
            'args': [text],
            'kwargs': kwargs
        }
        return self.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_label(self, label: str, **kwargs) -> SkyrampPlaywrightLocator:
        """Create a smart locator by label with LLM fallback."""
        original_locator = self._page.get_by_label(label, **kwargs)
        selector_info = {
            'method': 'get_by_label',
            'args': [label],
            'kwargs': kwargs
        }
        return self.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_test_id(self, test_id: str) -> SkyrampPlaywrightLocator:
        """Create a smart locator by test ID with LLM fallback."""
        original_locator = self._page.get_by_test_id(test_id)
        selector_info = {
            'method': 'get_by_test_id',
            'args': [test_id],
            'kwargs': {}
        }
        return self.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_title(self, title: str, **kwargs) -> SkyrampPlaywrightLocator:
        """Create a smart locator by title with LLM fallback."""
        original_locator = self._page.get_by_title(title, **kwargs)
        selector_info = {
            'method': 'get_by_title',
            'args': [title],
            'kwargs': kwargs
        }
        return self.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_placeholder(self, placeholder: str, **kwargs) -> SkyrampPlaywrightLocator:
        """Create a smart locator by placeholder with LLM fallback."""
        original_locator = self._page.get_by_placeholder(placeholder, **kwargs)
        selector_info = {
            'method': 'get_by_placeholder',
            'args': [placeholder],
            'kwargs': kwargs
        }
        return self.new_skyramp_playwright_locator(original_locator, selector_info)

    def get_by_alt_text(self, alt: str, **kwargs) -> SkyrampPlaywrightLocator:
        """Create a smart locator by alt text with LLM fallback."""
        original_locator = self._page.get_by_alt_text(alt, **kwargs)
        selector_info = {
            'method': 'get_by_alt_text',
            'args': [alt],
            'kwargs': kwargs
        }
        return self.new_skyramp_playwright_locator(original_locator, selector_info)

    def goto(self, url, **kwargs):
        """Navigate to url"""
        transformed_url = transform_url_for_docker(url)
        result = self._page.goto(transformed_url, **kwargs)
        content = self._page.content()
        if has_javascript(content):
            debug(f'javacript download detected when visiting {self._page.url}')
            debug('  wait for sometime for potential hydration')
            self._page.wait_for_timeout(DEFAULT_WAIT_FOR_TIMEOUT)
        else:
            debug(f'javascript not detected when visiting {self._page.url}')

        return result

    def expect_response(self, param, **kwargs):
        """ Wrap around expect_response with longer timeout """
        if kwargs is None or len(kwargs) == 0:
            kwargs = {"timeout": 30000}
        else:
            kwargs["timeout"] = 30000

        return self._page.expect_response(param, **kwargs)

    def add_llm_choices(self, original_locator, new_locator, stack):
        """Store selector chosen by llm for later report"""
        self._llm_choices.append({
            "original": str(original_locator),
            "new": str(new_locator),
            "stack": parse_error_stack(stack),
        })

    def get_llm_choices(self):
        """Get selectors chosen by llm"""
        return self._llm_choices

    def has_llm_choices(self):
        """Check is there are any selectors chosen by llm"""
        return len(self._llm_choices) != 0

    def check_navigation(self, original, result):
        """Check is page navigation happened"""
        new_url = self._page.url
        if new_url != original:
            debug(f'page navigation to {new_url} detected, wait a bit')
            self._page.wait_for_timeout(DEFAULT_WAIT_FOR_TIMEOUT)

        return result


    def clear_selector_cache(self):
        """Clear the cached selector improvements."""
        _selector_cache.clear()

    def __getattr__(self, name):
        """Forward other method calls to the original page."""
        return getattr(self._page, name)


# Convenience function for easy integration
def new_skyramp_playwright_page(page) -> SkyrampPlaywrightPage:
    """
    Wrap a Playwright page with intelligent selector improvement.
    
    Args:
        page: Original Playwright page object
    
    Returns:
        SkyrampPlaywrightPage with LLM-powered selector improvement
        
    Example:
        from playwright.sync_api import sync_playwright
        from skyramp.smart_playwright import wrap_playwright_page
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Wrap the page for intelligent selector improvement
            smart_page = wrap_playwright_page(page)
            
            # Use it like a normal page - fallback to LLM if selectors fail
            smart_page.goto("https://example.com")
            smart_page.get_by_role("button", name="Submit").click()
    """
    return SkyrampPlaywrightPage(page)

def expect(obj):
    """
    for skyramp locators, unwrap and execute,
    otherwise execute with playwright expect
    """
    if isinstance(obj, SkyrampPlaywrightLocator):
        return playwright_expect(obj.unwrap())
    if isinstance(obj, SkyrampPlaywrightPage):
        return playwright_expect(obj.unwrap())
    return playwright_expect(obj)
