from abstract_utilities import *
all_imps = []
def get_all_real_imps(file):
    contents = read_from_file(file)
    lines = contents.split('\n')
    for line in lines:
        if line.startswith('from '):
            from_line = line.split('from ')[-1]
            dot_fro = ""
            dirname = file
            for char in from_line:
                if  char != '.':
                    line = f"from {dot_fro}{eatAll(from_line,'.')}"
                    if line in all_imps:
                        line = ""
                    break
                if dot_fro == "":
                    dot_fro = ""
                dirname = os.path.dirname(dirname)
                dirbase = os.path.basename(dirname)
                dot_fro = f"{dirbase}.{dot_fro}"
        if line:
            all_imps.append(line)

    return '\n'.join(all_imps)
import_pkg_js=None
files = get_files_and_dirs(get_caller_dir(),allowed_exts=['.py'])[-1]
##files = [get_all_real_imps(f) for f in files if f and f.endswith('imports.py')]
for file in files:
    text = get_all_real_imps(file)
    import_pkg_js=get_all_imports(text=text,file_path=file,import_pkg_js=import_pkg_js)
lines  = []
for pkg,values in import_pkg_js.items():
    comments = []
    if pkg not in ["nulines","file_path","all_data"]: 
        line = values.get('line')
        imports = values.get('imports')
        for i,imp in enumerate(imports):
            if '#' in imp:
                imp_spl = imp.split('#')
                comments.append(imp_spl[-1])
                imports[i] = clean_line(imp_spl[0])
        imports = list(set(imports))   
        if '*' in imports:
            imports="*"
        else:
            imports=','.join(imports)
            if comments:
                comments=','.join(comments)
                imports+=f" #{comments}"
        import_pkg_js[pkg]["imports"]=imports
    line=f"from {pkg} import {imports}"
    lines.append(line)
print('\n'.join(lines))
