def postproc(model_output):
    '''
    Function for custom user postprocessing.

    Takes `model_output` which is a numpy array corresponding to the machine
    learning model output. `postproc` should return a numpy array with similar
    dimensions for transmission to and ingestion by the EDEX container.
    '''
    # input custom code here...
    return model_output
