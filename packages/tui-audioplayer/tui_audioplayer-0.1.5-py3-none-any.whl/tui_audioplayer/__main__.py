from pathlib import Path
print('Running' if __name__ == '__main__' else 'Importing', Path(__file__).resolve())

if __name__ == "__main__":
    from .radioplayer import RadioPlayerApp

    app = RadioPlayerApp()
    app.run()