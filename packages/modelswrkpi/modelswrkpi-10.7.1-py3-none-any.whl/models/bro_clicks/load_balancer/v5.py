import pandas as pd
from models.bro_clicks.initial_routes import InitialRoutes, ForeignInitialRoutes
from models.bro_clicks.load_balancer.v4 import LoadBalancerV4


class LoadBalancerV5(LoadBalancerV4):
    def __init__(self, *args, **kw):
        LoadBalancerV4.__init__(self, *args, **kw)
        self._model_class = ForeignInitialRoutes
        self._iin_schema = 'foreign_bins'
        self.version = 5

    def init_date(self, date, crm_id, reset_cap_count=True):
        sk = f'ui_{self._account_id}_clients'
        real_cap_space = self.get_processing_for_month(crm_id) if reset_cap_count else None

        qry = f"""
                SELECT '{date}'::date as date,  b.crm_id,  a.mid_id,   b.gateway_id, b.step, a.processor,                  
                        coalesce(e.approved, 0)  approved,  
                        coalesce(e.approved,0) initial_count, 
                        c.dly_initial_cap,  
                        b.minimum_price, 
                        coalesce(e.declined, 0) declined, 
                        d.approval_rate,  
                        c.dly_min_approval_rate, 
                        array_to_string(c.pr_exclude_cc_types,  ',') exclude_cc_types , 
                        c.date_added, 
                        c.enable_tds, 
                        array_to_string(c.tds_exclude_cc_types, ',') tds_exclude_cc_types,  
                        c.enabled, 
                        c.enable_initials, 
                        c.monthly_initial_cap, 
                        c.priority, 
                        c.router_id,  
                        d.router_id as cur_router_id,                                                
                        c.allow_prepaid, 
                        c.allow_non_prepaid,
                        d.soft_cap_alerted, 
                        d.initial_count_mtd  as  prev_mtd                      

                FROM {sk}.mids a 
                LEFT JOIN {sk}.steps b on b.mid_id = a.mid_id 
                LEFT JOIN {sk}.gateway_settings c on c.gateway_id = b.gateway_id and c.crm_id = b.crm_id
                LEFT JOIN {self.schema}.{self.table} d on c.gateway_id =d.gateway_id and c.crm_id = d.crm_id and  b.step = d.step and '{date}'::date =d.date
                LEFT JOIN (select  crm_id, gateway_id, coalesce(sum(declined),  0) declined,   coalesce(sum(approved), 0) approved 
                            from {self.schema}.conversions where  coalesce(test, 0) <>  1 and time_stamp::date =  '{date}'::date group by crm_id, gateway_id
                            ) e on  e.gateway_id =c.gateway_id and e.crm_id=c.crm_id
                where (b.close_date is  null or b.close_date >'{self.today()}')
                    and b.crm_id = '{crm_id}'
                    and b.gateway_id is not null
                    and a.processor not ilike '%%virtual%%'
                    and b.gateway_id::int <> 1
                    and a.processor != 'FlexCharge'                    

            """

        try:

            # if crm_id != 'crm_ll_2':
            #

            # print(qry)
            #     print('break')
            up = pd.read_sql(qry, self.engine)

            up = up.sort_values('step').drop_duplicates(['gateway_id', 'cur_router_id'], keep='first')
            up = up.loc[~up.router_id.isna()]
            up = up.explode('router_id')

            # delete  changes to routers
            del_gt_msk = (up.router_id != up.cur_router_id) & (
                up.gateway_id.isin(up.loc[~up.cur_router_id.isna()].gateway_id.unique()))
            del_gtys = up.loc[del_gt_msk].gateway_id.tolist()

            up = up.loc[(~up.gateway_id.isin(del_gtys)) | (~up.cur_router_id.isna())]

            # delete  changes to routers
            del_gt_msk = (up.router_id != up.cur_router_id)
            del_gtys = up.loc[del_gt_msk].gateway_id.tolist()
            self.engine.execute(
                f"delete from {self.schema}.{self.table} where gateway_id::int = ANY(ARRAY{del_gtys}::int[]) and  crm_id='{crm_id}'")
            up = up.drop(columns='cur_router_id')
        except Exception as e:
            raise e
        if reset_cap_count:
            try:
                up = up.merge(real_cap_space, on=['gateway_id'], how='left')
                up.initial_count_mtd = up.initial_count_mtd.fillna(0)
                up.initial_count_mtd += up.initial_count

            except:
                up['initial_count_mtd'] = up.prev_mtd.fillna(0)
                up.initial_count_mtd = up.initial_count_mtd.fillna(0)

            drim = float(self.get_drim())
            up.dly_initial_cap = pd.np.floor((up.monthly_initial_cap - up.initial_count_mtd) / drim)
            up.loc[up.dly_initial_cap < 0, 'dly_initial_cap'] = 0

        up.dly_initial_cap = up.dly_initial_cap.fillna(11)
        up.dly_min_approval_rate = up.dly_min_approval_rate.fillna(30)
        up.declined = up.declined.fillna(0)
        up.approval_rate = up.approval_rate.fillna(0)
        up.soft_cap_alerted = up.soft_cap_alerted.fillna(False)
        up.drop('prev_mtd', axis=1, errors='ignore', inplace=True)
        up = up.drop_duplicates(['gateway_id', 'router_id'])
        # self.engine.execute(f'truncate {self.schema}.{self.table}')
        self.upsert(up.dropna())

    def gty_qry(self, crm_id, date, step, processor, cc_type=False, decs='', proc_excl=[], is_tds=None,
                is_prepaid=False, is_decline_salvage=False, **kw):
        p_ex = ''
        if proc_excl and len(proc_excl) and not processor:
            p_ex = f"and a.processor not ilike all(ARRAY{[f'%%{p}%%' for p in proc_excl]}::text[])"

        return f""" --LEFT HERE NEED TO GET MCC!
                     select a.gateway_id::int,  a.fill_pct,a.dly_initial_cap,priority,initial_count,  a.approval_rate, a.date_added, a.processor, a.mid_id, a.monthly_initial_cap, a.soft_cap_alerted, initial_count_mtd,b.mcc from {self.schema}.{self.table} a
                     inner join (select crm_id,  gateway_id,  mcc from ui_54407332_clients.steps ) b  on b.crm_id =  a.crm_id and  b.gateway_id=a.gateway_id
                     {"inner join (select crm_id, gateway_id where enable_decline_salvage) ds on ds.crm_id = a.crm_id and ds.gateway_id::int = a.gateway_id::int" if is_decline_salvage else "" }
                     inner join processing.cap c on a.mid_id = c.mid_id and a.step=c.step and a.processor=c.processor and c.monthly_available > 200
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
                                   {f"and allow_prepaid" if is_prepaid else ""}
                                   {f"and allow_non_prepaid" if not is_prepaid else ""}
                                   --and fill_pct < 1                         

                     --order by date_added desc, approval_rate desc, fill_pct asc limit 1
                       order by priority desc, date_added  desc, fill_pct, approval_rate desc, initial_count

                 """

