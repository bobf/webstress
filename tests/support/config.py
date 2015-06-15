std_sample_config = """
targets:
  - name: test1
    base_url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
      - key: arg2
        value:
          fake: name

  - name: test2
    base_url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
"""

std_sample_config_2 = """
targets:
  - name: test1
    base_url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
      - key: arg2
        value:
          fake: name

  - name: test2
    base_url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
"""

non_unique_sample_config = """
targets:
  - name: test1
    base_url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
      - key: arg2
        value:
          fake: name

  - name: test1
    base_url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
"""

params_in_url_and_specified_config = """
targets:
  - name: test1
    base_url: http://localhost:8000/?foo=bar&bar=baz
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg2
        value: 20
"""
