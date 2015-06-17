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
                return {state: WS.INACTIVE, results: [], average: null};
            },
            render: function () {
                var data = this.props.data,
                    targets = data.targets.map(function (target) {
                        return (<Target data={target} />);
                    }),
                    response_codes,
                    state, tps, average;
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


                if (this.state.average) {
                    average = (
                        <div><h2>Average Duration:</h2> {this.state.average}</div>
                        );
                } else {
                    average = '';
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
                      </tr>
                      </tbody>
                      </table>
                      <div className="report">
                        {average}
                        {response_codes}
                      </div>
                      {tps}
                      <div>
                        <h2>Targets ({targets.length})</h2>
                        {targets}
                      </div>
                    </div>
                );
            },
            componentDidMount: function () {
                $content.do_layout();
            },
            componentDidUpdate: function () {
                $content.do_layout();
            },
            reset: function () {
                this.setState(this.getInitialState());
            },
            run_test: function () {
                var data = this.props.data,
                    config_uid = WS.get_uid(),
                    target_uid,
                    key, targets = [];

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
                return {results: [], average: null};
            },
            render: function () {
                var data = this.props.data,
                    params = this.props.data.params.map(function (param) {
                        return (<Param data={param} />);
                    }),
                    response_codes = (
                            <ResponseCodes data={this.state.results} />
                    ),
                    that = this,
                    average;

                // Make this target accessible elsewhere
                WS.targets[data.owner][data.name] = this;

                if (this.state.average) {
                    average = (
                        <div><h2>Average Duration:</h2> {this.state.average}</div>
                        );
                } else {
                    average = '';
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
                      </tbody>
                      </table>
                      <div><h2>Params:</h2> {params}</div>
                      {average}
                      {response_codes}
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
        Param = React.createClass({
            render: function () {
                var data = this.props.data;
                return (
                    <div>
                        <div>Key: {data.key}</div>
                        <div>Value: {data.value}</div>
                    </div>
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
                    cls = "code-" + results[i][0].substr(0, 1);
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
            columnWidth: 50,
            gutter: 10
        });
    };
})();
