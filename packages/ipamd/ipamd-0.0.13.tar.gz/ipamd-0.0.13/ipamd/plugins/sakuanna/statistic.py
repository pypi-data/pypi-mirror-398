import copy
from ipamd.public.models.common import AnalysisResult
from ipamd.public.utils.output import *
from ipamd.public.models.sequence import ProteinSequence
configure = {
    "type": 'function',
}

def func(protein: ProteinSequence, targets, format_='ratio'):
    all_amino_acids = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']
    rest_aa = copy.deepcopy(all_amino_acids)
    classes = {
        'aromatic': ['F', 'W', 'Y'],
        'positive': ['K', 'R', 'H'],
        'negative': ['D', 'E'],
        'charged': ['K', 'R', 'H', 'D', 'E'],
        'polar': ['S', 'T', 'N', 'Q'],
        'nonpolar': ['A', 'V', 'L', 'I', 'P', 'F', 'W', 'M'],
    }

    cnt_of_all_classes = {}
    def count(aa):
        if aa not in rest_aa:
            warning(f'Amino acid {aa} has already been counted, the final result may be wrong.')
        else:
            rest_aa.remove(aa)
        cnt_of_aa = 0
        for res in protein.sequence:
            if res == aa:
                cnt_of_aa += 1
        return cnt_of_aa

    for target in targets:
        if target in classes:
            target_aa = classes[target]
            cnt = 0
            for aa in target_aa:
                cnt += count(aa)
        elif target in all_amino_acids:
            cnt = count(target)
        else:
            warning(f'Target {target} is not valid. It should be one of {all_amino_acids} or {list(classes.keys())}.')
            continue
        cnt_of_all_classes[target] = cnt

    total_length = len(protein)
    cnt_of_all_classes['rest'] = total_length - sum(cnt_of_all_classes.values())

    if format_ == 'ratio':
        for key in cnt_of_all_classes:
            cnt_of_all_classes[key] = cnt_of_all_classes[key] / total_length

    data = AnalysisResult(
        title=f'Sequence statistic of {protein.name}',
        data=cnt_of_all_classes,
        type_=AnalysisResult.Type.RATIO
    )
    return data