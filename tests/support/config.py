std_sample_config = """
targets:
  - name: test1
    url: http://localhost:8000/
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
    url: http://localhost:8000/
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
    url: http://localhost:8000/
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
    url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
"""
