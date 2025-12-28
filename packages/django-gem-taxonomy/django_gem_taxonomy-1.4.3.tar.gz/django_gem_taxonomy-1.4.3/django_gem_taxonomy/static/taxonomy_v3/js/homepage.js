function validate_string(obj)
{
    tax_in = $($(obj).find('input[name="validate_input"]')[0]).val();
    $.ajax({
        url: "api/v1/validation/" + tax_in
    }).done(function(data) {
        $('div[name="validate_output"]').css('display', '');
        $('div[name="validate_output"]').empty();
        if (data['success'] == true && data['is_canonical'] == true) {
            $('div[name="validate_output"]').append('<p style="font-weight: bold;">Result: <span style="color: green;">&#x2B24;</span></p><p>Input: ' + tax_in + '</p><p>Validation: Success</p><p>Canonical Form: True</p>');
        }
        else if (data['success'] == true && data['is_canonical'] == false) {
            $('div[name="validate_output"]').append('<p style="font-weight: bold;">Result: <span style="color: orange;">&#x2B24;</span></p><p>Input: ' + tax_in + '</p><p>Validation: Success</p><p>Is Canonical: False</p><p>Canonical form: ' + data['canonical']);
        }
    }).fail(function(data) {
        $('div[name="validate_output"]').css('display', '');
        $('div[name="validate_output"]').empty();
        $('div[name="validate_output"]').append('<p style="font-weight: bold;">Result: <span style="color: red;">&#x2B24;</span></p><p>Input: ' + tax_in + '</p><p>Validation: Failed</p><p>Message: ' + data.responseJSON['message'] + '</p>');
    })
}

function explain_string(obj)
{
    var tax_in = $($(obj).find('input[name="explain_input"]')[0]).val();
    // var format_in = $($(obj).find('input[name="fmt"]:checked')[0]).val();
    var format_in = 'textmultiline';
    $.ajax({
        url: "api/v1/explanation/" + tax_in,
        data: {fmt:format_in},
    }).done(function(data) {
        $('div[name="explain_output"]').css('display', '');
        $('div[name="explain_output"]').empty();

        var tralight_col = 'green';
        if (data['success'] == true) {
            if (format_in == 'json') {
                var ppout = JSON.stringify(JSON.parse(data['explanation']),null,4);
            }
            else {
                var ppout = data['explanation'];
                if (!data['is_canonical']) {
                    tralight_col = 'orange';
                }
            }
            var n_lines = ppout.split(/\r\n|\r|\n/).length;
            var $rep = $('div[name="explain_output"]');
            $rep.append('<p style="font-weight: bold; margin-left: 16px; margin-top: 8px;"><span style="color: green;">&check;</span> Correct taxonomy string.</p>');
            if (data['is_canonical']) {
                $rep.append('<p style="font-weight: bold; margin-left: 16px;"><span style="color: green;">&check;</span> Canonical order.</p>');
            }
            else {
                $rep.append('<p style="font-weight: bold; margin-left: 16px;"><span style="color: orange;">&cross;</span> Not canonical order, that is: <span style="background-color: white; color: black; padding: 4px;">' + data['canonical'] + '</span></p>');
            }

            $rep.append($('<textarea style="font-size: 18px; padding: 8px; resize: none; width: 90%; margin: 8px 5% 16px 5%;"  rows="' + n_lines + '"/>').val(ppout));
        }
    }).fail(function(jqXHR) {
        data = JSON.parse(jqXHR.responseText);
        $('div[name="explain_output"]').css('display', '');
        $('div[name="explain_output"]').empty();
        $rep = $('div[name="explain_output"]');
        $rep.append('<p style="font-weight: bold; margin-left: 16px; margin-top: 8px;"><span style="color: red;">&cross;</span> Not correct taxonomy string.</p>');
        $rep.append('<textarea style="font-size: 18px; /* padding: 8px; */ resize: none; width: 90%; margin: 8px 5% 16px 5%;" rows="' + 8 + '">' + data['message'] + '</textarea>');
    })
}

function reset_subareas()
{
    $("div.accordion").css('display', 'none');
    $("div[name='validate_output']").css('display', 'none');
    $("div[name='validate_output']").empty();
    $("input[name='validate_input']").val('');

    $("div[name='explain_output']").css('display','none');
    $("div[name='explain_output']").empty();
    $("input[name='explain_input']").val('');

}

function manage_hp_accordion(item_name, fire_reload)
{
    var cur_disp = $('div.acc_' + item_name).css('display');

    reset_subareas();
    if (cur_disp == 'none') {
        $('div.acc_' + item_name).css('display', 'initial');
    }
    else {
        $('div.acc_' + item_name).css('display', 'none');
    }

    if (fire_reload)
        return true;
    else {
        event.preventDefault();
        return false;
    }
}

window.addEventListener('load', function () {
    var hash = window.location.hash.slice(1);

    var valid_hashes = ['orm', 'ser', 'pkg'];
    if (valid_hashes.indexOf(hash) > -1) {
        reset_subareas()
        $('div.acc_' + hash).css('display', 'initial');
        }
    }
);
