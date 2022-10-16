
function nice_time(time_in_seconds) {
    // Convert integer time to
    // days, hours:minutes display
    let time = time_in_seconds;

    let days = Math.floor(time / 86400);

    time = time % 86400;

    let hours = Math.floor(time / 3600);
    time = time % 3600;

    let minutes = Math.floor(time / 60);
    time = time % 60;

    let time_str = '';
    if (days > 1) { time_str += `${days} days ` }
    else if (days == 1) { time_str += `day ` }

    if (hours > 0 && minutes > 0) {
        if (minutes < 10) { minutes = '0' + minutes }
        time_str += `${hours}:${minutes} `
    } else if (hours > 1) {
        time_str += `${hours} hours `
    }
    else if (hours == 1) {
        if (days == 1) time_str += `and an hour `
        else time_str += `hour `
    }
    else if (days == 0) {
        time_str += `${minutes} minutes `
    }

    return time_str.trim();
}

/*
<label for="timeRange">Classes in the next <span id="rangeval">2 hours</span></label>
<input type="range" class="form-control-range" id="timeRange"
    min="0" max="100" step="1" value="10">
*/

const times = {
    0: 1800,
    10: 3600,
    20: 2 * 3600,
    30: 3 * 3600,
    60: 12 * 3600,
    70: 24 * 3600,
    80: 2 * 24 * 3600,
    90: 3 * 24 * 3600,
    100: 7 * 24 * 3600
}

// Gets the closest key from the table above
function getClosest(table, val) {
    let closest = Object.keys(table)[0];
    for (const [key, value] of Object.entries(table))
        if (Math.abs(key - val) < Math.abs(closest - val))
            closest = key;
    return closest;
}

// Interpolate between two values in the table above
function interpolate(table, val) {
    let closest = Object.keys(table)[0];
    let second_closest = Object.keys(table)[1];
    for (const [key, value] of Object.entries(table))
        if (Math.abs(key - val) < Math.abs(closest - val))
            closest = key;
    for (const [key, value] of Object.entries(table))
        if (key != closest && Math.abs(key - val) < Math.abs(second_closest - val))
            second_closest = key;

    let lower = Math.min(closest, second_closest);
    let upper = Math.max(closest, second_closest);
    let ratio = (val - lower) / (upper - lower);
    return table[lower] + ratio * (table[upper] - table[lower]);
}

$("#timeRange").on("change", function () {
    let closest = getClosest(times, $(this).val());
    $(this).val(closest);
    $('#rangeval').html(nice_time(times[closest]))
});

$("#timeRange").on("input", function () {
    //let val = Math.floor(interpolate(times, $(this).val()));
    let val = getClosest(times, $(this).val());
    $('#rangeval').html(nice_time(times[val]))
});

// Run once on page load
$("#timeRange").trigger("input");