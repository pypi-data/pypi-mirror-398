# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# oq-geoviewer
# Copyright (C) 2018-2019 GEM Foundation
#
# oq-geoviewer is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# oq-geoviewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.urls import path
# from .views import TaxtWEB, TaxtGraph
from .views import (GEMTaxonomyInfo,
                    GEMTaxonomyStringValidation,
                    GEMTaxonomyStringExplanation)

# from .views import HelpAtom, HelpAtomsGroup, HelpAttribute

urlpatterns = [
    path('info',
         GEMTaxonomyInfo.as_view(), name='taxonomy_info'),
    path('validation/',
         GEMTaxonomyStringValidation.as_view(), {'taxonomy_string': ''},
         name='taxonomy_validation_empty'),
    path('validation/<path:taxonomy_string>',
         GEMTaxonomyStringValidation.as_view(), name='taxonomy_validation'),
    path('explanation/',
         GEMTaxonomyStringExplanation.as_view(), {'taxonomy_string': ''},
         name='taxonomy_explanation_empty'),
    path('explanation/<path:taxonomy_string>',
         GEMTaxonomyStringExplanation.as_view(),
         name='taxonomy_explanation'),
 ]
