from utils import (read_multi, write_multi,
                   ITEM_NAMES_TABLE, LOCATION_NAMES_TABLE,
                   utilrandom as random)


loss, objname, locname = None, None, None
unknown_itemcodes = []


class LevelObject():
    def __init__(self, index, pointer):
        self.index = index
        self.pointer = pointer

    @property
    def tag(self):
        itemtype = "%x" % self.itemtype
        tag = "{0:0>4}-{1:0>2}".format(itemtype, self.index)
        return tag

    @property
    def quicktag(self):
        if hasattr(self, "name"):
            return self.name
        else:
            return "Object {0:0>4}".format("%x" % self.itemtype)

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
        if self.itemtype in objname:
            self.name = objname[self.itemtype]
        self.x = read_multi(f, length=2)
        self.y = read_multi(f, length=2)
        f.close()

    def write_data(self, filename):
        f = open(filename, 'r+b')
        f.seek(self.pointer)
        write_multi(f, self.itemtype, length=2)
        write_multi(f, self.x, length=2)
        write_multi(f, self.y, length=2)
        f.close()


class LevelObjectSet():
    def __init__(self, index):
        self.index = index
        self.ptrptr = 0xc874 + (3*index)
        if self.index in locname:
            self.name = locname[self.index]

    @property
    def num_objects(self):
        return len(self.levelobjects)

    def __repr__(self):
        from collections import Counter
        if hasattr(self, "name"):
            name = "%x %s" % (self.index, self.name)
        else:
            name = "%x" % self.index
        s = "%s %x\n" % (name, self.pointer)

        quicktags = []
        for l in self.levelobjects:
            quicktags.append(l.quicktag)
        quickdict = Counter(quicktags)
        for quicktag, amount in quickdict.most_common():
            s += "    x%s %s\n" % (amount, quicktag)

        return s.strip()

    def read_data(self, filename):
        f = open(filename, 'r+b')
        f.seek(self.ptrptr)
        pointer = read_multi(f, length=3)
        # 84d1f2 -> 251f2
        assert pointer & 0xFF8000 == 0x848000
        pointer = (pointer & 0x7FFF) | 0x20000
        self.pointer = pointer
        f.seek(self.pointer)
        num_objects = ord(f.read(1))
        f.close()
        self.levelobjects = []
        for i in xrange(num_objects):
            pointer = self.pointer + 1 + (6 * i)
            l = LevelObject(index=i, pointer=pointer)
            l.read_data(filename)
            self.levelobjects.append(l)

    def write_data(self, filename):
        f = open(filename, 'r+b')
        f.seek(self.pointer)
        f.write(chr(self.num_objects))
        f.close()
        for (i, l) in enumerate(self.levelobjects):
            l.pointer = self.pointer + 1 + (6 * i)
            l.index = i
            l.write_data(filename)

    def narrow_unknowns(self, strict=False):
        unknowns = [u for u in unknown_itemcodes if u in
                    [i.itemtype for i in self.levelobjects]]
        if unknowns:
            u = random.choice(unknowns)
            self.levelobjects = [i for i in self.levelobjects if
                                 i.itemtype == u or i.itemtype not in unknowns]
            if strict:
                self.levelobjects = [i for i in self.levelobjects
                                     if i.itemtype == u]


def get_level_object_sets(filename=None):
    global loss
    if loss is None:
        loss = []
        # Note: There are 180 maps total.
        for i in range(180):
            los = LevelObjectSet(i)
            los.read_data(filename)
            loss.append(los)
        return get_level_object_sets()
    else:
        return loss


def get_level_object_set(index):
    ls = [l for l in get_level_object_sets() if l.index == index]
    return ls[0]


def get_object_name_dict():
    global objname
    if objname is None:
        objname = {}
        for line in open(ITEM_NAMES_TABLE):
            line = line.strip()
            if ' ' in line:
                while '  ' in line:
                    line = line.replace('  ', ' ')
                (code, name) = tuple(line.split(' ', 1))
                code = int(code, 0x10)
                objname[code] = name
                objname[name] = code
            else:
                code = int(line, 0x10)
                unknown_itemcodes.append(code)
        return get_object_name_dict()
    else:
        return objname


def get_location_name_dict():
    global locname
    if locname is None:
        locname = {}
        for line in open(LOCATION_NAMES_TABLE):
            line = line.strip()
            if ' ' in line:
                while '  ' in line:
                    line = line.replace('  ', ' ')
                (code, name) = tuple(line.split(' ', 1))
                code = int(code, 0x10)
                locname[code] = name
                locname[name] = code
        return get_location_name_dict()
    else:
        return locname


get_object_name_dict()
get_location_name_dict()

if __name__ == "__main__":
    from sys import argv
    filename = argv[1]
    if len(argv) > 2:
        from shutil import copyfile
        outfile = argv[2]
        copyfile(filename, outfile)
    else:
        outfile = filename
    unknown_itemcodes = sorted(unknown_itemcodes)
    get_level_object_sets(filename)
    ls = get_level_object_sets()
    for l in ls[:20]:
        l.narrow_unknowns()
        l.write_data(outfile)
        print l
        print
