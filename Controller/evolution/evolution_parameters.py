class EvolutionParameters():
    """
    Interface for evolution parameters encapsulation.
    """

    def to_dictionary(self):
        raise NotImplementedError

    def to_string(self):
        raise NotImplementedError


class EvolutionaryAlgorithmParameters(EvolutionParameters):
    """
    Encapsulates parameters of the simple evolutionary algorithm.
    """

    @staticmethod
    def from_dict(data):
        """
        Loads parameters from json data into class instance.
        :param data: Data to be loaded.
        :return: Instance of EvolutionaryAlgorithmParameters using specified data.
        """
        params = EvolutionaryAlgorithmParameters(
            data["pop_size"],
            data["cxpb"],
            data["mut"],
            data["ngen"],
            data["game_batch_size"],
            data["cxindpb"],
            data["hof_size"],
            data["elite"],
            data["selection"])
        return params

    def __init__(self,
                 pop_size,
                 cxpb,
                 mut,
                 ngen,
                 game_batch_size,
                 cxindpb,
                 hof_size,
                 elite,
                 selection):
        self._pop_size = pop_size
        self._cxpb = cxpb
        self._mut = mut
        self._ngen = ngen
        self._game_batch_size = game_batch_size
        self._cxindpb = cxindpb
        self._hof_size = hof_size
        self._elite = elite
        self._selection = selection

    @property
    def pop_size(self):
        return self._pop_size

    @property
    def cxpb(self):
        return self._cxpb

    @property
    def mut(self):
        return self._mut

    @property
    def ngen(self):
        return self._ngen

    @property
    def fit_repetitions(self):
        return self._game_batch_size

    @property
    def cxindpb(self):
        return self._cxindpb

    @property
    def hof_size(self):
        return self._hof_size

    @property
    def elite(self):
        return self._elite

    @property
    def selection(self):
        return self._selection

    def to_dictionary(self):
        """
        Converts current object to json-style dictionary.
        :return: A dictionary with current object data.
        """
        data = {}
        data["pop_size"] = self._pop_size
        data["cxpb"] = self._cxpb
        data["mut"] = self._mut
        data["ngen"] = self._ngen
        data["game_batch_size"] = self._game_batch_size
        data["cxindpb"] = self._cxindpb
        data["hof_size"] = self._hof_size
        data["elite"] = self._elite
        data["selection"] = self._selection
        return data

    def to_string(self):
        """
        Returns a string representation of the current object.
        :return: a string representation of the current object.
        """
        return "pop_size: {}, xover: {}/{}, mut: {}, hof: {}, elite: {}, sel: {}".format(self.pop_size, self.cxpb,
                                                                                         self.cxindpb,
                                                                                         self.mut, self.hof_size,
                                                                                         self.elite, self.selection)


class EvolutionStrategyParameters(EvolutionParameters):
    """
    Encapsulates parameters of the evolution using evolution strategy.
    """

    @staticmethod
    def from_dict(data):
        """
        Loads parameters from json data into class instance.
        :param data: Data to be loaded.
        :return: Instance of EvolutionStrategyParameters using specified data.
        """
        params = EvolutionStrategyParameters(
            data["pop_size"],
            data["ngen"],
            data["game_batch_size"],
            data["hof_size"],
            data["elite"],
            data["sigma"])
        return params

    def __init__(self,
                 pop_size,
                 ngen,
                 game_batch_size,
                 hof_size,
                 elite,
                 sigma):
        self._pop_size = pop_size
        self._ngen = ngen
        self._game_batch_size = game_batch_size
        self._hof_size = hof_size
        self._elite = elite
        self._sigma = sigma

    @property
    def pop_size(self):
        return self._pop_size

    @property
    def ngen(self):
        return self._ngen

    @property
    def fit_repetitions(self):
        return self._game_batch_size

    @property
    def hof_size(self):
        return self._hof_size

    @property
    def elite(self):
        return self._elite

    @property
    def sigma(self):
        return self._sigma

    def to_dictionary(self):
        """
        Converts current object to json-style dictionary.
        :return: A dictionary with current object data.
        """
        data = {}
        data["pop_size"] = self._pop_size
        data["ngen"] = self._ngen
        data["game_batch_size"] = self._game_batch_size
        data["hof_size"] = self._hof_size
        data["elite"] = self._elite
        return data

    def to_string(self):
        """
        Returns a string representation of the current object.
        :return: a string representation of the current object.
        """
        return "Evolution Strategy - pop_size: {}, hof: {}, elite: {}, sigma: {}".format(self.pop_size, self.hof_size,
                                                                                         self.elite, self.sigma)


class DifferentialEvolutionParameters(EvolutionParameters):
    """
    Encapsulates parameters of the evolution using evolution strategy.
    """

    @staticmethod
    def from_dict(data):
        """
        Loads parameters from json data into class instance.
        :param data: Data to be loaded.
        :return: Instance of DifferentialEvolutionParameters using specified data.
        """
        params = DifferentialEvolutionParameters(
            data["pop_size"],
            data["ngen"],
            data["game_batch_size"],
            data["hof_size"],
            data["cr"],
            data["f"])
        return params

    def __init__(self,
                 pop_size,
                 ngen,
                 game_batch_size,
                 hof_size,
                 cr,
                 f):
        self._pop_size = pop_size
        self._ngen = ngen
        self._game_batch_size = game_batch_size
        self._hof_size = hof_size
        self._cr = cr
        self._f = f
        self.elite = 0 # Not currently using elite in diff evolution.

    @property
    def pop_size(self):
        return self._pop_size

    @property
    def ngen(self):
        return self._ngen

    @property
    def fit_repetitions(self):
        return self._game_batch_size

    @property
    def hof_size(self):
        return self._hof_size

    @property
    def cr(self):
        return self._cr

    @property
    def f(self):
        return self._f

    def to_dictionary(self):
        """
        Converts current object to json-style dictionary.
        :return: A dictionary with current object data.
        """
        data = {}
        data["pop_size"] = self._pop_size
        data["ngen"] = self._ngen
        data["game_batch_size"] = self._game_batch_size
        data["hof_size"] = self._hof_size
        data["cr"] = self._cr
        data["f"] = self._f
        return data

    def to_string(self):
        """
        Returns a string representation of the current object.
        :return: a string representation of the current object.
        """
        return "Differential Evolution - pop_size: {}, hof: {}, cr: {}, f: {}".format(self.pop_size,
                                                                                      self.hof_size,
                                                                                      self.cr,
                                                                                      self.f)
