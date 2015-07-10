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
                return {
                        state: WS.INACTIVE,
                        stats: {
                            response_times: [
                                {name: '__all__', results: []}]
                        }
                };
            },
            get_my_stats: function () {
                var data = _(
                    this.state.stats.response_times
                    ).where({name: "__all__"});
                return data.length ? data[0].results : null;
            },
            get_all_codes_stats: function () {
                var my_stats = this.get_my_stats(),
                    data;
                if (my_stats) {
                    data = _(my_stats).where({code: "__all__"});
                    return data.length ? data[0] : null;
                }
            },
            render: function () {
                var data = this.props.data,
                    targets = data.targets.map(function (target) {
                        return (<Target data={target} />);
                    }),
                    response_codes,
                    state, tps, duration_stats, run_time_stats, run_or_stop,
                    total_content_length,
                    my_stats = this.get_my_stats(),
                    all_codes_stats = this.get_all_codes_stats();
                WS.targets[data.name] = {};


                response_codes = (
                    <ResponseCodes data={my_stats} />
                );

                switch (this.state.state) {
                    case WS.COMPLETE:
                        state = (<span className="animated pulse state complete">Complete</span>);
                        break;
                    case WS.PENDING:
                        state = (<span className="animated flash infinite state pending">Pending</span>);
                        break;
                    case WS.WAITING:
                        state = (<span className="state waiting">Waiting</span>);
                        break;
                    case WS.INACTIVE:
                        state = (<span className="state inactive">Inactive</span>);
                        break;
                    case WS.STOPPED:
                        state = (<span className="state stopped">Stopped</span>);
                        break;
                }

                if (data.tps) {
                    tps = (<div className="tps"><h2 className="nowrap">TPS Throttle: </h2>{data.tps}</div>);
                } else {
                    tps = null;
                }

                if (my_stats.length) {
                    run_time_stats = (
                        <div>
                          <table className="run-times">
                            <thead>
                              <tr>
                                <th>Start Time</th>
                                <th>Run Time</th>
                                <th>Data Received</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr>
                                <td className="start-time nowrap">{this.state.stats.start_time}</td>
                                <td className="run-time nowrap">{this.state.stats.run_time}</td>
                                <td className="content-length nowrap">{WS.util.format_bytes(all_codes_stats.total_content_length)}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                    );
                    duration_stats = (
                        <DurationStats data={my_stats} />
                        );
                } else {
                    duration_stats = null;
                    run_time_stats = null;
                }
                if (!this.is_running()) {
                    run_or_stop = (
                        <button className="run-button nowrap" onClick={this.run_test}>Run Test</button>
                    );
                } else {
                    run_or_stop = (
                        <button className="stop-button nowrap" onClick={this.stop_test}>Stop Test</button>
                    );
                }
                return (
                    <div className="config grid-item">
                      <table className="test-info">
                      <tbody>
                      <tr>
                        <td><h1 className="config-name">{data.name}</h1></td>
                        <td><div>{state}</div></td>
                        <td>{run_or_stop}</td>
                        <td>{tps}</td>
                      </tr>
                      </tbody>
                      </table>
                      {run_time_stats}
                      <div className="report">
                        {total_content_length}
                        {response_codes}
                        {duration_stats}
                      </div>
                      <div className={classNames(
                                        "chart",
                                        {hidden: _([WS.INACTIVE, WS.WAITING]).contains(this.state.state)
                                      })} ref="chart"></div>
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
            is_running: function () {
                return _([WS.PENDING, WS.WAITING]).contains(this.state.state);
            },
            componentDidMount: function () {
                this.reset();
                $content.do_layout();
            },
            componentDidUpdate: function (props, state) {
                this.update_targets();
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
            update_targets: function () {
                var name = this.props.data.name,
                    targets = WS.targets[name],
                    i;
                if (!this.state.stats.response_times) {
                    // This can happen when we get an update before anything's
                    // been calculated
                    return;
                }
                for (i = 0; i < this.state.stats.response_times.length; i ++) {
                    target_stats = this.state.stats.response_times[i];
                    if (target_stats.name !== '__all__') {
                        targets[target_stats.name].setState(
                            {stats: target_stats.results});
                    }
                }
            },
            success_stats: function () {
                if (!this.state.stats.response_times) {
                    return null;
                }
                var data = _(
                    this.state.stats.response_times
                    ).where({name: "__all__"}),

                    stats = _(data[0].results).where({code: "200"});
                return stats.length ? stats[0] : null;

            },
            get_points: function () {
                var stats = this.success_stats();
                if (stats) {
                    return {
                        type: stats.chart_x_axis_type,
                        title: stats.chart_x_axis_title,
                        values: _(stats.response_time_points).map(
                                function (x) {
                                    return [x.x, x.y];
                            }),
                        tps_values: _(stats.tps_points).map(
                                function (x) {
                                    return [x.x, x.y];
                            }),
                    }
                } else {
                    return {};
                }
            },
            stop_test: function () {
                WS.call_remote("stop_test",
                               {kwargs:
                                       {uid: this.props.data.uid}
                });
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
                    duration_stats = null;
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

                for (i = 0; i < data.length; i ++) {
                    results.push([data[i].code, data[i].count]);
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
                    that = this,
                    histogram_data = this.histogram_data(),
                    rows, histogram;

                rows = _(data).map(function (item) {
                    var code = item.code,
                        peak = item.peak,
                        nadir = item.nadir,
                        mean = item.mean,
                        median = item.median,
                        percentiles = item.percentiles,
                        std_deviation = item.std_deviation,
                        tps_mean = item.tps_mean;
                    if (code == '__all__') {
                        return null;
                    }
                    return (
                        <tr>
                          <td className={WS.util.status_code_class(code)}>{code}</td>
                          <td className={WS.util.severity(peak)}>{WS.util.format(peak, 2)}</td>
                          <td className={WS.util.severity(nadir)}>{WS.util.format(nadir, 2)}</td>
                          <td className={WS.util.severity(mean)}>{WS.util.format(mean, 2)}</td>
                          <td className={WS.util.severity(median)}>{WS.util.format(median, 2)}</td>
                          <td>{WS.util.format(tps_mean, 2)}</td>
                        </tr>
                    );
                }, this);

                if (histogram_data) {
                    histogram = (
                        <Histogram data={histogram_data} />
                    );
                } else {
                    histogram = null;
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
            },
            histogram_data: function () {
                var data = _(
                    this.props.data
                    ).where({code: "200"});
                if (data.length) {
                    return {values: data[0].histogram_values,
                            edges: data[0].histogram_edges};
                } else {
                    return null;
                }
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
                    row = _.map(data.values, function (value) {
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
        // Used to dynamically re-draw layout here, let's keep the hook for
        // whatever happens in the future
    };
})();
