def setup_parser(root_parser):
    root_parser.add_argument('--host', type=str, help='服务地址')
    root_parser.add_argument('--sign-download-api', type=str, help='sign-download-api')
    root_parser.add_argument('--meta-download-api', type=str, help='meta-download-api')
    root_parser.add_argument('--auth-login-api', type=str, help='auth-login-api')

    # runtime
    root_parser.add_argument('--runtime', type=str, default="ks3util",  help='runtime')
    root_parser.add_argument('--debug', type=bool, default=False,  help='debug')
