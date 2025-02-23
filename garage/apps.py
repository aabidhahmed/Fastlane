from django.apps import AppConfig
import sys  # ✅ Import sys to check loading

class GarageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'garage'

    def ready(self):
        print("🚀 GarageConfig is loading...")  # ✅ Debug message
        sys.stdout.flush()  # ✅ Ensure it prints
        import garage.signals  # ✅ Ensure signals are loaded
