"""EnFROSP snow parameter retrieval."""

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

from dataclasses import dataclass
import numpy as np

from ..io.reader_enmap import EnMAPL1C


@dataclass
class SnowScreenerThresholds:
    """
    Configuration thresholds for the :class:`SnowScreener`.

    :param th_418:
        Lower and upper threshold for TOA reflectance at 418 nm between which
        snow is assumed (default: (0.8, 1.0)).

        Brighter scenes may be caused by 3-D illumination effects.
        Darker scenes may contain rocks, water, or ice, or may be affected
        by terrain shadows.

    :param th_1026:
        Lower and upper threshold for TOA reflectance at 1026 nm between which
        snow is assumed (default: (0.3, 0.8)) .

        Clouds are typically brighter than snow at this wavelength.

    :param th_1235:
        Lower and upper threshold for TOA reflectance at 1235 nm between which
        snow is assumed (default: (0.3, 0.65)).

        Clouds are typically brighter than snow at this wavelength.

    :param th_2200:
        Lower and upper threshold for TOA reflectance at 2200 nm between which
        snow is assumed (default: (0.01, 0.3)).

        Clouds are typically brighter than snow at this wavelength.

    :param k1:
        Coefficient applied to the SWIR band-ratio criterion (default: 0.4).

        Snow is assumed if::

            R(2200) <= k1 * R(1235)

        Clouds show smaller reflectance differences between these bands.

    :param k2:
        Coefficient applied to the oxygen A-band criterion at 763.4 nm (default: 1.7).

        Snow is assumed if::

            R(763) > k2 * min(R(763))

        Large reflectance at this channel indicates clouds or high-relief
        terrain where light does not reach the surface.
    """
    th_418: tuple[float, float] = (0.8, 1.0)
    th_1026: tuple[float, float] = (0.3, 0.8)
    th_1235: tuple[float, float] = (0.3, 0.65)
    th_2200: tuple[float, float] = (0.01, 0.3)
    k1: float = 0.4
    k2: float = 1.7

    def __post_init__(self):
        for attrN in ['th_418', 'th_1026', 'th_1235', 'th_2200']:
            low, high = getattr(self, attrN)
            if not (0.0 <= low <= high <= 1.0):
                raise ValueError(f"{attrN} must be within the range 0-1 with low <= high, got {low}-{high}.")

        for attrN in ['k1', 'k2']:
            attr = getattr(self, attrN)
            if attr < 0:
                raise ValueError(f"{attrN} must not be negative, got {attr}.")


class SnowScreener(object):
    def __init__(self,
                 enmap_image: EnMAPL1C,
                 thresholds: SnowScreenerThresholds = SnowScreenerThresholds(),
                 ):
        """Get an instance of SnowScreener.

        :param enmap_image:
            Instance of EnMAPL1C object.

        :param thresholds:
            Thresholds for the snow screening.
            See :class:`SnowScreenerThresholds` for parameter definitions.
        """
        self.im = enmap_image
        self.th_418 = thresholds.th_418
        self.th_1026 = thresholds.th_1026
        self.th_1235 = thresholds.th_1235
        self.th_2200 = thresholds.th_2200
        self.k1 = thresholds.k1
        self.k2 = thresholds.k2

    def compute_snow_mask(self):
        i_418 = np.argmin(np.abs(self.im.meta.wavelength - 418))
        i_763 = np.argmin(np.abs(self.im.meta.wavelength - 763.4))  # oxygen band
        i_1026 = np.argmin(np.abs(self.im.meta.wavelength - 1026))
        i_1235 = np.argmin(np.abs(self.im.meta.wavelength - 1235))
        i_2200 = np.argmin(np.abs(self.im.meta.wavelength - 2200))
        band_418 = self.im.toa_reflectance[:, :, i_418]
        band_763 = self.im.toa_reflectance[:, :, i_763]
        band_1026 = self.im.toa_reflectance[:, :, i_1026]
        band_1235 = self.im.toa_reflectance[:, :, i_1235]
        band_2200 = self.im.toa_reflectance[:, :, i_2200]

        mask_snow_or_clouds = (
            np.all(np.dstack([
                band_418 > self.th_418[0] * 10000,  # >0.8
                band_418 < self.th_418[1] * 10000,  # <1.0

                band_1026 > self.th_1026[0] * 10000,  # >0.3
                band_1026 < self.th_1026[1] * 10000,  # <0.8

                band_1235 > self.th_1235[0] * 10000,  # >0.3
                band_1235 < self.th_1235[1] * 10000,  # <0.65

                band_2200 > self.th_2200[0] * 10000,  # >0.01
                band_2200 < self.th_2200[1] * 10000,  # <0.3
            ]),
                axis=2)
        )

        mask_clouds = (
            np.all(np.dstack([
                mask_snow_or_clouds,  # assumes no-data value of 0
                band_2200 > self.k1 * band_1235,
                band_763 <= self.k2 * np.min(band_763[np.any(band_763)])  # assumes no-data value of 0
            ]),
                axis=2)
        )

        mask_snow = mask_snow_or_clouds & ~mask_clouds

        return mask_snow
