def info() -> str:
    return (
        "LangPy — Lexical layer for Python\n\n"
        "Write Python using human-language keywords.\n\n"
        "Supported languages:\n"
        "  .pyes  Spanish\n"
        "  .pypt  Portuguese\n"
        "  .pyfr  French\n\n"
        "Run `langpy --help` for usage."
    )


def help() -> str:
    return (
        "Usage:\n"
        "  langpy <file>\n"
        "  langpy --transpile <file>\n"
        "  langpy --output <out.py> <file>\n\n"
        "Options:\n"
        "  --help        Show this help message and exit\n"
        "  --version     Print package version and exit\n"
        "  --transpile   Transpile source and local LangPy imports to .py\n"
        "  --output      Transpile only input file to given output path\n"
        "  --force       Overwrite existing .py files (only with --transpile)\n\n"
        "Examples:\n"
        "  langpy main.pyes\n"
        "  langpy --transpile main.pypt\n"
        "  langpy --output build/main.py main.pyfr"
    )
