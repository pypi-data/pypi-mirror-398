from datetime import datetime
import logging
from trexmodel.models.datastore.customer_models import CustomerTierMembership,\
    CustomerTierMembershipAccumulatedRewardSummary
from trexmodel.models.datastore.membership_models import MerchantTierMembership
from trexconf import program_conf

logger = logging.getLogger("target_debug")

def convert_transaction_reward_summary_to_accumulated_reward_summary(transaction_reward_summary):
    accumulated_reward_summary = {}
    for key, value in transaction_reward_summary.items():
        accumulated_reward_summary[key] = value.get('amount')
    return accumulated_reward_summary

def update_customer_tier_membership_from_adding_reward_summary(customer_acct, merchant_acct=None, transaction_details=None, entitled_datetime=None, reward_summary={}):
    
    if merchant_acct is None:
        merchant_acct = customer_acct.registered_merchant_acct
    
    logger.debug('---update_customer_tier_membership_from_adding_reward_summary---')
    if merchant_acct.is_tier_membership_configured:
        merchant_tier_membership_list                               = MerchantTierMembership.list_by_merchant_acct(merchant_acct)
        existing_tier_membership                                    = customer_acct.tier_membership_entity
        membership_to_assign                                        = None
        
        #highest_entitle_qualification_details                       = {}
        carry_over_amount                                           = 0 
        accumulated_summary                                         = reward_summary.copy() 
        existing_tier_index                                         = -1
        final_tier_index                                            = len(merchant_tier_membership_list)-1
        upgraded_tier_index                                         = -1 
        completed_tier_accumulated_reward_summary                   = {}
        reward_summary_key                                          = map_accumulated_amount_key_from_qualified_type(merchant_tier_membership_list[-1].entitle_qualification_type)
        
        customer_tier_membership_accumulated_reward_summary_list    = CustomerTierMembershipAccumulatedRewardSummary.list_by_customer(customer_acct)
        
        logger.debug('customer_tier_membership_accumulated_reward_summary_list=%s', customer_tier_membership_accumulated_reward_summary_list)
        
        if existing_tier_membership:
            existing_tier_index = next((i for i, p in enumerate(merchant_tier_membership_list) if p.key_in_str == existing_tier_membership.key_in_str), -1)
        
        logger.debug('existing_tier_index=%d', existing_tier_index)
        
        if existing_tier_index+1==len(merchant_tier_membership_list):
            logger.debug('already in the highest tier, thus continue update the accumulated reward summary')
            
            CustomerTierMembershipAccumulatedRewardSummary.add_accumulated_reward(customer_acct, 
                                                                            accumulated_summary         = reward_summary,
                                                                            merchant_tier_membership    = existing_tier_membership,
            
                                                                            )
            
        else:
            
            if existing_tier_membership:
                for i in range(-1, existing_tier_index+1):
                    tier_accumulated_reward_summary = next((p for p in customer_tier_membership_accumulated_reward_summary_list if p.tier_index == i), None)
                    
                    if tier_accumulated_reward_summary:
                        
                        for k,v in tier_accumulated_reward_summary.accumulated_summary.items():
                            logger.debug('Going to %s add %s', accumulated_summary.get(k,0), v)
                            accumulated_summary[k] = accumulated_summary.get(k,0) +v
                            logger.debug('end up=%s', accumulated_summary[k])
                        
                        if tier_accumulated_reward_summary.completed==True:
                            for k,v in tier_accumulated_reward_summary.accumulated_summary.items():
                                completed_tier_accumulated_reward_summary[k] = completed_tier_accumulated_reward_summary.get(k,0)+v
            else:
                tier_accumulated_reward_summary = next((p for p in customer_tier_membership_accumulated_reward_summary_list if p.tier_index == -1), None)
                
                if tier_accumulated_reward_summary:
                    for k,v in tier_accumulated_reward_summary.accumulated_summary.items():
                        accumulated_summary[k] = accumulated_summary.get(k,0)+v
                
            #logger.debug('existing_tier_index=%s', existing_tier_index)
            
            total_accumulated_point         = accumulated_summary.get('point',0)
            total_accumulated_stamp         = accumulated_summary.get('stamp',0) 
            total_accumulated_prepaid       = accumulated_summary.get('prepaid',0)
            
            if total_accumulated_point<0:
                total_accumulated_point = 0;
            
            if total_accumulated_stamp<0:
                total_accumulated_stamp = 0;
            
            if total_accumulated_prepaid<0:
                total_accumulated_prepaid = 0;        
            
            #logger.debug('total_transact_amount=%s', total_transact_amount)
            logger.debug('total_accumulated_point=%s', total_accumulated_point)
            logger.debug('total_accumulated_stamp=%s', total_accumulated_stamp)
            logger.debug('total_accumulated_prepaid=%s', total_accumulated_prepaid)
                
            for i in range(existing_tier_index+1, len(merchant_tier_membership_list)):
                membership = merchant_tier_membership_list[i]
                
                if membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_AUTO_ASSIGN:
                    if membership_to_assign is None:
                        upgraded_tier_index = i
                        membership_to_assign = membership
                        
                        logger.debug('Found auto assign tier membership')
                      
                elif membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                    logger.debug('checking tier membership(%d-%s) is based on accumulated point amount, where amount is %s', i, membership.label, membership.entitle_qualification_value)
                    if total_accumulated_point >= membership.entitle_qualification_value:
                        upgraded_tier_index = i
                        membership_to_assign = membership
                        if total_accumulated_point-membership.entitle_qualification_value>0:
                            carry_over_amount       = total_accumulated_point - membership.entitle_qualification_value
                        
                        logger.debug('Found %s tier membership to assign', membership.label)
                    else:
                        logger.debug('Condition is not match and stop here')  
                        
                        break
                        
                elif membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                    logger.debug('checking tier membership(%d-%s) is based on accumulated stamp amount, where amount is %s', i, membership.label, membership.entitle_qualification_value)
                    if total_accumulated_stamp >= membership.entitle_qualification_value:
                        upgraded_tier_index = i
                        membership_to_assign = membership
                        if total_accumulated_stamp-membership.entitle_qualification_value>0:
                            carry_over_amount       = total_accumulated_stamp - membership.entitle_qualification_value
                        
                         
                        logger.debug('Found %s tier membership to assign', membership.label)
                    else:
                        logger.debug('Condition is not match and stop here')  
                        
                        break     
                        
                elif membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                    logger.debug('checking tier membership(%d-%s) is based on accumulated prepaid amount, where amount is %s',i, membership.label,  membership.entitle_qualification_value)
                    if total_accumulated_prepaid >= membership.entitle_qualification_value:
                        upgraded_tier_index = i
                        membership_to_assign = membership
                        if total_accumulated_prepaid-membership.entitle_qualification_value>0:
                            carry_over_amount           = total_accumulated_prepaid - membership.entitle_qualification_value
                        
                        logger.debug('Found %s tier membership to assign', membership.label)
                    else:
                        logger.debug('Condition is not match and stop here')        
                        break
                
            
            logger.debug('existing_tier_index=%d, upgraded_tier_index=%d', existing_tier_index, upgraded_tier_index)
            
                
            if membership_to_assign:
                logger.debug('found upgrading tier membership to assign')
                if existing_tier_index>=0:
                    upgraded_tier_level_count = upgraded_tier_index - existing_tier_index
                else:
                    upgraded_tier_level_count = upgraded_tier_index + 1  
                
                logger.debug('upgraded_tier_level_count=%d', upgraded_tier_level_count)
                    
                
                
                if transaction_details:
                    entitled_datetime = transaction_details.transact_datetime
                
                if entitled_datetime is None:
                    entitled_datetime = datetime.utcnow()
                
                logger.debug('membership_to_assign=%s, entitled_datetime=%s', membership_to_assign.label, entitled_datetime)
                
                if existing_tier_membership:
                    
                    logger.debug('existing_tier_membership=%s', existing_tier_membership.label)
                    
                    
                    CustomerTierMembership.change(customer_acct,
                                              membership_to_assign, 
                                              transaction_details=transaction_details,
                                              entitled_datetime=entitled_datetime,
                                              )
                    
                    logger.debug('final_tier_index=%d', final_tier_index)
                    for i in range(existing_tier_index, upgraded_tier_index+1):
                        tier_membership = merchant_tier_membership_list[i]
                        logger.debug('%d) tier_membership (%s)', i, tier_membership.label)
                        if i<upgraded_tier_index:
                            accumulated_completed_tier_reward_amount = merchant_tier_membership_list[i+1].entitle_qualification_value - merchant_tier_membership_list[i].entitle_qualification_value
                            logger.debug('accumulated_completed_tier_reward_amount=%s', accumulated_completed_tier_reward_amount)
                                
                            _accumulated_summary = {
                                                reward_summary_key: accumulated_completed_tier_reward_amount
                                            }
                                
                            logger.debug('Going to define completed tier membership %s with accumulated reward=%s', tier_membership.label, _accumulated_summary)
                            CustomerTierMembershipAccumulatedRewardSummary.complete(customer_acct, 
                                                                    accumulated_summary         = _accumulated_summary,
                                                                    merchant_tier_membership    = tier_membership,
                                                                    tier_index                  = i,
                                                                    )
                        else:
                            
                            _accumulated_summary = {
                                                    reward_summary_key:carry_over_amount
                                                }
                            
                            #check is the tier is the last tier, and check the tier 
                            logger.debug('Going to define new tier membership %s with accumulated reward=%s', tier_membership.label, _accumulated_summary)
                            CustomerTierMembershipAccumulatedRewardSummary.create(customer_acct, 
                                                                created_date                = entitled_datetime.date(), 
                                                                accumulated_summary         = _accumulated_summary,
                                                                merchant_tier_membership    = tier_membership,
                                                                tier_index                  = i,
                                                                )
                        
                        #check_reward_for_new_membership(customer_acct, transaction_details, membership_to_assign)
                        
                        
                        
                        
                    
                else:
                    logger.debug('found new tier membership to assign')
                    
                    CustomerTierMembership.create(customer_acct, 
                                                  membership_to_assign, 
                                                  transaction_details         = transaction_details,
                                                  entitled_datetime           = entitled_datetime,
                                                  
                                                  )
                    
                    if upgraded_tier_level_count>0:
                        
                        for i in range(upgraded_tier_level_count):
                            tier_membership = merchant_tier_membership_list[i]
                            logger.debug('%d) tier_membership (%s), entitle qualification value=%s', i, tier_membership.label, tier_membership.entitle_qualification_value)
                            if i==0:
                                
                                if tier_membership.entitle_qualification_type!=program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_AUTO_ASSIGN:
                                    _accumulated_summary = {
                                                        reward_summary_key: tier_membership.entitle_qualification_value
                                                    }
                                    logger.debug('_accumulated_summary=%s', _accumulated_summary) 
                                    
                                    CustomerTierMembershipAccumulatedRewardSummary.complete(customer_acct, 
                                                                        accumulated_summary         = _accumulated_summary,
                                                                        merchant_tier_membership    = None,
                                                                        tier_index                  = -1,
                                                                        )
                            
                            
                            
                                    
                                
                            if i<upgraded_tier_index:
                                accumulated_completed_tier_reward_amount = merchant_tier_membership_list[i+1].entitle_qualification_value - merchant_tier_membership_list[i].entitle_qualification_value
                                logger.debug('accumulated_completed_tier_reward_amount=%s', accumulated_completed_tier_reward_amount)
                                
                                _accumulated_summary = {
                                                        reward_summary_key: accumulated_completed_tier_reward_amount
                                                    }
                                
                                logger.debug('tier index=%d tier label=%s, tier completed reward summary=%s', i, tier_membership.label, _accumulated_summary)
                                
                                CustomerTierMembershipAccumulatedRewardSummary.complete(customer_acct, 
                                                                        accumulated_summary         = _accumulated_summary,
                                                                        merchant_tier_membership    = tier_membership,
                                                                        tier_index                  = i,
                                                                        )
                            else:
                                accumulated_tier_reward_amount = accumulated_summary.get(reward_summary_key) - merchant_tier_membership_list[i].entitle_qualification_value 
                                _accumulated_summary =    {
                                                            reward_summary_key: accumulated_tier_reward_amount
                                                            }
                                logger.debug('tier index=%d tier label=%s, tier achieved value=%s', i, tier_membership.label, _accumulated_summary)
                                
                                CustomerTierMembershipAccumulatedRewardSummary.create(customer_acct, 
                                                                        created_date                = entitled_datetime.date(), 
                                                                        accumulated_summary         = _accumulated_summary,
                                                                        merchant_tier_membership    = tier_membership,
                                                                        tier_index                  = i,
                                                                        )
                                    
                    else:
                        CustomerTierMembershipAccumulatedRewardSummary.create(customer_acct, 
                                                                            created_date                = entitled_datetime.date(), 
                                                                            accumulated_summary         = accumulated_summary,
                                                                            merchant_tier_membership    = membership_to_assign,
                                                                            tier_index                  = upgraded_tier_index,
                                                                            )
                    #check_reward_for_new_membership(customer_acct, transaction_details, membership_to_assign)
                    
                    
            else:
                if existing_tier_membership:
                    logger.debug('tier index=%d tier label=%s, tier achieved value=%s', existing_tier_index, existing_tier_membership.label, accumulated_summary)    
                    CustomerTierMembershipAccumulatedRewardSummary.add_accumulated_reward(customer_acct, 
                                                                        accumulated_summary         = reward_summary,
                                                                        merchant_tier_membership    = existing_tier_membership,
                                                                        )
                    
                    logger.debug('not tier membership to upgrade, thus remain as existing tier membership')
                else:
                    CustomerTierMembershipAccumulatedRewardSummary.add_accumulated_reward(customer_acct, 
                                                                        accumulated_summary         = reward_summary,
                                                                        )
                    
    else:
        logger.debug('no tier membership is configured thus ignore')
        
def update_customer_tier_membership_from_reverting_reward_summary(
        customer_acct, 
        merchant_acct=None, 
        reward_summary={}, ):
    
    if merchant_acct is None:
        merchant_acct = customer_acct.registered_merchant_acct
    
    logger.debug('---update_customer_tier_membership_from_reverting_reward_summary---')
    if merchant_acct.is_tier_membership_configured:
        merchant_tier_membership_list                               = MerchantTierMembership.list_by_merchant_acct(merchant_acct)
        existing_tier_membership                                    = customer_acct.tier_membership_entity
        membership_to_assign                                        = None
        
        #highest_entitle_qualification_details                       = {}
        accumulated_summary                                         = {}
        existing_tier_index                                         = -1
        downgraded_tier_index                                       = 0
        completed_tier_accumulated_reward_summary                   = {}
        reward_summary_key                                          = map_accumulated_amount_key_from_qualified_type(merchant_tier_membership_list[-1].entitle_qualification_type)
        customer_tier_membership_accumulated_reward_summary_list    = CustomerTierMembershipAccumulatedRewardSummary.list_by_customer(customer_acct)
        
        if existing_tier_membership:
            existing_tier_index = next((i for i, p in enumerate(merchant_tier_membership_list) if p.key_in_str == existing_tier_membership.key_in_str), -1)
            
            for i in range(-1, existing_tier_index+1):
                tier_accumulated_reward_summary = next((p for p in customer_tier_membership_accumulated_reward_summary_list if p.tier_index == i), None)
                
                if tier_accumulated_reward_summary:
                    
                    for k,v in tier_accumulated_reward_summary.accumulated_summary.items():
                        accumulated_summary[k] = accumulated_summary.get(k,0)+v
                    
                    if tier_accumulated_reward_summary.completed==True:
                        for k,v in tier_accumulated_reward_summary.accumulated_summary.items():
                            completed_tier_accumulated_reward_summary[k] = completed_tier_accumulated_reward_summary.get(k,0)+v
            
            logger.debug('completed_tier_accumulated_reward_summary=%s', completed_tier_accumulated_reward_summary)
            
        else:
            tier_accumulated_reward_summary = next((p for p in customer_tier_membership_accumulated_reward_summary_list if p.tier_index == -1), None)
            
            if tier_accumulated_reward_summary:
                logger.debug('tier_accumulated_reward_summary=%s', tier_accumulated_reward_summary)
                for k,v in tier_accumulated_reward_summary.accumulated_summary.items():
                    accumulated_summary[k] = accumulated_summary.get(k,0)+v
            
            logger.debug('accumulated_summary=%s', accumulated_summary)
            
        logger.debug('Going to deduct reverted reward summary')
        
        for k,v in accumulated_summary.items():
            accumulated_summary[k] = accumulated_summary[k] - reward_summary.get(k, 0) 
        
        logger.debug('accumulated_summary=%s', accumulated_summary)    
        logger.debug('existing_tier_index=%s', existing_tier_index)
        
        total_accumulated_point         = accumulated_summary.get('point',0)
        total_accumulated_stamp         = accumulated_summary.get('stamp',0) 
        total_accumulated_prepaid       = accumulated_summary.get('prepaid',0)
        
        if total_accumulated_point<0:
            total_accumulated_point = 0;
        
        if total_accumulated_stamp<0:
            total_accumulated_stamp = 0;
        
        if total_accumulated_prepaid<0:
            total_accumulated_prepaid = 0;        
        
        #logger.debug('total_transact_amount=%s', total_transact_amount)
        logger.debug('total_accumulated_point=%s', total_accumulated_point)
        logger.debug('total_accumulated_stamp=%s', total_accumulated_stamp)
        logger.debug('total_accumulated_prepaid=%s', total_accumulated_prepaid)
        
        proceed_to_check_downgrade_tier = True
        
        if existing_tier_membership:
            logger.debug('Check whether existing tier membership condition is still achieved')
            
            if existing_tier_membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_AUTO_ASSIGN:
                proceed_to_check_downgrade_tier = False
                  
            elif existing_tier_membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                logger.debug('checking tier membership(%s) is based on accumulated point amount, where amount is %s', existing_tier_membership.label, existing_tier_membership.entitle_qualification_value)
                if total_accumulated_point >= existing_tier_membership.entitle_qualification_value:
                    proceed_to_check_downgrade_tier = False
                    
            elif existing_tier_membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                logger.debug('checking tier membership(%s) is based on accumulated stamp amount, where amount is %s', existing_tier_membership.label, existing_tier_membership.entitle_qualification_value)
                if total_accumulated_stamp >= existing_tier_membership.entitle_qualification_value:
                    proceed_to_check_downgrade_tier = False
                    
            elif existing_tier_membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                logger.debug('checking tier membership(%s) is based on accumulated prepaid amount, where amount is %s',existing_tier_membership.label,  existing_tier_membership.entitle_qualification_value)
                if total_accumulated_prepaid >= existing_tier_membership.entitle_qualification_value:
                    proceed_to_check_downgrade_tier = False
            
        logger.debug('proceed_to_check_downgrade_tier=%s', proceed_to_check_downgrade_tier)
            
        if proceed_to_check_downgrade_tier:
            downgraded_tier_index = -1
            
            for i in range(existing_tier_index-1, -1, -1):
                membership = merchant_tier_membership_list[i]
                
                if membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_AUTO_ASSIGN:
                    if membership_to_assign is None:
                        downgraded_tier_index = i
                        membership_to_assign = membership
                        logger.debug('Found auto assign tier membership')
                        break
                      
                elif membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                    logger.debug('checking tier membership(%d-%s) is based on accumulated point amount, where amount is %s', i, membership.label, membership.entitle_qualification_value)
                    if total_accumulated_point >= membership.entitle_qualification_value:
                        downgraded_tier_index = i
                        membership_to_assign = membership
                        logger.debug('Found %s tier membership to assign', membership.label)
                        break
                        
                elif membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                    logger.debug('checking tier membership(%d-%s) is based on accumulated stamp amount, where amount is %s', i, membership.label, membership.entitle_qualification_value)
                    if total_accumulated_stamp >= membership.entitle_qualification_value:
                        downgraded_tier_index = i
                        membership_to_assign = membership
                        logger.debug('Found %s tier membership to assign', membership.label)
                        break     
                        
                elif membership.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                    logger.debug('checking tier membership(%d-%s) is based on accumulated prepaid amount, where amount is %s',i, membership.label,  membership.entitle_qualification_value)
                    if total_accumulated_prepaid >= membership.entitle_qualification_value:
                        downgraded_tier_index = i
                        membership_to_assign = membership
                        logger.debug('Found %s tier membership to assign', membership.label)
                        break
            
            logger.debug('existing_tier_index=%d, downgraded_tier_index=%d', existing_tier_index, downgraded_tier_index)   
            
            if existing_tier_membership:
                
                logger.debug('existing_tier_membership=%s, membership_to_assign=%s', existing_tier_membership.label, membership_to_assign.label)
                entitle_qualification_type = existing_tier_membership.entitle_qualification_type
                if membership_to_assign:
                    CustomerTierMembership.change(customer_acct,
                                              membership_to_assign, 
                                              is_upgrade = False
                                              )
                    '''
                    if downgraded_tier_index>0:
                        logger.debug('Going to check previous tier completed accumulated reward')
                        total_accumulated_amount = 0
                        
                        if entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                            total_accumulated_amount = total_accumulated_point - membership_to_assign.entitle_qualification_value
                        elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                            total_accumulated_amount = total_accumulated_stamp - membership_to_assign.entitle_qualification_value
                        elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                            total_accumulated_amount = total_accumulated_prepaid - membership_to_assign.entitle_qualification_value
                        
                        new_accumulated_summary = {
                                reward_summary_key : total_accumulated_amount
                            }
                        logger.debug('new_accumulated_summary=%s', new_accumulated_summary)
                        CustomerTierMembershipAccumulatedRewardSummary.update(customer_acct, membership_to_assign, 
                                                            accumulated_summary         = new_accumulated_summary,
                                                            )
                            
                    else:
                        
                        total_accumulated_amount = 0
                        
                        if membership_to_assign.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_AUTO_ASSIGN:
                            if entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                                total_accumulated_amount = total_accumulated_point
                            elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                                total_accumulated_amount = total_accumulated_stamp
                            elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                                total_accumulated_amount = total_accumulated_prepaid
                        else:
                            if entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                                total_accumulated_amount = total_accumulated_point - membership_to_assign.entitle_qualification_value
                            elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                                total_accumulated_amount = total_accumulated_stamp - membership_to_assign.entitle_qualification_value
                            elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                                total_accumulated_amount = total_accumulated_prepaid - membership_to_assign.entitle_qualification_value
                        
                        new_accumulated_summary = {
                                reward_summary_key : total_accumulated_amount
                            }
                        
                        CustomerTierMembershipAccumulatedRewardSummary.update(customer_acct, membership_to_assign, 
                                                            accumulated_summary         = new_accumulated_summary,
                                                            )
                    '''
                    
                    if membership_to_assign.entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_AUTO_ASSIGN:
                        if entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                            total_accumulated_amount = total_accumulated_point
                        elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                            total_accumulated_amount = total_accumulated_stamp
                        elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                            total_accumulated_amount = total_accumulated_prepaid
                    else:
                        if entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                            total_accumulated_amount = total_accumulated_point - membership_to_assign.entitle_qualification_value
                        elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                            total_accumulated_amount = total_accumulated_stamp - membership_to_assign.entitle_qualification_value
                        elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                            total_accumulated_amount = total_accumulated_prepaid - membership_to_assign.entitle_qualification_value
                    
                    new_accumulated_summary = {
                            reward_summary_key : total_accumulated_amount
                        }
                    
                    CustomerTierMembershipAccumulatedRewardSummary.update(customer_acct, membership_to_assign, 
                                                        accumulated_summary         = new_accumulated_summary,
                                                        )   
                    for i in range(existing_tier_index, downgraded_tier_index, -1):
                        membership = merchant_tier_membership_list[i]
                        CustomerTierMembershipAccumulatedRewardSummary.delete_for_customer_by_tier_membership(customer_acct, membership)
                    
                else:
                    if entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
                        total_accumulated_amount = total_accumulated_point
                    elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
                        total_accumulated_amount = total_accumulated_stamp
                    elif entitle_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
                        total_accumulated_amount = total_accumulated_prepaid
                    
                    new_accumulated_summary = {
                            reward_summary_key : total_accumulated_amount
                        }
                    CustomerTierMembershipAccumulatedRewardSummary.update(customer_acct, None, 
                                                            accumulated_summary         = new_accumulated_summary,
                                                            )
                    
                    for i in range(existing_tier_index, -1, -1):
                        membership = merchant_tier_membership_list[i]
                        CustomerTierMembershipAccumulatedRewardSummary.delete_for_customer_by_tier_membership(customer_acct, membership)
                    
                    
            else:
                CustomerTierMembershipAccumulatedRewardSummary.deduct_accumulated_reward(customer_acct, None, accumulated_summary=reward_summary)    
        else:
            CustomerTierMembershipAccumulatedRewardSummary.deduct_accumulated_reward(customer_acct, existing_tier_membership, accumulated_summary=reward_summary)
                    
    else:
        logger.debug('no tier membership is configured thus ignore')        

def assign_eligible_maintain_or_downgrade_tier_membership(customer_acct, merchant_acct=None, entitled_datetime=None):
    if merchant_acct is None:
        merchant_acct = customer_acct.registered_merchant_acct
    logger.debug('---assign_eligible_maintain_or_downgrade_tier_membership---')
    accumulated_reward_amount           = 0    
    membership_to_assign                = None
    existing_tier_index                 = -1
    existing_tier_membership            = customer_acct.tier_membership_entity
    merchant_tier_membership_list       = []
    assign_tier_membership_index        = -1
    maintain_tier_index                 = -1
    
    if entitled_datetime is None:
        entitled_datetime = datetime.utcnow()
    
    if merchant_acct.is_tier_membership_configured:
        merchant_tier_membership_list           = MerchantTierMembership.list_by_merchant_acct(merchant_acct)
        reward_summary_key                      = map_accumulated_amount_key_from_qualified_type(merchant_tier_membership_list[-1].entitle_qualification_type)
    
    if existing_tier_membership: 
        logger.debug('Going to get accumulated reward amount by existing tier membership(%s)', existing_tier_membership.label)
        existing_tier_index                 = next((i for i, p in enumerate(merchant_tier_membership_list) if p.key_in_str == existing_tier_membership.key_in_str), -1)
        
        customer_tier_membership_accumulated_reward_summary= CustomerTierMembershipAccumulatedRewardSummary.get_by_customer_and_merchant_tier_membership(customer_acct, existing_tier_membership)
        if customer_tier_membership_accumulated_reward_summary:
            accumulated_reward_amount = customer_tier_membership_accumulated_reward_summary.accumulated_summary.get(reward_summary_key, 0)
    else:
        customer_tier_membership_accumulated_reward_summary= CustomerTierMembershipAccumulatedRewardSummary.get_by_customer_and_merchant_tier_membership(customer_acct, None)
        if customer_tier_membership_accumulated_reward_summary:
            accumulated_reward_amount = customer_tier_membership_accumulated_reward_summary.accumulated_summary.get(reward_summary_key, 0)
        
        
    logger.debug('accumulated_reward_amount=%s', accumulated_reward_amount)
    total_merchant_tier_membership_level    = len(merchant_tier_membership_list) 
    
    for i in range(0, total_merchant_tier_membership_level):
        membership = merchant_tier_membership_list[i]
        
        if membership.maintain_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_AUTO_ASSIGN:
            if membership_to_assign is None:
                membership_to_assign = membership
                maintain_tier_index = i
                logger.debug('Found auto assign tier membership')
                
              
        elif membership.maintain_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_POINT_AMOUNT:
            logger.debug('checking tier membership(%d-%s) is based on accumulated point amount, where amount is %s', i, membership.label, membership.entitle_qualification_value)
            if accumulated_reward_amount >= membership.maintain_qualification_value:
                membership_to_assign = membership
                maintain_tier_index = i
                logger.debug('Found %s tier membership to assign', membership.label)
            else:
                logger.debug('Condition is not match and stop here')        
                break
                
                
        elif membership.maintain_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_STAMP_AMOUNT:
            logger.debug('checking tier membership(%d-%s) is based on accumulated stamp amount, where amount is %s', i, membership.label, membership.entitle_qualification_value)
            if accumulated_reward_amount >= membership.maintain_qualification_value:
                membership_to_assign = membership
                maintain_tier_index = i
                logger.debug('Found %s tier membership to assign', membership.label)
            else:
                logger.debug('Condition is not match and stop here')        
                break         
                
        elif membership.maintain_qualification_type == program_conf.MEMBERSHIP_ENTITLE_QUALIFICATION_TYPE_ACCUMULATED_PREPAID_AMOUNT:
            logger.debug('checking tier membership(%d-%s) is based on accumulated prepaid amount, where amount is %s',i, membership.label,  membership.entitle_qualification_value)
            if accumulated_reward_amount >= membership.maintain_qualification_value:
                membership_to_assign = membership
                maintain_tier_index = i
                logger.debug('Found %s tier membership to assign', membership.label)
            else:
                logger.debug('Condition is not match and stop here')        
                break
                            
    if membership_to_assign is not None:
        logger.debug('Found tier membership to assign = %s, assign_tier_membership_index=%d', membership_to_assign.label, assign_tier_membership_index)
        
        if existing_tier_membership:
            logger.debug('found maintain tier membership to assign')
            downgraded_tier_level_count = existing_tier_index - maintain_tier_index
            
            logger.debug('downgraded_tier_level_count=%d', downgraded_tier_level_count)
            
            balance_after_maintain_tier_reward_amount = accumulated_reward_amount - membership_to_assign.maintain_qualification_value
            
            accumulated_summary = {
                                reward_summary_key: balance_after_maintain_tier_reward_amount
                                }
            CustomerTierMembershipAccumulatedRewardSummary.update(customer_acct, membership_to_assign, accumulated_summary)
            
            if downgraded_tier_level_count>0:
                CustomerTierMembership.change(customer_acct, membership_to_assign, is_upgrade=False)
            
            for i in range(existing_tier_index, downgraded_tier_level_count, -1):
                tier_membership = merchant_tier_membership_list[i]
                CustomerTierMembershipAccumulatedRewardSummary.delete_for_customer_by_tier_membership(customer_acct, tier_membership)
        else:
            logger.debug('If there is tier to assign but there is no existing tier, which is not correct')
    else:
        if existing_tier_membership:
            logger.debug('Do not entitle any tier membership, thus going to remove customer tier membership')
            CustomerTierMembership.remove(customer_acct, existing_tier_membership)
        
        CustomerTierMembershipAccumulatedRewardSummary.delete_all_for_customer(customer_acct)
        
        logger.debug('Going to create balance of tier membership accumulated reward summary ')
        
        _accumulated_summary = {
                                map_accumulated_amount_key_from_qualified_type(merchant_tier_membership_list[-1].entitle_qualification_type)
                                : accumulated_reward_amount
                                }
        CustomerTierMembershipAccumulatedRewardSummary.create(customer_acct, 
                                                                created_date                = entitled_datetime.date(), 
                                                                accumulated_summary         = _accumulated_summary,
                                                                )
        
                

def map_accumulated_amount_key_from_qualified_type(entitle_qualification_type):
    
    if 'acc_point'==entitle_qualification_type:
        return 'point'
    elif 'acc_stamp'==entitle_qualification_type:
        return 'stamp'
    elif 'acc_prepaid'==entitle_qualification_type:
        return 'prepaid'


