'''
Created on Nov 14, 2025

@author: jacklok
'''

from trexmodel.models.datastore.ndb_models import BaseNModel, DictModel
from google.cloud import ndb
from trexmodel.models.datastore.merchant_models import MerchantUser, Outlet
from trexlib.utils.string_util import is_not_empty
from datetime import datetime
from trexconf import conf
import trexmodel.conf as model_conf
import logging

logger = logging.getLogger('model')

class FanClubSetup(BaseNModel, DictModel):
    '''
    Merchant Acct as ancestor
    
    '''
    
    group_name              = ndb.StringProperty(required=True)
    desc                    = ndb.StringProperty(required=True)      
    fan_club_type           = ndb.StringProperty(required=True, choices=set(['whatsapp','line','facebook', 'wechat']), default='whatsapp')
    invite_link             = ndb.StringProperty(required=True)
    assigned_outlet         = ndb.KeyProperty(name="assigned_outlet", kind=Outlet)
    
    is_archived             = ndb.BooleanProperty(default=False)
    is_published            = ndb.BooleanProperty(default=False)
    
    created_datetime        = ndb.DateTimeProperty(required=True, auto_now_add=True)
    archived_datetime       = ndb.DateTimeProperty(required=False)
    published_datetime      = ndb.DateTimeProperty(required=False)
    
    created_by              = ndb.KeyProperty(name="created_by", kind=MerchantUser)
    created_by_username     = ndb.StringProperty(required=False)
    
    modified_by             = ndb.KeyProperty(name="modified_by", kind=MerchantUser)
    modified_by_username    = ndb.StringProperty(required=False)
    
    archived_by             = ndb.KeyProperty(name="archived_by", kind=MerchantUser)
    archived_by_username    = ndb.StringProperty(required=False)
    
    published_by            = ndb.KeyProperty(name="published_by", kind=MerchantUser)
    published_by_username   = ndb.StringProperty(required=False)
    
    
    dict_properties = [
                        'group_name', 'desc', 'fan_club_type',  'invite_link',
                        'created_datetime', 'published_datetime', 'archived_datetime', 'is_published',
                        'assigned_outlet_key', 'allow_to_update'
                    ]
    
    
    @property
    def allow_to_update(self):
        return self.is_published
    
    @property
    def assigned_outlet_key(self):
        if self.assigned_outlet:
            return self.assigned_outlet.urlsafe().decode("utf-8")
        
    @property
    def merchant_acct(self):
        return self.key.parent().get()
    
    def to_configuration(self):
        return {
            'key'                   : self.key_in_str,
            'group_name'            : self.group_name,
            'fan_club_type'         : self.fan_club_type,
            'assigned_outlet_key'   : self.assigned_outlet_key,
            'desc'                  : self.desc,
            'invite_link'           : self.invite_link,
            }
    
    @staticmethod
    def create(merchant_acct, group_name=None, desc=None, fan_club_type=None, invite_link=None, assign_outlet_key=None,
               created_by=None):
        
        created_by_username = None
        if is_not_empty(created_by):
            if isinstance(created_by, MerchantUser):
                created_by_username = created_by.username
                
        
        fan_club_setup = FanClubSetup(
                                parent              = merchant_acct.create_ndb_key(),
                                group_name          = group_name,
                                desc                = desc,
                                fan_club_type       = fan_club_type,
                                invite_link         = invite_link,
                                created_by_username = created_by_username,
                                created_by          = created_by.create_ndb_key(),
                                assigned_outlet     = ndb.Key(urlsafe=assign_outlet_key),
                            ) 
        
        
        fan_club_setup.put()
        
        return fan_club_setup
        
    
    def archive(self, archived_by=None):
        
        archived_by_username = None
        if is_not_empty(archived_by):
            if isinstance(archived_by, MerchantUser):
                archived_by_username = archived_by.username
        
        self.is_archived                = True
        self.archived_datetime          = datetime.utcnow()
        self.archived_by                = archived_by.create_ndb_key()
        self.archived_by_username       = archived_by_username
        self.put()
        
        merchant_acct = self.merchant_acct
        merchant_acct.remove_fan_club_setup_configuration(self.to_configuration())
        
        
        
    def publish(self, published_by=None):
        
        published_by_username = None
        if is_not_empty(published_by):
            if isinstance(published_by, MerchantUser):
                published_by_username = published_by.username
        
        self.is_published               = True
        self.published_datetime         = datetime.utcnow()
        self.published_by               = published_by.create_ndb_key()
        self.published_by_username      = published_by_username
        self.put()    
        
        merchant_acct = self.merchant_acct
        merchant_acct.add_fan_club_setup_configuration(self.to_configuration())
    
    @staticmethod
    def list_by_merchant_acct(merchant_acct):
        result = FanClubSetup.query(ndb.AND(FanClubSetup.is_archived==False), ancestor=merchant_acct.create_ndb_key()).fetch(limit=conf.MAX_FETCH_RECORD)
        return result
    
    @staticmethod
    def list_archived_by_merchant_acct(merchant_acct):
        return FanClubSetup.query(ndb.AND(FanClubSetup.is_archived==True), ancestor=merchant_acct.create_ndb_key()).fetch(limit=model_conf.MAX_FETCH_RECORD)
    
    
    @staticmethod
    def update(fan_club_setup, group_name=None, desc=None, fan_club_type=None, assign_outlet_key=None, modified_by=None, invite_link=None):
        
        modified_by_username = None
        if is_not_empty(modified_by):
            if isinstance(modified_by, MerchantUser):
                modified_by_username = modified_by.username
                
        fan_club_setup.group_name            = group_name
        fan_club_setup.desc                  = desc
        fan_club_setup.fan_club_type         = fan_club_type
        fan_club_setup.invite_link           = invite_link
        fan_club_setup.assigned_outlet       = ndb.Key(urlsafe=assign_outlet_key)
        fan_club_setup.modified_by_username  = modified_by_username
        fan_club_setup.modified_by           = modified_by.create_ndb_key() if modified_by else None
        
        
        fan_club_setup.put()