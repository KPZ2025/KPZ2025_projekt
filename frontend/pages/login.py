from nicegui import ui
from state import session_info

def create():
    @ui.page('/')
    def login_page():
        with ui.column().classes('w-full h-screen justify-center items-center bg-slate-900'):
            with ui.card().classes('w-96 p-8 items-center text-center animation-fade-in'):
                ui.icon('lock', size='4xl', color='slate-700').classes('mb-4')
                ui.label('SYSTEM ZABLOKOWANY').classes('text-2xl font-bold text-slate-800')
                ui.label('Przyłóż kartę RFID, aby odblokować').classes('text-gray-500 mb-8')

                def simulate_rfid():
                    ui.notify('Logowanie...', type='positive')
                    session_info['user'] = 'Jan Kowalski'

                    ui.timer(1.0, lambda: ui.navigate.to('/dashboard'), once=True)

                ui.button('SYMULUJ ZBLIŻENIE KARTY', on_click=simulate_rfid) \
                    .props('size=lg color=primary icon=nfc').classes('w-full')