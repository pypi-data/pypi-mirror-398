class TrieNode:
    def __init__(self):
        self.childs: dict[str, IPATrie] = {}
        # self.isconsonant:bool = self.__is_consotant()
        self.isend: bool = False
        self.words = []

class IPATrie:
    def __init__(self):
        self.root = TrieNode()
    
    def add_word(self, ipa_word: list, word):

        node = self.root

        for ch in reversed(ipa_word):

            next_node = node.childs.get(ch, None)

            if next_node == None:
                next_node = TrieNode()
                node.childs[ch] = next_node

            node = next_node
        node.isend = True
        node.words.append(word)

    def _collect_words(self, node: TrieNode, result: dict, depth: int):
        if node.isend:
            for w in node.words:
                # keep the longest suffix match only
                result[w] = max(result.get(w, 0), depth)

        for child in node.childs.values():
            self._collect_words(child, result, depth)

    def search(self, target: list, min_suffix_len: int = 2) -> dict[str, int]:
        node = self.root
        depth = 0
        result: dict[str, int] = {}

        for ch in reversed(target):
            if ch not in node.childs:
                break

            node = node.childs[ch]
            depth += 1

            if depth >= min_suffix_len:
                self._collect_words(node, result, depth)

        return result
