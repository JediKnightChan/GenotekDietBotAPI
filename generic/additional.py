from django.http import JsonResponse
from django.conf import settings
import traceback


def api_safe_run(logger, token_required=False):
    def decorator(func):
        def func_wrapper(request, *args, **kwargs):
            try:
                if token_required:
                    if request.POST.get('token', None) != settings.BOTMOTHER_TOKEN:
                        logger.error("{}: Token mismatched. Get {}, expected {}".format(func.__name__,
                                                                                        request.POST.get('token', None),
                                                                                        settings.BOTMOTHER_TOKEN))
                        return JsonResponse({'error': 'Token mismatched', 'success': False}, status=400)
                return func(request, *args, **kwargs)
            except ZeroDivisionError:
                logger.error("{}: ZeroDivisionError. Body request is {}".format(func.__name__, request.body))
                return JsonResponse({'error': 'ZeroDivisionError', 'success': False}, status=400)
            except KeyError as e:
                logger.error("{}: {} error ({}). Body request is {}.\b Traceback: {}".format(func.__name__,
                                                                                             type(e),
                                                                                             e,
                                                                                             request.body,
                                                                                             traceback.format_exc()
                                                                                             ))
                return JsonResponse({'error': 'KeyError', 'success': False}, status=400)
            except Exception as e:
                logger.error("{}: Unknown {} error ({}). Body request is {}. Traceback: {}".format(func.__name__,
                                                                                                   type(e),
                                                                                                   e,
                                                                                                   request.body,
                                                                                                   traceback.format_exc()
                                                                                                   ))
                return JsonResponse({'error': 'Unknown error', 'success': False}, status=500)
        return func_wrapper
    return decorator
