"""Utility functions for CVE report aggregation."""

import subprocess

from .core.models import ScannerType


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH.

    Args:
        command: Name of the command to check.

    Returns:
        True if command exists, False otherwise.
    """
    try:
        subprocess.run(
            ["which", command],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_scanner_version(scanner: ScannerType) -> str:
    """Get the version of the scanner command.

    Args:
        scanner: Type of scanner ("grype", "trivy", or "both").

    Returns:
        Version string of the scanner, or "unknown" if unable to determine.
        For "both", returns a combined version string.
    """
    # Handle "both" scanner type by returning combined versions
    if scanner == "both":
        grype_version = _get_single_scanner_version("grype")
        trivy_version = _get_single_scanner_version("trivy")
        return f"grype {grype_version} + trivy {trivy_version}"

    return _get_single_scanner_version(scanner)


def _get_single_scanner_version(scanner: str) -> str:
    """Get the version of a single scanner command.

    Args:
        scanner: Name of the scanner ("grype" or "trivy").

    Returns:
        Version string of the scanner, or "unknown" if unable to determine.
    """
    try:
        result = subprocess.run(
            [scanner, "version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Parse the version output
        output = result.stdout.strip()

        # Extract version from output
        # Grype format: "Application: grype\nVersion: 0.100.0\n..."
        # Trivy format: "Version: 0.48.0\n..."
        for line in output.split("\n"):
            if "Version:" in line:
                version = line.split("Version:")[-1].strip()
                return version

        # If no "Version:" found, return first line
        return output.split("\n")[0] if output else "unknown"

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return "unknown"


# ASCII Logo
ASCII_LOGO = """
                                     **
                                    #-=#
                                   #-..=#
          #######                  *:..:*                  #######
        #########                 #==---+#                 ##########
      ###########      ###    *+=-*:...::*-=+*    ###      ###########
      ########         +:-=+++:...+-=::.:+...:+++=-:+#         ########
      ######          #=-==+=:...:=...--:=:...:=+==--#          #######
     #######           +...::....===-....--....::.:.+            ######
     #######           #*-:......-=..:===+-......:-*#            ######
     #######           #=::.......:-=--==:.......::-#            ######
     #######           #=........::......+-........-#            ######
     #######            =....:...-=::.:===+-.......=#            #######
    ########            *:.-----...=-=++=...==-:-..+             #######
   ########              +-.....==........=-.....-=#              ########
##########               #-...*+.:=......=#=.....:*                #########
##########               #=..-##+++:....-+##++-..-#                #########
 ##########               *-..-++=--::-:--=++-..:+                #########
     #######               +-.....-=---===.....=+                #######
     #######                #*=--=+=.::.-++--=+#         #       ######
     #######               #*:=:.-=:....:=-:::=+*****++*+*       ######
     #######              #=.:=.-...........-:=.:+.....:+        ######
     #######              +..:--=..........:+:-..=+-:-=*         ######
     #######              *:::..+..........=:..:.+-+#*           ######
      #######              #+--=-:........:-=-==*#*             #######
      ###########             *=-.:......:::+.-#           ############
       ##########             +.:=.::.:.-.-+-.:#           ###########
         ########             +...:+..:.=-.+:::#           #########
            #####             +.:.:*#++::::+===#            #####
                              *=+==*  *===+#
"""
