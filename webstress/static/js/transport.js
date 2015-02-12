// import Nevow.Athena

Transport.Dispatch = Nevow.Athena.Widget.subclass('Transport.Dispatch');

Transport.Dispatch.methods(
    function result(self, argument) {
        update(argument[0]);
        return argument;
    },
    function all_results(self, argument) {
        init_results();
        for (var i=0; i++; i < argument[0].length) {
            update(argument[0][i]);
        }
        return argument;
    }
    );

Transport.Dispatch.method(
    'clicked',
    function(self) {
        self.callRemote('receive',
            JSON.stringify({
                method: 'launch_test',
                args: [],
                kwargs: {targets: ["target_from_config_file"]}
            }));
    });

var results = {};

var init_results = function () {
    results.count = 0;
    results.total_duration = 0;
    results.average_duration = 0;
    results.status_codes = {};
};

init_results();

var update = function (result) {
    results.total_duration += parseFloat(result.duration);
    results.count++;
    results.average_duration = results.total_duration / results.count;
    results.status_codes[result.status_code] = (results.status_codes[result.status_code] || 0) + 1

    var status_html = "";
    for (var key in results.status_codes) {
        if (!results.status_codes.hasOwnProperty(key)) continue;
        status_html += "<div>" + key + ": " + results.status_codes[key] + "</div>";
    }

    var average_html = "<div>Average duration: " + results.average_duration + "</div>";
    if (results.count % 10 === 0) {
        my_div.innerHTML = average_html + status_html;
    }
};

var my_div = document.createElement('div');
my_div.style.fontSize = "24px";
my_div.style.border = "4px solid #999";
my_div.style.color = "#383";
my_div.style.padding = "20px";
document.body.appendChild(my_div);
