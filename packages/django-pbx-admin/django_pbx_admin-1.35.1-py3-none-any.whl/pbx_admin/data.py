from dataclasses import dataclass

from django_stubs_ext import StrOrPromise


@dataclass
class MenuItem:
    url: StrOrPromise
    name: StrOrPromise
    extra_html: StrOrPromise = ""
