from nicegui import ui
from theme import layout
import state

def create():
    @ui.page('/dashboard')
    async def dashboard_page():
        
        async def refresh_stats():
            success, msg = await state.db.fetch_from_server()
            
            if not success:
                ui.notify(f"Offline: {msg}", color='warning')

            products = state.db.products
            history = state.db.history

            total_skus = len(products)
            
            total_items = sum(p['qty'] for p in products)
            low_stock_count = sum(1 for p in products if p['status'] != 'OK')
            deliveries_count = sum(1 for h in history if h['qty_change'] > 0)
            dispatches_count = sum(1 for h in history if h['qty_change'] < 0)

            label_products.set_text(str(total_skus))
            label_deliveries.set_text(str(deliveries_count))
            label_dispatches.set_text(str(dispatches_count))
            label_alerts.set_text(str(low_stock_count))
            
            if low_stock_count > 0:
                icon_alerts.props('color=red')
            else:
                icon_alerts.props('color=green')

        with layout('Pulpit Główny'):

            with ui.grid(columns=3).classes('w-full gap-4'):
                def stat_card(title, initial_value, icon_name, color):
                    with ui.card().classes(f'border-l-4 border-{color} w-full'):
                        with ui.row().classes('items-center gap-4'):
                            icon_obj = ui.icon(icon_name, size='3em', color=color)
                            with ui.column().classes('gap-0'):
                                ui.label(title).classes('text-gray-500 text-sm')
                                val_label = ui.label(initial_value).classes('text-2xl font-bold')
                    return val_label, icon_obj
                
                label_products, _ = stat_card('Pozycje w magazynie', '...', 'inventory', 'blue')
                label_deliveries, _ = stat_card('Ilość Dostaw (Hist)', '...', 'local_shipping', 'green')
                label_dispatches, _ = stat_card('Ilość Wydań (Hist)', '...', 'shopping_cart_checkout', 'orange')
                label_alerts, icon_alerts = stat_card('Niski stan / Braki', '...', 'warning', 'orange')

            ui.separator().classes('my-6')
            
            ui.label('Szybkie Akcje').classes('text-lg font-bold mb-2')
            with ui.row():
                ui.button('Wydanie Towaru', icon='outbox', color='red').classes('w-48 h-16')
                ui.button('Przyjęcie Towaru', icon='move_to_inbox', color='green').classes('w-48 h-16')

        ui.timer(0.1, refresh_stats, once=True)