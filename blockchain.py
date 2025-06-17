import time
import hashlib
import json

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions  # list of txns
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), [], "0")
        self.chain.append(genesis_block)

    def last_block(self):
        return self.chain[-1]

    def add_transaction(self, sender, recipient, amount, message=""):
        transaction = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "message": message
        }
        self.unconfirmed_transactions.append(transaction)

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_block(self, block, proof):
        last_hash = self.last_block().hash
        if last_hash != block.previous_hash:
            return False
        if not proof.startswith('0' * Blockchain.difficulty):
            return False
        block.hash = proof
        self.chain.append(block)
        return True

    def mine(self):
        if not self.unconfirmed_transactions:
            return False
        last_block = self.last_block()
        new_block = Block(index=last_block.index + 1,
                          timestamp=time.time(),
                          transactions=self.unconfirmed_transactions,
                          previous_hash=last_block.hash)
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index
