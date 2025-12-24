import os
import platform
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper


def compress(source: str | os.PathLike | _TemporaryFileWrapper,
             target: str | os.PathLike,
             power: int = 0,
             ghostscript_command: str = None) -> None:
    """

    :param source: Source PDF file
    :param target: Target location to save the compressed PDF
    :param power: Power of the compression. Default value is 0. This can be
                    0: default,
                    1: prepress,
                    2: printer,
                    3: ebook,
                    4: screen
    :param ghostscript_command: The name of the ghostscript executable. If set to the default value None, is attempted
                                to be inferred from the OS.
                                If the OS is not Windows, "gs" is used as executable name.
                                If the OS is Windows, and it is a 64-bit version, "gswin64c" is used. If it is a 32-bit
                                version, "gswin32c" is used.
    """
    quality = {
        0: '/default',
        1: '/prepress',
        2: '/printer',
        3: '/ebook',
        4: '/screen'
    }

    if ghostscript_command is None:
        if platform.system() == 'Windows':
            if platform.machine().endswith('64'):
                ghostscript_command = 'gswin64c'
            else:
                ghostscript_command = 'gswin32c'
        else:
            ghostscript_command = 'gs'

    if isinstance(source, _TemporaryFileWrapper):
        source = source.name

    source = Path(source)
    target = Path(target)

    if not source.is_file():
        raise FileNotFoundError('invalid path for input PDF file')

    if source.suffix != '.pdf':
        raise ValueError('Input file must be a .pdf file')

    subprocess.call([ghostscript_command,
                     '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                     '-dPDFSETTINGS={}'.format(quality[power]),
                     '-dNOPAUSE', '-dQUIET', '-dBATCH',
                     '-sOutputFile={}'.format(target.as_posix()),
                     source.as_posix()],
                    shell=platform.system() == 'Windows'
                    )


def _compress(result: bytes,
               target: str | os.PathLike,
               power: int,
               ghostscript_command: str | None):
    with NamedTemporaryFile(suffix='.pdf', delete=platform.system() != 'Windows') as tmp_file:
        tmp_file.write(result)

        compress(tmp_file, target, power, ghostscript_command)
