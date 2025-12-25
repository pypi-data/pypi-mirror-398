import random
from models.db import Db, pd
from models.bro_clicks.initial_routes import ForeignInitialRoutes
from models.bro_clicks.load_balancer.v3 import LoadBalancerV3


class LoadBalancerV4(LoadBalancerV3):
    def __init__(self, *args, rewrite_route='foreign_initial_route', **kw):
        LoadBalancerV3.__init__(self, *args, rewrite_route=rewrite_route, **kw)
        self._model_class = ForeignInitialRoutes
        self._iin_schema = 'foreign_bins'
        self.version = 4

    def next_gateway(self, crm_id, date, step, click_id='', processor=False, cc_type=None, cc_first_6=False, recurse=0,
                     decs=False, ignore_user_exclusions=None,
                     proc_excl=[], is_tds=None, is_prepaid=True, **kwargs):
        # opt vals 1 = random gateway constrained only by cap,  2 = optimised gateway constrained only by cap, 3 = Hybrid approach not ignoring settings, 4 = over cap (over-rides to that if needed)
        if is_prepaid is None:
            raise TypeError('is_prepaid value must be pass as a boolean got NoneType')

        if is_prepaid:
            pp_campaign_class = 'prepaid'
        else:
            pp_campaign_class = 'post_paid'
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
            qry = self.gty_qry(crm_id, date, step, processor, cc_type, decs, proc_excl=proc_excl, is_tds=is_tds,
                               is_prepaid=is_prepaid, **kwargs)
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
                              # & (mod.conversion_rate != 1)  # take out dummy gateways
                              & ((mod.cc_first_6 == cc_first_6) | (mod.cc_first_6.isna()))
                              & (mod.campaign_class == pp_campaign_class)
                              & (((mod.cc_type == cc_type) | mod.cc_type.isna()) if 'cc_type' in mod.columns else (
                    True))
                              & (((mod.cc_level == str(self.iin_info['level'])) | (
                    mod.cc_level.isna())) if self.is_iin_data and 'level' in self.iin_info else (True))
                              & (((mod.bank == str(self.iin_info['bank'])) | (
                    mod.bank.isna())) if self.is_iin_data and 'bank' in self.iin_info else (True))
                              ]
                if len(mod):
                    df_opt = mod.copy().sort_values('conversion_rate', ascending=False).reset_index(drop=True)
                    df_opt['r_rank'] = df_opt.index + 1

                    # Optimization Filters

                    res = res.merge(df_opt.loc[df_opt.mod_type.isin(
                        ['cc_type_mcc_conversion', 'bank_conversion'])],
                                    on=['processor', 'mcc'],
                                    how='left').append(res.merge(
                        df_opt.loc[df_opt.mod_type.isin(['cc_type_cc_level_conversion', 'cc_type_conversion', 'iin_conversion'])].drop('mcc',
                                                                                                                     axis=1),
                        on=['processor'],
                        how='left')).sort_values('r_rank')
                else:
                    res['mod_type'] = 'undefined'
                    res['conversion_rate'] = 0
                # r_rank is Highest to lowest in terms of strength same as priority
                res.mod_type = res.mod_type.fillna('undefined').replace({'nan': 'undefined', '': 'undefined'})
                res.conversion_rate = res.conversion_rate.fillna(0)
            else:
                res['conversion_rate'] = 0
                res['mod_type'] = 'undefined'
            res = res.sort_values(**self.sort_map[self._opt_val]).drop_duplicates('gateway_id', keep='first')
            res['cc_type'] = cc_type
            res['cc_first_6'] = cc_first_6
            self.set_iin(cc_first_6=cc_first_6, cc_type=cc_type)
        except Exception as e:
            print('LBV4 error', str(e))
            raise e

        if res is None or not len(res):
            if not decs:
                if not recurse and is_tds is not None:
                    return self.next_gateway(crm_id, date, step, click_id, processor, cc_type, recurse=recurse + 1,
                                             is_tds=not is_tds, is_prepaid=is_prepaid)
                elif recurse == 1:
                    self.init_date(date, crm_id)
                    return self.next_gateway(crm_id, date, step, click_id, processor, cc_type, recurse=recurse + 1,
                                             is_tds=is_tds, is_prepaid=is_prepaid)
                elif recurse == 2 and is_tds is not None:
                    return self.next_gateway(crm_id, date, step, click_id, processor, cc_type, recurse=recurse + 1,
                                             is_tds=not is_tds, is_prepaid=is_prepaid)
                return 'out of processing'
            else:
                # if len(decs) < 4:
                #     return 'out of processing'
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

