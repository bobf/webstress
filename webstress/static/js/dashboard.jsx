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
                return {state: WS.INACTIVE, stats: {__all__: null}};
            },
            render: function () {
                var data = this.props.data,
                    targets = data.targets.map(function (target) {
                        return (<Target data={target} />);
                    }),
                    response_codes,
                    state, tps, duration_stats, run_time_stats;
                WS.targets[data.name] = {};

                response_codes = (
                    <ResponseCodes data={this.state.stats.__all__} />
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
                    tps = (<div className="tps"><h2 className="nowrap">TPS Throttle: </h2>{data.tps}</div>);
                } else {
                    tps = '';
                }

                if (this.state.stats.__all__) {
                    run_time_stats = (
                        <div>
                          <table className="run-times">
                            <tbody>
                              <tr>
                                <td className="start-time nowrap">{this.state.stats.__all__.__all__.start_time}</td>
                              </tr>
                              <tr>
                                <td className="run-time nowrap">Run time: {this.state.stats.__all__.__all__.run_time}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                    );
                    duration_stats = (
                        <DurationStats data={this.state.stats.__all__} />
                        );
                } else {
                    duration_stats = '';
                    run_time_stats = '';
                }

                return (
                    <div className="config grid-item">
                      <table className="test-info">
                      <tbody>
                      <tr>
                        <td><h1 className="config-name">{data.name}</h1></td>
                        <td><div>{state}</div></td>
                        <td><button className="run-button nowrap"
                                 onClick={this.run_test}>Run Test</button></td>
                        <td>{tps}</td>
                        <td>{run_time_stats}</td>
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
                this.reset();
                $content.do_layout();
            },
            componentDidUpdate: function (props, state) {
                var name = this.props.data.name,
                    targets = WS.targets[name],
                    key;
                for (key in targets) {
                    if (!targets.hasOwnProperty(key)) continue;

                    targets[key].setState({stats: this.state.stats[key]});
                }
                $content.do_layout();
            },
            reset: function () {
                this.setState(this.getInitialState());
                WS.active_tests[this.props.data.uid] = {config: this};

                WS.init_chart(this.refs.chart.getDOMNode(), this.get_points);
            },
            toggle_targets: function () {
                $(this.refs.collapse.getDOMNode()).toggleClass("hidden");
                $(this.refs.expand.getDOMNode()).toggleClass("hidden");
                $(this.refs.targets.getDOMNode()).toggle("fast");
                $(this.refs.targets_link.getDOMNode()).toggleClass("active");
            },
            get_points: function () {
                if (this.state.stats && this.state.stats.__all__ && this.state.stats.__all__["200"]) {
                    return this.state.stats.__all__["200"].chart_points;
                } else {
                    return [];
                }
            },
            run_test: function () {
                var data = this.props.data,
                    target,
                    key, targets = [],
                    that;

                this.reset();

                for (key in WS.targets[data.name]) {
                    if (!WS.targets[data.name].hasOwnProperty(key)) continue;
                    target = WS.targets[data.name][key];
                    targets.push({
                        "name": target.props.data.name,
                        "uid": target.props.data.uid
                    });
                    target.reset();
                    WS.active_tests[data.uid][target.props.uid] = {target: target};
                    this.setState({state: WS.WAITING});
                }

                WS.call_remote("launch_test",
                    {kwargs: {uid: data.uid,
                              config_name: data.name,
                              requested_targets: targets}
                });
            },
        }),
        Target = React.createClass({
            getInitialState: function () {
                return {stats: null};
            },
            render: function () {
                var data = this.props.data,
                    params = (
                        <Params data={this.props.data.params} />
                    ),
                    response_codes = (
                            <ResponseCodes data={this.state.stats} />
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
                var i, code, codes = {},
                    results = [], table = [],
                    head = [], row = [],
                    empty = (<div></div>),
                    cls, data;

                if (!this.props.data) {
                    return empty;
                }

                data = this.props.data;

                for (code in data) {
                    if (!data.hasOwnProperty(code)) continue;
                    results.push([code, data[code].count]);
                }
                results.sort();
                for (i = 0; i < results.length; i ++) {
                    if (results[i][0] === '__all__') {
                        continue;
                    }
                    cls = WS.util.status_code_class(results[i][0]);
                    head.push(<th className={cls}>{results[i][0]}</th>);
                    row.push(<td>{results[i][1]}</td>);
                }

                if (!results.length) {
                    return empty;
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
                    keys = _.chain(data).keys().without('__all__').value(),
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
                        std_deviation = data[key].std_deviation,
                        mean_tps;
                    if (data[key].chart_points) {
                        mean_tps = data[key].chart_points.tps.mean;
                    } else {
                        mean_tps = null;
                    }
                    return (
                        <tr>
                          <td className={WS.util.status_code_class(key)}>{key}</td>
                          <td className={WS.util.severity(peak)}>{WS.util.format(peak, 2)}</td>
                          <td className={WS.util.severity(nadir)}>{WS.util.format(nadir, 2)}</td>
                          <td className={WS.util.severity(mean)}>{WS.util.format(mean, 2)}</td>
                          <td className={WS.util.severity(median)}>{WS.util.format(median, 2)}</td>
                          <td>{WS.util.format(mean_tps, 2)}</td>
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
                        <th className="nowrap">Mean TPS</th>
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
