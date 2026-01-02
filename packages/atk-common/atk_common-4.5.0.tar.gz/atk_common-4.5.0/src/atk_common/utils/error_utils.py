def get_message(error):
    if hasattr(error, 'message'):
        return str(error.message)
    else:
        return str(error)
