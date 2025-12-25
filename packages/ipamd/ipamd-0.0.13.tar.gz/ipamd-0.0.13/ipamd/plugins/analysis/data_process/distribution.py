from ipamd.public.models.common import AnalysisResult
from ipamd.public.utils.output import error

configure = {
    "schema": 'full'
}
def func(slf, bins=10, new_name=None):
    result = AnalysisResult(
        title = slf.title + '-distro' if new_name is None else new_name,
        type_ = AnalysisResult.Type.UNKNOWN,
        data = {}
    )
    match slf.type:
        case AnalysisResult.Type.SCALAR | AnalysisResult.Type.DISTRIBUTION:
            result.type = slf.type
            result.data = slf.data
        case AnalysisResult.Type.VECTOR:
            max_value = max(slf.data.values())
            min_value = min(slf.data.values())
            bin_width = (max_value - min_value) / bins
            distro_list = []
            for i in range(bins):
                distro_list.append([])
            for v in slf.data.values():
                index = int((v - min_value) / bin_width - 1)
                distro_list[index].append(v)
            distro_dist = {}
            for i in range(bins):
                distro_dist[f'{(min_value + i * bin_width):.2f}-{(min_value + (i + 1) * bin_width):.2f}'] = distro_list[i]
            result.type = AnalysisResult.Type.DISTRIBUTION
            result.data = distro_dist
        case AnalysisResult.Type.MATRIX:
            pass
        case _:
            error('Unknown data type')
            raise ValueError('Unknown data type')
    return result