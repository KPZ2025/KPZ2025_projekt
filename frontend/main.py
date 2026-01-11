from nicegui import ui
from pages import login, dashboard, warehouse

login.create()
dashboard.create()
warehouse.create()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='System Apokalipsa', native=True, reload=False, language='pl')