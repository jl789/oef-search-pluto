py_library(
    name = "mocks",
    srcs = glob(["*Mock.py"]),
    deps = [
        "//dap_api/src/python:dap_api",
        "//dap_api/src/protos:py_dap_api_pb",
    ],
)

py_library(
    name = "classes",
    srcs = glob(["*Test.py"]),
    deps = [
        "//dap_api/src/python:dap_api",
        "//dap_api/src/protos:py_dap_api_pb",
        "//dap_2d_geo/src/python:dap_2d_geo",
        "//fetch_teams/oef_core_protocol:py_oef_protocol",
    ],
)

py_test(
    name = "tests",
    main = "tests.py",
    srcs = [
         "tests.py",
    ],
    deps = [
        "//dap_api/src/python:dap_api",
        "//ai_search_engine/src/python:search_engine",
        "//dap_api/experimental/python:experimental_lib",
        "//dap_attribute_store/src/python:dap_attribute_store",
        "//dap_in_memory/src/python:dap_in_memory",
        "//dap_api/src/protos:py_dap_api_pb",
        "//dap_2d_geo/src/python:dap_2d_geo",
        ":mocks",
        ":classes",
    ]
)
