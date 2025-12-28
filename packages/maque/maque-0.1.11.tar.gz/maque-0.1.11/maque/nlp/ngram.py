
def ngram(words: str, n: int, reverse=True):
    ngram_dict = {}
    words = ['<S>'] + list(words) + ['<E>']
    zip_args = ', '.join([f"words[{i}:]" for i in range(n)])
    zip_result = eval(f"zip({zip_args})")
    for i in zip_result:
        ngram_dict[i] = ngram_dict.get(i, 0) + 1
    return sorted(ngram_dict.items(), key=lambda i: i[1], reverse=reverse)
