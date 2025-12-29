import sys
import os
from streamlit.web import cli as stcli

def main():
    """
    Entry point for the gmailsweep command.
    It locates the app.py file within the installed package and runs it via Streamlit.
    """
    # Locate the app.py file relative to this script
    package_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(package_dir, "app.py")
    
    # Construct the argument list mimicking 'streamlit run src/gmailsweep/app.py'
    sys.argv = ["streamlit", "run", app_path]
    
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
