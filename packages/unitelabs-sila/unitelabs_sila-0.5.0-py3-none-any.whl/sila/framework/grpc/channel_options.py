import typing_extensions as typing

ChannelOptions = typing.TypedDict(
    "ChannelOptions",
    {
        "grpc.census": typing.Annotated[
            bool,
            typing.Doc("""Whether to enable census for tracing and stats collection."""),
        ],
        "grpc.loadreporting": typing.Annotated[
            bool,
            typing.Doc("""Whether to enable load reporting."""),
        ],
        "grpc.server_call_metric_recording": typing.Annotated[
            bool,
            typing.Doc("""Whether to enable call metric recording."""),
        ],
        "grpc.minimal_stack": typing.Annotated[
            bool,
            typing.Doc("""
                Request that optional features default to off (regardless of what
                they usually default to) - to enable tight control over what gets
                enabled
            """),
        ],
        "grpc.max_concurrent_streams": typing.Annotated[
            int,
            typing.Doc("""Maximum number of concurrent incoming streams to allow on a http2 connection."""),
        ],
        "grpc.max_receive_message_length": typing.Annotated[
            int,
            typing.Doc("""Maximum message length in bytes that the channel can receive. -1 means unlimited."""),
        ],
        "grpc.max_send_message_length": typing.Annotated[
            int,
            typing.Doc("""Maximum message length in bytes that the channel can send. -1 means unlimited."""),
        ],
        "grpc.max_connection_idle_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                Maximum time in milliseconds that a channel may have no outstanding rpcs,
                after which the server will close the connection. INT_MAX means unlimited.
                """
            ),
        ],
        "grpc.max_connection_age_ms": typing.Annotated[
            int,
            typing.Doc("""Maximum time in milliseconds that a channel may exist. INT_MAX means unlimited."""),
        ],
        "grpc.max_connection_age_grace_ms": typing.Annotated[
            int,
            typing.Doc(
                """Grace period in milliseconds after the channel reaches its max age. INT_MAX means unlimited."""
            ),
        ],
        "grpc.client_idle_timeout_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                Timeout in milliseconds after the last RPC finishes on the client channel at which the channel
                goes back into IDLE state. INT_MAX means unlimited and timeout must be greater than 1 second.
                Defaults to 30 minutes.
                """
            ),
        ],
        "grpc.per_message_compression": typing.Annotated[
            bool,
            typing.Doc(
                """
                Enable/disable support for per-message compression. Defaults to `True`,
                unless `grpc.minimal_stack` is enabled, in which case it defaults to `False`.
                """
            ),
        ],
        "grpc.per_message_decompression": typing.Annotated[
            bool,
            typing.Doc(
                """
                Experimental. Enable/disable support for per-message decompression. Defaults to `True`.
                If disabled, decompression will not be performed and the application will see the
                compressed message in the byte buffer.
                """
            ),
        ],
        "grpc.http2.initial_sequence_number": typing.Annotated[
            int,
            typing.Doc("""Initial stream ID for http2 transports."""),
        ],
        "grpc.http2.lookahead_bytes": typing.Annotated[
            int,
            typing.Doc(
                """
                Amount in bytes to read ahead on individual streams. Defaults to 64kb, larger
                values can help throughput on high-latency connections. NOTE: at some point
                we'd like to auto-tune this, and this parameter will become a no-op.
                """
            ),
        ],
        "grpc.http2.hpack_table_size.decoder": typing.Annotated[
            int,
            typing.Doc("""How much memory in bytes to use for hpack decoding."""),
        ],
        "grpc.http2.hpack_table_size.encoder": typing.Annotated[
            int,
            typing.Doc("""How much memory in bytes to use for hpack encoding."""),
        ],
        "grpc.http2.max_frame_size": typing.Annotated[
            int,
            typing.Doc(
                """
                How big a frame are we willing to receive via HTTP2. Min 16384, max 16777215.
                Larger values give lower CPU usage for large messages, but more head of line
                blocking for small messages.
                """
            ),
        ],
        "grpc.http2.bdp_probe": typing.Annotated[
            bool,
            typing.Doc("""Should BDP probing be performed?"""),
        ],
        "grpc.http2.min_ping_interval_without_data_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                Minimum allowed time in milliseconds between a server receiving successive
                ping frames without sending any data/header frame.
                """
            ),
        ],
        "grpc.server_max_unrequested_time_in_server": typing.Annotated[
            int,
            typing.Doc(
                """
                Maximum time to allow a request to be: (1) received by the server, but (2)
                not requested by a RequestCall (in the completion queue based API) before
                the request is cancelled.
                """
            ),
        ],
        "grpc.http2_scheme": typing.Annotated[
            int,
            typing.Doc("""Whether to override the http2 :scheme header."""),
        ],
        "grpc.http2.max_pings_without_data": typing.Annotated[
            int,
            typing.Doc(
                """
                How many pings can the client send before needing to send a data/header frame?
                (0 indicates that an infinite number of pings can be sent without sending a data
                frame or header frame). If experimental "max_pings_wo_data_throttle" is enabled,
                instead of pings being completely blocked, they are throttled.
                """
            ),
        ],
        "grpc.http2.max_ping_strikes": typing.Annotated[
            int,
            typing.Doc(
                """
                How many misbehaving pings the server can bear before sending goaway and closing
                the transport? (0 indicates that the server can bear an infinite number of misbehaving pings).
                """
            ),
        ],
        "grpc.http2.write_buffer_size": typing.Annotated[
            int,
            typing.Doc(
                """
                How much data are we willing to queue up per stream if GRPC_WRITE_BUFFER_HINT is set?
                This is an upper bound.
                """
            ),
        ],
        "grpc.http2.true_binary": typing.Annotated[
            bool,
            typing.Doc("""Should we allow receipt of true-binary data on http2 connections? Defaults to `True`."""),
        ],
        "grpc.experimental.http2.enable_preferred_frame_size": typing.Annotated[
            int,
            typing.Doc(
                """
                Experimental: determines whether the preferred crypto frame size http2 setting
                is sent to the peer at startup. If set to 0 (false), the preferred frame
                size is not sent to the peer. Otherwise it sends a default preferred crypto frame
                size value of 4GB to the peer at the startup of each connection. Defaults to 0.
                """
            ),
        ],
        "grpc.keepalive_time_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                After a duration of this time the client/server pings its peer to see if the
                transport is still alive. Int valued, milliseconds.
                """
            ),
        ],
        "grpc.keepalive_timeout_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                A duration of this time in milliseconds, after which if the keepalive ping sender does
                not receive the ping ack, it will close the transport.
                """
            ),
        ],
        "grpc.keepalive_permit_without_calls": typing.Annotated[
            bool,
            typing.Doc(
                """
                Whether it is permissible to send keepalive pings from the client without any outstanding streams.
                Int valued, 0(false)/1(true).
                """
            ),
        ],
        "grpc.default_authority": typing.Annotated[
            str, typing.Doc("""Default authority to pass if none specified on call construction. A string.""")
        ],
        "grpc.primary_user_agent": typing.Annotated[
            str,
            typing.Doc(
                """Primary user agent: goes at the start of the user-agent metadata sent on each request. A string."""
            ),
        ],
        "grpc.secondary_user_agent": typing.Annotated[
            str,
            typing.Doc(
                """Secondary user agent: goes at the end of the user-agent metadata sent on each request. A string."""
            ),
        ],
        "grpc.min_reconnect_backoff_ms": typing.Annotated[
            int, typing.Doc("""The minimum time between subsequent connection attempts, in ms""")
        ],
        "grpc.max_reconnect_backoff_ms": typing.Annotated[
            int, typing.Doc("""The maximum time between subsequent connection attempts, in ms""")
        ],
        "grpc.initial_reconnect_backoff_ms": typing.Annotated[
            int, typing.Doc("""The time between the first and second connection attempts, in ms""")
        ],
        "grpc.dns_min_time_between_resolutions_ms": typing.Annotated[
            int, typing.Doc("""Minimum amount of time between DNS resolutions, in ms""")
        ],
        "grpc.server_handshake_timeout_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                The timeout used on servers for finishing handshaking on an incoming connection.
                Defaults to 120 seconds.
                """
            ),
        ],
        "grpc.ssl_target_name_override": typing.Annotated[
            str,
            typing.Doc(
                """
                This *should* be used for testing only. The caller of the secure_channel_create
                functions may override the target name used for SSL host name checking using this
                channel argument which is of type GRPC_ARG_STRING. If this argument is not specified,
                the name used for SSL host name checking will be the target parameter (assuming that
                the secure channel is an SSL channel). If this parameter is specified and the
                underlying is not an SSL channel, it will just be ignored.
                """
            ),
        ],
        "grpc.ssl_session_cache": typing.Annotated[
            object,
            typing.Doc(
                """
                If non-zero, a pointer (of type grpc_ssl_session_cache*) to a session cache.
                (use grpc_ssl_session_cache_arg_vtable() to fetch an appropriate pointer arg vtable)
                """
            ),
        ],
        "grpc.tsi.max_frame_size": typing.Annotated[
            bool, typing.Doc("""If non-zero, it will determine the maximum frame size used by TSI's frame protector.""")
        ],
        "grpc.max_metadata_size": typing.Annotated[
            int,
            typing.Doc(
                """
                Maximum metadata size (soft limit), in bytes. Note this limit applies to the max sum
                of all metadata key-value entries in a batch of headers. Some random sample of requests
                between this limit and `GRPC_ARG_ABSOLUTE_MAX_METADATA_SIZE` will be rejected. Defaults
                to maximum of 8 KB and `GRPC_ARG_ABSOLUTE_MAX_METADATA_SIZE` * 0.8 (if set).
                """
            ),
        ],
        "grpc.absolute_max_metadata_size": typing.Annotated[
            int,
            typing.Doc(
                """
                Maximum metadata size (hard limit), in bytes. Note this limit applies to the max sum of
                all metadata key-value entries in a batch of headers. All requests exceeding this limit
                will be rejected. Defaults to maximum of 16 KB and `GRPC_ARG_MAX_METADATA_SIZE` * 1.25 (if set).
                """
            ),
        ],
        "grpc.so_reuseport": typing.Annotated[
            bool, typing.Doc("""If non-zero, allow the use of SO_REUSEPORT if it's available (default 1)""")
        ],
        "grpc.resource_quota": typing.Annotated[
            bool,
            typing.Doc(
                """
                If non-zero, a pointer (of type grpc_resource_quota*) to a buffer pool.
                (use grpc_resource_quota_arg_vtable() to fetch an appropriate pointer arg vtable)
                """
            ),
        ],
        "grpc.expand_wildcard_addrs": typing.Annotated[
            bool, typing.Doc("""If non-zero, expand wildcard addresses to a list of local addresses.""")
        ],
        "grpc.service_config": typing.Annotated[
            str,
            typing.Doc(
                """
                Service config data in JSON form. This value will be ignored if the
                name resolver returns a service config.
                """
            ),
        ],
        "grpc.service_config_disable_resolution": typing.Annotated[
            bool, typing.Doc("""Disable looking up the service config via the name resolver.""")
        ],
        "grpc.lb_policy_name": typing.Annotated[str, typing.Doc("""LB policy name.""")],
        "grpc.lb.ring_hash.ring_size_cap": typing.Annotated[
            int,
            typing.Doc(
                """
                Cap for ring size in the ring_hash LB policy.  The min and max ring size values
                set in the LB policy config will be capped to this value. Defaults to 4096.
                """
            ),
        ],
        "grpc.socket_mutator": typing.Annotated[
            object, typing.Doc("""The grpc_socket_mutator instance that set the socket options. A pointer.""")
        ],
        "grpc.socket_factory": typing.Annotated[
            object, typing.Doc("""The grpc_socket_factory instance to create and bind sockets. A pointer.""")
        ],
        "grpc.max_channel_trace_event_memory_per_node": typing.Annotated[
            int,
            typing.Doc(
                """
                The maximum amount of memory used by trace events per channel trace node.
                Once the maximum is reached, subsequent events will evict the oldest events
                from the buffer. The unit for this knob is bytes. Setting it to zero causes
                channel tracing to be disabled.
                """
            ),
        ],
        "grpc.enable_channelz": typing.Annotated[
            bool,
            typing.Doc(
                """
                If non-zero, gRPC library will track stats and information at at per channel level.
                Disabling channelz naturally disables channel tracing. Defaults to true (enabled).
                """
            ),
        ],
        "grpc.use_cronet_packet_coalescing": typing.Annotated[
            bool, typing.Doc("""If non-zero, Cronet transport will coalesce packets to fewer frames when possible.""")
        ],
        "grpc.experimental.tcp_read_chunk_size": typing.Annotated[
            int,
            typing.Doc(
                """
                Channel arg (integer) setting how large a slice to try and read from the wire each
                time recvmsg (or equivalent) is called. Defaults to 8191.
                """
            ),
        ],
        "grpc.experimental.tcp_min_read_chunk_size": typing.Annotated[int, typing.Doc("""""")],
        "grpc.experimental.tcp_max_read_chunk_size": typing.Annotated[int, typing.Doc("""""")],
        "grpc.experimental.tcp_tx_zerocopy_enabled": typing.Annotated[
            bool,
            typing.Doc(
                """TCP TX Zerocopy enable state: zero is disabled, non-zero is enabled. By default, it is disabled."""
            ),
        ],
        "grpc.experimental.tcp_tx_zerocopy_send_bytes_threshold": typing.Annotated[
            int,
            typing.Doc(
                """
                TCP TX Zerocopy send threshold: only zerocopy if >= this many bytes sent.
                Defaults to 16KB.
                """
            ),
        ],
        "grpc.experimental.tcp_tx_zerocopy_max_simultaneous_sends": typing.Annotated[
            int,
            typing.Doc(
                """
                TCP TX Zerocopy max simultaneous sends: limit for maximum number of pending calls
                to tcp_write() using zerocopy. A tcp_write() is considered pending until the kernel
                performs the zerocopy-done callback for all sendmsg() calls issued by the tcp_write().
                Defaults to 4.
                """
            ),
        ],
        "grpc.tcp_receive_buffer_size": typing.Annotated[
            int, typing.Doc("""Overrides the TCP socket receive buffer size, SO_RCVBUF.""")
        ],
        "grpc.grpclb_call_timeout_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                Timeout in milliseconds to use for calls to the grpclb load balancer.
                If 0 or unset, the balancer calls will have no deadline.
                """
            ),
        ],
        "grpc.TEST_ONLY_DO_NOT_USE_IN_PROD.xds_bootstrap_config": typing.Annotated[
            str,
            typing.Doc(
                """
                Specifies the xDS bootstrap config as a JSON string.
                FOR TESTING PURPOSES ONLY -- DO NOT USE IN PRODUCTION. This option allows controlling the
                bootstrap configuration on a per-channel basis, which is useful in tests.  However, this
                results in having a separate xDS client instance per channel rather than using the global
                instance, which is not the intended way to use xDS. Currently, this will (a) add unnecessary
                load on the xDS server and (b) break use of CSDS, and there may be additional side effects
                in the future.
                """
            ),
        ],
        "grpc.grpclb_fallback_timeout_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                Timeout in milliseconds to wait for the serverlist from the grpclb load balancer
                before using fallback backend addresses from the resolver. If 0, enter fallback
                mode immediately. Defaults to 10000.
                """
            ),
        ],
        "grpc.experimental.grpclb_channel_args": typing.Annotated[
            object,
            typing.Doc(
                """
                Experimental Arg. Channel args to be used for the control-plane channel created to the
                grpclb load balancers. This is a pointer arg whose value is a grpc_channel_args object.
                If unset, most channel args from the parent channel will be propagated to the grpclb channel.
                """
            ),
        ],
        "grpc.priority_failover_timeout_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                Timeout in milliseconds to wait for the child of a specific priority to complete its
                initial connection attempt before the priority LB policy fails over to the next priority.
                Defaults to 10 seconds.
                """
            ),
        ],
        "grpc.workaround.cronet_compression": typing.Annotated[
            bool, typing.Doc("""If non-zero, grpc server's cronet compression workaround will be enabled""")
        ],
        "grpc.optimization_target": typing.Annotated[
            typing.Literal["latency", "blend", "throughput"],
            typing.Doc(
                """
                String defining the optimization target for a channel. Can be: "latency"
                 - attempt to minimize latency at the cost of throughput "blend"
                 - try to balance latency and throughput "throughput"
                 - attempt to maximize throughput at the expense of latency.
                In the current implementation "blend" is equivalent to "latency".
                Defaults to "blend".
                """
            ),
        ],
        "grpc.enable_retries": typing.Annotated[
            bool,
            typing.Doc(
                """
                Enables retry functionality.  Defaults to true.  When enabled, transparent
                retries will be performed as appropriate, and configurable retries are
                enabled when they are configured via the service config. For details,
                see:   https://github.com/grpc/proposal/blob/master/A6-client-retries.md
                NOTE: Hedging functionality is not yet implemented, so those fields in the
                service config will currently be ignored.
                See also the GRPC_ARG_EXPERIMENTAL_ENABLE_HEDGING arg below.
                """
            ),
        ],
        "grpc.experimental.enable_hedging": typing.Annotated[
            bool,
            typing.Doc(
                """
                Enables hedging functionality, as described in:
                https://github.com/grpc/proposal/blob/master/A6-client-retries.md
                Defaults to false, since this functionality is currently not yet fully
                implemented. NOTE: This channel arg is experimental and will eventually
                be removed. Once hedging functionality has been implemented and proves stable,
                this arg will be removed, and the hedging functionality will be enabled via
                the GRPC_ARG_ENABLE_RETRIES arg above.
                """
            ),
        ],
        "grpc.per_rpc_retry_buffer_size": typing.Annotated[
            int, typing.Doc("""Per-RPC retry buffer size, in bytes. Default is 256 KiB.""")
        ],
        "grpc.mobile_log_context": typing.Annotated[
            object,
            typing.Doc(
                """Channel arg that carries the bridged objective c object for custom metrics logging filter."""
            ),
        ],
        "grpc.disable_client_authority_filter": typing.Annotated[
            bool, typing.Doc("""If non-zero, client authority filter is disabled for the channel""")
        ],
        "grpc.enable_http_proxy": typing.Annotated[
            bool, typing.Doc("""If set to zero, disables use of http proxies. Enabled by default.""")
        ],
        "grpc.http_proxy": typing.Annotated[
            bool,
            typing.Doc(
                """
                Channel arg to set http proxy per channel. If set, the channel arg value will be
                preferred over the environment variable settings.
                """
            ),
        ],
        "grpc.address_http_proxy": typing.Annotated[
            str,
            typing.Doc(
                """
                Specifies an HTTP proxy to use for individual addresses. The proxy must be
                specified as an IP address, not a DNS name. If set, the channel arg value
                will be preferred over the environment variable settings.
                """
            ),
        ],
        "grpc.address_http_proxy_enabled_addresses": typing.Annotated[
            str,
            typing.Doc(
                """Comma separated list of addresses or address ranges that are behind the address HTTP proxy."""
            ),
        ],
        "grpc.surface_user_agent": typing.Annotated[
            bool,
            typing.Doc(
                """
                If set to non zero, surfaces the user agent string to the server.
                Defaults to true (user agent is surfaced).
                """
            ),
        ],
        "grpc.inhibit_health_checking": typing.Annotated[
            bool, typing.Doc("""If set, inhibits health checking (which may be enabled via the service config.)""")
        ],
        "grpc.dns_enable_srv_queries": typing.Annotated[
            bool,
            typing.Doc(
                """
                If enabled, the channel's DNS resolver queries for SRV records. This is useful only when
                using the "grpclb" load balancing policy, as described in the following documents:
                https://github.com/grpc/proposal/blob/master/A5-grpclb-in-dns.md
                https://github.com/grpc/proposal/blob/master/A24-lb-policy-config.md
                https://github.com/grpc/proposal/blob/master/A26-grpclb-selection.md
                Note that this works only with the "ares" DNS resolver; it isn't supported by the
                "native" DNS resolver.
                """
            ),
        ],
        "grpc.dns_ares_query_timeout": typing.Annotated[
            bool,
            typing.Doc(
                """
                If set, determines an upper bound on the number of milliseconds that the c-ares
                based DNS resolver will wait on queries before cancelling them. The default value
                is 120,000. Setting this to "0" will disable the overall timeout entirely. Note
                that this doesn't include internal c-ares timeouts/backoff/retry logic, and so the
                actual DNS resolution may time out sooner than the value specified here.
                """
            ),
        ],
        "grpc.use_local_subchannel_pool": typing.Annotated[
            bool,
            typing.Doc(
                """
                If set, uses a local subchannel pool within the channel. Otherwise, uses the global subchannel pool.
                """
            ),
        ],
        "grpc.channel_pooling_domain": typing.Annotated[
            str, typing.Doc("""gRPC Objective-C channel pooling domain string.""")
        ],
        "grpc.channel_id": typing.Annotated[int, typing.Doc("""gRPC Objective-C channel pooling id.""")],
        "grpc.authorization_policy_provider": typing.Annotated[
            bool,
            typing.Doc(
                """
                Channel argument for grpc_authorization_policy_provider. If present, enables gRPC authorization check.
                """
            ),
        ],
        "grpc.experimental.server_config_change_drain_grace_time_ms": typing.Annotated[
            int,
            typing.Doc(
                """
                EXPERIMENTAL. Updates to a server's configuration from a config fetcher (for example,
                listener updates from xDS) cause all older connections to be gracefully shut down
                (i.e., "drained") with a grace period configured by this channel arg. Int valued, milliseconds.
                Defaults to 10 minutes.
                """
            ),
        ],
        "grpc.dscp": typing.Annotated[
            int,
            typing.Doc(
                """
                Configure the Differentiated Services Code Point used on outgoing packets.
                Integer value ranging from 0 to 63.
                """
            ),
        ],
        "grpc.happy_eyeballs_connection_attempt_delay_ms": typing.Annotated[
            int,
            typing.Doc("""Connection Attempt Delay for use in Happy Eyeballs, in milliseconds. Defaults to 250ms."""),
        ],
        "grpc.event_engine_use_memory_allocator_factory": typing.Annotated[
            object,
            typing.Doc(
                """
                It accepts a MemoryAllocatorFactory as input and If specified, it forces the default
                event engine to use memory allocators created using the provided factory.
                """
            ),
        ],
        "grpc.max_allowed_incoming_connections": typing.Annotated[
            int,
            typing.Doc(
                """
                Configure the max number of allowed incoming connections to the server. If unspecified, it is unlimited.
                """
            ),
        ],
        "grpc.experimental.stats_plugins": typing.Annotated[
            object, typing.Doc("""Configure per-channel or per-server stats plugins.""")
        ],
        "grpc.security_frame_allowed": typing.Annotated[
            bool, typing.Doc("""If non-zero, allow security frames to be sent and received.""")
        ],
    },
    total=False,
)
