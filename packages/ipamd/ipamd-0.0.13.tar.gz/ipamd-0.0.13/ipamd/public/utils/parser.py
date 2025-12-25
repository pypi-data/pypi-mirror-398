from ipamd.public.utils.output import error
def value_of(value, lookup_table):
    if type(value) != str:
        return value
    else:
        if value.startswith('compute:'):
            substr = value[8:]
            index_of_open_curly = 0
            while index_of_open_curly != -1:
                index_of_open_curly = substr.find('{', index_of_open_curly)
                if index_of_open_curly == -1:
                    break
                else:
                    index_of_close_curly = substr.find('}', index_of_open_curly)
                    if index_of_close_curly == -1:
                        index_of_close_curly = len(substr)
                    variable_name = substr[index_of_open_curly + 1:index_of_close_curly]
                    try:
                        value = lookup_table[variable_name]
                    except KeyError:
                        error(f'Variable {variable_name} not found in lookup table.')
                        raise ValueError
                    substr = substr[:index_of_open_curly] + str(value) + substr[index_of_close_curly + 1:]
            return eval(substr)
        elif value=='True':
            return True
        elif value=='False':
            return False
        else:
            return float(value)

def range_to_list(range_str):
    if range_str == '':
        return []
    ranges = range_str.split(',')
    result = []
    for r in ranges:
        if '-' in r:
            start, end = map(int, r.split('-'))
            result.extend(range(start, end+1))
        else:
            result.append(int(r))
    return result