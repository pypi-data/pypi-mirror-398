from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from pathlib import Path
import tempfile
import subprocess
import os
import sys
import shutil

# Friendly build_ext that checks for a working C compiler and prints helpful guidance if missing.
class FriendlyBuildExt(build_ext):
    def build_extensions(self):
        if not self._has_compiler():
            print(
                "\nERROR: A C compiler is required to build cert-uefi-support from source.\n"
                "Install one of the following for your platform:\n"
                " - Debian/Ubuntu: sudo apt install build-essential\n"
                " - Fedora: sudo dnf groupinstall 'Development Tools'\n"
                " - macOS: xcode-select --install\n"
                " - Windows: Install 'Build Tools for Visual Studio' (MSVC)\n"
                "Alternatively, install a prebuilt wheel if available on PyPI.\n"
            )
            sys.exit(1)
        super().build_extensions()

    def _has_compiler(self):
        """Try compiling a tiny C file using the detected compiler."""
        compiler = self.compiler
        # check for MSVC compiler and initiatlize it
        if hasattr(compiler, 'initialize'):
            compiler.initialize()

        tmpdir = tempfile.mkdtemp()
        src_file = os.path.join(tmpdir, "test.c")
        try:
            with open(src_file, "w") as f:
                f.write("int main(void){return 0;}")

            # Compile the source file
            try:
                objs = compiler.compile([src_file], output_dir=tmpdir)
            except Exception:
                return False

            # Optional: try linking (Windows MSVC may need this)
            try:
                exe_file = os.path.join(tmpdir, "test.exe")
                compiler.link_executable(objs, exe_file)
            except Exception:
                return False

            return True

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

# BaseTools path under edk2 repository (may be present as a submodule)
BaseToolsDir = Path("edk2/BaseTools")
if not BaseToolsDir.exists():
    print("WARNING: edk2/BaseTools not found. If you need full functionality run:")
    print("  git submodule update --init --recursive")
    # don't exit; allow builds to proceed if CI provides sources / necessary files

# Define extension modules (mirror previous setup.py logic)
edk2Module = Extension(
    'uefi_support.EfiCompressor',
    sources=[
        str(Path(BaseToolsDir, 'Source', 'C', 'Common', 'Decompress.c')),
        str(Path('uefi_support', 'EfiCompressor.c'))
    ],
    include_dirs=[
        str(Path(BaseToolsDir, 'Source', 'C', 'Include')),
        str(Path(BaseToolsDir, 'Source', 'C', 'Include', 'Ia32')),
        str(Path(BaseToolsDir, 'Source', 'C', 'Common'))
    ]
)

# LZMA SDK sources (vendored under edk2 path in original layout)
LzmaSDK = Path(BaseToolsDir, 'Source', 'C', 'LzmaCompress', 'Sdk', 'C')
LzmaSDKFiles = [str(Path(LzmaSDK, x)) for x in ['Alloc.c', 'LzFind.c', 'LzmaDec.c', 'LzmaEnc.c', '7zFile.c', '7zStream.c', 'Bra86.c']]

lzmaModule = Extension(
    "uefi_support.LzmaCompressor",
    sources = LzmaSDKFiles + [str(Path('uefi_support', 'LzmaCompressor.c'))],
    include_dirs = [ str(LzmaSDK) ],
    define_macros = [('_7ZIP_ST', None)]
)

# Huffman/unhuffme sources (vendored in unhuffme/)
HuffmanPath = Path('unhuffme')
HuffmanFiles = [str(Path(HuffmanPath, x))
                for x in ['dict_cpt_1.c', 'dict_cpt_2.c',
                          'dict_pch_1.c', 'dict_pch_2.c', 'huffman.c']]
huffmanModule = Extension(
    "uefi_support.HuffmanCompressor",
    sources = HuffmanFiles + [str(Path('uefi_support', 'HuffmanCompressor.c'))],
    include_dirs = [ str(HuffmanPath) ])

# libmspack sources (vendored under libmspack/)
mspackPath = Path("libmspack/libmspack/mspack")
mspackFiles = [str(Path(mspackPath, x))
               for x in ['system.c', 'cabd.c', 'lzxd.c', 'mszipd.c', 'qtmd.c']]

cabModule = Extension(
    "uefi_support.Cab",
    sources = mspackFiles + [str(Path('uefi_support', 'Cab.c'))],
    include_dirs = [ str(mspackPath) ],
)

setup(
    use_scm_version=True,
    package_dir={'uefi_support': 'uefi_support'},
    packages=['uefi_support'],
    package_data={'uefi_support': ['huff11.bin']},
    ext_modules=[edk2Module, lzmaModule, huffmanModule, cabModule],
    cmdclass={"build_ext": FriendlyBuildExt},
)

