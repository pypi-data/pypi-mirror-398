/**
 * Converts an HSV color value to RGB. Conversion formula
 * adapted from http://en.wikipedia.org/wiki/HSV_color_space.
 * Assumes h, s, and v are contained in the set [0, 1] and
 * returns r, g, and b in the set [0, 255].
 *
 * @param   Number  h       The hue
 * @param   Number  s       The saturation
 * @param   Number  v       The value
 * @return  Array           The RGB representation
 */
function hsv2rgb(h, s, v){
    var r, g, b;

    h = (h < 0.0 ? 0.0 : (h > 1.0 ? 1.0 : h));
    s = (s < 0.0 ? 0.0 : (s > 1.0 ? 1.0 : s));
    v = (v < 0.0 ? 0.0 : (v > 1.0 ? 1.0 : v));

    var i = Math.floor(h * 6);
    var f = h * 6 - i;
    var p = v * (1 - s);
    var q = v * (1 - f * s);
    var t = v * (1 - (1 - f) * s);

    switch(i % 6){
        case 0: r = v, g = t, b = p; break;
        case 1: r = q, g = v, b = p; break;
        case 2: r = p, g = v, b = t; break;
        case 3: r = p, g = q, b = v; break;
        case 4: r = t, g = p, b = v; break;
        case 5: r = v, g = p, b = q; break;
    }

    // return [r * 255, g * 255, b * 255];
    return ("#" +
            ("00" + Math.round(r * 255).toString(16)).slice(-2) +
            ("00" + Math.round(g * 255).toString(16)).slice(-2) +
            ("00" + Math.round(b * 255).toString(16)).slice(-2));
}

