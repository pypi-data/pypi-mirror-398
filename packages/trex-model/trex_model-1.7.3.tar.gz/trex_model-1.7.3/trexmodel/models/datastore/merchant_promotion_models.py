'''
Created on 2 Mar 2025

@author: jacklok
'''
from google.cloud import ndb
from trexmodel.models.datastore.ndb_models import BaseNModel, DictModel
from trexconf import conf
import logging


logger = logging.getLogger('target_debug')

class PromotionCode(BaseNModel, DictModel):    
    code   = ndb.StringProperty(required=True)
    desc    = ndb.StringProperty(required=False)
    created_datetime    = ndb.DateTimeProperty(required=True, auto_now_add=True)
    is_enabled          = ndb.BooleanProperty(required=False, default=True)
    dict_properties = ['code', 'desc', 'created_datetime', 'is_enabled', 'is_disabled']
    
    @property
    def is_disabled(self):
        return self.is_enabled==False
    
    @classmethod
    def create_code(cls,parent=None, code=None, desc=None):
        created_code = cls(
                            parent  = parent,
                            code    = code,
                            desc    = desc,
                            )
        
        created_code.put()
        
        return created_code
    
    @classmethod
    def get_by_code(cls, parent, code):
        return cls.query(ndb.AND(cls.code==code), ancestor=parent).fetch(limit=1)
    
        
    
class MerchantPromotionCode(PromotionCode):    
    '''
    Parent is MerchantAcct
    '''
    
    @property
    def merchant_acct_entity(self):
        return self.key.parent().get()
    
    @staticmethod
    def create(merchant_acct, code=None, desc=None):
        promotion_code = MerchantPromotionCode.create_code(parent=merchant_acct.create_ndb_key(), code=code, desc=desc)
        merchant_acct.add_promotion_code(code)
        
        return promotion_code
    '''
    def update(self, label=None, desc=None):
        self.label  = label
        self.desc   = desc
        self.put()
    '''
        
    @staticmethod
    def update(promotion_code, code=None, desc=None):
        merchant_acct = promotion_code.merchant_acct_entity
        
        merchant_acct.remove_promotion_code(promotion_code.code)
        merchant_acct.add_promotion_code(code)    
        
        promotion_code.code = code
        promotion_code.desc = desc
        promotion_code.put()
        
    @staticmethod
    def enable(promotion_code):
        promotion_code.is_enabled = True
        promotion_code.put()
        
        merchant_acct = promotion_code.merchant_acct_entity
        
        #logger.debug('merchant_acct=%s', merchant_acct)
        
        merchant_acct.add_promotion_code(promotion_code.code)
        
        
    @staticmethod
    def disable(promotion_code):
        promotion_code.is_enabled = False
        promotion_code.put()    
        
        merchant_acct = promotion_code.merchant_acct_entity
        
        #logger.debug('merchant_acct=%s', merchant_acct)
        
        merchant_acct.remove_promotion_code(promotion_code.code)
        
    @staticmethod
    def list_by_merchant_account(merchant_acct):
        return MerchantPromotionCode.query(ancestor = merchant_acct.create_ndb_key()).fetch(limit = conf.MAX_FETCH_RECORD)
    
    @staticmethod
    def get_by_merchant_code(merchant_acct, code):
        return MerchantPromotionCode.get_by_code(merchant_acct.create_ndb_key(), code)         
