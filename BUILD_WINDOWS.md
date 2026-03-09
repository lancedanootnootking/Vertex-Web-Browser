# Building Windows EXE

## Option 1: GitHub Actions (Recommended)
1. Push your code to GitHub
2. The workflow in `.github/workflows/build-windows.yml` will automatically build the Windows EXE
3. Download the artifact from the Actions tab

## Option 2: Windows Machine
1. Copy the project to a Windows machine
2. Install Python 3.12 from python.org
3. Run:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   pyinstaller --onefile --windowed --name="Vertex Browser" --icon="Vertex Browser.icns" main.py
   ```

## Option 3: Docker with Wine
1. Install Docker Desktop
2. Run: `chmod +x build-windows.sh && ./build-windows.sh`

## Option 4: Cloud Build Services
- Use Replit, CodeSandbox, or other cloud IDEs with Windows environment
- Upload project and run PyInstaller commands

## Notes
- PyQt6 Windows binaries are larger than macOS
- Windows EXE will include all dependencies (~150-200MB)
- Test on Windows for compatibility issues
