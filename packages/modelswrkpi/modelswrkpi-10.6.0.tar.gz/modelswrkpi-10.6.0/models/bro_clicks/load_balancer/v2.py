from models.bro_clicks.load_balancer.v1 import LoadBalancer
import pandas as pd


class LoadBalancerV2(LoadBalancer):
    def __init__(self, db, db_p, account_id='54407332', alert_call_back=False, **kwargs):
        LoadBalancer.__init__(self, db, db_p, account_id=account_id)
        self.alert_cb = alert_call_back

        self.sort_map = {
            # No optimization
            4: {'by': ['priority', 'date_added', 'fill_pct', 'approval_rate', 'initial_count'],
                'ascending': [False, False, True, False, True]}
        }

    def gty_qry(self, crm_id, date, step, processor, cc_type=False, decs='', proc_excl=[], is_tds=None, is_decline_salvage=False, **kw):
        p_ex = ''
        if proc_excl and len(proc_excl) and not processor:
            p_ex = f"and a.processor not ilike all(ARRAY{[f'%%{p}%%' for p in proc_excl]}::text[])"

        return f""" --LEFT HERE NEED TO GET MCC!
                     select a.gateway_id::int,  a.fill_pct,a.dly_initial_cap,priority,initial_count,  a.approval_rate, a.date_added, a.processor, a.mid_id, a.monthly_initial_cap, a.soft_cap_alerted, initial_count_mtd,b.mcc from {self.schema}.{self.table} a
                     inner join (select crm_id,  gateway_id,  mcc from ui_54407332_clients.steps ) b  on b.crm_id =  a.crm_id and  b.gateway_id=a.gateway_id
                      {"inner join (select crm_id, gateway_id where enable_decline_salvage) ds on ds.crm_id = a.crm_id and ds.gateway_id::int = a.gateway_id::int" if is_decline_salvage else "" }
                     inner join processing.cap c on a.mid_id = c.mid_id and a.step=c.step and a.processor=c.processor   and c.monthly_available > 200
                      {f"left join processing.cap_cc_type d on a.mid_id = d.mid_id and a.step= d.step  and a.processor = d.processor and d.cc_type = '{cc_type}' " if cc_type else ''}

                     where date = '{date}'::date and a.crm_id = '{crm_id}' and router_id = '{step if step in [1, 11] else 2}' and enabled and enable_initials
                                  {f"and a.processor = '{processor}'" if processor else ""}
                                   {f"and (exclude_cc_types is null or  exclude_cc_types::text  not ilike '%%{cc_type.lower()}%%')" if cc_type else ''}
                                   and (approval_rate > dly_min_approval_rate or(declined+initial_count<110))
                                   {'and (d.available_tc is null or d.available_tc >50)' if cc_type else ''}
                                   {decs}
                                   {p_ex}
                                   {f"and enable_tds = {bool(is_tds)}" if is_tds else ""}
                                   {f"and (tds_exclude_cc_types is null or tds_exclude_cc_types not ilike '%%{cc_type}%%')" if cc_type and is_tds else ""}
                                   --and fill_pct < 1                         
                     --order by date_added desc, approval_rate desc, fill_pct asc limit 1
                       order by priority desc, date_added  desc, fill_pct, approval_rate desc, initial_count

                 """

    def exclude_list(self, crm_id, step, click_id, alias='', c_token=''):
        if not c_token:
            c = 'absce'
        else:
            c = c_token
        decs = pd.read_sql(f"""SELECT  gateway_id, processor, approved  from {self.schema}.conversions 
                                where crm_id = '{crm_id}'
                                and time_stamp > (now() - INTERVAL '48 hours')::timestamp
                                and {f" c_token='{c}' " if c_token else f" click_id = '{click_id}' " } and coalesce(decline_reason, '') not ilike 'prepaid%%' """,

                           self.engine)

        whd = ""
        if len(decs):
            decs.gateway_id = decs.gateway_id.fillna(-1)
            decs.processor = decs.processor.fillna('')
            processors = decs.loc[decs.approved == 0].processor.astype(str).tolist()
            if len(decs) >= self._max_decline_attempts:
                raise Exception('declined due to too many attempts')
            p_break = []
            for p in processors:
                p_break.extend(p.split(' '))

            whd = f"""and {alias}gateway_id != all(ARRAY{decs.gateway_id.astype(int).tolist()}) 
                                 {f"and {alias}processor not ilike all(ARRAY{[f'%%{p}%%' for p in p_break]})" if len(p_break) else ""}"""

        return whd

    def next_gateway(self, crm_id, date, step, click_id='', processor=False, cc_type=None, recurse=0, decs=False,
                     proc_excl=[], is_tds=None,
                     **kwargs):
        try:
            decs = self.exclude_list(crm_id, step, click_id, alias='a.') if not decs else decs
        except Exception as e:
            return str(e)

        qry = self.gty_qry(crm_id, date, step, processor, cc_type, decs, proc_excl, is_tds=is_tds, **kwargs)
        # print(qry)
        res = None
        try:
            res = pd.read_sql(qry, self.engine)
        except Exception as e:
            print(str(e))
        if res is None or not len(res):
            if not decs:
                if not recurse and is_tds is not None:
                    return self.next_gateway(crm_id, date, step, click_id, processor, cc_type, recurse=recurse + 1,
                                             is_tds=not is_tds)
                elif recurse == 1:
                    self.init_date(date, crm_id)
                    return self.next_gateway(crm_id, date, step, click_id, processor, cc_type, recurse=recurse + 1,
                                             is_tds=is_tds)
                elif recurse == 2 and is_tds is not None:
                    return self.next_gateway(crm_id, date, step, click_id, processor, cc_type, recurse=recurse + 1,
                                             is_tds=None)

                return 'out of processing'
            else:
                return 'declined due to too many attempts'
        r = res.loc[res.fill_pct < 1]

        #  HARD CAP
        if not len(r):
            res = res.sort_values(['dly_initial_cap'], ascending=False).sort_values(['fill_pct'])

            def _get_aft_sc():
                nonlocal res
                if not len(res):
                    return 'out of processing'
                r2 = res.to_dict(orient='records')[0]
                if r2['initial_count_mtd'] >= r2['monthly_initial_cap']:
                    self.alert_cb('hard_cap_alert', crm_id=crm_id, gateway_id=r2['gateway_id'])
                    self.disable(crm_id=crm_id, gateway_id=r2['gateway_id'])
                    res = res.loc[res.gateway_id != r2['gateway_id']]
                    return _get_aft_sc()
                r2['is_tds'] = is_tds
                return r2

            if ~res.soft_cap_alerted.any():
                cnt = self.engine.execute(
                    f"""select count(*) from  {self.schema}.{self.table}  where date = '{date}'::date and crm_id = '{crm_id}' and router_id = '{step if step == 1 else 2}' and enabled and enable_initials and fill_pct<1""").scalar()
                if cnt == 0 or cnt is None:
                    self.alert_cb('soft_cap_alert', crm_id=crm_id)
                    self.set_soft_cap_alerted(crm_id)
            return _get_aft_sc()
        r = r.to_dict(orient='records')[0]
        r['is_tds'] = is_tds
        return r

    def increment_conversion(self, date, gateway_id, crm_id, approved, **kwargs):

        return self._increment_conversion(date, gateway_id, crm_id, approved, recurs_attempt=0, **kwargs)

