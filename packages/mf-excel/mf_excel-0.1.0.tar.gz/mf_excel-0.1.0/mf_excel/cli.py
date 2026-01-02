from mf_excel.backend.app import app
from mf_excel.backend.services.config import settings
import threading


def start_flask():
    app.run(host=settings.HOST, port=settings.PORT, debug=False, use_reloader=False)


threading.Thread(target=start_flask, daemon=True).start()
