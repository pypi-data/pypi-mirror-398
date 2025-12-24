class fastaReader:
    def __init__(self, path):
        self.path = path

    def read(self):
        seq_entry_list = []
        with open(self.path, 'r') as file:
            name = ''
            seq = ''
            comment = ''
            for line in file:
                if not line.strip():
                    continue
                if line.startswith('>'):
                    if name != '' and seq != '':
                        seq_entry_list.append((name, comment, seq))
                        comment = ''
                        seq = ''
                    for idx ,letter in enumerate(line[1:]):
                        if letter.isspace():
                            break
                    name = line[1:idx + 1].strip()
                    comment = line[idx+1:].strip()
                else:
                    if name == '':
                        raise ValueError("FASTA file format error: can't find fasta id.")
                    seq += line.strip()
            if name != '' and seq != '':
                seq_entry_list.append((name, comment, seq))
            return seq_entry_list

class fastaWriter:
    def __init__(self, path):
        self.path = path

    @staticmethod
    def __write_entry(file, name, comment, seq):
        file.write(f'>{name} {comment}\n')
        for idx, letter in enumerate(seq):
            file.write(letter)
            if (idx + 1) % 80 == 0:
                file.write('\n')
        file.write('\n')

    def append(self, name, comment, seq):
        with open(self.path, 'a') as file:
            self.__write_entry(file, name, comment, seq)

    def write_all(self, seq_entry_list):
        with open(self.path, 'w') as file:
            for name, comment, seq in seq_entry_list:
                self.__write_entry(file, name, comment, seq)

    def write(self, name, comment, seq):
        with open(self.path, 'w') as file:
            self.__write_entry(file, name, comment, seq)