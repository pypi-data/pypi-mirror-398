//
//
//      TaxtGraph
//
//

var gem_tax = null; /* taxonomy standard description structure */
var color_hs = {h: 0.0 / 360.0, s: 0.08};
var args_color_hue = 120.0 / 360.0;
var params_color_hue = 210.0 / 360.0;
var color_delta = 0.03

var gem_valid_args_types = ['filtered_attribute', 'filtered_atomsgroup']
var gem_valid_params_types = ['options', 'int', 'float', 'rangeable_int', 'rangeable_float']

// TODO:
// WIP: consistency check for 'shb_3state' when "Collapse all" and "Expand all"
//
// WIP: parameters types (DONE: filtered_attribute, filtered_atomsgroup, float, int, MISSING: rangeable int and float)
//
//
// add inner link
//
// HOT: PREFIX ARGUMENTS DESCRIPTION
//
// MANAGE MAYBE display: "none" or "block" depending on depth param
// adjust atomsgroup title with button that is missing and the other atom args description
// params for LFINF
// $subatom.append(
// FIX LEAFS HERE
// FIX IRREGULARITIES
//
//
//
//
// TODO:
//   DONE - Manage arguments (with attribute filtering?)
//   - Manage other atom types
//   - Manage taxonomy generation
//   - Manage parameters checks
//   - Generate proper taxonomy
//   - Taxonomy ingestion
//   - Permalink
//   - link between direction X and Y
//   - Populate attribs groups Building Information,
//         Exterior Attributes, Roof/Floor/Foundation
//   - Manage visual layout as taxtweb
//
//
// FAR TODO:
//   - highlight better searched atoms
//   - views to ingest:
//       . new attributes
//       . new atomsgroups
//       . new atoms
//   - manage taxonomy extensions (namespacing)
//
// DONE:
//
// DONE - ADD INFO ABOUT ARGS



function hs2rgb(color_hs)
{
    return hsv2rgb(color_hs['h'], color_hs['s'], 1.0);
}

function hs2satrgb(color_hs)
{
    var new_s = (color_hs['s'] + 0.08 < 255 ? color_hs['s'] + 0.08 : 255);
    return hsv2rgb(color_hs['h'], new_s, 1.0);
}

function shb_buttons_set($anc, match, state)
{
    $anc.find(match).removeClass('shb_enable').removeClass('shb_deep').removeClass('shb_disable').addClass('shb_' + state);
    $anc.find(match).each(
        function each_set_title() {
            hideshowbutton_settitle($(this), 'shb_' + state);
        });
}


function info_button_settitle($btn, cls)
{
    $btn.prop('title', (
        cls == 'gem_info_show' ? 'show information' : (
            cls == 'gem_info_hide' ? 'hide information' : 'unknown status')));
}

function info_buttons_set($anc, match, state)
{
    $anc.find(match).removeClass('gem_info_show').removeClass('gem_info_hide').addClass('gem_info_' + state);
    $anc.find(match).each(
        function each_set_title() {
            info_button_settitle($(this), 'gem_info_' + state);
        });
}

function filtered_atomsgroup_filter(atomsgroup_name, atoms_not_included)
{
    // console.log(atomsgroup_name);
    var atomsgroup = gem_tax['atomsgroup'][atomsgroup_name];
    var atoms_list = atomsgroup['atoms'];
    var atoms = atoms_list.filter((name) => atoms_not_included.indexOf(name) == -1);

    var atomsgroup_ret = {
        title: atomsgroup['title'] + ' (filtered)',
        name: atomsgroup['name'],
        atoms: atoms
    };
    return atomsgroup_ret;
}


function filtered_atomsgroup(atomsgroup_name, atoms_not_included)
{
    var atomsgroup = gem_tax['atomsgroup'][atomsgroup_name];
    var filtered_atomsgroup_ret = JSON.parse(JSON.stringify(atomsgroup));

    filtered_atomsgroup_ret['atoms_not_included'] = atoms_not_included;

    return filtered_atomsgroup_ret;
}

function filtered_attribute(attribute_name, atoms_not_included)
{
    // console.log(attribute_name);
    var attribute = gem_tax['attribute'][attribute_name];

    var filtered_attribute_ret = JSON.parse(JSON.stringify(attribute));
    // console.log('atoms_not_included.set: ' + atoms_not_included);
    filtered_attribute_ret['atoms_not_included'] = atoms_not_included.slice();

    return filtered_attribute_ret;
}

function make_args_desc(atom)
{
    var ret = '';

    var type_splitted = atom['args']['type'].split('(')
    var type_body = type_splitted[0]

    if (type_body == 'filtered_atomsgroup') {
        var arg_atomsgroup = eval(atom['args']['type']);
        var arg_title = 'Atoms Group - ' + arg_atomsgroup['title'];
        var arg_atoms_not_included = arg_atomsgroup['atoms_not_included'];
    }
    else if (type_body == 'filtered_attribute') {
        var arg_attribute = eval(atom['args']['type']);
        var arg_title = 'Attribute - ' + arg_attribute['title'];
        var arg_atoms_not_included = arg_attribute['atoms_not_included'];
    }

    if (type_body == 'filtered_atomsgroup' || type_body == 'filtered_attribute') {
        var is_plural = ('args_max' in atom['args'] ? atom['args']['args_max'] > 1 : true);
        ret += '<h5>Argument' + (is_plural ? 's' : '') + ' info</h5>';
        ret += 'Type: ' + arg_title + (arg_atoms_not_included.length > 0 ? " (filtered)" : "") + '</br>';
    }
    else {
        ret += 'Argument type: Unknown.</br>';
    }
    if ('args_min' in atom['args'] && 'args_max' in atom['args'] && atom['args']['args_min'] == atom['args']['args_max']) {
        ret += 'Number of arguments: ' + atom['args']['args_min'] + '.</br>';
    }
    else {
        ret += 'Number of arguments: min = ' + ('args_min' in atom['args'] ? atom['args']['args_min'] : '0')
            + ', max = ' + ('args_max' in atom['args'] ? atom['args']['args_max'] : 'many')  + '</br>';
    }
    if ('must_be_diff' in atom['args']) {
        if (atom['args']['must_be_diff']) {
            ret += 'Arguments must have different values.</br>';
        }
        else {
            ret += 'Arguments can have the same value.</br>';
        }
    }

    return ret;
}

function make_params_desc($anc, atom)
{
    var ret = '';

    var type_splitted = atom['params']['type'].split('(')
    var type_body = type_splitted[0]

    $anc.append($('<h5/>').text('Parameters info'));
    if (type_body == 'options') {
        $anc.append('Type: closed list of options'
                   ); // .append(showhide_button(0)));
    }
    else if (type_body == 'float') {
        $anc.append('Type: float.');
    }
    else if (type_body == 'rangeable_float') {
        $anc.append($('<h5/>').html('Parameter type: rangeable float.')).append('valid values are:<ul><li>a single float ("<code><i>ATOM</i>:<i>n</i></code>") OR</li><li>a range of floats ("<code><i>ATOM</i>:<i>n1</i>-<i>n2</i></code>") with <code><i>n1</i></code> and <code><i>n2</i></code> included OR</li><li>floats less than or greater than a specific value ("<code><i>ATOM</i>:&lt;<i>n</i></code>" or "<code><i>ATOM</i>:&gt;<i>n</i></code>"), with <code><i>n</i></code> excluded.</li></ul>');
    }
    else if (type_body == 'int') {
        $anc.append($('<h5/>').text('Parameter type: integer.'));
    }
    else if (type_body == 'rangeable_int') {
        $anc.append('Type: rangeable integer.<br/>').append('valid values are:<ul><li>a single integer ("<code><i>ATOM</i>:<i>n</i></code>") OR</li><li>a range of integers ("<code><i>ATOM</i>:<i>n1</i>-<i>n2</i></code>") with <code><i>n1</i></code> and <code><i>n2</i></code> included OR</li><li>integers less than or greater than a specific value ("<code><i>ATOM</i>:&lt;<i>n</i></code>" or "<code><i>ATOM</i>:&gt;<i>n</i></code>"), with <code><i>n</i></code> excluded.</li></ul>');
    }

    // the implicit number of parameters is 1.
    if (!('params_min' in atom['params']) && (!('params_max' in atom['params']))) {
        ret += 'Number of parameters: 1.</br>';
    }
    else if ('params_min' in atom['params'] && 'params_max' in atom['params'] && atom['params']['params_min'] == atom['params']['params_max']) {
        ret += 'Number of parameters: ' + atom['params']['params_min'] + '.</br>';
    }
    else {
        ret += 'Number of parameters: min = ' + ('params_min' in atom['params'] ? atom['params']['params_min'] : '0')
            + ', max = ' + ('params_max' in atom['params'] ? atom['params']['params_max'] : 'many')  + '</br>';
    }

    var range_left = "", range_right = "";

    if ('min' in atom['params']) {
        if (!('min_incl' in atom['params'])) {
            alert('"min" params attribute present but not "min_incl"');
        }
        var val_min = (type_body == 'float' ? atom['params']['min'].toFixed(1) : atom['params']['min']);
        if (!('max' in atom['params'])) {
            range_right = (atom['params']['min_incl'] ? " >= " : " > ") + val_min;
        }
        else {
            range_left = val_min + (atom['params']['min_incl'] ? " <= " : " < ");
        }
    }
    if ('max' in atom['params']) {
        if (!('max_incl' in atom['params'])) {
            alert('"max" params attribute present but not "max_incl"');
        }
        var val_max = (type_body == 'float' ? atom['params']['max'].toFixed(1) : atom['params']['max']);
        range_right = (atom['params']['max_incl'] ? " <= " : " < ") + val_max;
    }

    if (range_left != "" || range_right != "") {
        ret += 'Valid values: ' + range_left + 'val' + range_right + ' .<br/>';
    }

    if ('must_be_diff' in atom['params']) {
        if (atom['params']['must_be_diff']) {
            ret += 'Parameters must have different values.</br>';
        }
        else {
            ret += 'Parameters can have the same value.</br>';
        }
    }

    $anc.append($('<p/>').html(ret));
}

function place_render(scope, color_hs, depth, id_pfx)
{

    var is_visible = (depth == 0 ? false : true);
    // console.log("place_render: depth: " + depth + ' is_visible: ' + (is_visible ? 'true' : 'false'));
    var $place = $('<div/>').addClass('gem_hideable').addClass('gem_scope_' + scope).attr('id', id_pfx + '_place').css(
        {
            display: (is_visible ? 'block' : 'none'),
            backgroundColor: hs2rgb(color_hs),
            borderLeft: "3px solid " + hs2satrgb(color_hs),
            borderBottom: "1px solid " + hs2satrgb(color_hs),
            margin: '0px',
            padding: '4px',
            paddingLeft: '16px',
        });
    return $place;
}

function place_info_render(scope, color_hs, id_pfx)
{

    var is_visible = true;
    var $place = $('<div/>').attr('id', id_pfx + '_place_info').css(
        {
            display: (is_visible ? 'block' : 'none'),
            backgroundColor: hs2rgb(color_hs),
            borderLeft: "3px solid " + hs2satrgb(color_hs),
            borderBottom: "1px solid " + hs2satrgb(color_hs),
            margin: '0px',
            padding: '4px',
            paddingLeft: '16px',
        });
    return $place;
}

function attribute_place_render(scope, color_hs, depth, id_pfx)
{
    return place_render(scope, color_hs, depth, id_pfx);
}

function atomsgroup_place_render(scope, color_hs, depth, id_pfx)
{
    return place_render(scope, color_hs, depth, id_pfx);
}

function params_place_render(scope, color_hs, depth, id_pfx)
{
    return place_render(scope, color_hs, depth, id_pfx);
}

function atom_desc_place_render(scope, color_hs, depth, id_pfx)
{
    return place_render(scope, color_hs, depth, id_pfx);
}

function atomsgroup_add(scope, $atom, atomsgroup, atomsgroup_items, newcol_hs, id_pfx, is_deep, depth, color_hs)
{
    atomsgroup['atoms'] = atomsgroup_items.slice();
    var $atomsgroup_place = atomsgroup_place_render(scope, newcol_hs, depth, id_pfx + "__" + atomsgroup['name']);
    $atom.append($atomsgroup_place);
    atomsgroup_render(scope, $atomsgroup_place, id_pfx, atomsgroup, null, is_deep, depth, color_hs);
}

function add_leafs(scope, id_pfx, $atom, atom, depth, color_hs)
{
    var atomsgroup = null;
    var atomsgroup_name = '';
    var $atomsgroup_place = null;
    var $atom_info_cont = null;
    var args = '';
    var $args = null;

    if (atom['desc'] != '' || atom['args'] || atom['params']) {
        $atom_info_cont = $('<div/>').addClass('gem_info gem_info_hide').css('display', 'none');
        $atom.append($atom_info_cont);
    }
    if (atom['desc']) {
        var atom_desc = atom['desc'].replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('\n', '<br/>');
        var desc_id_pfx = id_pfx + '__' + atom['name'] + '__desc';
        var $atom_desc_place = place_info_render('atom', color_hs, desc_id_pfx);
        $atom_desc_place.append($('<p/>').css({margin: '8px 8px 8px 0px'}).append('<h5>Description</h5>').append(atom_desc));
        $atom_info_cont.append($atom_desc_place);
    }

    if (atom['args']) {
        // console.log('add_leafs: begin args');
        var to_convert_hsbutton = false;
        var args_id_pfx = id_pfx + '__' + atom['name'] + '__args';

        var type_splitted = atom['args']['type'].split('(');
        var type_body = type_splitted[0];
        if (gem_valid_args_types.indexOf(type_body) == -1) {
            alert('for atom ' + atom['name'] + " it's argument type "
                  + type_body + ' is unknown');
        }

        if (type_body == 'filtered_attribute') {
            var args_color_hs = {h: args_color_hue, s: color_hs['s'] + color_delta};
            var args_color_atoms_hs = {h: args_color_hue, s: color_hs['s'] + (color_delta * 2.0)};
            var arg_attribute = eval(atom['args']['type']);
            var sub_id_pfx = args_id_pfx + '__' + atom['name'];

            var $arg_attribute_place = place_info_render(scope, args_color_hs, sub_id_pfx);
            $arg_attribute_place.removeClass('gem_hideable');
            $arg_attribute_place.append($('<p/>').css({margin: '8px 8px 8px 0px'}).html(make_args_desc(atom)));

            $arg_attribute = attribute_render('argument', arg_attribute, args_id_pfx, 0, args_color_atoms_hs).addClass('gem_hideable').addClass('gem_scope_argument').css('display', 'none');

            $atom_info_cont.append($arg_attribute_place);
            $atom.append($arg_attribute);
            to_convert_hsbutton = true;
        }
        else if (type_body == 'filtered_atomsgroup') {
            var args_color_hs = {h: args_color_hue, s: color_hs['s'] + color_delta};
            var args_color_atoms_hs = {h: args_color_hue, s: color_hs['s'] + (color_delta * 2.0)};
            var arg_atomsgroup = eval(atom['args']['type']);
            var sub_id_pfx = args_id_pfx + '__' + atom['name'];

            var $arg_info_place = place_info_render(scope, args_color_hs, sub_id_pfx);
            var $arg_atomsgroup_place = atomsgroup_place_render('argument', args_color_hs, 0, sub_id_pfx);

            $arg_info_place.removeClass('gem_hideable');
            $arg_info_place.append($('<p/>').css({margin: '8px 8px 8px 0px'}).html(make_args_desc(atom)));

            // NOTE: at the beginning arguments with dropdown are hided (depth = 0)
            // $arg_atomsgroup_place.append($('<p/>').text(arg_atomsgroup['desc']).append(showhide_button(0)));

            atomsgroup_render('argument', $arg_atomsgroup_place, sub_id_pfx, arg_atomsgroup, arg_atomsgroup['atoms_not_included'], false, 0, args_color_atoms_hs);
            $atom.append($arg_atomsgroup_place);
            $atom_info_cont.append($arg_info_place);
            to_convert_hsbutton = true;
        }
        else {
            $atom_info_cont.append($('<p/>').text('Type [' + type_body + '] unknown'));
        }

        if (to_convert_hsbutton) {
            var $items = $.merge($atom.parents('div.gem_hideable'), $atom.parents('div.gem_scope_base'));
            shb_buttons_set($atom, '> * > button.shb', 'enable');
            shb_buttons_set($items, '> * > button.shb', 'deep');
        }
    }
    if (atom['params']) {
        var to_convert_hsbutton = false;
        var params_color_hs = {h: (scope == 'argument' ? args_color_hue : params_color_hue), s: color_hs['s'] + color_delta};
        var options_color_hs = {h: (scope == 'argument' ? args_color_hue : params_color_hue), s: color_hs['s'] + (color_delta * 2)};
        var params_id_pfx = id_pfx + '__' + atom['name'] + '__params';

        var type_splitted = atom['params']['type'].split('(')
        var type_body = type_splitted[0]
        if (gem_valid_params_types.indexOf(type_body) == -1) {
            alert('forx atom ' + atom['name'] + " it's parameters type "
                  + type_body + ' is unknown');
        }

        if (type_body == 'options') {
            $params_place = place_info_render(scope, params_color_hs, params_id_pfx);
            make_params_desc($params_place, atom);
            $params_options = place_render('param', options_color_hs, 0, params_id_pfx + '__options__')

            params_options_render('param', $params_options, params_id_pfx, atom);
            $atom.append($params_options);

            $atom_info_cont.append($params_place);
            to_convert_hsbutton = true;
        }
        else if (type_body == 'int') {
            $params_place = place_info_render(scope, params_color_hs, params_id_pfx);
            make_params_desc($params_place, atom);
            $atom_info_cont.append($params_place);
        }
        else if (type_body == 'rangeable_int') {
            $params_place = place_info_render(scope, params_color_hs, params_id_pfx);
            make_params_desc($params_place, atom);
            $atom_info_cont.append($params_place);
        }
        else if (type_body == 'float') {
            $params_place = place_info_render(scope, params_color_hs, params_id_pfx);
            make_params_desc($params_place, atom);
            $atom_info_cont.append($params_place);
        }
        else if (type_body == 'rangeable_float') {
            $params_place = place_info_render(scope, params_color_hs, params_id_pfx);
            make_params_desc($params_place, atom);
            $atom_info_cont.append($params_place);
        }
        if (to_convert_hsbutton) {
            var $items = $.merge($atom.parents('div.gem_hideable'), $atom.parents('div.gem_scope_base'));
            shb_buttons_set($atom, '> * > button.shb', 'enable');
        }
    }

    var atomsgroup_items = [];
    var color_atomsgroup_hs = {h: color_hs['h'], s: color_hs['s'] + color_delta};
    for (var sub_key in atom['rev_deps']) {
        // console.log('sub_key in rev_deps: ' + atom['rev_deps']);
        var sub = gem_tax['atom'][atom['rev_deps'][sub_key]];
        if (sub['group'] != atomsgroup_name) {
            if (atomsgroup != null) {
                // console.log("rev_deps if sub['group']" + atomsgroup_name);
                atomsgroup_add(scope, $atom, atomsgroup, atomsgroup_items, color_atomsgroup_hs, id_pfx + "__" + atomsgroup['name'],
                               true, depth, color_atomsgroup_hs);

                atomsgroup_items = [];
            }
            atomsgroup_name = sub['group'];
            atomsgroup = Object.assign({}, gem_tax['atomsgroup'][atomsgroup_name]);
        }
        atomsgroup_items.push(sub['name']);
    }
    if (atom['rev_deps'].length > 0) {
        atomsgroup_add(scope, $atom, atomsgroup, atomsgroup_items, color_atomsgroup_hs, id_pfx, true, depth, color_atomsgroup_hs);
    }
}

function hideshowbutton_settitle($btn, cls)
{
    $btn.prop('title', (cls == 'shb_disable' ? 'hide branch' : cls == 'shb_enable' ? 'show one level of branch' : 'show full branch'));
}

// 2192 ->
// 21b4 ^v
// hide or show all children of the associated div
function hideshowbutton_cb(obj)
{
    $this = $(this);

    if ($this.hasClass('shb_enable')) {
        // clicked button management
        $this.removeClass('shb_enable');
        if ($this.hasClass('shb_3state')) {
            $this.addClass('shb_deep'); // next action
            hideshowbutton_settitle($this, 'shb_deep');
        }
        else {
            $this.addClass('shb_disable');
            hideshowbutton_settitle($this, 'shb_disable');
        }

        // hide all children
        $(this).parent().parent().find('div.gem_hideable').css('display', 'none');

        // enable direct son
        var $children = $(this).parent().parent().find('> div.gem_hideable');
        $children.css('display', 'block');
        shb_buttons_set($children, '> * > button.shb', 'enable');
        shb_buttons_set($children, '> div > * > button.shb', 'enable');
        // console.log('enable');
    }
    else if ($this.hasClass('shb_deep')) {
        $this.removeClass('shb_deep');
        $this.addClass('shb_disable');
        hideshowbutton_settitle($this, 'shb_disable');

        var $children = $(this).parent().parent().find('div.gem_hideable');
        $children.css('display', 'block');
        shb_buttons_set($children, '> * > button.shb', 'disable');
        shb_buttons_set($children, '> div > * > button.shb', 'disable');
        // console.log('deep');
    }
    else if ($this.hasClass('shb_disable')) {
        $this.removeClass('shb_disable');
        $this.addClass('shb_enable');
        hideshowbutton_settitle($this, 'shb_enable');
        var $children = $(this).parent().parent().find('div.gem_hideable');
        $children.css('display', 'none');
        shb_buttons_set($children, '> * > button.shb', 'disable');
        shb_buttons_set($children, '> div > * > button.shb', 'disable');
        // console.log('disable');
    }
}

function depth2nextclass(depth)
{
    return (depth == -1 ? 'shb_disable' : (depth == 0 ? 'shb_enable' : 'shb_deep'));
}

function showhide_button(depth) {
    var cls_action = depth2nextclass(depth)
    $btn = $('<button style="margin-left: 8px;" type="button" class="shb btn btn-primary btn-sm" autocomplete="off"/>');
    hideshowbutton_settitle($btn, cls_action);
    $btn.addClass(cls_action);

    $btn.click(hideshowbutton_cb);
    return ($btn);
}

function info_button() {
    $btn = $('<button style="margin-left: 8px;" type="button" class="item_info gem_info_show btn btn-outline-dark btn-sm" autocompleteoff"/>');
    // hideshowbutton_settitle($btn, '&#9432;');
    // $btn.addClass(cls_action);

    $btn.click(info_button_cb);
    return ($btn);
}

function info_button_cb() {
    $this = $(this);

    if ($this.hasClass('gem_info_show')) {
        // clicked button management
        $this.removeClass('gem_info_show');
        $this.addClass('gem_info_hide'); // next action
        $this.removeClass('btn-outline-dark');
        $this.addClass('btn-dark');
        info_button_settitle($this, 'gem_info_hide');
        // hide all children
        $(this).parent().parent().find('> div.gem_info').css('display', 'inline-block');
    }
    else if ($this.hasClass('gem_info_hide')) {
        // clicked button management
        $this.removeClass('gem_info_hide');
        $this.addClass('gem_info_show'); // next action
        info_button_settitle($this, 'gem_info_show');

        // hide all children
        $(this).parent().parent().find('> div.gem_info').css('display', 'none');
        $this.removeClass('btn-dark');
        $this.addClass('btn-outline-dark');
    }
}

function taxtgraph_compress_all() {
    $('body').find('div.gem_hideable').css('display', 'none');
    $('body').find('div.atom_highlight').removeClass('atom_highlight');

    shb_buttons_set($('body'), 'button.shb', 'enable');

    $('body').find('input[name="atom"]').val('');
    $('a[name="atom-search-link"]').attr(
        'href', window.location.protocol + '//' + window.location.host + window.location.pathname);
    $('a[name="atom-search-link"]').css('display', 'none');
}

function taxtgraph_uncompress_all() {
    $('body').find('div.gem_hideable.gem_scope_atom').css('display', 'block');

    var $items = $.merge($('body').find('div.gem_hideable'),
                         $('body').find('div.gem_scope_base'));
    shb_buttons_set($items, '> * > button.shb', 'disable');

    var $begin_args = $('body').find('div.gem_hideable.gem_scope_atom > * > div.gem_hideable.gem_scope_argument'
                                    ).parent();
    var $begin_params = $('body').find('div.gem_hideable.gem_scope_atom > * > div.gem_hideable.gem_scope_param'
                                      ).parent();
    var $begin_limits = $.merge($begin_args, $begin_params);
    var $items = $.merge($begin_limits.parents('div.gem_hideable'), $begin_args.parents('div.gem_scope_base'));
    shb_buttons_set($items, '> * > button.shb', 'deep');
    shb_buttons_set($begin_limits, '> * > button.shb', 'enable');
}

function testResults (form) {
    var inputValue = form.inputbox.value;
    alert ("You typed: " + inputValue);
}


function showhide_parent($atom) {
    if ($atom[0].tagName == 'BODY') {
        return;
    }
    if ($atom.hasClass('gem_hideable')) {
        $atom.css('display', 'block');
    }
    showhide_parent($atom.parent());
}

function taxtgraph_form_highlightatom_cb(event) {
    taxtgraph_highlightatom(event.target['atom'].value.toUpperCase());
}

function taxtgraph_highlightatom(atom_name) {
    taxtgraph_compress_all();
    var $atoms = $('body').find('div[name="' + atom_name + '"]');
    $atoms.addClass('atom_highlight');
    for (i = 0 ; i < $atoms.length ; i++) {
        var $atom = $($atoms[i]);
        $atom.css({
            display: 'block'
        });
        showhide_parent($atom.parent());
    }
    /* add disable buttons to all the tree */
    shb_buttons_set($('body'), 'button.shb', 'enable');
    var $items = $.merge($atoms.parents('div.gem_hideable'), $atoms.parents('div.gem_scope_base'));
    shb_buttons_set($items, '> * > button.shb', 'deep');
    shb_buttons_set($atoms, '> * > button.shb', 'enable');

    var query = '';
    if (atom_name && atom_name != "") {
        var urlParams = new URLSearchParams();
        urlParams.set('atom', atom_name);

        query = '?' + urlParams.toString()
    }
    $('a[name="atom-search-link"]').attr('href',
                                         window.location.protocol + '//' + window.location.host + window.location.pathname +
                                         query);
    $('a[name="atom-search-link"]').css('display', 'inline-block');
    $('input[name="atom"]').val(atom_name);
}

function hexToRGB(hex) {
    let r = parseInt(hex.substring(1,3), 16);
    let g = parseInt(hex.substring(3,5), 16);
    let b = parseInt(hex.substring(5), 16);
    return "(" + r + ", " + g + ", " + b + ")";
}

function test_main()
{
    for (var i = 0 ; i < 20 ; i++) {
        var hex = hs2rgb({h: color_hs['h'], s: color_hs['s'] + color_delta * parseFloat(i)});
        console.log(i + ') s: ' + (color_hs['s'] + color_delta * parseFloat(i)).toFixed(4) + ' hex: ' + hex + ' dec: ' + hexToRGB(hex));
    }
}

function atomsgroup_render(scope, $anc, id_pfx, atomsgroup, atoms_not_included, is_deep, depth, color_hs)
{
    var newcol_hs = {h: color_hs['h'], s: color_hs['s'] + color_delta};

    // console.log('atoms_not_included: ' + atoms_not_included);

    if (atoms_not_included !== null && atoms_not_included.length > 0) {
        for (var i = 0 ; i < atoms_not_included.length ; i++) {
            if (atomsgroup['atoms'].indexOf(atoms_not_included[i]) != -1) {
                atomsgroup = filtered_atomsgroup_filter(atomsgroup['name'], atoms_not_included)
                break;
            }
        }
    }

    $anc.append(
            $('<h5/>').text(atomsgroup['title']).append(
                showhide_button(depth)));

    // console.log('atomsgroup["title"]: ' + atomsgroup['title']);
    // console.log('DEPTH: ' + depth);
    var atoms_list = atomsgroup['atoms'];
    for (var atom_id in atoms_list) {
        var atom = gem_tax['atom'][atoms_list[atom_id]];
        var $atom_title = $('<h5/>').addClass('gem_atom').text('[' + atom['name'] + '] ' + atom['title']
                                                              ).append(showhide_button(depth));
        if (atom['desc'] != '' || atom['args'] || atom['params']) {
            $atom_title.append(info_button(depth));
        }
        var $atom = $('<div/>').attr('name', atom['name']).addClass(
            'gem_hideable').addClass('gem_scope_' + scope).css(
                    {backgroundColor: hs2rgb(newcol_hs),
                     borderLeft: "3px solid " + hs2satrgb(newcol_hs),
                     borderBottom: "1px solid " + hs2satrgb(newcol_hs),
                     margin: '4px 0px 4px 0px',
                     padding: '4px',
                     paddingLeft: '16px',
                     display: (depth == 0 ? 'none' : 'block')
                    });
        $atom.append($atom_title);
        var sub_id_pfx = id_pfx + '__' + atomsgroup['name'];
        $anc.append($atom);
        add_leafs(scope, sub_id_pfx, $atom, atom, depth, newcol_hs);
    }
}

function params_options_render(scope, $anc, id_pfx, atom) // atomsgroup, atoms_not_included, is_deep, depth, color_hs)
{
    var newcol_hs = {h: color_hs['h'], s: color_hs['s'] + color_delta};

    // console.log('atoms_not_included: ' + atoms_not_included);

    // console.log('atomsgroup["title"]: ' + atomsgroup['title']);
    // console.log('DEPTH: ' + depth);
    var options = gem_tax['param'][atom['name']].slice();
    options.sort(function (a, b) {
        return a['prog'] - b['prog'];
    });

    options.unshift({name: '', prog: 0, title: 'Unknown Type'});
    for (var option_id in options) {
        var option = options[option_id];
        var option_name = (option['name'] == '' ? '' : ':') + option['name'];
        var $option = $('<div/>').attr('name', option_name).addClass('gem_scope_' + scope).append($('<h5/>').html(
                '[<span style="color: grey;">' + atom['name'] + '</span>' + option_name + '] ' +atom['title'] + ': ' + option['title']));
        $anc.append($option);
    }
}

function attribute_render(scope, attribute, id_pfx, depth, color_hs)
{
    var depth_child = depth > 0 ? depth - 1 : depth;
    var color_atomsgroup_hs = {h: color_hs['h'], s: color_hs['s'] + color_delta};

    var atoms_not_included = ('atoms_not_included' in attribute ? attribute['atoms_not_included'] : null);

    var attribute_title = attribute['title'] + (atoms_not_included === null ? '' : ' (filtered)')
    // console.log('title: ' + attribute_title + '  depth: ' + depth + ' depth_child: ' + depth_child);
    var $attribute = $('<div/>').attr('id', attribute['name']).append(
        $('<h4/>').text(attribute_title).append(showhide_button(depth_child))).css(
            {backgroundColor: hs2rgb(color_hs),
             borderLeft: "3px solid " + hs2satrgb(color_hs),
             borderBottom: "1px solid " + hs2satrgb(color_hs),
             padding: '4px',
             paddingLeft: '16px'
            });
    if (scope == 'atom') {
        $attribute.addClass('gem_scope_base');
    }
    for (var a in attribute['atomsgroups']) {
        var atomsgroup = gem_tax['atomsgroup'][attribute['atomsgroups'][a]];

        if (atomsgroup['is_persistent'] == true) {
            // console.log("OUT atomsgroup_place_render: depth = " + depth);
            var $atomsgroup_place = atomsgroup_place_render(scope, color_atomsgroup_hs, depth, attribute['name']);
            $attribute.append($atomsgroup_place);
            atomsgroup_render(scope, $atomsgroup_place, attribute['name'], atomsgroup,
                              atoms_not_included, true, depth, color_atomsgroup_hs);
        }
    }
    return $attribute;
}

function taxtgraph_main() {
    // return test_main();
    var depth = -1;

    // console.log(gem_tax);
    attributes = gem_tax['attribute'];

    attributes_arr = Object.entries(attributes)
    attributes_arr.sort(function (a,b) {
        return a[1]['prog'] - b[1]['prog'];
    });

    for (var e = 0 ; e < attributes_arr.length ; e++) {
        attribute = attributes_arr[e][1];
        var $attribute = attribute_render('atom', attribute, '', depth, color_hs);
        $('#app').append($attribute);
    }
    // remove buttons for elements without children
    $('body').find('button.shb').each(function rm_button() {
        var $this = $(this);
        if ($this.parent().parent().find('div.gem_hideable').length == 0) {
            $this.remove();
        }
    });

    $('body').find('button.shb').each(function add3state() {
        var $this = $(this);
        if ($this.parent().parent().find('div.gem_hideable button.shb').length > 0) {
            $(this).addClass('shb_3state');
        }
    });
}
