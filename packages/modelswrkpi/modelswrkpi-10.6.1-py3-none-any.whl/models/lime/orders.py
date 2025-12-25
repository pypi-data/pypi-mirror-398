from models.db import Db


class Orders(Db):
    def __init__(self, db, crm_id):
        Db.__init__(self, db, crm_id, 'orders')
        self.set_constraint('orders_pk', ['order_id'])

    def get_orders_by_customer(self, order_ids=False, customer_ids=False):
        qry = None
        if order_ids and len(order_ids) > 50:
            if not isinstance(order_ids, list):
                order_ids = [order_ids]
            qry = """
               select a.order_id from {s}.{t} as a
               inner join (select distinct(a.customer_id) as customer_id from {s}.{t} as a
                           inner join unnest(ARRAY{oids}::int[]) as b(order_id) on a.order_id = b.order_id
                    ) as b on b.customer_id = a.customer_id
               where a.customer_id <> 0
                       """.format(s=self.schema, t=self.table, r=self._append_relation(), oids=list(set(order_ids)))

        elif order_ids:
            if not isinstance(order_ids, list):
                order_ids = [order_ids]
            qry = """SELECT order_id FROM {r} 
            WHERE customer_id <> 0  AND customer_id in( select customer_id from {r} where order_id in({oids}))
            """.format(r=self._append_relation(), oids=self._make_list(set(order_ids)))

        elif customer_ids and len(customer_ids) > 500:
            qry = """select a.order_id from {s}.{t} as a
                     inner join unnest(ARRAY{cids}::int) as b(cid) on a.customer_id = b.cid
                       """.format(s=self.schema, t=self.table, r=self._append_relation(), cids=list(set(customer_ids)))
        elif customer_ids:
            qry = """SELECT order_id FROM {r} 
            WHERE customer_id <> 0 and customer_id in({cids})
            """.format(r=self._append_relation(), cids=self._make_list(set(customer_ids)))

        else:
            raise ValueError("you must pass either order_ids or customer_ids as a list or set")
        return[str(q[0]) for q in self.engine.execute(qry+""" AND order_id <> 0 ORDER BY order_id""")]


class EmployeeNotes(Db):
    def __init__(self, db, crm_id):
        Db.__init__(self, db, crm_id, 'employee_notes')
        self.set_constraint('employee_notes_pk', ['date_time', 'order_id', 'note_index'])


class SystemNotes(Db):
    def __init__(self, db, crm_id):
        Db.__init__(self, db, crm_id, 'system_notes')
        self.set_constraint('system_notes_pk', ['date_time', 'order_id', 'note_index'])