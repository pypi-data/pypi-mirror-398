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

# import subprocess
# from django.conf import settings
from django.core.management import call_command
from pprint import pprint
from django.core.management.base import BaseCommand
import copy
import json

from django_gem_taxonomy.models import Attribute, AtomsGroup, Atom, Param


class Command(BaseCommand):
    help = ("Based on taxonomy vers 3 constraint typologies"
            " build attributes/atoms relationships db.")

    def add_arguments(self, parser):
        parser.add_argument('json_filename')

        # Optional arguments
        # parser.add_argument(
        #         '-p', '--docker-project', nargs=1, help='docker project name',
        #         default='oqgeoviewer')
        # parser.add_argument(
        #     '-l', '--list', action='store_true', help='Show projects that need'
        #     ' maintenance')
        # parser.add_argument(
        #     '-f', '--force', action='store_true', help='Rebuild cache in any'
        #     ' case')
        # parser.add_argument(
        #     '-k', '--keep-cache', action='store_true',
        #     help='Keep the existing cache')

    def handle(self, *args, **options):
        tax_json_in = None
        with open(options['json_filename'], 'r') as f:
            tax_json_in = json.load(f)

        for attr_in in tax_json_in['Attribute']:
            attr = Attribute.objects.create(
                name=attr_in['name'],
                prog=attr_in['prog'],
                title=attr_in['title'],
            )
            pprint(attr)

        for atg_in in tax_json_in['AtomsGroup']:
            atoms_group = AtomsGroup.objects.create(
                name=atg_in['name'],
                prog=atg_in['prog'],
                title=atg_in['title'],
                attr=Attribute.objects.get(name=atg_in['group'])
            )
            pprint(atoms_group)

        atom = Atom.objects.create(
            name='_ARG',
            prog=0,
            desc=('Virtual atom dependency to prevent arguments-only atoms'
                  ' to be visualized as unconstrained atoms'),
            args=None,
            params=None,
            type=json.dumps({"name": "virtual"}),
            group=None,
            attr=None,
        )
        for at_in in tax_json_in['Atom']:
            atom_name = at_in['name']
            atom_type = (tax_json_in['AtomType'][atom_name]
                         if atom_name in tax_json_in['AtomType']
                         else json.dumps({"name": "option"}))

            atom_args = (json.loads(at_in['args'])
                         if at_in['args'] else None)
            try:
                atom_params = (json.loads(at_in['params'])
                               if at_in['params'] else None)
            except Exception as inst:
                import pdb ; pdb.set_trace()

            print(atom_name)
            # import pdb ; pdb.set_trace()
            atom = Atom.objects.create(
                name=at_in['name'],
                prog=at_in['prog'],
                title=at_in['title'],
                desc=at_in['desc'],
                args=atom_args,
                params=atom_params,
                type=atom_type,
                group=AtomsGroup.objects.get(name=at_in['group']),
                attr=Attribute.objects.get(name=at_in['attr']),
            )
            try:
                if atom.name in tax_json_in['AtomsDeps']:
                    for dep in tax_json_in['AtomsDeps'][atom.name]:
                        atom.deps.add(Atom.objects.get(name=dep))
            except Exception as inst:
                import pdb ; pdb.set_trace()

            # import pdb ; pdb.set_trace()

        for param_atom, pa_ins in tax_json_in['Param'].items():
            for pa_in in pa_ins:
                param_name = pa_in['name']
                param_title = pa_in['title']
                param_desc = pa_in['desc']
                param_prog = pa_in['prog']

                Param.objects.create(
                    atom=Atom.objects.get(name=param_atom),
                    name=param_name,
                    title=param_title,
                    desc=param_desc,
                    prog=param_prog,
                )

        call_command('dumpdata', 'django_gem_taxonomy', indent=4,
                     output='out/taxonomy_standard_dump.json')

        tax_dump_in = json.load(open('out/taxonomy_standard_dump.json', 'r'))

        tax = {}
        for el in tax_dump_in:
            model = el['model'].replace('django_gem_taxonomy.', '')
            if model not in tax:
                tax[model] = {}
            tax[model][el['pk']] = el['fields']

            # NOTE: code to investigate wrong name set
            # if 'name' not in tax[model][el['pk']]:
            #     print('WARNING name missing in: %s' % tax[model][el['pk']])
            # elif tax[model][el['pk']]['name'] != el['pk']:
            #     print('WARNING different name in: %s (%s)' % (
            #         tax[model][el['pk']], el['pk']))

            if 'name' not in tax[model][el['pk']]:
                tax[model][el['pk']]['name'] = el['pk']

        for el_key, el_val in tax['atom'].items():
            if 'rev_deps' not in el_val:
                el_val['rev_deps'] = []
            for el_dep_key, el_dep_val in tax['atom'].items():
                if el_dep_val['name'] == el_val['name']:
                    continue
                if el_val['name'] in el_dep_val['deps']:
                    el_val['rev_deps'].append(el_dep_val['name'])

        # sort rev_deps by 'group' and 'prog' to generate proper dropdown menu
        for atom_key, atom_val in tax['atom'].items():
            if atom_val['rev_deps']:
                rev_deps_new = sorted(
                    atom_val['rev_deps'],
                    key=lambda x: (
                        tax['atomsgroup'][tax['atom'][x]['group']]['prog'],
                        tax['atom'][x]['prog']))
                atom_val['rev_deps'] = rev_deps_new

        #for atg_key in tax['attrsgroup_ord']:
        #    atg = tax['attrsgroup'][atg_key]
        #    atg['attributes'] = sorted(
        #        atg['attributes'],
        #        key=lambda x: tax['attribute'][x]['prog'])


        # ordered atomgroups into attributes
        for atomsgroup_key, atomsgroup_val in tax['atomsgroup'].items():
            attr = tax['attribute'][atomsgroup_val['attr']]
            if 'atomsgroups' not in attr:
                attr['atomsgroups'] = []
            attr['atomsgroups'].append(atomsgroup_key)

        # sort atomsgroups by ['atomsgroup'][x]['prog']
        for attr_key, attr_val in tax['attribute'].items():
            attr_val['atomsgroups'] = sorted(
                attr_val['atomsgroups'],
                key=lambda x: tax['atomsgroup'][x]['prog'])

        for atom_key, atom_val in tax['atom'].items():
            if atom_val['group']:
                group = tax['atomsgroup'][atom_val['group']]
                if 'atoms' not in group:
                    group['atoms'] = []
                group['atoms'].append(atom_key)

        # sort atoms by ['atom'][x]['prog']
        for atomsgroup_key, atomsgroup_val in tax['atomsgroup'].items():
            atomsgroup_val['is_persistent'] = False

            # FIXME: check 'if 'atoms' in atomsgroup_val' needed
            #        because we start from a atoms partial populated
            #        standard definition
            if 'atoms' in atomsgroup_val:
                # check to set atomsgroup as persistent
                atoms_list = atomsgroup_val['atoms']
                for atom_name in atoms_list:
                    atom = tax['atom'][atom_name]
                    if not atom['deps']:
                        atomsgroup_val['is_persistent'] = True
                        break

                atomsgroup_val['atoms'] = sorted(
                    atomsgroup_val['atoms'],
                    key=lambda x: tax['atom'][x]['prog'])

        tax['atom_type'] = tax_json_in['AtomType']

        tax['param'] = copy.deepcopy(tax_json_in['Param'])

        json.dump(tax, open('out/taxonomy_standard4taxtweb.json', 'w'),
                  indent=4)
