from models.db import Db


class Orders(Db):
    def __init__(self, db):
        Db.__init__(self, db, 'crm_global', 'orders')
        self.set_constraint('orders_pk', ['crm_id', 'order_id', 'month_date'])

    def delete_crm(self, crm_id):
        self.engine.execute(f"Delete from {self.schema}.{self.table} where crm_id = '{crm_id}'")


class EmployeeNotes(Db):
    def __init__(self, db):
        Db.__init__(self, db, 'crm_global', 'employee_notes')
        self.set_constraint('employee_notes_pk', ['crm_id', 'date_time', 'native_order_id', 'note_index'])

    def delete_crm(self, crm_id):
        self.engine.execute(f"Delete from {self.schema}.{self.table} where crm_id = '{crm_id}'")


class SystemNotes(Db):
    def __init__(self, db):
        Db.__init__(self, db, 'crm_global', 'system_notes')
        self.set_constraint('system_notes_pk', ['crm_id', 'date_time', 'native_order_id', 'note_index'])

    def delete_crm(self, crm_id):
        self.engine.execute(f"Delete from {self.schema}.{self.table} where crm_id = '{crm_id}'")