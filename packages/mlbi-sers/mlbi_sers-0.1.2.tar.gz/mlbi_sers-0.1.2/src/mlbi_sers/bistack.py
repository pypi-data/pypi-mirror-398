import os, sys, shutil, subprocess, importlib, re
from typing import List, Tuple, Dict, Optional, Any

try:
    # Py>=3.8
    from importlib import metadata as _im
except Exception:
    import importlib_metadata as _im  # fallback

def _pkg_base_name(pkg: str) -> str:
    """
    'scoda-viz==0.4.20' -> 'scoda-viz'
    'pandas>=2.2' -> 'pandas'
    """
    return re.split(r"==|>=|<=|~=|>|<", pkg, maxsplit=1)[0].strip()

def _get_dist_version(dist_name: str) -> Optional[str]:
    try:
        return _im.version(dist_name)
    except _im.PackageNotFoundError:
        return None

        
def _pip_install(pkg: str, quiet: bool = True, upgrade: bool = False) -> int:
    cmd = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    if quiet:
        cmd.append("-q")
    cmd.append(pkg)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE if quiet else None,
                          stderr=subprocess.STDOUT if quiet else None, text=True)
    return proc.returncode


def _is_colab() -> bool:
    try:
        import google.colab  # type: ignore
        return True
    except Exception:
        return "COLAB_RELEASE_TAG" in os.environ

def ensure_condacolab(run_install: bool = False, quiet: bool = True) -> Tuple[bool, Optional[Any]]:
    """
    Google Colab 여부를 감지해 condacolab을 준비합니다.

    매개변수
    ----------
    run_install : bool
        True면 condacolab.install()를 실행합니다.
        *주의*: Colab 런타임이 즉시 재시작되며, 이후 코드는 실행되지 않습니다.
    quiet : bool
        pip 설치 시 -q(quiet) 옵션 사용 여부.

    반환
    ----------
    (is_colab, condacolab_module_or_None)
    - is_colab: 현재 환경이 Colab이면 True
    - condacolab_module_or_None: Colab이면 condacolab 모듈(설치/임포트 완료), 아니면 None
    """

    # 1) Colab 감지
    is_colab = _is_colab()
    if not is_colab:
        return False, None

    # 2) condacolab 설치/임포트
    try:
        condacolab = importlib.import_module("condacolab")
    except ModuleNotFoundError:
        _pip_install("condacolab")
        condacolab = importlib.import_module("condacolab")

    # 3) 필요 시 conda 설치 및 런타임 재시작
    if run_install:
        condacolab.install()   # 여기서 Colab 런타임이 재시작됩니다.
        # 재시작되므로 아래 코드는 실행되지 않음

    else:
        # 설치만 하고 환경 점검(재시작 없이)
        try:
            condacolab.check()
        except Exception:
            pass

    return True, condacolab


# -------------------- 공통 유틸 --------------------
def _run(cmd: List[str], capture: bool = True, prn: bool = False) -> Tuple[int, str]:
    if prn:
        """Run command. Prints stdout live and returns (returncode, output_text)."""
        # import subprocess

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_lines = []

        # 실시간 streaming
        for line in process.stdout:
            if prn: print(line, end="")      # 👉 화면에 즉시 출력
            if capture:
                output_lines.append(line)

        process.wait()
        output_text = "".join(output_lines) if capture else ""
        return process.returncode, output_text
    else:
        """Run command. Returns (returncode, stdout+stderr text)."""
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            text=True,
            check=False,
        )
        out = (proc.stdout or "").strip() if capture else ""
        return proc.returncode, out

def _which(binname: str) -> Optional[str]:
    return shutil.which(binname)

def _sudo_prefix() -> List[str]:
    try:
        is_root = (os.geteuid() == 0)
    except AttributeError:
        is_root = False
    if is_root or _is_colab():
        return []
    return ["sudo"]

def _print_status(name: str, version: Optional[str], installed_now: bool):
    tag = "installed" if installed_now else "already installed"
    vtxt = version or "unknown-version"
    print(f"{name}: {tag} (v{vtxt})")

# -------------------- Java 버전 --------------------
def _parse_java_version(text: str) -> Optional[Tuple[int,int,int,str]]:
    m = re.search(r'version\s+"(\d+)(?:\.(\d+))?(?:\.(\d+))?', text)
    raw = ""
    if m:
        raw = m.group(0)
        major = int(m.group(1) or 0)
        minor = int(m.group(2) or 0)
        patch = int(m.group(3) or 0)
        if major == 1 and minor >= 8:   # 1.8.x → 8
            major = 8
        return (major, minor, patch, raw)
    m2 = re.search(r'version\s+"1\.8\.', text)
    if m2:
        return (8,0,0,'1.8')
    return None

def _get_java_version() -> Optional[Tuple[int,int,int,str]]:
    code, out = _run(["bash","-lc","java -version"], capture=True)
    if code != 0:
        return None
    # 보통 stderr로 나오지만, 우리는 stdout+stderr 합쳐 받음
    return _parse_java_version(out)

def _ensure_java(required_major: int, prefer: str = "apt", allow_conda_fallback: bool = True) -> str:
    """
    Java가 없거나 major가 낮으면 설치. 성공/기설치 버전 문자열 반환(없으면 "unknown").
    """
    v = _get_java_version()
    if v and v[0] >= required_major:
        return f"{v[0]}.{v[1]}.{v[2]}"

    # 설치 필요
    if prefer == "apt" and _which("apt-get"):
        _run(_sudo_prefix()+["apt-get","update","-y","-qq"])
        pkg = f"openjdk-{required_major}-jdk"
        rc,_ = _run(_sudo_prefix()+["apt-get","install","-y","-qq",pkg])
        if rc == 0:
            v2 = _get_java_version()
            return f"{v2[0]}.{v2[1]}.{v2[2]}" if v2 else "unknown"

        if not allow_conda_fallback:
            return "unknown"

    # conda fallback
    conda = _which("conda")
    if conda:
        _run([conda,"install","-y","-q","-c","conda-forge",f"openjdk={required_major}"])
        v3 = _get_java_version()
        return f"{v3[0]}.{v3[1]}.{v3[2]}" if v3 else "unknown"

    return "unknown"


# -------------------- 버전 프로브 --------------------
def _probe_version(cmd: List[str], regex: str = r'([0-9]+(?:\.[0-9A-Za-z_-]+)*)') -> Optional[str]:
    code, out = _run(cmd, capture=True)
    if code != 0:
        return None
    m = re.search(regex, out, flags=re.IGNORECASE)
    return m.group(1) if m else out.splitlines()[0].strip() if out else None

def _version_minimap2():      return _probe_version(["minimap2", "--version"])
def _version_bwa():           return _probe_version(["bash","-lc",'bwa 2>&1 | grep -m1 -i "Version"'], r'Version:\s*([^\s]+)')
def _version_bowtie2():       return _probe_version(["bowtie2", "--version"], r'version\s+([0-9][^\s]*)')
def _version_star():          return _probe_version(["STAR", "--version"])
def _version_samtools():      return _probe_version(["bash","-lc","samtools --version | head -n1"], r'samtools\s+([0-9][^\s]*)')
def _version_featureCounts(): return _probe_version(["featureCounts", "-v"], r'featureCounts\s+v?([0-9][^\s]*)')
def _version_stringtie():     return _probe_version(["stringtie", "--version"], r'StringTie\s+v?([0-9][^\s]*)')
def _version_gffread():       return _probe_version(["gffread", "--version"])
def _version_bcftools():      return _probe_version(["bcftools", "--version"])
def _version_salmon():        return _probe_version(["salmon", "--version"])

apt_pkgs = {
    # (표시이름, apt패키지, 바이너리, 버전함수)
    'minimap2':       ("minimap2", "minimap2", "minimap2", _version_minimap2),
    'bwa':            ("bwa",      "bwa",      "bwa",      _version_bwa),
    'bowtie2':        ("bowtie2",  "bowtie2",  "bowtie2",  _version_bowtie2),
    'star':           ("STAR",     "rna-star", "STAR",     _version_star),
    'samtools':       ("samtools", "samtools", "samtools", _version_samtools),
    'featurecounts':  ("featureCounts(subread)", "subread","featureCounts", _version_featureCounts),
    'stringtie':      ("stringtie","stringtie","stringtie",_version_stringtie),
    'gffread':        ("gffread", "gffread", "gffread", _version_gffread),
    'bcftools':       ("bcftools", "bcftools", "bcftools", _version_bcftools),
    'salmon':         ("salmon", "salmon", "salmon", _version_bcftools),
}

# -------------------- APT 패키지 처리 --------------------
def _apt_ensure_and_report( arg, install: bool = True, apt_cmd = 'apt-get'):

    name, aptpkg, binname, vfunc = arg
    binpath = _which(binname)
    if binpath:
        v = vfunc()
        _print_status(name, v, installed_now=False)
        return

    # install
    if install:
        rc,_ = _run(_sudo_prefix()+[apt_cmd,"install","-y","-qq",aptpkg])
        if rc != 0:
            # universe 필요한 경우 한 번 더 시도
            _run(_sudo_prefix()+["add-apt-repository","-y","universe"])
            _run(_sudo_prefix()+[apt_cmd,"update","-y","-qq"])
            rc,_ = _run(_sudo_prefix()+[apt_cmd,"install","-y","-qq",aptpkg])
        v = vfunc() if _which(binname) else None
        _print_status(name, v, installed_now=True)

    return


# -------------------- conda install --------------------
def _conda_install(package = 'rmats', install: bool = True, ensure_channels: bool = True):
    conda = _which("conda")
    if not conda:
        print("conda not found; skip %s (set up conda/condacolab first if needed)." % package)
        return

    def _conda_list_pkg(pkg: str) -> Optional[str]:
        rc,out = _run([conda,"list",pkg])
        if rc==0 and re.search(rf'^{pkg}\s+([0-9][^\s]*)', out, flags=re.MULTILINE):
            v = re.search(rf'^{pkg}\s+([0-9][^\s]*)', out, flags=re.MULTILINE).group(1)
            return v
        return None

    if ensure_channels:
        _run([conda,"config","--add","channels","bioconda"])
        _run([conda,"config","--add","channels","conda-forge"])
        # _run([conda,"config","--set","channel_priority","strict"])

    v = _conda_list_pkg(package)
    if v:
        _print_status("%s (conda)" % package, v, installed_now=False)
        return
    elif not install:
        print("%s (conda): not installed " % package)
    else:
        # _run([conda,"install","-y","-q","rmats"])
        _run([conda,"install","-y","-q","-c", 'bioconda', package])

        v2 = _conda_list_pkg(package) or "unknown"
        _print_status("%s (conda)" % package, v2, installed_now=True)

    return


# -------------------- 버전 프로브 --------------------
def _version_rsem():          return _probe_version(["rsem-calculate-expression", "--version"])
def _version_rmats():         return _probe_version(["rmats.py", "--version"])
def _version_cnvkit():        return _probe_version(["cnvkit.py", "version"])
def _version_gatk():          return _probe_version(["gatk", "--version"])
def _version_hifiasm_meta():  return _probe_version(["hifiasm_meta", "--version"])

conda_pkgs = {
    'rmats':  ('rmats.py', _version_rmats),
    'rsem':   ('rsem-calculate-expression', _version_rsem)
}

other_pkgs = {
  'gatk':         ("gatk", _version_gatk),
  'cnvkit':       ("cnvkit.py", _version_cnvkit),
  'hifiasm_meta': ("hifiasm-meta/hifiasm_meta", _version_hifiasm_meta)
}

def _install_gatk(install: bool = True, pkg = 'gatk', gatk_version = '4.4.0.0'):

    print(f"== Installing GATK .. cloning repo .. ", end = '')
    wget_path = 'https://github.com/broadinstitute/gatk/releases/download/%s/gatk-%s.zip' % (gatk_version, gatk_version)
    _run(['wget', wget_path], prn = False)
    _run(['unzip', 'gatk-%s.zip' % gatk_version], prn = False )
    _run(['rm', 'gatk-%s.zip' % gatk_version], prn = False )
    _run(['ln', '-s', f"/content/gatk-{gatk_version}/gatk", "/usr/local/bin/gatk"], prn=False)
    print(" Installation complete! ==")
    binname, vfunc = other_pkgs[pkg]
    binpath = _which(binname)
    if binpath:
        v = vfunc()
        _print_status(pkg, v, installed_now=True)
        return True
    else:
        print("gatk: installation failed ")
        return False

def _install_cnvkit(install: bool = True, pkg = 'cnvkit'):

    print(f"== Installing CNVkit .. cloning repo .. ", end = '')
    git_path = 'https://github.com/etal/cnvkit'
    _run(['git', 'clone', git_path], prn = False)
    _run(['pip', 'install', "matplotlib<3.9", '--force-reinstall']) ## to avoid cnvkit=0.9.12 error
    _run(['python', '-m', 'pip', 'install', '-e', '%s/.' % pkg], prn = False )
    print(" Installation complete! ==")
    binname, vfunc = other_pkgs[pkg]
    binpath = _which(binname)
    if binpath:
        v = vfunc()
        _print_status(pkg, v, installed_now=True)
        return True
    else:
        print("gatk: installation failed ")
        return False


def _install_hifiasm_meta(install_dir: str = "./", pkg = 'hifiasm_meta') -> str:
    """
    Clone and build hifiasm-meta, then add its directory to PATH via ~/.bashrc.
    Returns the absolute path to the hifiasm-meta directory.
    """
    install_dir = os.path.expanduser(install_dir)
    os.makedirs(install_dir, exist_ok=True)
    print(f"== Installing hifiasm-meta .. ", end = '')

    repo_dir = os.path.join(install_dir, "hifiasm-meta")

    # 1) git clone (이미 있으면 스킵)
    if not os.path.isdir(repo_dir):
        print("cloning repo .. ", end = '')
        rc, out = _run(
            ["git", "clone", "https://github.com/xfengnefx/hifiasm-meta.git"],
            capture=True, prn = False
        )
        if rc != 0:
            print(out)
            raise RuntimeError("git clone failed")
    else:
        print("dir already exists. Skipping clone.")

    # 2) make 빌드
    print("making .. ", end = '')
    old_cwd = os.getcwd()
    try:
        os.chdir(repo_dir)
        rc, out = _run(["make"], capture=True, prn = False)
        if rc != 0:
            raise RuntimeError("make failed")
    finally:
        os.chdir(old_cwd)

    _run(['ln', '-s', f"/content/hifiasm-meta/hifiasm_meta", "/usr/local/bin/hifiasm_meta"], prn=False)
    print(" Installation complete! ==")

    binname, vfunc = other_pkgs[pkg]
    binpath = _which(binname)
    if binpath:
        v = vfunc()
        _print_status(pkg, v, installed_now=True)
        return True
    else:
        print("hifiasm_meta: installation failed ")
        return False

    return

# -------------------- 메인 엔트리 --------------------
def install_common_bi_tools(  pkgs_to_install: List[str] = None, check_only = False ):

    """
    ------------------------------------------------------------
    📌 Install/check common NGS & RNA-seq tools (Colab-friendly)
    ------------------------------------------------------------

    Overview
    --------
    Wrapper to *check* or *install* frequently used bioinformatics tools
    (mapping, quantification, CNV, variant calling, long-read assembly).

    - APT (Colab only):
        minimap2, bwa, bowtie2, STAR, samtools,
        salmon, subread(featureCounts), stringtie
    - Conda:
        Java 17, rMATS, rsem
    - git clone / wget (other tools):
        CNVkit, GATK, hifiasm-meta

    Parameters
    ----------
    pkgs_to_install : list of str or None
        List of package keys to process.
        Valid keys include (examples):
            ["minimap2", "bwa", "STAR", "samtools",
             "salmon", "featureCounts", "stringtie",
             "rMATS", "rsem", "gatk", "cnvkit", "hifiasm_meta"]
        If None:
            → Print available keys and return without installing.

    check_only : bool (default=False)
        If True  → only check whether tools are installed and print status,
                   do NOT install anything.
        If False → install missing tools using:
                      • apt-get (on Colab)
                      • conda (for rMATS, rsem, Java)
                      • custom installers (GATK, CNVkit, hifiasm-meta)

    Behavior
    --------
    • Ensures Conda/conda-colab is available when needed (for conda tools).
    • For APT tools:
        - Runs `apt-get update` once.
        - Installs tools only on Colab; on non-Colab, prints "skipping".
    • For GATK:
        - Checks Java version (requires ≥ 17).
        - Installs or upgrades Java via apt/conda, then downloads GATK.
    • For CNVkit, hifiasm-meta:
        - Uses dedicated helper installers (git clone / pip etc.).

    Returns
    -------
    None
        Prints status / versions for each requested package.
        Side effect: installs tools into current environment when
        check_only=False.

    Example
    -------
    >>> install_common_bi_tools(
            pkgs_to_install=[
                "bwa", "samtools", "STAR",
                "salmon", "rsem", "rMATS",
                "gatk", "cnvkit"
            ],
            check_only=False
        )

    # Just check what is installed (no changes):
    >>> install_common_bi_tools(["bwa","samtools","gatk"], check_only=True)
    """

    java_required_major = 17
    java_prefer = "conda", # "apt" or "conda"
    java_allow_conda_fallback = True

    """
    - APT: minimap2, bwa, bowtie2, STAR, samtools, salmon, subread(featureCounts), stringtie
      (Installation performed only in Colab)
    - Conda: Java 17, rMATS, rsem
    - git clone/wget: CNVkit, GATK, hifiasm-meta
    """

    check = check_only
    lst_apt_pkgs = list(apt_pkgs.keys())
    lst_conda_pkgs = list(conda_pkgs.keys())
    lst_other_pkgs = list(other_pkgs.keys())

    if pkgs_to_install is None:
        pkgs = lst_apt_pkgs + lst_conda_pkgs + lst_other_pkgs
        print('Select from .. \n[\'%s\']' % ('\',\n \''.join(pkgs)))
        return

    lst_conda_pkgs_to_install = list(set(pkgs_to_install).intersection(lst_conda_pkgs))
    if True: # (len(lst_conda_pkgs_to_install) > 0) or ((java_prefer == "conda") and ('gatk' in pkgs_to_install)):
        is_colab, ccl = ensure_condacolab(run_install= not check)
        if not is_colab:
            check = True

    # 1) APT 도구들
    # 한 번만 update
    apt_cmd = 'apt-get'
    if _which(apt_cmd):
        _run(_sudo_prefix()+[apt_cmd,"update","-y","-qq"])
    else:
        print("%s not found; skipping APT section." % apt_cmd)
        return
    #'''

    for pkg in pkgs_to_install:

        if pkg in lst_apt_pkgs:
            if _is_colab():
                arg = apt_pkgs[pkg]
                _apt_ensure_and_report( arg, install =  not check, apt_cmd =apt_cmd )
            else:
                print('Skipping %s installment. (apt-Install only in colab)' % pkg)

        elif pkg in lst_conda_pkgs:
            binname, vfunc = conda_pkgs[pkg]
            binpath = _which(binname)
            if binpath:
                v = vfunc()
                _print_status(pkg, v, installed_now=False)
            elif not check:
                _conda_install(package = pkg, install = not check, ensure_channels = True)

        elif pkg == 'gatk':
            binname, vfunc = other_pkgs[pkg]
            binpath = _which(binname)
            if binpath:
                v = vfunc()
                _print_status(pkg, v, installed_now=False)
            elif not check:
                # install Java
                jv = _get_java_version()
                if jv and jv[0] >= java_required_major:
                    _print_status(f"Java (requires ≥{java_required_major})", f"{jv[0]}.{jv[1]}.{jv[2]}", installed_now=False)
                else:
                    v2 = _ensure_java(java_required_major, prefer=java_prefer, allow_conda_fallback=java_allow_conda_fallback)
                    _print_status(f"Java (requires ≥{java_required_major})", v2, installed_now=True)

                _install_gatk(install = not check)

        elif pkg == 'cnvkit':
            binname, vfunc = other_pkgs[pkg]
            binpath = _which(binname)
            if binpath:
                v = vfunc()
                _print_status(pkg, v, installed_now=False)
            elif not check:
                _install_cnvkit(install = not check)

        elif pkg == 'hifiasm_meta':
            binname, vfunc = other_pkgs[pkg]
            binpath = _which(binname)
            if binpath:
                v = vfunc()
                _print_status(pkg, v, installed_now=False)
            elif not check:
                _install_hifiasm_meta()

        else:
            print("%s: not supported" % pkg)

    return

