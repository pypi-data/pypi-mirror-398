import logging
from procrastimate.wordList.vagueWords import STOP_WORDS, WEAK_VERBS, STRONG_VERBS, VAGUE_NOUNS, SCOPE_WORDS, CONSTRAINT_WORDS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def vagueChecker(task: str):
    task_word_list = cleanTaskDescription(task)
    list_len = len(task_word_list)
    content_words = [w for w in task_word_list if w not in STOP_WORDS]

    has_weak_verb = any(w in WEAK_VERBS for w in content_words)
    has_vague_noun = any(w in VAGUE_NOUNS for w in content_words)
    has_strong_verb = any(w in STRONG_VERBS for w in content_words)

    if (has_weak_verb or has_vague_noun) and not has_strong_verb:
        return True

    return False


def cleanTaskDescription(task: str) -> list:
    word_list = task.split()
    clean_list = []
    for i in range(0, len(word_list)):
        if word_list[i] in STOP_WORDS:
            continue
        else:
            clean_list.append(word_list[i])

    return clean_list

