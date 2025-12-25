# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Optional, Tuple

# Core Source imports
from core_utils_base.formatting_utils import DEFAULT_LINE_SIZE, get_title, get_title_line

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                             Useful methods for comments                                              #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_lengths(
    max_len: int = DEFAULT_LINE_SIZE,
    len_imports: Optional[int] = None,
    len_module: Optional[int] = None,
    len_group: Optional[int] = None,
) -> Tuple[int, int, int]:
    """Line length for each type of comment.

    Args:
        max_len (int): Default line length.
        len_imports (Optional[int]): Line length used for the title "imports".
        len_module (Optional[int]): Line length used for the main title of the module.
        len_group (Optional[int]): Line length used for the title of a class method group.

    """
    _len_imports = len_imports or max_len
    _len_module = len_module or max_len
    _len_group = (len_group or max_len) - 20
    return _len_imports, _len_module, _len_group


def print_common(max_len: int = DEFAULT_LINE_SIZE, len_imports: Optional[int] = None, len_module: Optional[int] = None):
    """Output example:
        print_common(max_len=80)

    # ───────────────────────────────── imports ────────────────────────────────── #

    # ──────────────────────────────────────────────────────────────────────────── #
    #       specifies all modules that shall be loaded and imported into the       #
    #            current namespace when we use 'from package import *'             #
    # ──────────────────────────────────────────────────────────────────────────── #

    """
    _len_imports, _len_module, _ = get_lengths(max_len=max_len, len_imports=len_imports, len_module=len_module)
    print("\n" + get_title_line(title="imports", max_len=_len_imports))
    print(
        "\n"
        + get_title(
            title=[
                "specifies all modules that shall be loaded and imported into the",
                "current namespace when we use 'from package import *'",
            ],
            max_len=_len_module,
        )
    )


def print_all_comment_types(
    title: str,
    max_len: int = DEFAULT_LINE_SIZE,
    len_module: Optional[int] = None,
    len_group: Optional[int] = None,
):
    """Output example:
        print_all_comment_types(title="Configuration Factory", max_len=80)

    # ────────────────────────── Configuration Factory ─────────────────────────── #

    # ──────────────────────────────────────────────────────────────────────────── #
    #                            Configuration Factory                             #
    # ──────────────────────────────────────────────────────────────────────────── #

    # ----------------------------------------------------------
    #                   Configuration Factory
    # ----------------------------------------------------------

    # ----------------- Configuration Factory ------------------

    # ---------------- Configuration Factory ----------------- #

    # ──────────────── Configuration Factory ───────────────── #

    """
    _, _len_module, _len_group = get_lengths(max_len=max_len, len_module=len_module, len_group=len_group)
    print("\n" + get_title_line(title=title, max_len=_len_module))
    print("\n" + get_title(title=title, max_len=_len_module))
    print("\n" + get_title(title=title, print_char="-", with_end=False, max_len=_len_group))
    print("\n" + get_title_line(title=title, print_char="-", with_end=False, max_len=_len_group))
    print("\n" + get_title_line(title=title, print_char="-", max_len=_len_group))
    print("\n" + get_title_line(title=title, max_len=_len_group))


# ───────────────────────────────────────────── Python script execution ────────────────────────────────────────────── #

if __name__ == "__main__":
    print_common()
    print_all_comment_types(title="")
