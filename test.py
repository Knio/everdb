import cgitb
cgitb.enable(format='text')

import karchive

import time
import random
random.seed(0)

def rand(n):
    return ''.join(chr(random.getrandbits(8)) for i in xrange(n))


def test_empty():
    a = karchive.open('karchive_test.deleteme')
    a.close()
    print '=========='
    a = karchive.open('karchive_test.deleteme')



def test_one():
    a = karchive.open('karchive_test.deleteme')
    f = a.open("test1")
    f.write('data')
    f.close()
    a.close()

    a = karchive.open('karchive_test.deleteme')
    assert a.open('test1').read() == 'data'



def test_archive():


    a = karchive.open('karchive_test.deleteme')

    v = {}

    for i in xrange(100):
        name = rand(random.randint(0, 100))
        data = rand(random.randint(0, 4096 * 4))
        v[name] = data

        f = a.open(name)
        f.write(data)

    a.close()

    print '==========================================='
    a = karchive.open('karchive_test.deleteme')

    for name, data in v.iteritems():
        assert a.open(name).read() == data




if __name__ == '__main__':
    test_empty()
    test_one()
    test_archive()
