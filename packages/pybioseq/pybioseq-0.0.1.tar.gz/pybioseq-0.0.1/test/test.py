from pybioseq.fasta import *
from pybioseq import converter
writer = fastaWriter('test.fasta')
writer.append(name='test', comment='test', seq='AAASDFERRIIKLA')
reader = fastaReader('test.fasta').read()
seq = reader[0][2]
for s in seq:
    print(converter.to3(s))
print(converter.translate('AAA'))