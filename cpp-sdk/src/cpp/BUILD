cc_library(
    name = "lib",
    visibility = [
        "//visibility:public",
    ],
    srcs = [
        "Listner.cpp"
    ],
    hdrs = [
         "Transport.hpp",
         "DapInterface.hpp",
         "DapException.hpp",
         "Listener.hpp",
         "CircularBuffer.hpp",
         "char_array_buffer.hpp",
         "TransportFactory.hpp",
         "asio_inc.hpp",
         "proto.hpp",
         "DapServer.hpp"
         ],
    deps = [
        "@boost//:asio",
        "//dap_api/src/protos:cc_dap_api_pb",
        "//api/src/proto/core:cc_api_pb",
        "//network/src/proto:cc_network_pb",
    ],
)

cc_binary(
    name = "server",
    visibility = [
        "//visibility:public",
    ],
    srcs = glob(["main.cpp"]),
    deps = [
        ":lib",
        #"@fetch_oef_search_language//:lib"
    ],
    #linkshared = True,
    #linkstatic = True,
)

