# Create an Interface to find Different types of rhymes
import pathlib
from pprint import pprint
import traceback
import epitran
from .ipa_trie import IPATrie

class Rhime():

    words = None
    ipa_translits = {}
    def __init__(self):
        self.epi = epitran.Epitran("hin-Deva")

    def direct_rhyme(self):
        ...

    def __get_suffix_match_len(self, target_ipa: str, candidate_ipa: str) -> int:

        match_len = 0
        len_word = min(len(target_ipa), len(candidate_ipa))

        for ch in range(1, len_word  + 1):
            if target_ipa[-ch] == candidate_ipa[-ch]:
                match_len += 1
            else:
                break
        return match_len

    def ipa_rhyme(self, target, min_mch_len=2, max_mch_len = 1000):

        rhyme_results = []
        if not self.ipa_translits:
            for word in self.words:
                try:
                    self.ipa_translits[word] = self.epi.transliterate(word)
                except Exception as error:
                    print("Failed to transliterate word %s into IPA".format(word))
        
        target_ipa = self.ipa_translits.get(target)
        if target_ipa is None:
            target_ipa = self.epi.transliterate(target)
            self.words.append(target)
            self.ipa_translits[target] = target_ipa
        

        for candidate_word, candidate_ipa in self.ipa_translits.items():
            if candidate_word == target:
                continue

            match_len = self.__get_suffix_match_len(target_ipa, candidate_ipa)
            if match_len >= min_mch_len and match_len <= max_mch_len:
                score = match_len / max(len(candidate_ipa), len(target_ipa))
                rhyme_results.append((candidate_word, score))
        
        return sorted(rhyme_results, key = lambda x: (-x[1], x[0]))
    


    def buildTrie(self):
        self.IPATrie = IPATrie()

        for word in self.words:
            try:
                ipa_list = self.epi.trans_list(word)
                pass
            except Exception as error:
                print("Failed to transliterate word %s into IPA".format(word))
                ipa_list = None

            if ipa_list:
                self.IPATrie.add_word(ipa_list, word)
    
    def get_ipa_rhyme(self, target):

        return self.IPATrie.search(self.epi.trans_list(target))

    
    def load_words_frm_file(self, filepath: str) -> None:
        """"
        Adds words from a file to self.words list
        """

        path = pathlib.Path(filepath)
        if not path.exists(follow_symlinks=False):
            raise FileNotFoundError(filepath)
        
        try:
            with open(path, "r") as file:
                words = file.readlines()
        except Exception as error:
            print(traceback.format_exc())
        
        words = list(set(map(str.strip, words)))
        words = list(filter(lambda x: len(x) > 1, words))
        print(len(words),"Words loaded")
        if not self.words:
            self.words = words
            return
        self.words += words