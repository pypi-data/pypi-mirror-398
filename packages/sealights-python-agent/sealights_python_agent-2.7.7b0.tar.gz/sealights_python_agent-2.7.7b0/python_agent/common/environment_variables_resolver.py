import os

from python_agent.common.constants import PREFIXES, MESSAGES_CANNOT_BE_NONE


class EnvironmentVariablesResolver(object):
    """
    This class resolves Sealights Related environment variables.
    """

    def __init__(self, int_properties, target_object):
        if target_object is None:
            raise Exception("'target_object'" + MESSAGES_CANNOT_BE_NONE)

        self.key_to_case_sensitive_key = {}
        self.int_properties = int_properties or []

        keys = dir(target_object)
        for case_sensitive_key in keys:
            # Windows have upper case keys, so we keep a mapping between upper key (ie, 'APPNAME') to case sensitive one (ie, 'appName').
            self.key_to_case_sensitive_key[case_sensitive_key.upper()] = (
                case_sensitive_key
            )

    def resolve(self):
        result = {}
        for prefix in PREFIXES:
            result.update(self.resolve_with_prefix(prefix))
        return result

    def resolve_with_prefix(self, prefix):
        result = {}
        for key in os.environ.keys():
            if key.lower().startswith(prefix.lower()):
                value = os.environ[key]
                uppercase_key = key[len(prefix) :].upper()
                if not self.key_to_case_sensitive_key.get(uppercase_key):
                    # could be an external environment variable that isn't in the target object
                    continue
                case_sensitive_key = self.key_to_case_sensitive_key[uppercase_key]
                if case_sensitive_key in self.int_properties:
                    value = int(value)
                # Update the underlying dictionary. We assume object use the case sensitive keys
                result.update({case_sensitive_key: value})
        return result
