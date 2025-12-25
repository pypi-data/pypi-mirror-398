import random
import pandas as pd
from models.bro_clicks.initial_routes import InitialRoutes
import datetime as dt
from threading import Thread, Lock
from copy import deepcopy
from models.bro_clicks.load_balancer.v2 import LoadBalancerV2


class LoadBalancerV3(LoadBalancerV2):
    routes = None
    _lock_static = Lock()
    _lock_static_route_get = Lock()
    _lock_model_replace = Lock()
    _last_updated = False
    _max_stale_seconds = random.randint(600, 1200)
    _route_schema = 'initial_route'

    def __init__(self, db, db_p, account_id='54407332', alert_call_back=False,
                 min_sample_count=500, optimise_pct=0.1,
                 randomise_pct=0.1, opt_type=4,
                 route_methods=['bank_conversion',
                                'iin_conversion',
                                'cc_type_conversion',
                                'cc_type_mcc_conversion',
                                'cc_type_cc_level_conversion',
                                ],
                 rewrite_route='initial_route',
                 iin_schema='bro_clicks',
                 **kwargs):

        is_new_route = False
        if rewrite_route:
            is_new_route = LoadBalancerV3._route_schema != rewrite_route
            LoadBalancerV3._route_schema = rewrite_route
        self._iin_schema = iin_schema
        self._model_class = InitialRoutes
        LoadBalancerV2.__init__(self, db, db_p, account_id=account_id, alert_call_back=alert_call_back, **kwargs)
        self._opt_arr = self._rand_arr(100, opt_type, {'key': 1, 'pct': randomise_pct}, {'key': 2, 'pct': optimise_pct})
        self._route_methods = route_methods
        self._opt_val = self.get_opt_type()
        print('opt val', self._opt_val, 'opt_type', opt_type)
        self._min_sample_count = min_sample_count
        self._t_get_bin = False
        self.iin_info = None
        self.is_iin_data = False
        self._t_get_route = False
        self.sort_map = {
            # Random
            1: {'by': ['fill_pct', 'initial_count'], 'ascending': [True, True]},
            # Pure conversion rate
            2: {'by': ['conversion_rate', 'initial_count'], 'ascending': [False, True]},
            # Hybrid optimization
            3: {'by': ['priority', 'conversion_rate', 'date_added', 'fill_pct', 'approval_rate', 'initial_count'],
                'ascending': [False, False, False, True, False, True]},
            # No optimization
            4: {'by': ['priority', 'date_added', 'fill_pct', 'approval_rate', 'initial_count'],
                'ascending': [False, False, True, False, True]}
        }
        self._join_on_del = False
        self.version = 3
        self._to_engine = self.db_p.engine.execution_options(postgresql_statement_timeout=2000)
        self.init_static(db_p.engine.execution_options(postgresql_statement_timeout=160*60), route_methods=route_methods, is_rewrite=is_new_route)
        self._bin_engine =  self.db_p.engine.execution_options(postgresql_statement_timeout=3900)
    def __del__(self):
        self._joiner(self._t_get_bin)
        # self._join_lb()

    @staticmethod
    def _rand_arr(length, default_val, *settings):
        a = []
        for s in settings:
            a += [s['key'] for i in range(int(length * s['pct']))]
        a += [default_val for i in range(length - len(a))]
        return a

    @staticmethod
    def _rand_val(arr):
        try:
            return arr[random.randint(0, 100)]
        except Exception as e:
            print(str(e))
        return 1

    def get_opt_type(self):
        return self._rand_val(self._opt_arr)

    @staticmethod
    def _joiner(*threads):
        for t in threads:
            try:
                t.join()
            except:
                pass

    def set_bin_info(self, cc_first_6):
        def _exec():
            nonlocal cc_first_6
            try:
                self.iin_info = pd.read_sql(f"select * from {self._iin_schema}.iin_data where bin='{cc_first_6}'",
                                            self._bin_engine.engine).astype(str).applymap(str.lower).replace({'none': None})
                if len(self.iin_info):
                    self.is_iin_data = True
                    self.iin_info = self.iin_info.to_dict(orient='records')[0]
                    if self.iin_info['bank_map'] is not None:
                        self.iin_info['bank'] = self.iin_info['bank_map']
                    if 'level' not in self.iin_info:
                        self.iin_info['level'] = None
                else:
                    self.iin_info = {}
            except Exception as e:
                print(f'LB V3 set bin error: str(e)', flush=True)
            self.iin_info['cc_first_6'] = cc_first_6

        self._t_get_bin = Thread(target=_exec)
        self._t_get_bin.start()

    @staticmethod
    def get_auto_routes(db, route_methods=[
        'bank_conversion',
        'iin_conversion',
        'cc_type_conversion',
        'cc_type_mcc_conversion',
        'cc_type_cc_level_conversion'
    ]):
        threads = []
        print('LBV3 get auto routes')
        if LoadBalancerV3._lock_static_route_get.acquire(timeout=0.001):
            rts = pd.DataFrame()
            _lock_rt = Lock()
            failed = False

            def _getter(table, where=''):
                nonlocal _lock_rt, rts, failed
                try:
                    raw_conn = db.engine.raw_connection()
                    try:
                        cursor = raw_conn.cursor()
                        cursor.execute("SET statement_timeout = 100000")
                        # Pandas can take the raw connection, but results vary by driver
                        _rt = pd.read_sql(f"""select * from {LoadBalancerV3._route_schema}.{table} {where}""", con=raw_conn)
                        raw_conn.commit()
                    except Exception as e:
                        print(f'Load Balancer route get query execution exception: {str(e)}')
                        raw_conn.rollback()
                        raw_conn.close()
                        failed = True
                        return

                    raw_conn.close()
                    _rt['mod_type'] = table
                except Exception as e:
                    print(f'Load Balancer route get exception: {str(e)}')
                    return
                _lock_rt.acquire()
                rts = rts.append(_rt)
                _lock_rt.release()

            for r in route_methods:
                threads.append(Thread(target=_getter, args=(r,)))
                threads[len(threads) - 1].start()
            LoadBalancerV3._joiner(*threads)
            LoadBalancerV3._lock_model_replace.acquire()
            if not failed:
                LoadBalancerV3.routes = rts.replace({'none': pd.np.nan})
            LoadBalancerV3._lock_model_replace.release()
            print('LBV3 get auto routes done')
            LoadBalancerV3._lock_static_route_get.release()
        else:
            print('LBV3 get auto routes static lock already acquired')

    def _join_lb(self):
        print('join lb')
        self._joiner(self._t_get_route)

    @staticmethod
    def async_del(lb):
        print('async del')
        lb._join_lb()

    @staticmethod
    def last_update_diff():
        lst = LoadBalancerV3._last_updated
        diff = (dt.datetime.now() - lst).total_seconds()
        return 50000 if lst is None else (dt.datetime.now() - lst).total_seconds()

    @staticmethod
    def check_stale_data():
        return LoadBalancerV3._max_stale_seconds < LoadBalancerV3.last_update_diff()

    def init_static(self, db, route_methods=['bank_conversion',
                                             'iin_conversion',
                                             'cc_type_conversion',
                                             'cc_type_mcc_conversion',
                                             'cc_type_cc_level_conversion'],
                    is_rewrite=False,
                    **kwargs):

        if LoadBalancerV3._lock_static.acquire(timeout=(0.001 if is_rewrite else 100)):

            lb = LoadBalancerV3
            try:
                if not lb._last_updated or lb.routes is None or not len(lb.routes) or LoadBalancerV3.check_stale_data() or 'cc_first_8' not in lb.columns:
                    print('init_static')
                    LoadBalancerV3._last_updated = dt.datetime.now()

                    self._t_get_route = Thread(target=lb.get_auto_routes, args=(db, route_methods))
                    self._t_get_route.start()
                else:
                    print('LBV3 cache is up to date')
            except Exception as e:
                print('LBV3 static init exception', str(e))

            LoadBalancerV3._lock_static.release()
        else:
            print('LBV3 init static lock already aquired')
        return LoadBalancerV3

    @staticmethod
    def update_static(cc_type, cc_first_6, processor, mcc, bank, level, mod_types=False):
        try:
            LoadBalancerV3._lock_static.acquire()
            if not mod_types:
                mod_types = list(LoadBalancerV3.routes.unique())
            if 'iin_conversion' in mod_types:
                pass
        except Exception as e:
            print(f'LB update static failed: {str(e)}')
        LoadBalancerV3._lock_static.release()

    def set_iin(self, **kwargs):

        if self.iin_info is None or not len(self.iin_info):
            self.iin_info = kwargs
        else:
            self.iin_info = {**self.iin_info, **kwargs}
        if 'approved' in self.iin_info:
            self.iin_info.pop('approved')
        if 'declined' in self.iin_info:
            self.iin_info.pop('declined')
        if 'conversion_rate' in self.iin_info:
            self.iin_info.pop('conversion_rate')
        if 'level' not in self.iin_info:
            self.iin_info['level'] = None

    def next_gateway(self, crm_id, date, step, click_id='', processor=False, cc_type=None, cc_first_6=False, recurse=0,
                     decs=False, ignore_user_exclusions=None,
                     proc_excl=[], is_tds=None, **kwargs):
        # opt vals 1 = random gateway constrained only by cap,  2 = optimised gateway constrained only by cap, 3 = Hybrid approach not ignoring settings, 4 = over cap (over-rides to that if needed)

        if ignore_user_exclusions is None:
            ignore_user_exclusions = self._opt_val < 2
        if cc_first_6:
            self.set_bin_info(cc_first_6)
        try:
            decs = self.exclude_list(crm_id, step, click_id, 'a.') if not decs else decs
        except Exception as e:
            return str(e)
        self._joiner(self._t_get_bin)

        try:
            qry = self.gty_qry(crm_id, date, step, processor, cc_type, decs, proc_excl=proc_excl, is_tds=is_tds, **kwargs)
            res = pd.read_sql(qry, self.engine)
            cc_type = cc_type.lower()
            if 'master' in cc_type:
                cc_type = 'master'
            if self._opt_val > 1 and self._opt_val < 4 and self.routes is not None:

                self._lock_model_replace.acquire()
                mod = self.routes if self.is_iin_data else self.routes.loc[
                    self.routes.mod_type.isin(['cc_type_conversion', 'cc_type_mcc_conversion'])]
                self._lock_model_replace.release()
                mod = mod.loc[(mod.approved + mod.declined >= self._min_sample_count)
                              & (mod.conversion_rate != 1)  # take out dummy gateways
                              & ((mod.cc_first_6 == cc_first_6) | (mod.cc_first_6.isna()))
                              & (((mod.cc_type == cc_type) | mod.cc_type.isna()) if 'cc_type' in mod.columns else (
                    True))
                              & (((mod.cc_level == str(self.iin_info['level'])) | (
                    mod.cc_level.isna())) if self.is_iin_data and 'level' in self.iin_info else (True))
                              & (((mod.bank == str(self.iin_info['bank'])) | (
                    mod.bank.isna())) if self.is_iin_data and 'bank' in self.iin_info else (True))
                              ]

                df_opt = mod.copy().sort_values('conversion_rate', ascending=False).reset_index(drop=True)
                df_opt['r_rank'] = df_opt.index + 1

                # Optimization Filters

                res = res.merge(df_opt.loc[df_opt.mod_type.isin(
                    ['cc_type_mcc_conversion', 'bank_conversion', 'iin_conversion'])],
                                on=['processor', 'mcc'],
                                how='left').append(res.merge(
                    df_opt.loc[df_opt.mod_type.isin(['cc_type_cc_level_conversion', 'cc_type_conversion'])].drop('mcc',
                                                                                                                 axis=1),
                    on=['processor'],
                    how='left')).drop_duplicates()
                # r_rank is Highest to lowest in terms of strength same as priority
                res.mod_type = res.mod_type.fillna('undefined').replace({'nan': 'undefined', '': 'undefined'})
                res.conversion_rate = res.conversion_rate.fillna(0)
            else:
                res['conversion_rate'] = 0
            res = res.sort_values(**self.sort_map[self._opt_val]).drop_duplicates('gateway_id', keep='first')
            res['cc_type'] = cc_type
            res['cc_first_6'] = cc_first_6
            self.set_iin(cc_first_6=cc_first_6, cc_type=cc_type)
        except Exception as e:
            print('LBV3 error', str(e))
            raise e

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
                                             is_tds=not is_tds)
                return 'out of processing'
            else:
                return 'declined due to too many attempts'

        r = res.loc[res.fill_pct < 1]
        if 'conversion_rate' not in res:
            res['conversion_rate'] = 0
        #  HARD CAP
        if not len(r):

            res = res.sort_values(['dly_initial_cap', 'conversion_rate'], ascending=[True, False]).sort_values(
                ['fill_pct'])

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
                self.set_iin(**r2)
                r2['is_tds'] = is_tds
                return r2

            # SOFT CAP
            if ~res.soft_cap_alerted.any():
                cnt = self.engine.execute(
                    f"""select count(*) from  {self.schema}.{self.table}  
                    where date = '{date}'::date and crm_id = '{crm_id}' 
                    and router_id = '{step if step == 1 else 2}' 
                    and enabled and enable_initials and fill_pct<1
                    """).scalar()
                if cnt == 0 or cnt is None:
                    self.alert_cb('soft_cap_alert', crm_id=crm_id)
                    self.set_soft_cap_alerted(crm_id)
            return _get_aft_sc()
        r = r.to_dict(orient='records')[0]
        if cc_type:
            r['cc_type'] = cc_type
        if cc_first_6:
            r['cc_first_6'] = cc_first_6

        self.set_iin(**r)
        r['is_tds'] = is_tds
        return r

    def update_models(self, approved, test=0, **kwargs):

        if self.routes is None:
            return

        if not int(test):
            self._lock_model_replace.acquire()
            r = self.routes.mod_type.unique()
            self._lock_model_replace.release()
            for k in r:
                _in = deepcopy(self.iin_info)
                self.iin_info.pop('response_code', None)
                try:
                    getattr(self._model_class, k)(self._to_engine).increment_conversion(approved, list(self.routes.columns),
                                                                              **{**_in, **kwargs})
                except:
                    print('increment error')

    def add_test_result(self, crm_id, order_id, approved, optimised, test=0, **kwargs):
        try:
            self._model_class.optimised_orders(self.db_p).upsert(
                pd.DataFrame([{**self.iin_info, **{'crm_id': crm_id, 'order_id': order_id, 'is_optimised': optimised,
                                                   'is_test_cc': int(test), 'approved': int(approved), 'version':self.version}}]))
        except Exception as e:
            # raise e
            print('LB ADD TEST RESULT ERROR', str(e))

    def increment_conversion(self, date, gateway_id, crm_id, approved, order_id, **kwargs):
        self.add_test_result(crm_id, order_id, approved, self._opt_val, **kwargs)
        try:
            self.update_models(approved, **kwargs)
        except Exception as e:
            pass

        return self._increment_conversion(date, gateway_id, crm_id, approved, recurs_attempt=0, **kwargs)
