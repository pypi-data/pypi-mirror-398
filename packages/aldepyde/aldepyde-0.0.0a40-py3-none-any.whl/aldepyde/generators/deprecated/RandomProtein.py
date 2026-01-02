import random
import math
import requests
import json

from aldepyde.stats.ProteinStats import *

class InvalidDistribution(Exception):
    pass

class ImpossibleSetting(Exception):
    pass


# TODO This whole thing needs to be cleaned up to better align with more modern python
class RandomProtein:
    # Hardcode data for now
    def __init__(self, His_Is_Charged=True, Cys_Is_Polar=True, Charged_Is_Polar=True, Distribution="Swiss"):
        self.Analyzer = ProteinStats(His_Is_Charged, Cys_Is_Polar, Charged_Is_Polar)

        self._ACCEPTED_METHODS = ["Random", "Custom", "Builder", "Grouper"]
        self._ACCEPTED_PRESETS = ["Swiss", "CHG"]
        self.His_Is_Charged = His_Is_Charged
        self.Cys_Is_Polar = Cys_Is_Polar
        self.Charged_Is_Polar = Charged_Is_Polar

        self.LoadPresetDistribution(Distribution)

        self._AAs = "ARNDCEQGHILKMFPSTWYV"
        self._POSITIVE = "RK"
        self._NEGATIVE = "ED"
        self._POLAR = "STNQ"
        self._NONPOLAR = "AVILMFYWGP"
        self._CHARGED = "RKED"

        if His_Is_Charged:
            self._CHARGED += "H"
            self._POSITIVE += "H"
        else:
            self._POLAR += "H"

        if Cys_Is_Polar:
            self._POLAR += "C"
        else:
            self._NONPOLAR += "C"

        if Charged_Is_Polar:
            self._POLAR += self._POSITIVE
            self._POLAR += self._NEGATIVE

    def GetNP(self):
        return self. _NONPOLAR



    def LoadPresetDistribution(self, preset="Swiss"):
        if preset.upper() == "Swiss".upper():
            _stream = pkg_resources.resource_stream("aldepyde", 'json/Swiss_Prot.json')
            self.distribution = json.load(_stream)['Amino Acid Distribution']
        elif preset.upper() == "CHG":
            _stream = pkg_resources.resource_stream("aldepyde", 'json/CHG.json')
            self.distribution = json.load(_stream)['Amino Acid Distribution']
        else:
            raise InvalidDistribution(
                f"Preset must be one of the following: {self._ACCEPTED_PRESETS}\n\t"
                f"Chosen: {preset}")

    def GetAminoAcids(self):
        return self._AAs

    def SetAminoAcids(self, AAs):
        if isinstance(AAs, str):
            self._AAs = str
        elif isinstance(AAs, list):
            self._AAs = "".join(AAs)

    # TODO add setters for polar, nonpolar, etc.

    def AddAminoAcid(self, AA):
        if AA not in self._AAs:
            self._AAs += AA

    def RemoveAminoAcid(self, AA):
        if AA in self._AAs:
            self._AAs.replace(AA, "")
        if AA in self._POLAR:
            self._POLAR.replace(AA, "")
        if AA in self._CHARGED:
            self._CHARGED.replace(AA, "")
        if AA in self._POSITIVE:
            self._POSITIVE.replace(AA, "")
        if AA in self._NEGATIVE:
            self._NEGATIVE.replace(AA, "")

    def ConfigureAA(self, AA, is_polar=False, is_charged=False, is_positive=False, is_negative=False):
        # if is_charged and not (is_positive or is_negative):
        #     raise ImpossibleSettingsException("The residue must be either positive or negative if it carries a charge")
        if is_negative and is_positive:
            raise ImpossibleSetting("The residue cannot be both positive and negative")

        if is_charged and self.Charged_Is_Polar and AA not in self._POLAR:
            self._POLAR += AA
        if is_charged and AA not in self._CHARGED:
            self._CHARGED += AA
        if is_negative and AA not in self._NEGATIVE:
            self._NEGATIVE += AA
        if is_positive and AA not in self._POSITIVE:
            self._POSITIVE += AA
        if is_polar and AA not in self._POLAR:
            self._POSITIVE += AA
        elif AA not in self._NONPOLAR:
            self._NONPOLAR += AA
        if AA not in self._AAs:
            self._AAs += AA

    def configure(self, His_Is_Charged=True, Cys_Is_Polar=True, Charged_Is_Polar=True):
        self.__init__(His_Is_Charged, Cys_Is_Polar, Charged_Is_Polar)

    def _load(self, json_str):
        self.distribution = self._NormalizeValues(json.loads(json_str)["Amino Acid Distribution"])

    def _NormalizeValues(self, dic):
        total = 0
        for key in dic.keys():
            total += float(dic[key])
        for key in dic.keys():
            dic[key] = float(dic[key]) / total
        return dic

    def LoadDistributionFromFile(self, dist_json_path):
        with open(dist_json_path, "r") as fp:
            self._load(fp.read())

    def LoadDistributionFromURL(self, URL):
        response = requests.get(URL)
        if response.status_code == 200:
            self._load(json.dumps(response.json()))
        else:
            raise ConnectionError(f"Invalid url: {URL}")

    def GenerateProtein(self, length, batch_size=1, method="Random", percent_polar=None,
                        percent_charged=None, final_charge=None, charge_range=None,
                        timeout=30, max_attempts=None, verbose=False, cleanup=False, crash_at_bad_settings=False):

        self.verbose = verbose
        # TODO make it so max_attempts is actually used
        if not self.VerifySettings(length, batch_size=batch_size, method=method, percent_polar=percent_polar,
                                   percent_charged=percent_charged, final_charge=final_charge,
                                   charge_range=charge_range,
                                   max_attempts=max_attempts, crash=crash_at_bad_settings):
            return None

        method = method.upper()
        ret_list = []
        for _ in range(batch_size):
            sequence = "$" * length
            if method == "Random".upper():
                # sequence = self._Random(length)
                attempt = 0
                while not self._ValidateSequence(sequence, percent_polar,
                                                 percent_charged, final_charge, charge_range):
                    sequence = self._Random(length)
                    if verbose:
                        attempt += 1
                        print(f"\rAttempt: {attempt}", end="")
            elif method == "Custom".upper():
                sequence = self._Custom(length)
            elif method == "Builder".upper():
                sequence = self._Builder(length, percent_charged, percent_polar, final_charge)
            elif method == "Grouper".upper():
                attempt = 0
                while not self._ValidateSequence(sequence, percent_polar,
                                                 percent_charged, final_charge, charge_range):
                    sequence = self._Grouper(length, percent_polar, percent_charged, final_charge)
                    if verbose:
                        attempt += 1
                        print(f"\rAttempt: {attempt}", end="")

            if cleanup:
                if verbose:
                    print("\nCleaning result sequence")
                sequence = self._CleanPolar(sequence, percent_polar)
            ret_list.append(sequence)

        if verbose:
            for result in ret_list:
                print(
                    f"Result: {result}\nPercent Polar: {self.Analyzer.PercentPolar(result)}\n"
                    f"Percent Charged: {self.Analyzer.PercentCharged(result)}"
                    f"\nPercent NonPolar: {self.Analyzer.PercentNonPolar(result)}"
                    f"\nTotal Charge: {self.Analyzer.GetCharge(result)}\n")

        return ret_list

    def _Random(self, length):
        sequence = ""
        for i in range(length):
            sequence += self._AAs[random.randrange(0, len(self._AAs))]
        return sequence

    def _Custom(self, length):
        items = list(self.distribution.keys())
        probabilities = list(self.distribution.values())
        return "".join(random.choices(items, weights=probabilities, k=length))

    def _Builder(self, length, percent_charged, percent_polar, final_charge):
        sequence = []
        pc = percent_charged
        pp = percent_polar

        percent_unclear = 0

        unclear = ""

        if percent_charged is None:
            percent_charged = 0
            unclear += self._CHARGED
        if percent_polar is None:
            percent_polar = 0
            unclear += self._POLAR
        unclear += self._NONPOLAR

        u = set()
        for c in unclear:
            u.add(c)
        unclear = ""
        for c in u:
            unclear += c

        if pc is None or pp is None:
            percent_unclear = 1 - (percent_polar + percent_charged)

        # sequence = ["X"] * length
        for i in range(math.ceil(length * percent_polar)):
            sequence.append(random.choice(self._POLAR))
        for i in range(math.ceil(length * percent_polar),
                       math.ceil(length * percent_polar) + math.ceil(
                           length * percent_charged) - self.Analyzer.NumCharged(sequence)):
            sequence.append(random.choice(self._CHARGED))

        if percent_unclear < 0:
            for _ in range(length * percent_unclear):
                sequence.append(random.choice(self._NONPOLAR))

        if final_charge is not None:
            disparity = final_charge - self.Analyzer.GetCharge(sequence)
            ind = 0
            while not (disparity == 0 or disparity == -1 or disparity == 1) and ind < len(sequence):
                if disparity > 0 and sequence[ind] in self._NEGATIVE:
                    sequence[ind] = random.choice(self._POSITIVE)
                    disparity -= 2
                if disparity < 0 and sequence[ind] in self._POSITIVE:
                    sequence[ind] = random.choice(self._NEGATIVE)
                    disparity += 2
                ind += 1

            # if not ind < len(sequence):
            while not (disparity == 0):
                if disparity == 0 or len(sequence) >= length:
                    break
                elif disparity > 0:
                    sequence += random.choice(self._POSITIVE)
                    disparity -= 1
                else:
                    sequence += random.choice(self._NEGATIVE)
                    disparity += 1

        while len(sequence) < length:
            sequence.append(random.choice(self._NONPOLAR))
        random.shuffle(sequence)
        return "".join(sequence)

    def _Grouper(self, length, percent_polar, percent_charged, final_charge):
        if percent_polar is None:
            percent_polar = 0
        if percent_charged is None:
            percent_charged = 0
        if final_charge is None:
            final_charge = 0

        if final_charge != 0 and percent_charged == 0:
            raise ImpossibleSetting("If final_charge is nonzero, percent_charged must also be nonzero")
        p_pos = 0
        if final_charge > 0:
            p_neg = (1 - (final_charge / (percent_charged * length))) / 2
            p_pos = 1 - p_neg
        # else:
        elif final_charge < 0:
            p_pos = (1 - abs(final_charge) / (percent_charged * length)) / 2

        if self.Charged_Is_Polar:
            percent_charged = percent_charged + percent_polar * (len(self._CHARGED) / (len(self._POLAR)))
            unique = "".join([c for c in self._POLAR if c not in self._CHARGED])
            percent_polar = percent_polar - percent_polar * (len(unique) / (len(self._POLAR)))

        sequence = ""
        for i in range(length):
            r = random.random()
            if r < percent_polar:
                sequence += self._POLAR[random.randrange(0, len(self._POLAR))]
            elif percent_polar < r and r < percent_polar + percent_charged:
                r2 = random.random()
                if p_pos > r2:
                    sequence += self._POSITIVE[random.randrange(0, len(self._POSITIVE))]
                else:
                    sequence += self._NEGATIVE[random.randrange(0, len(self._NEGATIVE))]
            else:
                sequence += self._NONPOLAR[random.randrange(0, len(self._NONPOLAR))]
        return sequence

    def _ValidateSequence(self, sequence, percent_polar, percent_charged, total_charge, charge_range):
        if '$' in sequence:
            return False

        if charge_range is None:
            charge_range = 0

        # Polar condition

        if percent_polar is None:
            polar = True
        elif percent_polar < 0:
            polar = True
        else:
            polar = self.Analyzer.PercentPolar(sequence) >= percent_polar
        # Charge condition

        if percent_charged is None:
            charge = True
        elif percent_charged < 0:
            charge = True
        else:
            charge = self.Analyzer.PercentCharged(sequence) >= percent_charged
        # Charge total condition
        charge_t = False
        if total_charge is None:
            charge_t = True
        else:
            charge_t = self.Analyzer.GetCharge(sequence) <= (total_charge + charge_range) \
                       and self.Analyzer.GetCharge(sequence) >= (total_charge - charge_range)

        return (polar and charge and charge_t)

    def VerifySettings(self, length, batch_size, method, percent_polar,
                       percent_charged, final_charge, charge_range, max_attempts, crash=True):

        disregard_charge = False
        if final_charge is None:
            disregard_charge = True
        if batch_size <= 0:
            raise ImpossibleSetting("Batch size must be larger than 0")

        if (max_attempts is not None) and (max_attempts < 0 or not isinstance(max_attempts, int)):
            if crash:
                raise ImpossibleSetting("The number of specified max attempts must be a positive integer or None")
            return False

        if method not in self._ACCEPTED_METHODS:
            if crash:
                raise ImpossibleSetting(
                    f"Selected method must be one of the following: {self._ACCEPTED_METHODS}.\n\t Chosen: {method}")
            return False

        if not ((percent_charged is None or percent_charged >= 0) and (percent_polar is None or percent_polar >= 0)):
            if crash:
                raise ImpossibleSetting("All provided probabilities must be positive or 0")
            return False

        if not self.Charged_Is_Polar:
            a = 0
            b = 0
            if percent_polar is not None:
                a = percent_polar
            if percent_charged is not None:
                b = percent_charged
            if a + b > 1:
                if crash:
                    raise ImpossibleSetting(
                        "The sum of provided probabilities must be less than or equal to 1 if charged residues are not considered polar")
                return False
        if not disregard_charge and length < abs(final_charge):
            if crash:
                raise ImpossibleSetting(
                    f"The length of the output protein must be less than or equal to the magnitude of the charge ({length} < {final_charge})")
            return False
        return True

        if percent_charged == 0 and final_charge != 0:
            if crash:
                raise ImpossibleSetting(f"A nonzero charge cannot be present if the percent_charged is not 0")
            return False

    def _CleanPolar(self, sequence, percent_polar):
        if percent_polar is None:
            return sequence
        disparity = self.Analyzer.NumPolar(sequence) - math.floor(len(sequence) * percent_polar)
        ind = 0
        s = list(sequence)
        while disparity > 0 and ind < len(s):
            if (s[ind] in self._POLAR) and (s[ind] not in self._CHARGED):
                s[ind] = random.choice(self._NONPOLAR)
                disparity -= 1
            ind += 1
        return "".join(s)