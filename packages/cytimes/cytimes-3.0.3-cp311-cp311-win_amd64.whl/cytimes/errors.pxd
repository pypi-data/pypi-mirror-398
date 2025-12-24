# cython: language_level=3

# Raise error helpers
cpdef bint raise_error(object exc, object cls=?, str input_msg=?, str error_msg=?, Exception tb_exc=?)
cpdef bint raise_configs_token_error(object cls=?, str error_msg=?, Exception tb_exc=?)
cpdef bint raise_configs_value_error(object cls=?, str error_msg=?, Exception tb_exc=?)
cpdef bint raise_parser_failed_error(object cls=?, str error_msg=?, Exception tb_exc=?)
cpdef bint raise_argument_error(object cls=?, str input_msg=?, str error_msg=?, Exception tb_exc=?)
cpdef bint raise_type_error(object cls=?, str input_msg=?, str error_msg=?, Exception tb_exc=?)
