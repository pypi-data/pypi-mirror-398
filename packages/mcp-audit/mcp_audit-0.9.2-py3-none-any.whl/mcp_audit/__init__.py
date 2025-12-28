import warnings
warnings.warn("mcp-audit is deprecated. Install token-audit instead.", DeprecationWarning, stacklevel=2)
from token_audit import *
def main():
    print("\n⚠️  mcp-audit is deprecated. Use: pip install token-audit\n")
    from token_audit.cli import main as cli_main
    return cli_main()
