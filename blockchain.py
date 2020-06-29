# Define a class to the validators in epoch t, t+1 and t+2
import numpy as np

import requests
import json 

import near_api

YOCTO_CONSTANT = 10**24 #how many yocto in 1 unit

class Blockchain():
  def __init__(self, endpoint_url = 'https://rpc.mainnet.near.org'):
    self.status = None
    self.genesis = None
    self.validators = None

    # RPC hook
    self.provider = near_api.providers.JsonProvider(endpoint_url)
    
    self.update()    
    
  def update(self):
    #load validators and update everything
    self.status = self.get_status_rpc()
    self.genesis = self.get_genesis_config_rpc()
    self.validators = self.get_validators_rpc()

    if None in (self.status, self.genesis, self.validators):
        raise SystemExit('Couldn\'t load lists from RPC')

    #self.min_uptime = genesis['online_min_threshold'][0]/genesis['online_min_threshold'][1]

  def get_current_validators(self):
    return self.get_validators('current')
  def get_next_validators(self):
    return self.get_validators('next')
  def get_proposals(self):
    return self.get_validators('proposals')

  def get_percentage_epoch(self):
    epoch_length = self.genesis['epoch_length']
    epoch_start_height = self.validators['epoch_start_height'] 
    latest_block_height = self.status['sync_info']['latest_block_height']

    return 100.0 * (latest_block_height - epoch_start_height)/epoch_length

  def get_validators(self, epoch = 'current'):
    validators = None
    if epoch == 'current':
        validators = {x['account_id']: x for x in self.validators['current_validators']} 
    elif epoch == 'next':
        validators = {x['account_id']: x for x in self.validators['next_validators']} 
    elif epoch == 'proposals':
        '''
        During the epoch, outcome of staking transactions produce `proposals`, which are collected, in the form of `Proposal`s.
        At the end of every epoch `T`, next algorithm gets executed to determine validators for epoch `T + 2`:

        1. For every validator in `current_validators` determine `num_blocks_produced`, `num_chunks_produced` based on what 
        they produced during the epoch.
        2. Remove validators, for whom `num_blocks_produced < num_blocks_expected * BLOCK_PRODUCER_KICKOUT_THRESHOLD` or 
        `num_chunks_produced < num_chunks_expected * CHUNK_PRODUCER_KICKOUT_THRESHOLD`.
        3. Add validators from `proposals`, if validator is also in `current_validators`, considered stake of the proposal is `0 
        if proposal.stake == 0 else proposal.stake + reward[proposal.account_id]`.
        4. Find seat price `seat_price = findSeatPrice(current_validators - kickedout_validators + proposals, num_seats)`, where 
        each validator gets `floor(stake[v] / seat_price)` seats and `seat_price` is highest integer number such that total number 
        of seats is at least `num_seats`.
        '''
        validators = {x['account_id']: x for x in self.validators['current_proposals']}  
        next_validators = {x['account_id']: x for x in self.validators['next_validators']}
        # append next validators to proposal
        for account_id, properties in next_validators.items():
            # if accound id already in proposals, then don't update it with rewards from next
            if account_id not in validators:
                validators[account_id] = {'account_id': account_id, 'stake': properties['stake']}
            
    return validators


  def get_seat_price(self, epoch = 'current'):
    validators = self.get_validators(epoch)
    stakes = []
    total_stakes = 0
    for properties  in validators.values():
        stakes.append(int(properties['stake']))
        total_stakes += int(properties['stake'])

    """
    Find seat price given set of stakes and number of seats required.
    Seat price is highest integer number such that if you sum `floor(stakes[i] / seat_price)` it is at least `number_seats`.
    """        
    number_seats = self.genesis['num_block_producer_seats']
    assert total_stakes >= number_seats, "Total stakes should be above number of seats"
    left, right = YOCTO_CONSTANT, total_stakes + 1
    while True:
        if left == right - 1:
            return left
        seat_price = (left + right) // 2
        found = False
        current_sum = 0
        for stake in stakes:
            current_sum += stake // seat_price # number of seats for current validator = floor(stake / seat_price)
            if current_sum >= number_seats: # if there are too many seats then the current price (=mid) is too low. Move left threshold up
                left = seat_price
                found = True
                break

        if not found:
            right = seat_price


  def get_status_rpc(self):
    # request data for status
    return self.provider.get_status()

  def get_validators_rpc(self):
    # request data to get validators
    return self.provider.get_validators()
  
  def get_genesis_config_rpc(self):
    # request data to genesis config
    return self.provider.json_rpc('EXPERIMENTAL_genesis_config', [None])

  