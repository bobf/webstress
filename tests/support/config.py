standard = """
targets:
  - url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
      - key: arg2
        value:
          fake: name
  - url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
"""
