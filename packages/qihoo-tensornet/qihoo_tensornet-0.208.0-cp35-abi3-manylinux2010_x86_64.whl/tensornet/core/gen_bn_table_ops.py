"""Python wrappers around TensorFlow ops.

This file is MACHINE GENERATED! Do not edit.
Original C++ source file: core/kernels/bn_table_ops_dummy.cc, core/ops/bn_table_ops.cc
"""

import collections

from tensorflow.python import pywrap_tfe as pywrap_tfe
from tensorflow.python.eager import context as _context
from tensorflow.python.eager import core as _core
from tensorflow.python.eager import execute as _execute
from tensorflow.python.framework import dtypes as _dtypes

from tensorflow.python.framework import op_def_registry as _op_def_registry
from tensorflow.python.framework import ops as _ops
from tensorflow.python.framework import op_def_library as _op_def_library
from tensorflow.python.util.deprecation import deprecated_endpoints
from tensorflow.python.util import dispatch as _dispatch
from tensorflow.python.util.tf_export import tf_export

from typing import TypeVar

@_dispatch.add_fallback_dispatch_list
@_dispatch.add_type_based_api_dispatcher
@tf_export('update_moments')
def update_moments(vars, table_handle, name=None):
  r"""pull mean, var, count from parameter server

  Args:
    vars: A list of at least 1 `Tensor` objects with type `resource`.
    table_handle: An `int`.
    name: A name for the operation (optional).

  Returns:
    The created Operation.
  """
  _ctx = _context._context or _context.context()
  tld = _ctx._thread_local_data
  if tld.is_eager:
    try:
      _result = pywrap_tfe.TFE_Py_FastPathExecute(
        _ctx, "UpdateMoments", name, vars, "table_handle", table_handle)
      return _result
    except _core._NotOkStatusException as e:
      _ops.raise_from_not_ok_status(e, name)
    except _core._FallbackException:
      pass
    try:
      _result = _dispatcher_for_update_moments(
          (vars, table_handle, name,), None)
      if _result is not NotImplemented:
        return _result
      return update_moments_eager_fallback(
          vars, table_handle=table_handle, name=name, ctx=_ctx)
    except _core._SymbolicException:
      pass  # Add nodes to the TensorFlow graph.
    except (TypeError, ValueError):
      _result = _dispatch.dispatch(
            update_moments, (), dict(vars=vars, table_handle=table_handle,
                                     name=name)
          )
      if _result is not _dispatch.OpDispatcher.NOT_SUPPORTED:
        return _result
      raise
  else:
    _result = _dispatcher_for_update_moments(
        (vars, table_handle, name,), None)
    if _result is not NotImplemented:
      return _result
  # Add nodes to the TensorFlow graph.
  if not isinstance(vars, (list, tuple)):
    raise TypeError(
        "Expected list for 'vars' argument to "
        "'update_moments' Op, not %r." % vars)
  _attr_N = len(vars)
  table_handle = _execute.make_int(table_handle, "table_handle")
  try:
    _, _, _op, _outputs = _op_def_library._apply_op_helper(
        "UpdateMoments", vars=vars, table_handle=table_handle, name=name)
  except (TypeError, ValueError):
    _result = _dispatch.dispatch(
          update_moments, (), dict(vars=vars, table_handle=table_handle,
                                   name=name)
        )
    if _result is not _dispatch.OpDispatcher.NOT_SUPPORTED:
      return _result
    raise
  return _op
UpdateMoments = tf_export("raw_ops.UpdateMoments")(_ops.to_raw_op(update_moments))
_dispatcher_for_update_moments = update_moments._tf_type_based_dispatcher.Dispatch


def update_moments_eager_fallback(vars, table_handle, name, ctx):
  if not isinstance(vars, (list, tuple)):
    raise TypeError(
        "Expected list for 'vars' argument to "
        "'update_moments' Op, not %r." % vars)
  _attr_N = len(vars)
  table_handle = _execute.make_int(table_handle, "table_handle")
  vars = _ops.convert_n_to_tensor(vars, _dtypes.resource)
  _inputs_flat = list(vars)
  _attrs = ("table_handle", table_handle, "N", _attr_N)
  _result = _execute.execute(b"UpdateMoments", 0, inputs=_inputs_flat,
                             attrs=_attrs, ctx=ctx, name=name)
  _result = None
  return _result


@_dispatch.add_fallback_dispatch_list
@_dispatch.add_type_based_api_dispatcher
@tf_export('bn_statistics_push')
def bn_statistics_push(vars, table_handle, synchronized, name=None):
  r"""save local bn vars to ps

  Args:
    vars: A list of at least 1 `Tensor` objects with type `resource`.
    table_handle: An `int`.
    synchronized: A `bool`.
    name: A name for the operation (optional).

  Returns:
    The created Operation.
  """
  _ctx = _context._context or _context.context()
  tld = _ctx._thread_local_data
  if tld.is_eager:
    try:
      _result = pywrap_tfe.TFE_Py_FastPathExecute(
        _ctx, "BnStatisticsPush", name, vars, "table_handle", table_handle,
        "synchronized", synchronized)
      return _result
    except _core._NotOkStatusException as e:
      _ops.raise_from_not_ok_status(e, name)
    except _core._FallbackException:
      pass
    try:
      _result = _dispatcher_for_bn_statistics_push(
          (vars, table_handle, synchronized, name,), None)
      if _result is not NotImplemented:
        return _result
      return bn_statistics_push_eager_fallback(
          vars, table_handle=table_handle, synchronized=synchronized,
          name=name, ctx=_ctx)
    except _core._SymbolicException:
      pass  # Add nodes to the TensorFlow graph.
    except (TypeError, ValueError):
      _result = _dispatch.dispatch(
            bn_statistics_push, (), dict(vars=vars, table_handle=table_handle,
                                         synchronized=synchronized, name=name)
          )
      if _result is not _dispatch.OpDispatcher.NOT_SUPPORTED:
        return _result
      raise
  else:
    _result = _dispatcher_for_bn_statistics_push(
        (vars, table_handle, synchronized, name,), None)
    if _result is not NotImplemented:
      return _result
  # Add nodes to the TensorFlow graph.
  if not isinstance(vars, (list, tuple)):
    raise TypeError(
        "Expected list for 'vars' argument to "
        "'bn_statistics_push' Op, not %r." % vars)
  _attr_N = len(vars)
  table_handle = _execute.make_int(table_handle, "table_handle")
  synchronized = _execute.make_bool(synchronized, "synchronized")
  try:
    _, _, _op, _outputs = _op_def_library._apply_op_helper(
        "BnStatisticsPush", vars=vars, table_handle=table_handle,
                            synchronized=synchronized, name=name)
  except (TypeError, ValueError):
    _result = _dispatch.dispatch(
          bn_statistics_push, (), dict(vars=vars, table_handle=table_handle,
                                       synchronized=synchronized, name=name)
        )
    if _result is not _dispatch.OpDispatcher.NOT_SUPPORTED:
      return _result
    raise
  return _op
BnStatisticsPush = tf_export("raw_ops.BnStatisticsPush")(_ops.to_raw_op(bn_statistics_push))
_dispatcher_for_bn_statistics_push = bn_statistics_push._tf_type_based_dispatcher.Dispatch


def bn_statistics_push_eager_fallback(vars, table_handle, synchronized, name, ctx):
  if not isinstance(vars, (list, tuple)):
    raise TypeError(
        "Expected list for 'vars' argument to "
        "'bn_statistics_push' Op, not %r." % vars)
  _attr_N = len(vars)
  table_handle = _execute.make_int(table_handle, "table_handle")
  synchronized = _execute.make_bool(synchronized, "synchronized")
  vars = _ops.convert_n_to_tensor(vars, _dtypes.resource)
  _inputs_flat = list(vars)
  _attrs = ("table_handle", table_handle, "N", _attr_N, "synchronized",
  synchronized)
  _result = _execute.execute(b"BnStatisticsPush", 0, inputs=_inputs_flat,
                             attrs=_attrs, ctx=ctx, name=name)
  _result = None
  return _result


@_dispatch.add_fallback_dispatch_list
@_dispatch.add_type_based_api_dispatcher
@tf_export('bn_statistics_pull')
def bn_statistics_pull(vars, table_handle, name=None):
  r"""save local bn vars to ps

  Args:
    vars: A list of at least 1 `Tensor` objects with type `resource`.
    table_handle: An `int`.
    name: A name for the operation (optional).

  Returns:
    The created Operation.
  """
  _ctx = _context._context or _context.context()
  tld = _ctx._thread_local_data
  if tld.is_eager:
    try:
      _result = pywrap_tfe.TFE_Py_FastPathExecute(
        _ctx, "BnStatisticsPull", name, vars, "table_handle", table_handle)
      return _result
    except _core._NotOkStatusException as e:
      _ops.raise_from_not_ok_status(e, name)
    except _core._FallbackException:
      pass
    try:
      _result = _dispatcher_for_bn_statistics_pull(
          (vars, table_handle, name,), None)
      if _result is not NotImplemented:
        return _result
      return bn_statistics_pull_eager_fallback(
          vars, table_handle=table_handle, name=name, ctx=_ctx)
    except _core._SymbolicException:
      pass  # Add nodes to the TensorFlow graph.
    except (TypeError, ValueError):
      _result = _dispatch.dispatch(
            bn_statistics_pull, (), dict(vars=vars, table_handle=table_handle,
                                         name=name)
          )
      if _result is not _dispatch.OpDispatcher.NOT_SUPPORTED:
        return _result
      raise
  else:
    _result = _dispatcher_for_bn_statistics_pull(
        (vars, table_handle, name,), None)
    if _result is not NotImplemented:
      return _result
  # Add nodes to the TensorFlow graph.
  if not isinstance(vars, (list, tuple)):
    raise TypeError(
        "Expected list for 'vars' argument to "
        "'bn_statistics_pull' Op, not %r." % vars)
  _attr_N = len(vars)
  table_handle = _execute.make_int(table_handle, "table_handle")
  try:
    _, _, _op, _outputs = _op_def_library._apply_op_helper(
        "BnStatisticsPull", vars=vars, table_handle=table_handle, name=name)
  except (TypeError, ValueError):
    _result = _dispatch.dispatch(
          bn_statistics_pull, (), dict(vars=vars, table_handle=table_handle,
                                       name=name)
        )
    if _result is not _dispatch.OpDispatcher.NOT_SUPPORTED:
      return _result
    raise
  return _op
BnStatisticsPull = tf_export("raw_ops.BnStatisticsPull")(_ops.to_raw_op(bn_statistics_pull))
_dispatcher_for_bn_statistics_pull = bn_statistics_pull._tf_type_based_dispatcher.Dispatch


def bn_statistics_pull_eager_fallback(vars, table_handle, name, ctx):
  if not isinstance(vars, (list, tuple)):
    raise TypeError(
        "Expected list for 'vars' argument to "
        "'bn_statistics_pull' Op, not %r." % vars)
  _attr_N = len(vars)
  table_handle = _execute.make_int(table_handle, "table_handle")
  vars = _ops.convert_n_to_tensor(vars, _dtypes.resource)
  _inputs_flat = list(vars)
  _attrs = ("table_handle", table_handle, "N", _attr_N)
  _result = _execute.execute(b"BnStatisticsPull", 0, inputs=_inputs_flat,
                             attrs=_attrs, ctx=ctx, name=name)
  _result = None
  return _result


