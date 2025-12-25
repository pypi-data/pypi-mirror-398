from models.bro_clicks.load_balancer.v6 import LoadBalancerV6
import pandas as pd
from numpy import nan as np_nan


class LoadBalancerV7(LoadBalancerV6):

    def __init__(self, *args, **kw):
        LoadBalancerV6.__init__(self, *args, **kw)
        self.version = 7
        self.is_cc_type_cap_split = True

    def init_date(self, date, crm_id, reset_cap_count=True):
        sk = f'ui_{self._account_id}_clients'
        real_cap_space = self.get_processing_for_month_cc_type(crm_id) if reset_cap_count else None

        qry = f"""
                  SELECT '{date}'::date as date,  b.crm_id, a.mid_id,   b.gateway_id, b.step, a.processor,                  
                                                  coalesce(e.approved, 0)  approved,  
                                                  coalesce(e.o_approved,0) initial_count,
                                                  coalesce(e.v_approved,0) visa_count,  
                                                  c.dly_initial_cap,  
                                                  c.visa_dly_cap,
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
                                                  c.visa_monthly_cap,
                                                  c.priority, 
                                                  c.router_id,  
                                                  d.router_id as cur_router_id,                                                
                                                  d.soft_cap_alerted,
                                                   d.visa_soft_cap_alerted,  
                                                  d.initial_count_mtd  as  prev_mtd,
                                                  d.visa_count_mtd  as  prev_visa_mtd,
                                                 TRUE as visa_enabled,
                                                 TRUE as mc_enabled                         

                  FROM {sk}.mids a 
                  LEFT JOIN {sk}.steps b on b.mid_id = a.mid_id 
                  LEFT JOIN {sk}.gateway_settings c on c.gateway_id = b.gateway_id and c.crm_id = b.crm_id
                  LEFT JOIN {self.schema}.{self.table} d on c.gateway_id =d.gateway_id and c.crm_id = d.crm_id and  b.step = d.step and '{date}'::date =d.date
                  LEFT JOIN (select  crm_id, gateway_id, 
                  coalesce(sum(declined),  0) declined,   
                  coalesce(sum(approved), 0) approved,
                  coalesce(sum(approved) filter (where lower(cc_type)='visa'), 0) v_approved,
                  coalesce(sum(approved) filter (where lower(cc_type)<>'visa'), 0) o_approved   
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
                up = up.merge(real_cap_space[['gateway_id', 'initial_count_mtd']], on=['gateway_id'], how='left')
                up.initial_count_mtd = up.initial_count_mtd.fillna(0)
                up.initial_count_mtd += up.initial_count

            except:
                up['initial_count_mtd'] = up.prev_mtd.fillna(0)
                up.initial_count_mtd = up.initial_count_mtd.fillna(0)

            try:
                up = up.merge(real_cap_space[['gateway_id', 'visa_count_mtd']], on=['gateway_id'], how='left')
                up.visa_count_mtd = up.visa_count_mtd.fillna(0)
                up.visa_count_mtd += up.visa_count

            except:
                up['visa_count_mtd'] = up.prev_visa_mtd.fillna(0)
                up.initial_count_mtd = up.initial_count_mtd.fillna(0)

            drim = float(self.get_drim())
            up.dly_initial_cap = pd.np.floor((up.monthly_initial_cap - up.initial_count_mtd) / drim)
            up.visa_dly_cap = pd.np.floor((up.visa_monthly_cap - up.visa_count_mtd) / drim)
            up.loc[up.dly_initial_cap < 0, 'dly_initial_cap'] = 0
            up.loc[up.visa_dly_cap < 0, 'visa_dly_cap'] = 0
        up.visa_enabled = up.visa_count_mtd.fillna(0) < up.visa_monthly_cap.fillna(0)
        up.mc_enabled = up.initial_count_mtd.fillna(0) < up.monthly_initial_cap.fillna(0)
        up.dly_initial_cap = up.dly_initial_cap.fillna(11)
        up.visa_dly_cap = up.visa_dly_cap.fillna(11)
        up.dly_min_approval_rate = up.dly_min_approval_rate.fillna(30)
        up.declined = up.declined.fillna(0)
        up.approval_rate = up.approval_rate.fillna(0)
        up.soft_cap_alerted = up.soft_cap_alerted.fillna(False)
        up.visa_soft_cap_alerted = up.visa_soft_cap_alerted.fillna(False)
        up.drop(['prev_mtd', 'prev_visa_mtd'], axis=1, errors='ignore', inplace=True)
        up = up.drop_duplicates(['gateway_id', 'router_id'])
        # self.engine.execute(f'truncate {self.schema}.{self.table}')
        self.upsert(up.dropna())

    def gty_qry(self, crm_id, date, step, processor, cc_type=False, decs='', proc_excl=[], is_tds=None,
                is_prepaid=False, is_decline_salvage=False, **kw):
        p_ex = ''
        cc_enable_clause = ''
        if proc_excl and len(proc_excl) and not processor:
            p_ex = f"and a.processor not ilike all(ARRAY{[f'%%{p}%%' for p in proc_excl]}::text[])"

        if str(cc_type).lower() == 'visa':
            dyna_cap_cols = "a.visa_fill_pct fill_pct, a.visa_dly_cap dly_initial_cap, a.visa_monthly_cap monthly_initial_cap,  a.visa_soft_cap_alerted soft_cap_alerted, a.visa_count_mtd initial_count_mtd, a.visa_count initial_count, a.soft_cap_alerted sca2"
            cc_enable_clause = 'and a.visa_enabled'
        else:
            dyna_cap_cols = "a.fill_pct, a.dly_initial_cap, a.monthly_initial_cap, a.soft_cap_alerted, initial_count_mtd, initial_count, a.visa_soft_cap_alerted sca2"
            cc_enable_clause = 'and a.mc_enabled'

        return f""" --LEFT HERE NEED TO GET MCC!
                       select a.gateway_id::int,  priority,   a.approval_rate, a.date_added, a.processor, a.mid_id, b.mcc,
                       {dyna_cap_cols} 
                       from {self.schema}.{self.table} a
                       inner join (select crm_id,  gateway_id,  mcc from ui_54407332_clients.steps ) b  on b.crm_id =  a.crm_id and  b.gateway_id=a.gateway_id
                       {"inner join (select crm_id, gateway_id where enable_decline_salvage) ds on ds.crm_id = a.crm_id and ds.gateway_id::int = a.gateway_id::int" if is_decline_salvage else ""}
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
                                     {cc_enable_clause}
                                     --and fill_pct < 1                         

                       --order by date_added desc, approval_rate desc, fill_pct asc limit 1
                         order by priority desc, date_added  desc, fill_pct, approval_rate desc, initial_count

                   """

    def next_gateway(self, crm_id, date, step, click_id='', processor=False, cc_type=None, cc_first_8=False, recurse=0,
                     decs=False, ignore_user_exclusions=None,
                     proc_excl=[], is_tds=None, is_prepaid=True, c_token=None, **kwargs):
        # opt vals 1 = random gateway constrained only by cap,  2 = optimised gateway constrained only by cap, 3 = Hybrid approach not ignoring settings, 4 = over cap (over-rides to that if needed)
        if is_prepaid is None:
            raise TypeError('is_prepaid value must be pass as a boolean got NoneType')

        if is_prepaid:
            pp_campaign_class = 'prepaid'
        else:
            pp_campaign_class = 'post_paid'
        if ignore_user_exclusions is None:
            ignore_user_exclusions = self._opt_val < 2
        if cc_first_8:
            self.set_bin_info(cc_first_8)
        try:
            decs = self.exclude_list(crm_id, step, click_id, 'a.', c_token=c_token) if not decs else decs
        except Exception as e:
            return str(e)

        try:
            qry = self.gty_qry(crm_id, date, step, processor, cc_type, decs, proc_excl=proc_excl, is_tds=is_tds,
                               is_prepaid=is_prepaid, **kwargs)
            res = pd.read_sql(qry, self.engine)
            cc_type = cc_type.lower()
            if 'master' in cc_type:
                cc_type = 'master'
            try:
                result = self._t_get_bin.result(timeout=4)  # Wait for 2 seconds
            except TimeoutError:
                print("IIN INFO timed out!")
            except Exception as e:
                print(f"An error occurred: {e}")
            if self._opt_val > 1 and self._opt_val < 4 and self.routes is not None:

                self._lock_model_replace.acquire()
                mod = self.routes if self.is_iin_data else self.routes.loc[
                    self.routes.mod_type.isin(['cc_type_conversion', 'cc_type_mcc_conversion'])]
                self._lock_model_replace.release()
                if len(mod):  # and 'conversion_rate' in mod.columns:
                    if 'cc_level' not in mod.columns:
                        mod['cc_level'] = np_nan
                    if 'mcc' not in mod.columns:
                        mod['mcc'] = np_nan
                    mod = mod.loc[(mod.approved + mod.declined >= self._min_sample_count)
                                  # & (mod.conversion_rate != 1)  # take out dummy gateways
                                  & ((mod.cc_first_8 == cc_first_8) | (mod.cc_first_8.isna()))
                                  & (mod.campaign_class == pp_campaign_class)
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
                        ['cc_type_mcc_conversion', 'bank_conversion'])],
                                    on=['processor', 'mcc'],
                                    how='left').append(res.merge(
                        df_opt.loc[df_opt.mod_type.isin(
                            ['cc_type_cc_level_conversion', 'cc_type_conversion', 'iin_conversion'])].drop('mcc',
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
            res['cc_first_8'] = cc_first_8
            self.set_iin(cc_first_8=cc_first_8, cc_type=cc_type)
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
                    self.alert_cb('hard_cap_alert', crm_id=crm_id, gateway_id=r2['gateway_id'], cc_type=cc_type)
                    self.disable(crm_id=crm_id, gateway_id=r2['gateway_id'], cc_type=cc_type)
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
                    self.alert_cb('soft_cap_alert', crm_id=crm_id, cc_type=cc_type)
                    self.set_soft_cap_alerted(crm_id, cc_type=cc_type)
            return _get_aft_sc()
        r = r.to_dict(orient='records')[0]
        if cc_type:
            r['cc_type'] = cc_type
        if cc_first_8:
            r['cc_first_8'] = cc_first_8

        self.set_iin(**r)
        r['is_tds'] = is_tds
        return r