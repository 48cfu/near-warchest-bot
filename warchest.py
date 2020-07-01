

# if Microsoft windows uncomment the following 2 lines
import gevent.monkey
gevent.monkey.patch_all()


import requests
#import eventlet
import json 

import math
import numpy as np

import time
import sys

#eventlet.monkey_patch()

from validators import Validators
from blockchain import Blockchain

''' 
RUN PARAMETERS
'''
DEBUG = True
UPDATES_PER_HOUR = 12 #
NODE_ENV = 'betanet' # define blockchain environment
CONTRACT_NAME = 'validator_italia_contract'

PATH_TO_JSON_PRIVATE_KEY_FILE_MASTER_ACCOUNT = 'path_to_home/.near_credentials/betanet/validator_italia.betanet.json'
AGGRESSIVENESS = 0.1 # between 0 and 1. Eg. 0.1 means lock 10% above estimated seat price
YOCTO_CONSTANT = 10**24 #how many yocto in 1 unit
# Amount of gas attached by default 1e14.
DEFAULT_ATTACHED_GAS = 100000000000000
DEPOSIT_ALL_TOKENS_FROM_MASTERACCOUNT_INTO_CONTRACT = True

''' 
NETWORK PARAMETERS
'''
ENDPOINT_URL = 'https://rpc.' + NODE_ENV + '.near.org'
UPDATE_RATE = 60 * (60 // UPDATES_PER_HOUR) #seconds


'''
Main program
'''
bot_has_been_executed = True

while True:
    try: 
        # create blockchain object    
        near_blockchain = Blockchain(ENDPOINT_URL)
        
        # get percentage of epoch and if greater than 95% then update warchest once
        epoch_percentage = near_blockchain.get_percentage_epoch()

        if DEBUG:
            #print('Current', json.dumps(near_blockchain.get_current_validators(), indent=4, sort_keys=True))
            #print('NExt', json.dumps(near_blockchain.get_next_validators(), indent=4, sort_keys=True))
            #print('Proposals',json.dumps(near_blockchain.get_proposals(), indent=4, sort_keys=True))
            #print('Genesis',json.dumps(near_blockchain.genesis, indent=4, sort_keys=True))
            print('Epoch t     seat price', near_blockchain.get_seat_price(epoch='current'))
            print('Epoch t + 1 seat price', near_blockchain.get_seat_price(epoch='next'))
            print('Epoch t + 2 seat price', near_blockchain.get_seat_price(epoch='proposals'))
            print('Percentage current epoch ', epoch_percentage)

        # Make sure bot runs only once per epoch to avoid spamming       
        if epoch_percentage > 95 and bot_has_been_executed:
            bot_has_been_executed = False
        elif epoch_percentage <= 95:
            bot_has_been_executed = True

        # if in debug mode always run
        if not bot_has_been_executed:
            # create master account
            validators_node = Validators(CONTRACT_NAME, PATH_TO_JSON_PRIVATE_KEY_FILE_MASTER_ACCOUNT, ENDPOINT_URL)
            estimated_seat_price_nextnext_epoch = near_blockchain.get_seat_price(epoch='proposals')
            amount_master_account_unlocked = int(validators_node.get_master_account().state['amount'])

            # ping contract before proceding
            # near call my_validator ping '{}' --accountId user1
            '''
            validators_node.get_master_account().function_call(
                contract_id = CONTRACT_NAME, 
                method_name = 'ping', 
                args = None, 
                gas = DEFAULT_ATTACHED_GAS)
            '''

            # if master account has more that 1 NEAR deposit it to contract
            if amount_master_account_unlocked > YOCTO_CONSTANT and DEPOSIT_ALL_TOKENS_FROM_MASTERACCOUNT_INTO_CONTRACT:
                # always try to cover for account cost by subtracting 1 NEAR from the available amount
                to_deposit_in_near = (amount_master_account_unlocked - YOCTO_CONSTANT)// YOCTO_CONSTANT 
                
                # near call my_validator deposit '{}' --accountId user1 --amount AMOUNT_IN_NEAR
                validators_node.get_master_account().function_call(
                    contract_id = CONTRACT_NAME, 
                    method_name = 'deposit', 
                    args = None, 
                    gas = DEFAULT_ATTACHED_GAS, 
                    amount = to_deposit_in_near)

            
            # Total staked balance of the entire pool
            # near view my_validator get_total_staked_balance '{}'
            contract_state = validators_node.provider.get_account(account_id = CONTRACT_NAME)

            # Total locked balance of the entire pool
            amount_contract_account_locked = int(validators_node.get_master_account().view_function(
                                                            contract_id = CONTRACT_NAME, 
                                                            method_name = 'get_total_staked_balance', 
                                                            args = None)['result'])

            # Pool's seat price to bid at epoch t + 2
            to_propose = int(estimated_seat_price_nextnext_epoch * (1 + AGGRESSIVENESS))

            if DEBUG:
                print('Master account state', validators_node.get_master_account().state)
                print('Contract staked balance', amount_contract_account_locked)
                print('To propose at time t + 2', to_propose)
            
            if amount_contract_account_locked < to_propose:
                # low current locked stake. Stake some near token

                # master account UNSTACKED balance
                # near view my_validator get_account_unstaked_balance '{"account_id": "user1"}'
                amount_master_account_unstaked_balance = int(validators_node.get_master_account().view_function(
                                                            contract_id = CONTRACT_NAME, 
                                                            method_name = 'get_account_unstaked_balance', 
                                                            args = {'account_id':  validators_node.get_master_account().account_id})['result'])

                if DEBUG:
                    print('Low current locked stake. Stake some near token!')
                    print('Available unstaked balance', amount_master_account_unstaked_balance)

                to_stake = min(to_propose - amount_contract_account_locked, amount_master_account_unstaked_balance)

                if to_stake > 0:
                    # do the actual staking transaction
                    # near call <POOL_ID> stake '{"amount": "<STAKE_AMOUNT>"}' --accountId <WARCHEST_ID>
                    receipt = validators_node.get_master_account().function_call(
                        contract_id = CONTRACT_NAME, 
                        method_name = 'stake', 
                        args = {'amount': str(to_stake)}, 
                        gas = DEFAULT_ATTACHED_GAS)
                    if DEBUG:
                        print('Staking receipt', receipt)
            elif amount_contract_account_locked > to_propose:
                # high current locked stake. Unstake some near token

                # master account STACKED balance
                # near view my_validator get_account_staked_balance '{"account_id": "user1"}'
                amount_master_account_staked_balance = int(validators_node.get_master_account().view_function(
                                                            contract_id = CONTRACT_NAME, 
                                                            method_name = 'get_account_staked_balance', 
                                                            args = {'account_id':  validators_node.get_master_account().account_id})['result'])

                if DEBUG:
                    print('High current locked stake. Unstake some near token!')
                    print('Available staked balance', amount_master_account_staked_balance)

                to_unstake = min(amount_contract_account_locked - to_propose, amount_master_account_staked_balance)
                if to_unstake > 0:
                    # near call <POOL_ID> stake '{"amount": "<STAKE_AMOUNT>"}' --accountId <WARCHEST_ID>
                    receipt = validators_node.get_master_account().function_call(
                        contract_id = CONTRACT_NAME, 
                        method_name = 'unstake', 
                        args = {'amount': str(to_unstake)}, 
                        gas = DEFAULT_ATTACHED_GAS)

                    if DEBUG:
                        print('Staking receipt', receipt)
        else:
            print('Nothing to do now. Epoch at %s percent' % epoch_percentage)
            

    except:
        # avoid service from dying. retry again in 60 seconds
        # can add logging
        if DEBUG:
            print("Unexpected error:", sys.exc_info()[0])
            print('Waiting 60 seconds before sending other requests')
        time.sleep(60) 
        continue
    if DEBUG:
        print('Waiting %s seconds before sending other requests' % UPDATE_RATE)
    # wait some minutes before sending other RPC requests
    time.sleep(UPDATE_RATE)
