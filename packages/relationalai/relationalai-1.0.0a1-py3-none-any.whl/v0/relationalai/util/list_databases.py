
import v0.relationalai as rai
from tablescope import show

models = rai.Provider().list_models()

print(f"Showing {len(models)} models...")

show(models)
