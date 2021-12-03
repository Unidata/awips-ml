FROM tensorflow/serving:latest-devel
MAINTAINER "Rio McMahon" <rmcmahon@ucar.edu>

# create dummy model using simple script
COPY ./tfc/etc/build_dummy_model.py /
RUN python /build_dummy_model.py
CMD tensorflow_model_server --port=8500 --rest_api_port=8501 --model_name=model --model_base_path=/models/model

# alternative option is to copy in a pre-saved model
# input path to specific model - tfc looks for model at specific path
# set the ENV variable with a path like ./tfc/models/[model name]
# note that the tensorflow server requires a model version number so the full path should be something like ./tfc/models/[model name]/[version number]/[model saved weights]
# ENV MODEL_PATH [input path to model here]
# COPY $MODEL_PATH /models/model
