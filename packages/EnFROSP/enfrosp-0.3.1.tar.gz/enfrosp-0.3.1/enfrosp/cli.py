#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for enfrosp."""

# EnFROSP, EnMAP Fast Retrieval Of Snow Properties
#
# Copyright (c) 2024–2025, GFZ Helmholtz Centre Potsdam, Daniel Scheffler (danschef@gfz.de)
#
# This software was developed within the context of the EnMAP project supported
# by the DLR Space Administration with funds of the German Federal Ministry of
# Economic Affairs and Energy (on the basis of a decision by the German Bundestag:
# 50 EE 1529) and contributions from DLR, GFZ and OHB System AG.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter
import sys
import os
import json
from functools import wraps

from enfrosp import __version__
from enfrosp import Retrieval
from enfrosp.masking.snow_screening import SnowScreenerThresholds

_SNOW_DEFAULTS = SnowScreenerThresholds()


def get_enfrosp_argparser():
    """Get a console argument parser for EnFROSP."""
    parser = ArgumentParser(
        prog='enfrosp',
        description='EnFROSP command line argument parser',
        epilog="use '>>> enfrosp -h' for detailed documentation and usage hints."
    )
    parser.add_argument('--version', action='version', version=__version__)

    #####################
    # GENERAL ARGUMENTS #
    #####################

    general_opts_parser = ArgumentParser(add_help=False)
    gop_p = general_opts_parser.add_argument

    gop_p('-i', '--path_enmap_zipfile', type=str, default=None,
          help='input path of the EnMAP L1C image to be processed (zip-archive)')
    gop_p('-o', '--path_outdir', type=str, default=os.path.abspath(os.path.curdir),
          help='output directory where the processed data is saved')
    gop_p('--aot', type=float, default=None,
          help='aerosol optical thickness (AOT) to override the default value '
               '(0.05 for Antarctica, 0.085 for the rest of the world)')
    gop_p('--ae', type=float, default=None,
          help='angström exponent (AE) to override the default value '
               '(1.3 for Antarctica, 1.2 for the rest of the world)')
    gop_p('-s', '--snow_pixels_only', type=_str2bool, default=False, nargs='?', const=True,
          help='run retrieval only on snow pixels (enables threshold-based classification)')
    _add_snow_screening_options(general_opts_parser)

    retr_subparser = _add_retrieve_subparser(parser)
    retr_allsubparsers = retr_subparser.add_subparsers()

    _add_clean_snow_grain_size_subparser(retr_allsubparsers, general_opts_parser)
    _add_polluted_snow_albedo_impurities_subparser(retr_allsubparsers, general_opts_parser)
    _add_polluted_snow_broadband_albedo_subparser(retr_allsubparsers, general_opts_parser)

    return parser


def _add_snow_screening_options(general_opts_parser):
    snow_opts = general_opts_parser.add_argument_group(
        title="Snow screening options",
        description=(
            "Threshold-based snow classification parameters.\n"
            "See SnowScreenerThresholds documentation for details."
        )
    )

    sop = snow_opts.add_argument

    sop(
        "--snow_th_418",
        type=float,
        nargs=2,
        metavar=("LOW", "HIGH"),
        default=_SNOW_DEFAULTS.th_418,
        help=(
            "TOA reflectance threshold at 418 nm used for snow detection "
            "(overrides SnowScreenerThresholds.th_418)"
        ),
    )

    sop(
        "--snow_th_1026",
        type=float,
        nargs=2,
        metavar=("LOW", "HIGH"),
        default=_SNOW_DEFAULTS.th_1026,
        help=(
            "TOA reflectance threshold at 1026 nm "
            "(overrides SnowScreenerThresholds.th_1026)"
        ),
    )

    sop(
        "--snow_th_1235",
        type=float,
        nargs=2,
        metavar=("LOW", "HIGH"),
        default=_SNOW_DEFAULTS.th_1235,
        help=(
            "TOA reflectance threshold at 1235 nm "
            "(overrides SnowScreenerThresholds.th_1235)"
        ),
    )

    sop(
        "--snow_th_2200",
        type=float,
        nargs=2,
        metavar=("LOW", "HIGH"),
        default=_SNOW_DEFAULTS.th_2200,
        help=(
            "TOA reflectance threshold at 2200 nm "
            "(overrides SnowScreenerThresholds.th_2200)"
        ),
    )

    sop(
        "--snow_k1",
        type=float,
        default=_SNOW_DEFAULTS.k1,
        help=(
            "SWIR band-ratio coefficient k1 "
            "(overrides SnowScreenerThresholds.k1)"
        ),
    )

    sop(
        "--snow_k2",
        type=float,
        default=_SNOW_DEFAULTS.k2,
        help=(
            "Oxygen A-band coefficient k2 "
            "(overrides SnowScreenerThresholds.k2)"
        ),
    )


def _add_retrieve_subparser(parent_parser):
    subparsers = parent_parser.add_subparsers()

    retr_subparser = subparsers.add_parser(
        'retrieve',
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='Retrieve several snow properties from EnMAP L1C data.',
        help="retrieve snow properties from EnMAP L1C data (sub argument parser) - "
             "use 'enfrosp retrieve -h' for documentation and usage hints")

    return retr_subparser


def _add_clean_snow_grain_size_subparser(parent_parser, general_opts_parser):
    parser = parent_parser.add_parser(
        'clean_snow_grain_size',
        parents=[general_opts_parser],
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='Retrieve clean snow grain size.',
        help="retrieve clean snow grain size (sub argument parser) - "
             "use 'enfrosp retrieve clean_snow_grain_size -h' for documentation and usage hints"
    )
    parser.set_defaults(func=retrieve_clean_snow_grain_size)


def _add_polluted_snow_albedo_impurities_subparser(parent_parser, general_opts_parser):
    parser = parent_parser.add_parser(
        'polluted_snow_albedo_impurities',
        parents=[general_opts_parser],
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='Retrieve polluted snow albedo and impurities.',
        help="retrieve polluted snow albedo and impurities (sub argument parser) - "
             "use 'enfrosp retrieve clean_snow_grain_size -h' for documentation and usage hints"
    )
    parser.set_defaults(func=retrieve_polluted_snow_albedo_impurities)


def _add_polluted_snow_broadband_albedo_subparser(parent_parser, general_opts_parser):
    parser = parent_parser.add_parser(
        'polluted_snow_broadband_albedo',
        parents=[general_opts_parser],
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='Retrieve polluted snow broadband albedo.',
        help="retrieve polluted snow broadband albedo (sub argument parser) - "
             "use 'enfrosp retrieve polluted_snow_broadband_albedo -h' for documentation and usage hints"
    )
    parser.set_defaults(func=retrieve_polluted_snow_broadband_albedo)


def record_args_in_gui_test(func):
    """Decorator that records argparse arguments to a JSON file if IS_ENFROSP_GUI_TEST=1 and cancels the execution."""

    @wraps(func)
    def wrapper(cli_args: Namespace):
        if os.getenv('IS_ENFROSP_GUI_TEST') == "1":
            if not os.path.isdir(cli_args.path_outdir):
                raise NotADirectoryError(cli_args.path_outdir)

            data = vars(cli_args)  # converts Namespace → dict
            data.pop("func", None)  # remove callable
            path_output = os.path.join(cli_args.path_outdir, 'received_args_kwargs.json')

            with open(path_output, "w") as f:
                json.dump(data, f, indent=4)

            return None  # do not run the function as we are only interested in validating the arguments

        return func(cli_args)

    return wrapper


def build_snow_screener_config(args) -> SnowScreenerThresholds:
    cfg = SnowScreenerThresholds()

    if args.snow_th_418 is not None:
        cfg.th_418 = args.snow_th_418

    if args.snow_th_1026 is not None:
        cfg.th_1026 = args.snow_th_1026

    if args.snow_th_1235 is not None:
        cfg.th_1235 = args.snow_th_1235

    if args.snow_th_2200 is not None:
        cfg.th_2200 = args.snow_th_2200

    if args.snow_k1 is not None:
        cfg.k1 = args.snow_k1

    if args.snow_k2 is not None:
        cfg.k2 = args.snow_k2

    return cfg


def _init_retrieval(cli_args: Namespace) -> Retrieval:
    return (
        Retrieval(
            path_enmap_zipfile=cli_args.path_enmap_zipfile,
            path_outdir=cli_args.path_outdir,
            aot=cli_args.aot,
            ae=cli_args.ae,
            snow_pixels_only=cli_args.snow_pixels_only,
            snow_screening_thresholds=build_snow_screener_config(cli_args)
        )
    )


@record_args_in_gui_test
def retrieve_clean_snow_grain_size(cli_args: Namespace) -> Retrieval:
    rt = _init_retrieval(cli_args)
    rt.run_clean_snow_grain_size_retrieval(
        output_level=2  # FIXME hardcoded
    )
    return rt


@record_args_in_gui_test
def retrieve_polluted_snow_albedo_impurities(cli_args: Namespace) -> Retrieval:
    rt = _init_retrieval(cli_args)
    rt.run_polluted_snow_albedo_impurities_retrieval(
        write_rs=True,  # FIXME hardcoded
        write_rp=True,  # FIXME hardcoded
        write_bba_plane=True  # FIXME hardcoded
    )
    return rt


@record_args_in_gui_test
def retrieve_polluted_snow_broadband_albedo(cli_args: Namespace) -> Retrieval:
    rt = _init_retrieval(cli_args)
    rt.run_clean_snow_grain_size_retrieval(output_level=0)
    rt.run_polluted_snow_albedo_impurities_retrieval()
    rt.run_polluted_snow_broadband_albedo_retrieval()

    return rt


def _find_deepest_parser(parser: argparse.ArgumentParser, argv: list):
    current = parser
    remaining = list(argv)

    while remaining:
        sp_actions = [a for a in current._actions if isinstance(a, argparse._SubParsersAction)]
        if sp_actions:
            next_parser = sp_actions[0].choices.get(remaining[0])
            if next_parser:
                current = next_parser
                remaining = remaining[1:]
            else:
                break
        else:
            break

    return current, remaining


def _str2bool(v):
    """Convert string parameter to bool.

    From: https://stackoverflow.com/a/43357954/2952871

    :param v:
    :return:
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def main(parsed_args: Namespace = None) -> int:
    if parsed_args is None:
        parser = get_enfrosp_argparser()
        target_parser, argv = _find_deepest_parser(parser, sys.argv[1:])

        if argv:
            parsed_args = parser.parse_args()
        else:
            target_parser.print_help()
            return 0

    parsed_args.func(parsed_args)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
