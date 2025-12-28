# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# oq-geoviewer
# Copyright (C) 2024 GEM Foundation
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
from django.db import models
import json

class Attribute(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    prog = models.IntegerField()
    title = models.TextField()


class AtomsGroup(models.Model):
    class Meta:
        unique_together = [['attr', 'prog']]

    name = models.CharField(max_length=256, primary_key=True)
    prog = models.IntegerField()
    title = models.TextField()
    attr = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    # mutex identify if it is possible or not dropdown multi-selection
    mutex = models.BooleanField(default=True)

# TODO: parameters description atom(param1[,param2[...,paramN]])
# class AtomParam(models.Model):
#     atom = models.ForeignKey(Atom)

# TODO: arguments description atom[:arg1[:arg2[...:argN]]]
# class AtomArg(models.Model):
#     atom = models.ForeignKey(Atom)


class Atom(models.Model):
    class Meta:
        unique_together = [['group', 'prog']]

    name = models.CharField(max_length=32, primary_key=True)
    prog = models.IntegerField()
    title = models.TextField()
    desc = models.TextField()
    group = models.ForeignKey(AtomsGroup, on_delete=models.CASCADE, null=True)
    attr = models.ForeignKey(Attribute, on_delete=models.CASCADE, null=True)
    type = models.TextField()
    args = models.JSONField(blank=True, null=True)
    params = models.JSONField(blank=True, null=True)
    deps = models.ManyToManyField('self', symmetrical=False,
                                  related_name='revdeps')
    # is_pseudoid = models.BooleanField()

    def entry_type(self):
        return json.loads(self.type)


class Param(models.Model):
    class Meta:
        unique_together = [['atom', 'name'], ['atom', 'name', 'prog']]

    atom = models.ForeignKey(Atom, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=32)
    title = models.TextField()
    desc = models.TextField()
    prog = models.IntegerField()
