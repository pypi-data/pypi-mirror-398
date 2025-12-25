"""
Main entry point for pyWATS Client Application
"""

def main():
    """Launch the pyWATS client application"""
    from pywats_client.__main__ import main as client_main
    client_main()

if __name__ == "__main__":
    main()