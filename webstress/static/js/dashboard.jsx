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
            render: function () {
                var data = this.props.data,
                    targets = data.targets.map(function (target) {
                        return (<Target data={target} />);
                    });
                WS.targets[data.name] = {};
                return (
                    <div className="config grid-item">
                      <h1 className="config-name">{data.name}</h1>
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
            }
        }),
        Target = React.createClass({
            getInitialState: function () {
                return {results: [], average: null};
            },
            render: function () {
                var data = this.props.data;
                var params = this.props.data.params.map(function (param) {
                        return (<Param data={param} />);
                    }),
                    response_codes = (
                            <ResponseCodes data={this.state.results} />
                    ),
                    that = this;

                // Make this target accessible elsewhere
                WS.targets[data.owner][data.name] = this;
                return (
                    <div className="target">
                      <div><h2>Name:</h2> {data.name}</div>
                      <input className="run-button"
                             type="button" value="Run Test"
                             onClick={this.run_test} />
                      <div><h2>Hits:</h2> {data.hits}</div>
                      <div><h2>URL:</h2> {data.base_url}</div>
                      <div><h2>Params:</h2> {params}</div>
                      <div><h2>Average Duration:</h2> {this.state.average || ''}</div>
                      {response_codes}
                    </div>
                );
            },
            run_test: function () {
                var data = this.props.data,
                    uid = WS.get_uid();
                WS.call_remote("launch_test",
                    {kwargs:
                        {_uid: uid,
                         requested_targets:
                            [{"name": data.name, "config": data.owner}]}
                    });
                WS.active_tests[uid] = {target: this};
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
                    head = [], row = [];

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
                    head.push(<th>{results[i][0]}</th>);
                    row.push(<td>{results[i][1]}</td>);
                }

                return (
                    <div>
                        <h2>Response Codes</h2>
                        <table className="results">
                            <thead>{head}</thead>
                            <tbody>
                                <tr>{row}</tr>
                            </tbody>
                        </table>
                    </div>
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
            columnWidth: 10,
            gutter: 10
        });
    };
})();
