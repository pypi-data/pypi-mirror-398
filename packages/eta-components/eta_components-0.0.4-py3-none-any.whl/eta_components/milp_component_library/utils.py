import warnings


class DeprecatedClassMeta(type):
    def __new__(cls, name, bases, classdict, *args, **kwargs):
        alias = classdict.get("_DeprecatedClassMeta__alias")

        if alias is not None:

            def new(cls, *args, **kwargs):
                alias = cls._DeprecatedClassMeta__alias

                if alias is not None:
                    warnings.warn(
                        f"{cls.__name__} has been renamed to {alias.__name__}, the alias will be removed in the future",
                        DeprecationWarning,
                        stacklevel=2,
                    )

                return alias(*args, **kwargs)

            classdict["__new__"] = new
            classdict["_DeprecatedClassMeta__alias"] = alias

        fixed_bases = []

        for b in bases:
            alias = getattr(b, "_DeprecatedClassMeta__alias", None)

            if alias is not None:
                warnings.warn(
                    f"{b.__name__} has been renamed to {alias.__name__}, the alias will be removed in the future",
                    DeprecationWarning,
                    stacklevel=2,
                )

            # Avoid duplicate base classes.
            base = alias or b
            if base not in fixed_bases:
                fixed_bases.append(base)

        fixed_bases = tuple(fixed_bases)

        # noinspection PyArgumentList
        return super().__new__(cls, name, fixed_bases, classdict, *args, **kwargs)

    def __instancecheck__(cls, instance):
        return any(cls.__subclasscheck__(c) for c in {type(instance), instance.__class__})

    def __subclasscheck__(cls, subclass):
        if subclass is cls:
            return True
        return issubclass(subclass, cls._DeprecatedClassMeta__alias)


class DeprecationHelper:
    def __init__(self, new_target, message: str):
        self.new_target = new_target
        self.message = message

    def _warn(self):
        warnings.warn(self.message, stacklevel=1)

    def __call__(self, *args, **kwargs):
        self._warn()
        return self.new_target(*args, **kwargs)

    def __getattr__(self, attr):
        self._warn()
        return getattr(self.new_target, attr)
