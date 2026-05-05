import sys
import traceback

print("=" * 50)
print("Starting test...")
print("=" * 50)

try:
    print("1. Importing sys... OK")
    
    print("2. Importing os...")
    import os
    print("   OK")
    
    print("3. Importing PyQt6...")
    from PyQt6.QtWidgets import QApplication, QMainWindow
    print("   OK")
    
    print("4. Importing modules...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from modules.login_tab import LoginTab
    print("   OK")
    
    print("5. Creating app...")
    app = QApplication(sys.argv)
    print("   OK")
    
    print("6. Creating window...")
    window = QMainWindow()
    window.setWindowTitle("Test")
    window.resize(400, 300)
    print("   OK")
    
    print("7. Showing window...")
    window.show()
    print("   OK")
    
    print("8. Starting event loop...")
    sys.exit(app.exec())
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTraceback:")
    traceback.print_exc()
    input("\nPress Enter to exit...")
