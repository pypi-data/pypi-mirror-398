from ipamd.public.utils.output import *
from ipamd.public.models.common import AnalysisResult
configure = {
    "schema": 'full'
}
def func(slf, precision=3):
    match slf.type:
        case AnalysisResult.Type.SCALAR:
            output(f'{slf.data:.{precision}f}')
        case AnalysisResult.Type.VECTOR:
            for x in slf.data.keys():
                output(f'{x}: {slf.data[x]:.{precision}f}')
        case AnalysisResult.Type.DISTRIBUTION:
            for group in slf.data.keys():
                data = slf.data[group]
                output(f'{group}: [' + ', '.join([f'{x:.{precision}f}' for x in data]) + ']')
        case AnalysisResult.Type.MATRIX:
            for x in slf.data.keys():
                row = slf.data[x]
                output(f'[' + ', '.join([f'{row[y]:.{precision}f}' for y in row.keys()]) + ']')
        case AnalysisResult.Type.RATIO:
            for group in slf.data.keys():
                data = slf.data[group]
                output(f'{group}: {data}')
        case _:
            output(slf.data)