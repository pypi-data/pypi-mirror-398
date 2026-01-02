# import pkg_resources
# from aldepyde.data import data as data

class ProteinStats:
    #TODO Clean this class a lot... also add some things
    #TODO Isoelectric point
    def __init__(self, His_Is_Charged=True, Cys_Is_Polar=True, Charged_Is_Polar=True):
        self.AAs = "ARNDCEQGHILKMFPSTWYV"
        self.POSITIVE = "RK"
        self.NEGATIVE = "ED"
        self.POLAR = "STNQ"
        self.NONPOLAR = "AVILMFYWGP"
        self.CHARGED = "RKED"

        if His_Is_Charged:
            self.CHARGED += "H"
            self.POSITIVE += "H"
        else:
            self.POLAR += "H"

        if Cys_Is_Polar:
            self.POLAR += "C"
        else:
            self.NONPOLAR += "C"

        if Charged_Is_Polar:
            self.POLAR += self.POSITIVE
            self.POLAR += self.NEGATIVE

    def GetNumResidues(self, sequence):
        ret_dic = {}
        for c in self.AAs:
            ret_dic[c] = sequence.count(c)
        return ret_dic


    def GetCharge(self, sequence):
        total_charge = 0
        for c in sequence:
            if c in self.POSITIVE:
                total_charge += 1
            elif c in self.NEGATIVE:
                total_charge -= 1
        return total_charge

    def NumCharged(self, sequence):
        total = 0
        for c in sequence:
            if c in self.CHARGED:
                total += 1
        return total

    def NumPolar(self, sequence):
        total = 0
        for c in sequence:
            if c in self.POLAR:
                total += 1
        return total

    def PercentCharged(self, sequence):
        num_charged = 0
        for c in sequence:
            if c in self.POSITIVE or c in self.NEGATIVE:
                num_charged += 1
        return num_charged / len(sequence)

    def PercentPolarC(self, sequence):
        num_polar = 0
        for c in sequence:
            if c in self.POLAR_CHECK:
                num_polar += 1
        return num_polar / len(sequence)

    def PercentPolar(self, sequence):
        num_polar = 0
        for c in sequence:
            if c in self.POLAR:
                num_polar += 1
        return num_polar / len(sequence)

    def PercentNonPolar(self, sequence):
        num_not = 0
        for c in sequence:
            if c in self.NONPOLAR:
                num_not += 1
        return num_not / len(sequence)

    # def GetMass(self, sequence, from_abundances=False):
    #     return data.ProteinMass(sequence, from_abundances=from_abundances)