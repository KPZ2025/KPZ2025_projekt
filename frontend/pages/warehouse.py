from nicegui import ui
from theme import layout
import state

def create():
    @ui.page('/warehouse')
    async def warehouse_page():
        with layout('Stan Magazynowy'):
                        
            async def refresh_data():
                ui.notify('Aktualizacja danych...', type='info', timeout=1000)
                
                success, msg = await state.db.fetch_from_server()
                
                if success:
                    table.rows = state.db.products
                    table.update()
                    filter_table() 
                else:
                    ui.notify(f"Błąd: {msg}", type='negative')

            def filter_table():
                val = search.value.lower()
                all_data = state.db.products
                
                if not val:
                    table.rows = all_data
                else:
                    table.rows = [
                        row for row in all_data 
                        if val in row['name'].lower()
                    ]
                table.update()

            with ui.row().classes('w-full justify-between items-center mb-4'):
                search = ui.input(placeholder='Szukaj produktu...', on_change=filter_table) \
                    .props('outlined dense icon=search').classes('w-64')
                
                with ui.row().classes('gap-2'):
                    ui.button(icon='refresh', on_click=refresh_data).props('flat round color=grey')
                    ui.button('Dodaj nowy', icon='add', color='primary')

            columns = [
                {'name': 'name',   'label': 'Nazwa Produktu', 'field': 'name',   'align': 'left', 'sortable': True},
                {'name': 'qty',    'label': 'Ilość',          'field': 'qty',    'sortable': True},
                {'name': 'unit',   'label': 'Jedn.',          'field': 'unit'},
                {'name': 'status', 'label': 'Status',         'field': 'status', 'sortable': True},
            ]

            table = ui.table(columns=columns, rows=state.db.products, row_key='id') \
                .classes('w-full') \
                .props('flat bordered')

            table.add_slot('body-cell-status', r'''
                <q-td :props="props">
                    <q-badge :color="props.value === 'OK' ? 'green' : (props.value === 'EMPTY' ? 'red' : 'orange')">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')
            
            ui.timer(0.1, refresh_data, once=True)