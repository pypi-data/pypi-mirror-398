import smartpy as sp


@sp.module
def m():
    import smartpy.stdlib.address_utils as address_utils

    class C(sp.Contract):
        def __init__(self):
            self.data.is_kt1 = False
            self.data.is_same_key_address = False

        @sp.entrypoint
        def ep(self, address):
            self.data.is_kt1 = address_utils.is_kt1(address)

        @sp.entrypoint
        def key_address(self, key):
            self.data.is_same_key_address = address_utils.check_key_address(key)


sc = sp.test_scenario("Test")
c = m.C()
sc += c

alice = sp.test_account("alice")
bob = sp.test_account("bob")

c.ep(alice.address)
sc.verify(c.data.is_kt1 == False)

c.ep(c.address)
sc.verify(c.data.is_kt1 == True)

# Highest KT1 address
c.ep(sp.address("KT1XvNYseNDJJ6Kw27qhSEDF8ys8JhDopzfG"))
sc.verify(c.data.is_kt1 == True)
sc.verify(
    sp.stdlib.address_utils.is_kt1(sp.address("KT1XvNYseNDJJ6Kw27qhSEDF8ys8JhDopzfG"))
    == True
)

# Lowest KT1 address
c.ep(sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT"))
sc.verify(c.data.is_kt1 == True)

# Highest tz1 address
c.ep(sp.address("tz1iydgEAWLmDA7qqDXwPsXEJRXWa9LZHgXV"))
sc.verify(c.data.is_kt1 == False)

# Lowest tz1 address
c.ep(sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"))
sc.verify(c.data.is_kt1 == False)

# Key address
c.key_address((alice.public_key_hash, alice.address))
sc.verify(c.data.is_same_key_address == True)

c.key_address((bob.public_key_hash, alice.address))
sc.verify(c.data.is_same_key_address == False)

c.key_address((alice.public_key_hash, bob.address))
sc.verify(c.data.is_same_key_address == False)

c.key_address((bob.public_key_hash, bob.address))
sc.verify(c.data.is_same_key_address == True)
