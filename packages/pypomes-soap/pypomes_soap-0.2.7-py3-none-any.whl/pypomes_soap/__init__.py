from .soap_pomes import (
    soap_post, soap_post_zeep, soap_get_attachment,
    soap_get_dict, soap_get_cids, soap_build_envelope,
)

__all__ = [
    # soap_pomes
    "soap_post", "soap_post_zeep", "soap_get_attachment",
    "soap_get_dict", "soap_get_cids", "soap_build_envelope",
]

from importlib.metadata import version
__version__ = version("pypomes_soap")
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())
