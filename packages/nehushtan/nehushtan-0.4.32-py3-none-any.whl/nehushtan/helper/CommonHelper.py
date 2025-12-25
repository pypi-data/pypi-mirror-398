import importlib
import platform
import secrets
import string
import uuid
import warnings
from typing import Union


class CommonHelper:

    @staticmethod
    def read_target(target: Union[dict, tuple, list, None], keychain: tuple, default: any = None):
        if not keychain:
            return default

        c_target, not_find = target.copy(), object()
        for i in keychain:
            if isinstance(c_target, dict):
                c_target = c_target.get(i, not_find)
            elif isinstance(c_target, (tuple, list)):
                c_len = len(c_target)
                if isinstance(i, int) and -c_len <= i <= c_len - 1:
                    c_target = c_target[i]
                else:
                    c_target = not_find
            else:
                break
        ret = default if c_target is not_find else c_target
        return ret

    @staticmethod
    def read_dictionary(dictionary: dict, keychain: tuple, default: any = None):
        warnings.warn('DEPRECATED use read_target()', DeprecationWarning)
        return CommonHelper.read_target(dictionary, keychain, default)

    @staticmethod
    def read_array(array: tuple, keychain: tuple, default: any = None):
        warnings.warn('DEPRECATED use read_target()', DeprecationWarning)
        return CommonHelper.read_target(array, keychain, default)

    @staticmethod
    def write_dictionary(target_dict: dict, keychain: tuple, value: any):
        _target = target_dict
        for index, _key in enumerate(keychain):
            _value = _target.get(_key)
            if not isinstance(_value, dict):
                # Since 0.2.14
                # a great change: all non-dict-type entry would be cleared as an empty dict
                _value = {}
            if index == len(keychain) - 1:
                _value = value
            _target[_key] = _value
            _target = _value

        return target_dict

    @staticmethod
    def class_with_class_path(module_path: str, class_name: str = None):
        """
        Since 0.1.22
        Since 0.2.19 When the class name is the same with PY file name, `class_name` is optional.

        For a/b.py -> class b
        class_with_namespace is like 'package.sub_package.class', 'a.b'
        class_name is 'b'
        return a CLASS definition, to be used with parameters to make instance
        """
        module = importlib.import_module(module_path)
        if class_name is None:
            class_name = module_path.split('.')[-1]
        a_class = getattr(module, class_name)
        return a_class

    @staticmethod
    def class_with_module_and_name(module_base: str, sub_module_name: str):
        """
        Since 0.1.21
        Since 0.2.19 It is not so convinence to use, consider using `class_with_class_path`.

        For a/b.py -> class b
        module_base is a
        sub_module_name is b
        """
        warnings.warn('Use `class_with_class_path` instead.')

        module = __import__(module_base)
        a_class = getattr(module, sub_module_name)
        return a_class

    @staticmethod
    def generate_random_uuid_hex():
        """
        Generate a random UUID.
        Since 0.4.15
        """
        return uuid.uuid4().hex

    @staticmethod
    def generate_a_password_string(
            length=8,
            least_special_ascii_letters=-1,
            least_lower_case_letters=1,
            least_upper_case_letters=1,
            least_digits=1,
    ):
        """
        Since 0.4.21
        Parameters named as `least_*` are following one rule:
        - if it is less than 0, this kind of chars would not appear;
        - else, the total appearence count in generated password would be no less than it.
        The sum of them (if less than 0, count it as 0) should not be longer than `length`.
        """

        options = ''
        if least_lower_case_letters < 0:
            least_lower_case_letters = 0
        else:
            options += string.ascii_lowercase

        if least_upper_case_letters < 0:
            least_upper_case_letters = 0
        else:
            options += string.ascii_uppercase

        if least_digits < 0:
            least_digits = 0
        else:
            options += string.digits

        if least_special_ascii_letters < 0:
            least_special_ascii_letters = 0
        else:
            special = r"!#()*,-.:;<>@[]^_{}"
            options += special

        if least_upper_case_letters + least_lower_case_letters + least_digits + least_special_ascii_letters > length:
            raise RuntimeError("generate_secure_password error: check parameters")

        password = "".join(secrets.choice(options) for i in range(length))

        total_s = 0
        total_l = 0
        total_u = 0
        total_d = 0
        for c in password:
            if c.islower():
                total_l += 1
            elif c.isupper():
                total_u += 1
            elif c.isdigit():
                total_d += 1
            else:
                total_s += 1

        if total_d >= least_digits \
                and total_u >= least_upper_case_letters \
                and total_l >= least_lower_case_letters \
                and total_s >= least_special_ascii_letters:
            return password

        return CommonHelper.generate_a_password_string(
            length=length,
            least_special_ascii_letters=least_special_ascii_letters,
            least_lower_case_letters=least_lower_case_letters,
            least_upper_case_letters=least_upper_case_letters,
            least_digits=least_digits,
        )

    @staticmethod
    def get_python_version():
        """
        Since 0.4.25
        """
        return platform.python_version()

    @staticmethod
    def is_python_version_at_least(big_version: int, middle_version: int = 0, small_version: int = 0):
        """
        Since 0.4.25
        """
        x = platform.python_version_tuple()
        return int(x[0]) >= big_version and int(x[1]) >= middle_version and int(x[2]) >= small_version
