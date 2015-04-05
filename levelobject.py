from utils import read_multi


class LevelObject():
    def __init__(self, index, pointer):
        self.index = index
        self.pointer = pointer

    @property
    def tag(self):
        itemtype = "%x" % self.itemtype
        tag = "{0:0>4}-{1:0>2}".format(itemtype, self.index)
        return tag

    def __repr__(self):
        if hasattr(self, "name"):
            name = "%s %s" % (self.tag, self.name)
        else:
            name = self.tag
        s = "%s: (%s, %s)" % (name, self.x, self.y)
        return s

    def read_data(self, filename):
        f = open(filename, 'r+b')
        f.seek(self.pointer)
        self.itemtype = read_multi(f, length=2)
        self.x = read_multi(f, length=2)
        self.y = read_multi(f, length=2)
        f.close()


class LevelObjectSet():
    def __init__(self, index):
        self.index = index
        self.ptrptr = 0xc874 + (3*index)

    def __repr__(self):
        if hasattr(self, "name"):
            name = "%x %s" % (self.index, self.name)
        else:
            name = "%x" % self.index
        s = "%s %x" % (name, self.pointer)

        s2s = []
        for l in self.levelobjects:
            s2 = "    " + str(l)
            s2s.append(s2)

        s2s = sorted(s2s)
        s = "\n".join([s]+s2s)
        return s

    def read_data(self, filename):
        f = open(filename, 'r+b')
        f.seek(self.ptrptr)
        pointer = read_multi(f, length=3)
        # 84d1f2 -> 251f2
        assert pointer & 0xFF8000 == 0x848000
        pointer = (pointer & 0x7FFF) | 0x20000
        self.pointer = pointer
        f.seek(self.pointer)
        self.num_objects = ord(f.read(1))
        f.close()
        self.levelobjects = []
        for i in xrange(self.num_objects):
            pointer = self.pointer + 1 + (6 * i)
            l = LevelObject(index=i, pointer=pointer)
            l.read_data(filename)
            self.levelobjects.append(l)


def get_level_object_sets(filename):
    # Note: There are 180 maps total.
    loss = []
    for i in range(180):
        los = LevelObjectSet(i)
        los.read_data(filename)
        loss.append(los)
    return loss


if __name__ == "__main__":
    from sys import argv
    filename = argv[1]
    loss = get_level_object_sets(filename)
    for l in loss[:10]:
        print l
        print
