

$('#button').on('click', async function (event) {
    console.log("buttonpress");
    addHidden();
    event.preventDefault();
    await searchEvent();
    addCollapse();
    console.log('search done')

    //Changes text to visible
    setTimeout(removeHidden, 1999);
});

function removeHidden() {
    $("#event-type-desc").removeClass("hidden");
}

function addHidden() {
    $("#event-type-desc").addClass("hidden");
}


async function searchEvent() {
    const eventData = await getData("/api/locateEvents");
    console.log(eventData);

    let data = accessData(eventData);
    console.log(data == null);
    if (data == null || data == '' || data.length == 0) {
        let quip = ['In terms of classes, we have no classes', 'There\'s nothing for miles', 'Time to chillax...'];
        quip = quip[Math.floor(Math.random() * quip.length)];

        text = "Adjust your timeframe or try again later";
        data = `<h3>No lectures found!</h3><p>${text}</p><p style="font-style: italic; text-align:center;">${quip}</p>`;
    }
    document.getElementById("event-type-desc").innerHTML = `
    <h1 class="app-title">Events</h1>
    ${data}
    `
}

function accessData(database) {
    let results = "";
    for (let eventType of Object.entries(database)) {
        let datachanged = false;
        let block_results = `
            <div>
            <div style="min-height:30px"> </div>
            <div class="collapse show" id="collapse_${eventType[0]}">
        `
        for (let event of Object.entries(eventType[1])) {
            // console.log(event[1]);
            block_results += printData(event[1]);
            datachanged = true;
        }

        block_results += `
            </div>
            </div>
            
        `

        // Only change results if there are actually values in it
        if (datachanged) results += block_results
    }
    return results
}

async function getData(url) {
    const btn = $('#button');
    const btnText = btn.textContent;
    btn.innerHTML = "<i class=\"fa fa-spinner fa-spin\"></i>" + btnText;

    const timespan = times[getClosest(times, $('#timeRange').val())];
    const response = await fetch(url + `?span=${timespan}`);

    btn.innerHTML = btnText;
    return response.json();
}


//Convert UTC seconds to local time 12-hour clock
function convertTime(time) {
    return time;
}

function printData(event) {

    let S_time = new Date(event.start_time * 1000); //- 1800000);
    let E_time = new Date(event.end_time * 1000);

    let am_pm = ['', 'am']
    if (S_time.getHours() >= 12 && E_time.getHours() >= 12) {
        am_pm[1] = 'pm';
        S_time.setHours(S_time.getHours() - 12);
    }
    else if (S_time.getHours() < 12 && E_time.getHours() < 12) {
        am_pm[1] = 'am';
        S_time.setHours(S_time.getHours() - 12);
    }
    else if (E_time.getHours() >= 12) {
        am_pm[0] = 'am'
    }

    let S_mins = S_time.getMinutes();
    if (S_mins < 10) { S_mins = '0' + S_mins }

    let E_mins = E_time.getMinutes();
    if (E_mins < 10) { E_mins = '0' + E_mins }

    return `\n\n
        <div class="event">
            <div style="min-height:30px"> </div>
            <div class="row">
                <div class="w-100"></div>
                <div class="col-xxl-9 offset-xxl-5">
                    <p style="font-weight: bold;font-size: 20px;">${event.name}</p>
                </div>
                <div class="col" style="width: 150px;min-width: 0;">
                    <p style="text-align: right;"><i class="fa fa-calendar-o" aria-hidden="true"></i>
                    ${S_time.getMonth() + 1}/${S_time.getDate()}</p>
                </div>
            </div>
            <p style="padding-left: 1rem;">${event.description}</p>
            <div class="row">
                <div class="col">
                    <p><i class="fa fa-map-marker" aria-hidden="true"></i>
                    <strong>${event.location}</strong></p>
                </div>
                <div class="col">
                    <p><i class="fa fa-clock-o" aria-hidden="true"></i>
                    ${S_time.getHours() % 12}:${S_mins}${am_pm[0]} - ${E_time.getHours() % 12}:${E_mins}${am_pm[1]}</p>
                </div>
            </div>
        </div>\n\n`
}

function addCollapse() {
    $('.collapsor').on('click', async function (event) {
        // find the neightboring div and toggle it
        console.log("collapse time");
        console.log(event)
        let neighbor = $(this).next()
        if ($(neighbor).is(":hidden")) {
            $(neighbor).slideDown("slow");
        }
        else {
            $(neighbor).slideUp("slow");
        }
    });
}


