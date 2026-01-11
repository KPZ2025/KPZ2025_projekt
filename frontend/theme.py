from nicegui import ui
from contextlib import contextmanager
from state import session_info, logout

@contextmanager
def layout(page_title):
    if not session_info['user']:
        ui.navigate.to('/')
        yield
        return

    with ui.header().classes('bg-slate-800 text-white items-center justify-between'):
        with ui.row().classes('items-center'):
            ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
            ui.label('System Apokalipsa').classes('text-xl font-bold')
        
        with ui.row().classes('items-center gap-4'):
            ui.label(f"Zalogowany: {session_info['user']}").classes('text-sm opacity-80')
            ui.button(icon='logout', on_click=logout).props('flat round color=white')

    with ui.left_drawer(value=True).classes('bg-slate-100') as left_drawer:
        ui.label('MENU').classes('text-gray-500 text-xs font-bold mb-2 mt-2 ml-4')
        
        with ui.column().classes('w-full gap-0'):
            def nav_btn(label, icon, target):
                ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(target)) \
                    .props('flat align=left').classes('w-full text-slate-700 hover:bg-slate-200')

            nav_btn('Pulpit', 'dashboard', '/dashboard')
            nav_btn('Magazyn', 'inventory_2', '/warehouse')
            nav_btn('Audyt Blockchain', 'verified_user', '#')
            nav_btn('Ustawienia', 'settings', '#')

    with ui.column().classes('w-full p-4'):
        ui.label(page_title).classes('text-2xl font-light mb-4 text-slate-700')
        yield