# import logging
# import urllib
# import functools
#
# from selenium.webdriver.remote.webdriver import WebDriver
#
# from python_agent.test_listener.state_tracker import StateTracker
#
#
# log = logging.getLogger(__name__)
#
#
# def identify_framework(frames):
#     for frame in frames:
#         if "pytest" in frame[1]:
#             return "pytest"
#         if "unittest" in frame[1]:
#             return "unittest"
#
#
# def is_test_equal_to_frame(framework, frame):
#     current_test_identifier = StateTracker().current_test_identifier
#     if not current_test_identifier:
#         return False
#     if framework == "pytest":
#         test_id = urllib.url2pathname(current_test_identifier.split("/")[-1])
#         file_name = frame[1].split("/")[-1] if frame[1] else ""
#         test_name = frame[3] if frame[3] else ""
#         return file_name + "::" + test_name == test_id
#     if framework == "unittest":
#         test_id = urllib.url2pathname(current_test_identifier.split("/")[-1])
#         file_name_test = frame[0].f_locals["self"].id() if frame[0] else ""
#         return file_name_test == test_id
#
#
# def new_execute(f):
#     @functools.wraps(f)
#     def wrapper(*args, **kwargs):
#         try:
#             import inspect
#             self = args[0]
#             frames = inspect.stack()
#             for index, frame in enumerate(frames):
#                 framework = identify_framework(frames)
#                 if is_test_equal_to_frame(framework, frame):
#                     params = {
#                         "sessionId": self.session_id,
#                         "cookie": {
#                             "name": config.TEST_IDENTIFIER,
#                             "value": StateTracker().current_test_identifier
#                         }
#                     }
#                     self.command_executor.execute("addCookie", params)
#         except Exception as e:
#             log.exception("failed to set cookie. cookie: %s. error: %s"
#                           % (StateTracker().current_test_identifier, str(e)))
#             print str(e)
#         return f(*args, **kwargs)
#     return wrapper
#
# WebDriver.execute = new_execute(WebDriver.execute)
