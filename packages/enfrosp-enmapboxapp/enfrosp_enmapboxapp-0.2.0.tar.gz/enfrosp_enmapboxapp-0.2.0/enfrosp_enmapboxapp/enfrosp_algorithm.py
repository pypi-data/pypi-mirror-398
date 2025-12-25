# SPDX-License-Identifier: GPL-3.0-or-later
# FileType: SOURCE
# FileCopyrightText: 2025, Daniel Scheffler at GFZ Potsdam

# -*- coding: utf-8 -*-
"""This module provides the EnFROSPAlgorithm."""

import os
from os.path import expanduser
import psutil
from importlib.util import find_spec
from importlib.metadata import version as get_version
from datetime import date
from threading import Thread
from queue import Queue
from subprocess import Popen, PIPE
from glob import glob

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterNumber,
    NULL
)

from .version import __version__, check_minimal_enfrosp_version
from enfrosp.masking.snow_screening import SnowScreenerThresholds

_SNOW_DEFAULTS = SnowScreenerThresholds()
THRESHOLD_PARAMS = {
    'snow_th_418': ('snow_th_418_min', 'snow_th_418_max'),
    'snow_th_1026': ('snow_th_1026_min', 'snow_th_1026_max'),
    'snow_th_1235': ('snow_th_1235_min', 'snow_th_1235_max'),
    'snow_th_2200': ('snow_th_2200_min', 'snow_th_2200_max'),
}


class EnFROSPAlgorithm(QgsProcessingAlgorithm):
    # NOTE: The parameter assignments made here follow the parameter names in enfrosp/cli.py

    # Input parameters
    P_path_enmap_zipfile = 'path_enmap_zipfile'
    P_path_outdir = 'path_outdir'
    P_retrieve_clean_snow_grain_size = 'retrieve_clean_snow_grain_size'
    P_retrieve_polluted_snow_albedo_impurities = 'retrieve_polluted_snow_albedo_impurities'
    P_retrieve_polluted_snow_broadband_albedo = 'retrieve_polluted_snow_broadband_albedo'
    P_aot = 'aot'
    P_ae = 'ae'
    P_snow_pixels_only = 'snow_pixels_only'
    P_snow_th_418_min = 'snow_th_418_min'
    P_snow_th_418_max = 'snow_th_418_max'
    P_snow_th_1026_min = 'snow_th_1026_min'
    P_snow_th_1026_max = 'snow_th_1026_max'
    P_snow_th_1235_min = 'snow_th_1235_min'
    P_snow_th_1235_max = 'snow_th_1235_max'
    P_snow_th_2200_min = 'snow_th_2200_min'
    P_snow_th_2200_max = 'snow_th_2200_max'
    P_snow_k1 = 'snow_k1'
    P_snow_k2 = 'snow_k2'

    # # Output parameters
    P_OUTPUT_RASTER = 'outraster'
    # P_OUTPUT_VECTOR = 'outvector'
    # P_OUTPUT_FILE = 'outfile'
    P_OUTPUT_FOLDER = 'outfolder'

    def group(self):
        return 'Snow'

    def groupId(self):
        return 'Snow'

    def name(self):
        return 'EnFROSPAlgorithm'

    def displayName(self):
        return f'EnFROSP - EnMAP Fast Retrieval Of Snow Properties (v{__version__})'

    def createInstance(self, *args, **kwargs):
        return type(self)()

    @staticmethod
    def _get_default_output_dir():
        userhomedir = expanduser('~')

        default_enfrosp_dir = \
            os.path.join(userhomedir, 'Documents', 'EnFROSP', 'Output') if os.name == 'nt' else\
            os.path.join(userhomedir, 'EnFROSP', 'Output')

        outdir_nocounter = os.path.join(default_enfrosp_dir, date.today().strftime('%Y%m%d'))

        counter = 1
        while os.path.isdir('%s__%s' % (outdir_nocounter, counter)):
            counter += 1

        return '%s__%s' % (outdir_nocounter, counter)

    def addParameter(self, param, *args, advanced=False, help_str=None, **kwargs):
        """Add a parameter to the QgsProcessingAlgorithm.

        This overrides the parent method to make it accept an 'advanced' parameter.

        :param param:       the parameter to be added
        :param args:        arguments to be passed to the parent method
        :param advanced:    whether the parameter should be flagged as 'advanced'
        :param help_str:    help text to be displayed as balloon tip as mouse-over event
        :param kwargs:      keyword arguments to be passed to the parent method
        """
        if help_str:
            param.setHelp(help_str)
        if advanced:
            param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        super(EnFROSPAlgorithm, self).addParameter(param, *args, **kwargs)

    def initAlgorithm(self, configuration=None):
        ####################
        # basic parameters #
        ####################

        self.addParameter(
            QgsProcessingParameterFile(
                name=self.P_path_enmap_zipfile,
                description='EnMAP Level-1C image',
                fileFilter='ZIP files (ENMAP01-____L1C*.zip ENMAP01-____L1C*.ZIP)'),
            help_str='Input path of the EnMAP L1C image to be processed as ZIP file (ENMAP01-____L1C*.ZIP).'
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                name=self.P_path_outdir,
                description='Output directory',
                defaultValue=self._get_default_output_dir(),
                optional=True),
            help_str='Output directory where the processed data and log files are saved.'
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.P_retrieve_clean_snow_grain_size,
                description='retrieve clean snow grain size',
                defaultValue=True),
            help_str=''
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.P_retrieve_polluted_snow_albedo_impurities,
                description='retrieve polluted snow albedo and impurities',
                defaultValue=True),
            help_str=''
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.P_retrieve_polluted_snow_broadband_albedo,
                description='retrieve polluted snow broadband albedo',
                defaultValue=True),
            help_str=''
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.P_snow_pixels_only,
                description='snow pixels only',
                defaultValue=False),
            help_str='Run retrieval only on snow pixels (enables threshold-based classification).'
        )

        #######################
        # advanced parameters #
        #######################

        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.P_aot,
                description='[Retrievals] - aerosol optical thickness (AOT)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.05, minValue=0, maxValue=1),
            advanced=True,
            help_str='Custom aerosol optical thickness (AOT) to override the default value '
                     '(0.05 for Antarctica, 0.085 for the rest of the world).',
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.P_ae,
                description='[Retrievals] - angström exponent (AE)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.3, minValue=0),
            advanced=True,
            help_str='Custom angström exponent (AE) to override the default value '
                     '(1.3 for Antarctica, 1.2 for the rest of the world)',
        )

        for wvl in [418, 1026, 1235, 2200]:
            for minmax in ['Minimum', 'Maximum']:

                param = getattr(self, f'P_snow_th_{wvl}_{"min" if minmax == "Minimum" else "max"}')
                default = getattr(_SNOW_DEFAULTS, f'th_{wvl}')[0 if minmax == 'Minimum' else 1]

                self.addParameter(
                    QgsProcessingParameterNumber(
                        name=param,
                        description=f'[Snow screening] - {minmax} TOA reflectance for snow pixels at {wvl} nm',
                        type=QgsProcessingParameterNumber.Double,
                        defaultValue=default, minValue=0, maxValue=1),
                    advanced=True,
                    help_str=f'{minmax} TOA reflectance assumed for snow pixels at {wvl} nm [0 - 1]',
                )

        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.P_snow_k1,
                description='[Cloud screening] - SWIR band-ratio coefficient k1',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.4, minValue=0),
            advanced=True,
            help_str="""
            Coefficient applied to the SWIR band-ratio criterion to distinguish between
            snow and clouds (default: 0.4). Snow is assumed if R(2200) <= k1 * R(1235).
            Idea: Clouds show smaller reflectance differences between these bands.
            """,
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.P_snow_k2,
                description='[Cloud screening] - Oxygen A-band coefficient k2',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.7, minValue=0),
            advanced=True,
            help_str="""
            Coefficient applied to the oxygen A-band criterion at 763.4 nm
            to distinguish between snow and clouds (default: 1.7).
            Snow is assumed if R(763) > k2 * min(R(763)).
            Idea: Large reflectance at this channel indicates clouds or
            high-relief terrain where light does not reach the surface.
            """,
        )

    @staticmethod
    def shortHelpString(*args, **kwargs):
        """Display help string.

        Example:
        '<p>Here comes the HTML documentation.</p>' \
        '<h3>With Headers...</h3>' \
        '<p>and Hyperlinks: <a href="www.google.de">Google</a></p>'

        :param args:
        :param kwargs:
        """
        text = \
            """
            <p>EnFROSP is a Python algorithm developed at GFZ Potsdam for advanced atmospheric correction of EnMAP \
            hyperspectral satellite data over snow and ice. It implements several snow parameter retrieval algorithms \
            originally developed in FORTRAN by Alexander Kokhanovsky, enabling the retrieval of key snow properties \
            such as grain size, albedo, and impurities for both clean and polluted snow. EnFROSP takes \
            the official EnMAP L1C data product, provided by the German Aerospace Center (DLR), as input and \
            delivers the retrieval results as ENVI BSQ files.</p>
            <p>General information about this EnMAP-Box app can be found \
            <a href="https://enmap.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/doc/">here</a>. \
            For details, e.g., about the algorithms implemented in EnFROSP, take a look at the \
            <a href="https://enmap.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/EnFROSP/doc/index.html">EnFROSP \
            backend documentation</a>.</p> \
            <p>Move the mouse over the individual parameters to view the tooltips for more information or check out \
            the <a href="https://enmap.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/EnFROSP/doc/usage.html#
            command-line-utilities">documentation</a>.</p>
            """

        return text

    def helpString(self):
        return self.shortHelpString()

    @staticmethod
    def helpUrl(*args, **kwargs):
        return 'https://enmap.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/doc/'

    @staticmethod
    def _get_preprocessed_parameters(parameters):
        # replace Enum parameters with corresponding strings (not needed in case of unittest)
        for n, opts in [
            # ('output_format', {0: 'GTiff', 1: 'ENVI'}),
            # ('output_interleave', {0: 'band', 1: 'line', 2: 'pixel'}),
            # ('mode_ac', {0: 'land', 1: 'water', 2: 'combined'}),
            # ('land_ac_alg', {0: 'SICOR', 1: 'ISOFIT'}),
            # ('isofit_surface_category', {0: 'multicomponent_surface', 1: 'ree', 2: 'custom'}),
            # ('deadpix_P_algorithm', {0: 'spectral', 1: 'spatial'}),
            # ('deadpix_P_interp_spectral', {0: 'linear', 1: 'quadratic', 2: 'cubic'}),
            # ('deadpix_P_interp_spatial', {0: 'linear', 1: 'bilinear', 2: 'cubic', 3: 'spline'}),
            # ('ortho_resampAlg', {0: 'nearest', 1: 'bilinear', 2: 'gauss', 3: 'cubic',
            #                      4: 'cubic_spline', 5: 'lanczos', 6: 'average'}),
            # ('vswir_overlap_algorithm', {0: 'order_by_wvl', 1: 'average', 2: 'vnir_only', 3: 'swir_only'}),
            # ('target_projection_type', {0: 'UTM', 1: 'Geographic'}),
        ]:
            if isinstance(parameters[n], int):
                parameters[n] = opts[parameters[n]]

        # remove all parameters not to be forwarded to the EnFROSP CLI
        parameters = {k: v for k, v in parameters.items() if v not in [None, NULL, 'NULL', '']}

        return parameters

    @staticmethod
    def _get_cmd(parameters) -> str:
        clean_snow_grain_size = parameters.pop('retrieve_clean_snow_grain_size')
        polluted_snow_albedo_impurities = parameters.pop('retrieve_polluted_snow_albedo_impurities')
        polluted_snow_broadband_albedo = parameters.pop('retrieve_polluted_snow_broadband_albedo')

        if polluted_snow_broadband_albedo:
            # runs ALL retrievals because they are all required for the broadband albedo
            cmd_parser_str = 'enfrosp retrieve polluted_snow_broadband_albedo'
        else:
            if polluted_snow_albedo_impurities:
                # runs only polluted snow albedo and impurities retrieval
                cmd_parser_str = 'enfrosp retrieve polluted_snow_albedo_impurities'
            elif clean_snow_grain_size:
                # runs only clean snow grain size retrieval
                cmd_parser_str = 'enfrosp retrieve clean_snow_grain_size'
            else:
                return 'NO RETRIEVAL'

        cli_args = []
        th_args = []

        # handle threshold tuples
        # TODO: probably better include into _get_preprocessed_parameters
        for cli_key, (min_key, max_key) in THRESHOLD_PARAMS.items():
            min_val = parameters.pop(min_key, None)
            max_val = parameters.pop(max_key, None)

            if min_val is not None and max_val is not None:
                th_args.append(f"--{cli_key} {min_val} {max_val}")

        # remaining single-value parameters
        cli_args.extend(
            f"--{key} {parameters[key]}"
            for key in sorted(parameters)
            if parameters[key] not in [None, NULL, 'NULL', '']
        )

        return f"{cmd_parser_str} {' '.join(cli_args)} {' '.join(th_args)}"

    @staticmethod
    def _run_cmd(cmd, qgis_feedback=None, **kwargs):
        """Execute external command and get its stdout, exitcode and stderr.

        Code based on: https://stackoverflow.com/a/31867499

        :param cmd: a normal shell command including parameters
        """
        def reader(pipe, queue):
            try:
                with pipe:
                    for line in iter(pipe.readline, b''):
                        queue.put((pipe, line))
            finally:
                queue.put(None)

        process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, **kwargs)
        q = Queue()
        Thread(target=reader, args=[process.stdout, q]).start()
        Thread(target=reader, args=[process.stderr, q]).start()

        stdout_qname = None
        stderr_qname = None

        # for _ in range(2):
        for source, line in iter(q.get, None):
            if qgis_feedback.isCanceled():
                # qgis_feedback.reportError('CANCELED')

                proc2kill = psutil.Process(process.pid)
                for proc in proc2kill.children(recursive=True):
                    proc.kill()
                proc2kill.kill()

                raise KeyboardInterrupt

            linestr = line.decode('latin-1').rstrip()
            # print("%s: %s" % (source, linestr))

            # source name seems to be platform/environment specific, so grab it from dummy STDOUT/STDERR messages.
            if linestr == 'Connecting to EnFROSP STDOUT stream.':
                stdout_qname = source.name
                continue
            if linestr == 'Connecting to EnFROSP STDERR stream.':
                stderr_qname = source.name
                continue

            if source.name == stdout_qname:
                qgis_feedback.pushInfo(linestr)
            elif source.name == stderr_qname:
                qgis_feedback.reportError(linestr)
            else:
                qgis_feedback.reportError(linestr)

        exitcode = process.poll()

        return exitcode

    def _handle_results(self, parameters: dict, feedback, exitcode: int) -> dict:
        success = False

        if exitcode:
            feedback.reportError("\n" +
                                 "=" * 60 +
                                 "\n" +
                                 "An exception occurred. Processing failed.")

        # list output dir
        if 'output_dir' in parameters:
            outdir = parameters['output_dir']
            outraster_matches = \
                glob(os.path.join(outdir, '*', '*SPECTRAL_IMAGE.TIF')) or \
                glob(os.path.join(outdir, '*', '*SPECTRAL_IMAGE.bsq')) or \
                glob(os.path.join(outdir, '*', '*SPECTRAL_IMAGE.bil')) or \
                glob(os.path.join(outdir, '*', '*SPECTRAL_IMAGE.bip'))
            outraster = outraster_matches[0] if len(outraster_matches) > 0 else None

            if os.path.isdir(outdir):
                if os.listdir(outdir):
                    feedback.pushInfo("The output folder '%s' contains:\n" % outdir)
                    feedback.pushCommandInfo('\n'.join([os.path.basename(f) for f in os.listdir(outdir)]) + '\n')

                    if outraster:
                        subdir = os.path.dirname(outraster_matches[0])
                        feedback.pushInfo(subdir)
                        feedback.pushInfo("...where the folder '%s' contains:\n" % os.path.split(subdir)[-1])
                        feedback.pushCommandInfo('\n'.join(sorted([os.path.basename(f)
                                                                   for f in os.listdir(subdir)])) + '\n')
                        success = True
                    else:
                        feedback.reportError("No output raster was written.")

                else:
                    feedback.reportError("The output folder is empty.")

            else:
                feedback.reportError("No output folder created.")

            # return outputs
            if success:
                return {
                    'success': True,
                    self.P_OUTPUT_RASTER: outraster,
                    # self.P_OUTPUT_VECTOR: parameters[self.P_OUTPUT_RASTER],
                    # self.P_OUTPUT_FILE: parameters[self.P_OUTPUT_RASTER],
                    self.P_OUTPUT_FOLDER: outdir
                }
            else:
                return {'success': False}

        else:
            feedback.pushInfo('The output was skipped according to user setting.')
            return {'success': True}

    @staticmethod
    def _prepare_enfrosp_environment() -> dict:
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['IS_ENFROSP_GUI_CALL'] = '1'
        # os.environ['IS_ENFROSP_GUI_TEST'] = '1'

        enfrosp_env = os.environ.copy()
        enfrosp_env["PATH"] = ';'.join([
            i for i in enfrosp_env["PATH"].split(';') if 'OSGEO' not in i]
        )  # actually not needed
        if "PYTHONHOME" in enfrosp_env.keys():
            del enfrosp_env["PYTHONHOME"]
        if "PYTHONPATH" in enfrosp_env.keys():
            del enfrosp_env["PYTHONPATH"]

        # FIXME is this needed?
        enfrosp_env['IPYTHONENABLE'] = 'True'
        enfrosp_env['PROMPT'] = '$P$G'
        enfrosp_env['PYTHONDONTWRITEBYTECODE'] = '1'
        enfrosp_env['PYTHONIOENCODING'] = 'UTF-8'
        enfrosp_env['TEAMCITY_VERSION'] = 'LOCAL'
        enfrosp_env['O4W_QT_DOC'] = 'C:/OSGEO4~3/apps/Qt5/doc'
        if 'SESSIONNAME' in enfrosp_env.keys():
            del enfrosp_env['SESSIONNAME']

        # import pprint
        # s = pprint.pformat(enfrosp_env)
        # with open('D:\\env.json', 'w') as fp:
        #     fp.write(s)

        return enfrosp_env

    def processAlgorithm(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        if not find_spec('enfrosp'):
            raise ImportError("enfrosp", "EnFROSP must be installed into the QGIS Python environment "
                                         "when calling 'EnFROSPAlgorithm'.")

        # check if the minimal needed EnFROSP backend version is installed
        # (only works if EnFROSP is installed in the same environment)
        check_minimal_enfrosp_version(get_version('enfrosp'))

        parameters = self._get_preprocessed_parameters(parameters)
        print(parameters)

        # print parameters and console call to log
        # for key in sorted(parameters):
        #     feedback.pushInfo('{} = {}'.format(key, repr(parameters[key])))

        cmd_str = self._get_cmd(parameters)
        if cmd_str == 'NO RETRIEVAL':
            feedback.pushInfo('No retrievals selected. Nothing to do.')
            return {'success': True}

        else:
            # print(f"{cmd_str}\n\n")
            feedback.pushInfo(f"\nCalling EnFROSP with the following command:\n{cmd_str}\n\n")

            # prepare environment for subprocess
            enfrosp_env = self._prepare_enfrosp_environment()
            # path_enfrosp_runscript = self._locate_enfrosp_run_script()

            # run EnFROSP in subprocess that activates the EnFROSP Conda environment
            # feedback.pushDebugInfo('Using %s to start EnFROSP.' % path_enfrosp_runscript)
            feedback.pushInfo("The EnFROSP log messages are written to the *.log file "
                              "in the specified output folder.")

            exitcode = self._run_cmd(cmd_str,
                                     qgis_feedback=feedback,
                                     env=enfrosp_env)

            return self._handle_results(parameters, feedback, exitcode)
