from __future__ import annotations


__all__ = ('session_logger', 'router_logger', 'dispatcher_logger', 'runner_logger')


from logging import getLogger


session_logger = getLogger('funpaybotengine.session')
router_logger = getLogger('funpaybotengine.router')
dispatcher_logger = getLogger('funpaybotengine.dispatcher')
runner_logger = getLogger('funpaybotengine.runner')
