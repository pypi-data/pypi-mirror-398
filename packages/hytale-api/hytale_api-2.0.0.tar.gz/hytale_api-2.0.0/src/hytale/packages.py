from .http import get
from .models.package import Package


def get_packages() -> dict[str, Package]:
    """Get all the current store packages.

    Returns:
        dict[str, Package]: A dictionary mapping package names to Package objects.
    """
    data = get("/packages", "store.")

    for pkg_dict in data.values():
        if "class" in pkg_dict:
            pkg_dict["class_"] = pkg_dict.pop("class")  # class is a python keyword

    return {key: Package.from_dict(pkg_dict) for key, pkg_dict in data.items()}
