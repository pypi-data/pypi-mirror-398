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

from django.urls import path, include
from django.views.generic import TemplateView
from .views import TaxGraph

from .views import StructureAtom, StructureAtomsGroup, StructureAttribute

app_name = 'taxonomy'

urlpatterns = [
    path('', TemplateView.as_view(template_name='django-gem-taxonomy/homepage/homepage.html'),
         name='home'),

    path('structure/attribute/',
         StructureAttribute.as_view(), name='taxonomy_struct_attributes'),
    path('structure/atom/',
         StructureAtom.as_view(), name='taxonomy_struct_atoms'),
    path('structure/atom/<str:atom>',
         StructureAtom.as_view(), name='taxonomy_struct_atom'),

    path('structure/atoms_group/',
         StructureAtomsGroup.as_view(), name='taxonomy_struct_atomsgroups'),
    path('structure/atoms_group/<str:atoms_group>',
         StructureAtomsGroup.as_view(), name='taxonomy_struct_atomsgroup'),

    path('structure/attribute/<str:attribute>',
         StructureAttribute.as_view(), name='taxonomy_struct_attribute'),

    path('graph/',
         TaxGraph.as_view(), name='taxonomy_taxgraph'),

    path('api/v1/', include('django_gem_taxonomy.urls_api_v1')),
 ]
# [A-Z0-9]+
