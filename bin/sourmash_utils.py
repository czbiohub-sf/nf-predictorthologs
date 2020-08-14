from sourmash import signature as sig
from tqdm import tqdm

def load_sketches(filenames, ksize, molecule):
    sketches = []
    for filename in tqdm(filenames):
        s = sig.load_signatures(filename, ksize=ksize, select_moltype=molecule)
        sketches.extend(s)
    return sketches
