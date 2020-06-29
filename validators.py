# Define a class to the validators in epoch t, t+1 and t+2
import numpy as np

import requests
import json 
#from mpmath import mpf, mp
import math

#import eventlet
#eventlet.monkey_patch()

import near_api

YOCTO_CONSTANT = 10**24 #how many yocto in 1 unit

class Validators():
    '''
    The file path_to_json_private_key_file_master_account should contain account_id and secret_key as json fields
    '''
    def __init__(self, pool_name, path_to_json_private_key_file_master_account, endpoint_url = 'https://rpc.mainnet.near.org'):
        self.pool_name = pool_name

        # RPC hook
        self.provider = near_api.providers.JsonProvider(endpoint_url)

        # create master account signer object
        self.signer = near_api.signer.Signer.from_json_file(path_to_json_private_key_file_master_account)

        # create master account object
        self.master_account = near_api.account.Account(self.provider, self.signer, self.signer.account_id)
        self.master_account.fetch_state()
        #print(self.master_account.state)

    def get_master_account(self):
        return self.master_account

    def get_locked_in_contract(self):
        #self.provider.
        pass
