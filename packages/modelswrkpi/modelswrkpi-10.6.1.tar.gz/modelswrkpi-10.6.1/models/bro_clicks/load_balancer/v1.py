import random
from models.db import Db, pd
from calendar import monthrange
import datetime as dt
from models import config


class LoadBalancer(Db):
    _max_decline_attempts = 5
    def __init__(self, db, db_p, account_id='54407332', **kw):
        Db.__init__(self, db, f"bro_clicks", 'load_balancer_2')
        self.set_constraint('load_balancer_2_pk', ['date', 'crm_id', 'gateway_id', 'router_id'])
        self.db_p = db_p
        self._account_id = account_id
        self.is_cc_type_cap_split = False

    @staticmethod
    def set_max_decline_attempts(attempts):
        LoadBalancer._max_decline_attempts = int(attempts)
        print(f'max decline attempts set to {attempts}', flush=True)

    @staticmethod
    def now():
        return dt.datetime.now() - dt.timedelta(hours=config.timeOffset)

    @staticmethod
    def today():
        return LoadBalancer.now().date()

    @staticmethod
    def get_first_om():
        now = LoadBalancer.now()
        return dt.datetime(year=now.year, month=now.month, day=1)

    @staticmethod
    def get_last_dom(now=False):
        now = now if now else LoadBalancer.now()
        weekday_of, last_day = monthrange(now.year, now.month)
        return last_day

    @staticmethod
    def get_drim():
        now = LoadBalancer.now()
        return LoadBalancer.get_last_dom() - now.day + 1

    def get_processing_for_month(self, crm_id):
        qry = f"""
                select b.gateway_id, 
                count(a.order_id)::int  initial_count_mtd 
                from  augmented_data.order_cycles a 
                inner join crm_global.orders  b on  a.order_id  = b.order_id and a.crm_id  =  b.crm_id   and a.crm_id = '{crm_id}'
                where a.time_stamp  > '{self.get_first_om()}' and a.time_stamp < '{self.today()}'::timestamp
                      and a.bc_inferred  = 0
                      and a.decline_reason is null
                      and b.is_test_cc::int <> '1'                                            
                group by b.gateway_id
        """

        # print(qry)
        return pd.read_sql(qry, self.db_p.engine).fillna(0)

    def get_processing_for_month_cc_type(self, crm_id):
        qry = f"""
                select
                gateway_id, 
                (initial_count_mtd - visa_count_mtd)::int as initial_count_mtd,
                visa_count_mtd
                from
                (select b.gateway_id, 
                        count(a.order_id)::int initial_count_mtd, 
                        (count(a.order_id) filter(where lower(cc_type) = 'visa'))::int visa_count_mtd 
                        from  augmented_data.order_cycles a 
                inner join crm_global.orders  b on  a.order_id  = b.order_id and a.crm_id  =  b.crm_id   and a.crm_id = '{crm_id}'
                where a.time_stamp  > '{self.get_first_om()}' and a.time_stamp < '{self.today()}'::timestamp
                      and a.bc_inferred  = 0
                      and a.decline_reason is null
                      and b.is_test_cc::int <> '1'                                            
                group by b.gateway_id) a
        """

        # print(qry)
        return pd.read_sql(qry, self.db_p.engine).fillna(0)

    def init_date(self, date, crm_id, reset_cap_count=True):
        sk = f'ui_{self._account_id}_clients'
        real_cap_space = self.get_processing_for_month(crm_id) if reset_cap_count else None

        qry = f"""
                SELECT '{date}'::date as date,  b.crm_id, a.mid_id,   b.gateway_id, b.step, a.processor,                  
                                                coalesce(e.approved, 0)  approved,  
                                                coalesce(e.approved,0) initial_count, 
                                                c.dly_initial_cap,  b.minimum_price, 
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

    def _increment_conversion(self, date, gateway_id, crm_id, approved, recurs_attempt=0, cc_type=None, **kwargs):
        if cc_type.lower() == 'visa':
            inc_p = '(visa_count +1)'
            m_inc_p = '(visa_count_mtd +1)'
            inc = 'visa_count'
            m_inc = 'visa_count_mtd'

        else:
            inc_p = '(initial_count +1)'
            m_inc_p = '(initial_count_mtd +1)'
            inc = 'initial_count'
            m_inc = 'initial_count_mtd'
        dnc = 'declined'
        dnc_p = '(declined + 1)'
        try:
            qry = f"""
                UPDATE {self.schema}.{self.table} 
                set   {f"{inc} ={inc_p},  approval_rate = ((initial_count+visa_count+1)::numeric / ({dnc}+(initial_count+visa_count+1)::numeric))*100, {m_inc} = {m_inc_p}" if approved
        else f"{dnc} ={dnc_p}, approval_rate = case when visa_count+initial_count>0 then ((visa_count+initial_count)::numeric / ({dnc_p}+visa_count+initial_count)::numeric * 100) else 0 end "
            }
                where crm_id = '{crm_id}' and date = '{date}'::date and gateway_id='{gateway_id}'                
                returning gateway_id  
            """

            if self.engine.execute(qry).scalar() is None and not recurs_attempt:
                self.init_date(date, crm_id)
                if not recurs_attempt:
                    return self._increment_conversion(date, gateway_id, crm_id, approved, recurs_attempt + 1)

        except Exception as e:
            print(e)
            return False
        return True

    def increment_conversion(self, date, gateway_id, crm_id, approved, **kwargs):
        return self._increment_conversion(date, gateway_id, crm_id, approved, recurs_attempt=0, **kwargs)

    def set_soft_cap_alerted(self, crm_id, cc_type=None, **kw):
        self.engine.execute(
            f"""Update {self.schema}.{self.table} 
            {"set visa_soft_cap_alerted=true" if cc_type.lower()=='visa' else "set  soft_cap_alerted=true"}
             where crm_id= '{crm_id}'""")

    def disable(self, crm_id, gateway_id, cc_type=None, **kw):
        set_clause = 'set enable_initials=false'
        if cc_type:
            if cc_type.lower() == 'visa':
                set_clause = ' set visa_enabled=false '
            elif cc_type:
                set_clause = ' set mc_enabled=false '

        self.engine.execute(
            f"""Update {self.schema}.{self.table} {set_clause} where crm_id= '{crm_id}' and gateway_id = '{int(gateway_id)}'""")
        if not cc_type:
            self.db_p.engine.execute(
            f"update ui_54407332_clients.gateway_settings set enable_initials=false where crm_id='{crm_id}' and gateway_id='{gateway_id}'")
