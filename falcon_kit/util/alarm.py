"""Special handling for exceptions, for the UI.
"""

def alarm(e):
    """
    Write traceback into PBFALCON_ERRFILE (until we stop using pbfalcon).
    Write a special JSON object expected by pbcommand.models.common.
    """
    import datetime
    import os
    import traceback
    import uuid
    from ..io import serialize

    tb = traceback.format_exc()
    # pbfalcon wants us to write errs here.
    errfile = os.environ.get('PBFALCON_ERRFILE')
    if errfile:
        with open(errfile, 'w') as ofs:
            ofs.write(tb)  # in python3, this will include the entire chain of exceptions

    # this is propagated to SMRT Link UI
    # see PacBioAlarm class in pbcommand.models.common for details -- nat
    special = [
        {
            "exception": e.__class__.__name__,
            "info": tb,
            "message": str(e) + "\n" + str(e.__cause__),
            "name": e.__class__.__name__,
            "severity": "ERROR",
            "owner": "python3",
            "createdAt": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "id": str(uuid.uuid4())
        }
    ]
    # Technically, we should add "causes" recursively, but "info" will include the full chain anyway.

    serialize('alarms.json', special)
