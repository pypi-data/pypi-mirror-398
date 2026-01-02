from modalg.group import AdditiveIdentity, AdditiveInverse, Group
from modalg.abelianGroup import AbelianGroup
from modalg import myfunctions
from modalg.ring import MultiplicativeIdentity, Ring
from modalg.comm_ring import CommutativeRing

def test_CommRing1():
    ''' testing commutativity of multiplication '''
    a = CommutativeRing()
    b = CommutativeRing()
    a.addObject(2)
    a.addObject(3)
    b.addObject(2)
    b.addObject(3)
    a.multiply(2,3)
    b.multiply(3,2)
    assert a.group[7] == b.group[7]

def test_CommRing2():
    ''' testing def of multiplicative and additive inverses '''
    a = CommutativeRing()
    a.addObject('apple')
    a.multiply('apple', MultiplicativeIdentity())
    assert a.__str__() == "Ring: ['Additive identity', 'Multiplicative identity', 'Additive inverse of Multiplicative identity', 'apple', 'Additive inverse of apple']"
    a.multiply('apple', AdditiveIdentity())
    assert a.__str__() == "Ring: ['Additive identity', 'Multiplicative identity', 'Additive inverse of Multiplicative identity', 'apple', 'Additive inverse of apple']"
    a.multiply('apple', AdditiveInverse('apple'))
    assert a.__str__() == """Ring: ['Additive identity', 'Multiplicative identity', 'Additive inverse of Multiplicative identity', 'apple', 'Additive inverse of apple', {('apple', 'Additive inverse of apple'), ('Additive inverse of apple', 'apple')}, "Additive inverse of {('apple', 'Additive inverse of apple'), ('Additive inverse of apple', 'apple')}"]"""

def test_CommRing3():
    a = CommutativeRing()
    a.addObject(2)
    a.addObject(3)
    a.multiply(2,3)
    print(a)
  #  assert a.__str__() == "Ring: ['Additive identity', 'Multiplicative identity', 'Additive inverse of Multiplicative identity', '2', 'Additive inverse of 2', '3', 'Additive inverse of 3', '{(2, 3), (3, 2)}', 'Additive inverse of {(2, 3), (3, 2)}']"
    a.multiply({(2,3),(3,2)}, 3)
   # assert a.__str__() == "Ring: ['Additive identity', 'Multiplicative identity', 'Additive inverse of Multiplicative identity', '2', 'Additive inverse of 2', '3', 'Additive inverse of 3', '{(2, 3), (3, 2)}', 'Additive inverse of {(2, 3), (3, 2)}', '{(2, 3, 3), (3, 3, 2)}', 'Additive inverse of {(2, 3, 3), (3, 3, 2)}']"

    
test_CommRing1()
test_CommRing2()
#test_CommRing3()
