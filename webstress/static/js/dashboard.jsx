if (typeof window.WS === 'undefined') window.WS = {};

(function () {
    var $content,
        config_grid,
        ConfigGrid = React.createClass({
            getInitialState: function () {
                return {data: []};
            },
            render: function () {
                var configs = this.state.data.map(function (config) {
                    return (<Config data={config} />);
                });
                return (<div>{configs}</div>);
            }
        }),
        Config = React.createClass({
            getInitialState: function () {
                return {state: WS.INACTIVE, results: [], stats: null};
            },
            render: function () {
                var data = this.props.data,
                    targets = data.targets.map(function (target) {
                        return (<Target data={target} />);
                    }),
                    response_codes,
                    state, tps, duration_stats;
                WS.targets[data.name] = {};

                response_codes = (
                    <ResponseCodes data={this.state.results} />
                );

                switch (this.state.state) {
                    case WS.COMPLETE:
                        state = (<span className="state complete">Complete</span>);
                        break;
                    case WS.PENDING:
                        state = (<span className="state pending">Pending</span>);
                        break;
                    case WS.WAITING:
                        state = (<span className="state waiting">Waiting</span>);
                        break;
                    case WS.INACTIVE:
                        state = (<span className="state inactive">Inactive</span>);
                        break;
                }

                if (data.tps) {
                    tps = (<div className="tps"><h2>TPS Throttle:</h2>{data.tps}</div>);
                } else {
                    tps = '';
                }

                if (this.state.stats) {
                    duration_stats = (
                        <DurationStats data={this.state.stats} />
                        );
                } else {
                    duration_stats = '';
                }

                return (
                    <div className="config grid-item">
                      <table className="test-info">
                      <tbody>
                      <tr>
                        <td><h1 className="config-name">{data.name}</h1></td>
                        <td><div>{state}</div></td>
                        <td><button className="run-button"
                                 onClick={this.run_test}>Run Test</button></td>
                        <td>{tps}</td>
                      </tr>
                      </tbody>
                      </table>
                      <div className="report">
                        {response_codes}
                        {duration_stats}
                      </div>
                      <div ref="chart"></div>
                      <a href="#" ref="targets_link" onClick={this.toggle_targets} className="targets">
                         <span ref="collapse" className="icon hidden">[-]</span>
                         <span ref="expand" className="icon">[+]</span>
                         <span className="wording">Targets ({targets.length})</span></a>

                      <div ref="targets" className="targets">
                        {targets}
                      </div>
                    </div>
                );
            },
            componentDidMount: function () {
                $content.do_layout();
            },
            componentDidUpdate: function (props, state) {
                $content.do_layout();
                if (state.stats && state.stats["200"]) {
                    this._points = state.stats["200"].chart_points;
                } else {
                    this._points = [];
                }
            },
            reset: function () {
                this.setState(this.getInitialState());
                this._points = [];

                WS.init_chart(this.refs.chart.getDOMNode(), this.get_points);
            },
            toggle_targets: function () {
                $(this.refs.collapse.getDOMNode()).toggleClass("hidden");
                $(this.refs.expand.getDOMNode()).toggleClass("hidden");
                $(this.refs.targets.getDOMNode()).toggle("fast");
                $(this.refs.targets_link.getDOMNode()).toggleClass("active");
            },
            get_points: function () {
                return this._points;
            },
            run_test: function () {
                var data = this.props.data,
                    config_uid = WS.get_uid(),
                    target_uid,
                    key, targets = [],
                    that;

                this.reset();

                WS.active_tests[config_uid] = {config: this};

                for (key in WS.targets[data.name]) {
                    if (!WS.targets[data.name].hasOwnProperty(key)) continue;
                    target_uid = WS.get_uid();
                    target = WS.targets[data.name][key];
                    targets.push({
                        "name": target.props.data.name,
                        "uid": target_uid
                    });
                    target.reset();
                    WS.active_tests[config_uid][target_uid] = {target: target};
                    this.setState({state: WS.WAITING});
                }

                WS.call_remote("launch_test",
                    {kwargs: {uid: config_uid,
                              config_name: data.name,
                              requested_targets: targets}
                });
            },
        }),
        Target = React.createClass({
            getInitialState: function () {
                return {results: [], stats: null};
            },
            render: function () {
                var data = this.props.data,
                    params = (
                        <Params data={this.props.data.params} />
                    ),
                    response_codes = (
                            <ResponseCodes data={this.state.results} />
                    ),
                    that = this,
                    duration_stats;

                // Make this target accessible elsewhere
                WS.targets[data.owner][data.name] = this;

                if (this.state.stats) {
                    duration_stats = (
                        <DurationStats data={this.state.stats} />
                        );
                } else {
                    duration_stats = '';
                }
                return (
                    <div className="target">
                      <table className="target">
                      <tbody>
                      <tr>
                        <td><h2>Name</h2></td>
                        <td>{data.name}</td>
                      </tr>
                      <tr>
                        <td><h2>Hits</h2></td>
                        <td>{data.hits}</td>
                      </tr>
                      <tr>
                        <td><h2>URL</h2></td>
                        <td><a href={data.base_url}>{data.base_url}</a></td>
                      </tr>
                      <tr>
                        <td><h2>Params</h2></td>
                        <td>{params}</td>
                      </tr>
                      </tbody>
                      </table>
                      {response_codes}
                      {duration_stats}
                    </div>
                );
            },
            reset: function () {
                this.setState(this.getInitialState());
            },
            componentDidUpdate: function () {
                $content.do_layout();
            }

        }),
        Params = React.createClass({
            render: function () {
                var params = this.props.data.map(function (param) {
                        return (
                            <tr>
                              <td className="name">{param.key}</td>
                              <td>{param.value}</td>
                            </tr>
                        );
                    });

                return (
                    <table className="params">
                        <thead>
                            <th>Name</th>
                            <th>Value</th>
                        </thead>
                        <tbody>
                          {params}
                        </tbody>
                    </table>
                );
            }
        }),
        ResponseCodes = React.createClass({
            render: function () {
                var data = this.props.data,
                    i, code, codes = {},
                    results = [], table = [],
                    head = [], row = [], cls;

                for (i = 0; i < data.length; i ++) {
                    if (!data[i].success && data[i].status_code == null) {
                        code = 'Failed';
                    } else {
                        code = data[i].status_code;
                    }
                    codes[code] = (codes[code] || 0) + 1;
                }
                for (code in codes) {
                    if (!codes.hasOwnProperty(code)) continue;
                    results.push([code, codes[code]]);
                }
                results.sort();
                for (i = 0; i < results.length; i ++) {
                    cls = WS.util.status_code_class(results[i][0]);
                    head.push(<th className={cls}>{results[i][0]}</th>);
                    row.push(<td>{results[i][1]}</td>);
                }

                if (!results.length) {
                    return (<div></div>);
                } else {
                    return (
                    <div>
                        <table className="results">
                            <thead>
                                <tr>{head}</tr>
                            </thead>
                            <tbody>
                                <tr>{row}</tr>
                            </tbody>
                        </table>
                    </div>
                    );
                }
            }
        }),
        DurationStats = React.createClass({
            render: function () {
                var data = this.props.data,
                    keys = _.keys(data),
                    that = this,
                    rows, histogram;
                if (_.isEmpty(data)) {
                    return "";
                }

                keys.sort();
                rows = _.map(keys, function (key) {
                    var peak = data[key].peak,
                        nadir = data[key].nadir,
                        mean = data[key].mean,
                        median = data[key].median,
                        percentiles = data[key].percentiles,
                        std_deviation = data[key].std_deviation
                    return (
                        <tr>
                          <td className={WS.util.status_code_class(key)}>{key}</td>
                          <td className={WS.util.severity(peak)}>{WS.util.format(peak, 2)}</td>
                          <td className={WS.util.severity(nadir)}>{WS.util.format(nadir, 2)}</td>
                          <td className={WS.util.severity(mean)}>{WS.util.format(mean, 2)}</td>
                          <td className={WS.util.severity(median)}>{WS.util.format(median, 2)}</td>
                        </tr>
                    );
                }, this);

                if (data["200"]) {
                    histogram = (
                        <Histogram data={data["200"].histogram} />
                    );
                } else {
                    histogram = '';
                }
                return (
                    <div>
                    <table className="duration-stats">
                    <thead>
                        <th className="blank"></th>
                        <th>Peak</th>
                        <th>Nadir</th>
                        <th>Mean</th>
                        <th>Median</th>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                    </table>
                    {histogram}
                    </div>
                );
            }
        }),
        Histogram = React.createClass({
            render: function () {
                var data = this.props.data,
                    head = _.map(_.rest(data.edges), function (right_edge, i) {
                        var left_edge = data.edges[i];
                        return (
                            <th className="divide-right">
                              {WS.util.format(left_edge, 2)}
                              <span className="arrows">&harr;</span>
                              {WS.util.format(right_edge, 2)}
                            </th>
                        );
                    }, this),
                    row = _.map(data.histogram, function (value) {
                        return (
                            <td>{value}</td>
                        );
                    }, this);

                return (
                    <table className="duration-stats histogram">
                      <thead>
                        <tr>
                          <th className="blank bold">Seconds</th>
                          {head}
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className={WS.util.status_code_class("200")}>Success</td>
                          {row}
                        </tr>
                      </tbody>
                    </table>
                );
            }
        });


    $content = $('<div class="grid"></div>');

    config_grid = React.render(
        <ConfigGrid />,
        $content.get(0)
    );

    WS.config_grid = config_grid;

    $content.appendTo(document.body);

    $content.do_layout = function () {
        $content.masonry({
            itemSelector: ".grid-item",
            columnWidth: 90,
            gutter: 10
        });
    };
})();
