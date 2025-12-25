from ipamd.public.utils.output import *
from ipamd.public.models.common import AnalysisResult
configure = {
    "schema": 'full'
}
def func(slf, other):
    new_data = AnalysisResult(
        title=slf.title,
        type_=AnalysisResult.Type.VECTOR,
        data={}
    )
    match (slf.type, other.type):
        case (AnalysisResult.Type.SCALAR, AnalysisResult.Type.SCALAR):
            new_data.data = {
                slf.title: slf.data,
                other.title: other.data
            }
        case (AnalysisResult.Type.VECTOR, AnalysisResult.Type.SCALAR):
            new_data.data = {k: v for k, v in slf.data.items()}
            new_data.data[other.title] = other.data
        case _:
            error('Data type not suitable for merging')
            return None
    return new_data