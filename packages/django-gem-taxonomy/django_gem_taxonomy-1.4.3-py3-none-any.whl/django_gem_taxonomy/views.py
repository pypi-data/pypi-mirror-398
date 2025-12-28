# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# django_gem_taxonomy
# Copyright (C) 2024-2025 GEM Foundation
#
# django_gem_taxonomy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django_gem_taxonomy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
from django.views import View
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

# from django.conf import settings

from .models import Atom, AtomsGroup, Attribute
from .version import __version__
from openquake.gem_taxonomy import GemTaxonomy
from parsimonious.exceptions import ParseError as ParsimParseError
from parsimonious.exceptions import (IncompleteParseError as
                                     ParsimIncompleteParseError)


class TaxtWEB(View):
    def get(self, request):
        template = 'taxtweb.html'
        return render(request, template, {})


class TaxGraph(View):
    def get(self, request):
        template = 'django-gem-taxonomy/taxgraph/taxgraph.html'
        return render(request, template, {})


class StructureAtom(View):
    def get(self, request, atom=None):
        param = None
        template = 'django-gem-taxonomy/structure/atom.html'

        if atom is None:
            atoms = Atom.objects.all().order_by('name')
        else:
            atoms = None
            if ':' in atom:
                parts = atom.split(':')
                atom_id = parts[0]
                param_id = parts[1]

                atom = Atom.objects.get(name=atom_id)
                param = atom.param_set.get(name=param_id)
                template = 'django-gem-taxonomy/structure/param.html'
            else:
                atom = Atom.objects.get(name=atom)

        return render(request, template, {'atoms': atoms,
                                          'atom': atom,
                                          'param': param,
                                          })


class StructureAtomsGroup(View):
    def get(self, request, atoms_group=None):
        template = 'django-gem-taxonomy/structure/atoms_group.html'

        if atoms_group is None:
            atoms_groups = AtomsGroup.objects.all().order_by('prog')
            atoms_group = None
        else:
            atoms_groups = None
            atoms_group = AtomsGroup.objects.get(name=atoms_group)

        # import pdb ; pdb.set_trace()
        return render(request, template, {'atoms_groups': atoms_groups,
                                          'atoms_group': atoms_group})


class StructureAttribute(View):
    def get(self, request, attribute=None):
        template = 'django-gem-taxonomy/structure/attribute.html'

        if attribute is None:
            attributes = Attribute.objects.all().order_by('name')
            attribute = None
        else:
            attributes = None
            attribute = Attribute.objects.get(name=attribute)

        return render(request, template, {'attributes': attributes,
                                          'attribute': attribute})


class GEMTaxonomyInfo(APIView):
    def get(self, request):
        if request.method != 'GET':
            return Response({'message': 'Not implemented'}, status=405)

        info = GemTaxonomy.info(fmt='dict')
        return Response({**{'django_gem_taxonomy_version': __version__},
                         **info}, status=200)


class GEMTaxonomyStringValidation(APIView):
    # authentication_classes = [SessionAuthentication]

    def get(self, request, taxonomy_string):
        """
        Retrieve information about submitted taxonomy string
        """
        if request.method != 'GET':
            return Response({'message': 'Not implemented'}, status=405)

        gt = GemTaxonomy()

        try:
            _, _, report = gt.validate(taxonomy_string)
        except (ValueError, ParsimParseError,
                ParsimIncompleteParseError) as exc:
            return Response({'success': False, 'message': str(exc)},
                            status=400)
        return Response({**{'success': True}, **report}, status=200)


class GEMTaxonomyStringExplanation(APIView):
    # authentication_classes = [SessionAuthentication]

    def get(self, request, taxonomy_string):
        """
        Retrieve information about submitted taxonomy string
        """
        if request.method != 'GET':
            return Response({'message': 'Not implemented'}, status=405)

        fmt = request.query_params.get('fmt', 'json')

        gt = GemTaxonomy()

        try:
            fmt, expl, val_reply = gt.explain(taxonomy_string, fmt=fmt)
        except (ValueError, ParsimParseError,
                ParsimIncompleteParseError) as exc:
            return Response({'success': False, 'message': str(exc)},
                            status=400)

        if fmt in [GemTaxonomy.EXPL_OUT_TYPE.SINGLELINE,
                   GemTaxonomy.EXPL_OUT_TYPE.MULTILINE]:
            return Response({**{'success': True},
                             **{'explanation': expl},
                             **val_reply},
                            status=200)
        elif fmt in [GemTaxonomy.EXPL_OUT_TYPE.JSON]:
            return Response({**{'success': True},
                             **{'explanation': json.dumps(expl)},
                             **val_reply},
                            status=200)
        else:
            return Response({
                'success': False,
                'message': 'Unknown explain format %d' % fmt},
                            status=400)
