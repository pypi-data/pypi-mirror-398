from ipamd.public.models.common import AnalysisResult
configure = {
    "schema": 'full'
}
def func(slf, filename, precision=6):
    fp = open(filename, 'w')
    match slf.type:
        case AnalysisResult.Type.SCALAR:
            fp.writelines(f'{slf.data:.{precision}f}')
        case AnalysisResult.Type.VECTOR:
            for x in slf.data.keys():
                fp.writelines(f'{x}: {slf.data[x]:.{precision}f}')
        case AnalysisResult.Type.DISTRIBUTION:
            for group in slf.data.keys():
                data = slf.data[group]
                fp.writelines(f'{group}: [' + ', '.join([f'{x:.{precision}f}' for x in data]) + ']')
        case AnalysisResult.Type.MATRIX:
            for x in slf.data.keys():
                row = slf.data[x]
                fp.writelines(f'[' + ', '.join([f'{row[y]:.{precision}f}' for y in row.keys()]) + ']')