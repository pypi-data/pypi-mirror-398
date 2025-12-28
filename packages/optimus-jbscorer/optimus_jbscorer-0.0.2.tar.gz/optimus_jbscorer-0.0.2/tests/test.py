import pkgutil
[m.name for m in pkgutil.iter_modules() if "optimus" in m.name]
