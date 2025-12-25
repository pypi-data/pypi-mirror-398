from ipamd.public.models.common import AnalysisResult
import copy
configure = {
    "schema": 'full'
}
def func(slf, action='average', new_name=None):
    result = AnalysisResult(
        title=slf.title + '-normalized' if new_name is None else new_name,
        type_=slf.type,
        data=copy.deepcopy(slf.data)
    )
    match slf.type, action:
        case AnalysisResult.Type.SCALAR:
            pass
        case AnalysisResult.Type.VECTOR:
            max_value = max(slf.data.values())
            for v in slf.data.keys():
                result.data[v] /= max_value
        case AnalysisResult.Type.MATRIX | AnalysisResult.Type.DISTRIBUTION:
            all_values = []
            for v in slf.data:
                for vv in v:
                    all_values.append(vv)
            max_value = max(all_values)
            for v in slf.data.keys():
                for vv in slf.data[v].keys():
                    result.data[v][vv] /= max_value

    return result