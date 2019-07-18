class Asset(object):
    __cache__ = {}
    __installed__ = {}
    def __init__(self, dic):
        self.dic = dic
        self.id = dic['id']
        asset = Asset.__cache__[self.id] = self
        self.__dict__.update(dic)

    @classmethod
    def get(self, id):
        return Asset.__cache__.get(id, None)

    @classmethod
    def get_asset(self, id):
        asset = Asset.get(id)
        if asset:
            return asset.dic


    def is_installed(self):
        filename = basename(self.dic['file'])
        folder = self.dic['folder']

        return filename in self.__installed__[folder]
